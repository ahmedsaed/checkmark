"""
Checkmark - AI Chess Benchmarking Platform
Backend FastAPI application entry point
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from typing import List
from datetime import datetime
import asyncio
import json

# Import services
from services.chess_engine import ChessEngine
from services.match_service import MatchService
from services.ai_model_service import AIModelService
from utils.mongo_db import get_database, close_database
import logging
from auth import (
    get_current_user,
    create_access_token,
    verify_password,
    LoginRequest,
    LoginResponse,
)
from schemas import (
    MatchCreate,
    ModelCreate,
    ModelUpdate,
    ModelResponse,
    BenchmarkCreate,
    MatchResponse,
    BenchmarkResponse,
    GameStatusResponse,
    MatchListResponse,
    ModelListResponse,
    APIResponse,
)


async def get_db():
    """FastAPI dependency that yields the MongoDB database."""
    db = await get_database()
    return db


async def get_chess_engine():
    """FastAPI dependency that yields the ChessEngine singleton."""
    engine = ChessEngine()
    return engine


async def get_match_service(chess_engine=Depends(get_chess_engine)):
    """FastAPI dependency that yields the MatchService."""
    service = MatchService(chess_engine)
    return service


async def get_ai_model_service():
    """FastAPI dependency that yields the AIModelService."""
    service = AIModelService()
    return service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup and cleanup on shutdown"""
    global active_sse_connections
    # MongoDB connection is lazy — first call to get_database() connects
    yield
    # Cleanup on shutdown
    logger.info(f"Shutting down {len(active_sse_connections)} SSE connections")
    for match_id, connections in active_sse_connections.items():
        for conn in connections:
            try:
                conn.close()
            except Exception:
                pass
    await close_database()


app = FastAPI(
    title="Checkmark Chess Benchmarking API",
    description="AI-powered chess benchmarking platform with model evaluation",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/matchmaking.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("checkmark")

# Track active SSE connections per match for cleanup
active_sse_connections: dict[str, set] = {}


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Checkmark Chess Benchmarking API", "status": "running"}


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest, db=Depends(get_db)):
    """Authenticate admin and return a JWT access token."""
    admins_col = db["admins"]
    admin_doc = await admins_col.find_one({"username": request.username})
    
    if not admin_doc or not verify_password(request.password, admin_doc["password_hash"]):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )
    
    token = create_access_token(subject=admin_doc["username"])
    return LoginResponse(access_token=token)


# ---------------------------------------------------------------------------
# Match endpoints
# ---------------------------------------------------------------------------

@app.post("/api/matches", response_model=MatchResponse)
async def create_match(
    match_data: MatchCreate,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
    service: MatchService = Depends(get_match_service),
):
    """Create a new match between two models and start auto-play"""
    try:
        match = await service.create_match(
            model_a_id=match_data.model_a_id,
            model_b_id=match_data.model_b_id,
            mode=match_data.mode,
            max_moves=match_data.max_moves,
        )
        
        # Start background auto-play task (fire-and-forget)
        asyncio.create_task(
            service.auto_play_match(match["id"], max_moves=match_data.max_moves)
        )
        
        return match
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/matches", response_model=MatchListResponse)
async def list_matches(
    status: str = None,
    db=Depends(get_db),
    service: MatchService = Depends(get_match_service),
):
    """List all matches, optionally filtered by status"""
    matches = await service.list_matches(status=status)
    return MatchListResponse(
        matches=matches,
        total=len(matches),
    )


