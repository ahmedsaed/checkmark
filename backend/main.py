"""
Checkmark - AI Chess Benchmarking Platform
Backend FastAPI application entry point
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List
from datetime import datetime

# Import services
from services.chess_engine import ChessEngine
from services.match_service import MatchService
from services.ai_model_service import AIModelService
from utils.mongo_db import get_database, close_database
from middleware.move_validation import MoveValidationMiddleware
from schemas import (
    MatchCreate,
    MoveCreate,
    ModelCreate,
    BenchmarkCreate,
    MatchResponse,
    MoveResponse,
    ModelResponse,
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
    # Add move validation middleware at startup
    app.add_middleware(MoveValidationMiddleware)
    # MongoDB connection is lazy — first call to get_database() connects
    yield
    # Cleanup on shutdown
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


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Checkmark Chess Benchmarking API", "status": "running"}


# ---------------------------------------------------------------------------
# Match endpoints
# ---------------------------------------------------------------------------

@app.post("/api/matches", response_model=MatchResponse)
async def create_match(
    match_data: MatchCreate,
    db=Depends(get_db),
    service: MatchService = Depends(get_match_service),
):
    """Create a new match between two models"""
    try:
        match = await service.create_match(
            model_a_id=match_data.model_a_id,
            model_b_id=match_data.model_b_id,
            mode=match_data.mode,
            time_control=match_data.time_control,
            white_side=match_data.white_side,
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


@app.post("/api/matches/{match_id}/moves", response_model=MoveResponse)
async def make_move(
    match_id: str,
    move_data: MoveCreate,
    db=Depends(get_db),
    service: MatchService = Depends(get_match_service),
    chess_engine=Depends(get_chess_engine),
):
    """Execute a move in the game"""
    try:
        move_result = await service.make_move(
            match_id=match_id,
            san=move_data.move_san,
            white_move=move_data.white_move,
            chess_engine=chess_engine,
        )
        return move_result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Model endpoints
# ---------------------------------------------------------------------------

@app.post("/api/models", response_model=ModelResponse)
async def create_model(
    model_data: ModelCreate,
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


# ---------------------------------------------------------------------------
# Benchmark endpoints
# ---------------------------------------------------------------------------

@app.post("/api/benchmarks", response_model=BenchmarkResponse)
async def create_benchmark(
    benchmark_data: BenchmarkCreate,
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