@app.get("/api/matches/{match_id}", response_model=MatchResponse)
async def get_match(
    match_id: str,
    db=Depends(get_db),
    service: MatchService = Depends(get_match_service),
):
    """Get match details"""
    match = await service.get_match(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match


@app.get("/api/matches/{match_id}/status", response_model=GameStatusResponse)
async def get_match_status(
    match_id: str,
    db=Depends(get_db),
    service: MatchService = Depends(get_match_service),
    chess_engine=Depends(get_chess_engine),
):
    """Get current game status (checkmate, stalemate, active)"""
    match = await service.get_match(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    board = chess_engine.parse_fen(match["board_fen"])
    status_info = chess_engine.get_game_status(board)
    
    return GameStatusResponse(
        status=status_info["status"],
        winner=status_info.get("winner"),
        is_checkmate=status_info["is_checkmate"],
        is_stalemate=status_info["is_stalemate"],
        is_insufficient_material=status_info.get("is_insufficient_material", False),
        move_count=status_info["move_count"],
    )


@app.get("/api/matches/{match_id}/stream")
async def stream_match(
    match_id: str,
    service: MatchService = Depends(get_match_service),
):
    """SSE stream of a match. Streams thinking, moves, and match_end events."""
    match = await service.get_match(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    async def event_stream():
        try:
            from bson import ObjectId
            db = await service._get_db()
            turns_col = db["turns"]
            moves_col = db["moves"]

            def move_to_dict(doc):
                return {
                    "id": str(doc["_id"]),
                    "match_id": str(doc["match_id"]),
                    "move_number": doc["move_number"],
                    "san": doc["san"],
                    "uci": doc["uci"],
                    "from_square": doc["from_square"],
                    "to_square": doc["to_square"],
                    "promotion": doc.get("promotion"),
                    "is_check": doc.get("is_check", False),
                    "is_checkmate": doc.get("is_checkmate", False),
                    "thinking_time_ms": doc.get("thinking_time_ms"),
                    "timestamp": doc["timestamp"].isoformat() if doc.get("timestamp") else None,
                }

            # Fetch existing turns and moves
            cursor_turns = turns_col.find({"match_id": ObjectId(match["id"])}).sort("turn_number", 1)
            existing_turns = []
            async for doc in cursor_turns:
                existing_turns.append({
                    "turn_number": doc["turn_number"],
                    "side": doc["side"],
                    "model_name": doc.get("model_name", "Unknown"),
                    "thinking_text": doc.get("thinking_text", ""),
                    "move_san": doc.get("move_san"),
                })

            # Fetch existing moves
            cursor_moves = moves_col.find({"match_id": ObjectId(match["id"])}).sort("move_number", 1)
            existing_moves = []
            async for doc in cursor_moves:
                existing_moves.append(move_to_dict(doc))

            # Track last move number and last turn number we've sent
            last_move_number = existing_moves[-1]["move_number"] if existing_moves else 0
            last_turn_number = existing_turns[-1]["turn_number"] if existing_turns else 0

            # Send thinking events for existing turns
            for turn in existing_turns:
                if turn["thinking_text"].strip():
                    thinking_event = {
                        "type": "thinking",
                        "turn_number": turn["turn_number"],
                        "side": turn["side"],
                        "model_name": turn["model_name"],
                        "text": turn["thinking_text"],
                    }
                    yield f"data: {json.dumps(thinking_event)}\n\n"

            # Send move events for existing moves
            for move in existing_moves:
                yield f"data: {json.dumps(move)}\n\n"

            # If match is finished, send completion event and stop
            if match.get("status") != "active":
                yield f"data: {json.dumps({'type': 'match_end', 'status': match.get('status'), 'winner': match.get('winner_id')})}\n\n"
                return

            # Poll for new turns and moves while match is ongoing
            while True:
                await asyncio.sleep(1)

                # Check match status
                current_match = await service.get_match(match_id)
                if not current_match:
                    yield f"data: {json.dumps({'type': 'match_removed'})}\n\n"
                    break

                # Fetch new turns
                cursor_turns = turns_col.find({
                    "match_id": ObjectId(current_match["id"]),
                    "turn_number": {"$gt": last_turn_number},
                }).sort("turn_number", 1)
                new_turns = []
                async for doc in cursor_turns:
                    new_turns.append({
                        "turn_number": doc["turn_number"],
                        "side": doc["side"],
                        "model_name": doc.get("model_name", "Unknown"),
                        "thinking_text": doc.get("thinking_text", ""),
                        "move_san": doc.get("move_san"),
                    })

                # Stream thinking events for new turns
                for turn in new_turns:
                    if turn["thinking_text"].strip():
                        thinking_event = {
                            "type": "thinking",
                            "turn_number": turn["turn_number"],
                            "side": turn["side"],
                            "model_name": turn["model_name"],
                            "text": turn["thinking_text"],
                        }
                        yield f"data: {json.dumps(thinking_event)}\n\n"
                    last_turn_number = max(last_turn_number, turn["turn_number"])

                # Fetch new moves
                cursor_moves = moves_col.find({
                    "match_id": ObjectId(current_match["id"]),
                    "move_number": {"$gt": last_move_number},
                }).sort("move_number", 1)
                new_moves = []
                async for doc in cursor_moves:
                    new_moves.append(move_to_dict(doc))

                # Stream new moves
                for move in new_moves:
                    yield f"data: {json.dumps(move)}\n\n"
                    last_move_number = max(last_move_number, move["move_number"])

                if new_turns or new_moves:
                    logger.info(f"Match {match_id}: streamed {len(new_turns)} thinking event(s) and {len(new_moves)} move(s)")

                # Check if match finished
                if current_match.get("status") != "active":
                    yield f"data: {json.dumps({'type': 'match_end', 'status': current_match.get('status'), 'winner': current_match.get('winner_id')})}\n\n"
                    break

        except GeneratorExit:
            # Client disconnected
            logger.info(f"Match {match_id}: SSE client disconnected")
            return
        except Exception as e:
            logger.error(f"Match {match_id}: SSE stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Model endpoints
# ---------------------------------------------------------------------------

@app.post("/api/models", response_model=ModelResponse)
async def create_model(
    model_data: ModelCreate,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
    service: AIModelService = Depends(get_ai_model_service),
):
    """Register a new AI model"""
    try:
        model = await service.create_model(
            name=model_data.name,
            provider=model_data.provider,
            model_id=model_data.model_id,
            capabilities=model_data.capabilities,
        )
        return model
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/models", response_model=ModelListResponse)
async def list_models(
    db=Depends(get_db),
    service: AIModelService = Depends(get_ai_model_service),
):
    """List all registered models"""
    models = await service.list_models()
    return ModelListResponse(
        models=models,
        total=len(models),
    )


@app.get("/api/models/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: str,
    db=Depends(get_db),
    service: AIModelService = Depends(get_ai_model_service),
):
    """Get model details and benchmark stats"""
    model = await service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@app.put("/api/models/{model_id}", response_model=ModelResponse)
async def update_model(
    model_id: str,
    model_data: ModelUpdate,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
    service: AIModelService = Depends(get_ai_model_service),
):
    """Update a model's metadata (name, provider, model_id only)"""
    # Get existing model to verify it exists
    existing = await service.get_model(model_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # Only allow updating these fields
    updates = {}
    if model_data.name is not None:
        updates["name"] = model_data.name
    if model_data.provider is not None:
        updates["provider"] = model_data.provider
    if model_data.model_id is not None:
        updates["model_id"] = model_data.model_id
    
    if not updates:
        # No updates provided, return existing model
        return existing
    
    try:
        updated = await service.update_model(model_id, updates)
        if not updated:
            raise HTTPException(status_code=500, detail="Failed to update model")
        return updated
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/models/{model_id}")
async def delete_model(
    model_id: str,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Delete a model"""
    models_col = db["models"]
    
    from bson import ObjectId
    try:
        result = await models_col.delete_one({"_id": ObjectId(model_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid model ID")
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return {"success": True, "message": f"Model '{model_id}' deleted"}


# ---------------------------------------------------------------------------
# Benchmark endpoints
# ---------------------------------------------------------------------------

@app.post("/api/benchmarks", response_model=BenchmarkResponse)
async def create_benchmark(
    benchmark_data: BenchmarkCreate,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
    service: AIModelService = Depends(get_ai_model_service),
):
    """Record benchmark results for a model"""
    try:
        benchmark = await service.create_benchmark(
            model_id=benchmark_data.model_id,
            match_id=benchmark_data.match_id,
            elo_estimate=benchmark_data.elo_estimate,
            move_accuracy=benchmark_data.move_accuracy,
            thinking_time_avg=benchmark_data.thinking_time_avg,
        )
        return benchmark
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/benchmarks/{model_id}", response_model=BenchmarkResponse)
async def get_benchmarks(
    model_id: str,
    db=Depends(get_db),
    service: AIModelService = Depends(get_ai_model_service),
):
    """Get benchmark statistics for a model"""
    benchmark = await service.get_benchmark(model_id)
    if not benchmark:
        raise HTTPException(status_code=404, detail="Benchmark not found")
    return benchmark


@app.get("/api/benchmarks/rankings", response_model=List[BenchmarkResponse])
async def get_rankings(
    db=Depends(get_db),
    service: AIModelService = Depends(get_ai_model_service),
):
    """Get overall model rankings"""
    rankings = await service.get_rankings()
    return rankings


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
