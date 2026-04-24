"""
Checkmark - AI Chess Benchmarking Platform
Backend FastAPI application entry point
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List
from datetime import datetime

# Import services
from services.chess_engine import ChessEngine
from services.match_service import MatchService
from services.ai_model_service import AIModelService
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
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup and cleanup on shutdown"""
    # Initialize services
    chess_engine = ChessEngine()
    match_service = MatchService(chess_engine)
    ai_model_service = AIModelService()
    
    # Store services globally (in production, use dependency injection)
    app.state.chess_engine = chess_engine
    app.state.match_service = match_service
    app.state.ai_model_service = ai_model_service
    
    yield


app = FastAPI(
    title="Checkmark Chess Benchmarking API",
    description="AI-powered chess benchmarking platform with model evaluation",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Checkmark Chess Benchmarking API", "status": "running"}


# Match endpoints
@app.post("/api/matches", response_model=MatchResponse)
async def create_match(match_data: MatchCreate):
    """Create a new match between two models"""
    return {"message": "Match created", "match_id": "mock-match-123"}


@app.get("/api/matches/{match_id}", response_model=MatchResponse)
async def get_match(match_id: str):
    """Get match details"""
    return {
        "id": match_id,
        "status": "active",
        "move_count": 0,
        "white_model": "model-a",
        "black_model": "model-b",
    }


@app.get("/api/matches/{match_id}/status", response_model=GameStatusResponse)
async def get_match_status(match_id: str):
    """Get current game status (checkmate, stalemate, active)"""
    return {
        "status": "active",
        "is_checkmate": False,
        "is_stalemate": False,
        "winner": None,
        "move_count": 12,
    }


@app.post("/api/matches/{match_id}/moves", response_model=MoveResponse)
async def make_move(match_id: str, move_data: MoveCreate):
    """Execute a move in the game"""
    return {
        "success": True,
        "move_number": 7,
        "move_from": "e2",
        "move_to": "e4",
        "is_check": False,
    }


# Model endpoints
@app.post("/api/models", response_model=ModelResponse)
async def create_model(model_data: ModelCreate):
    """Register a new AI model"""
    return {"message": "Model registered", "model_id": "mock-model-456"}


@app.get("/api/models/{model_id}", response_model=ModelResponse)
async def get_model(model_id: str):
    """Get model details and benchmark stats"""
    return {
        "id": model_id,
        "name": "Model Name",
        "provider": "openrouter",
        "model_id": "anthropic/claude-3.5",
        "wins": 10,
        "losses": 5,
        "draws": 2,
    }


# Benchmark endpoints
@app.post("/api/benchmarks", response_model=BenchmarkResponse)
async def create_benchmark(benchmark_data: BenchmarkCreate):
    """Record benchmark results for a model"""
    return {"message": "Benchmark recorded", "benchmark_id": "mock-benchmark-789"}


@app.get("/api/benchmarks/{model_id}", response_model=BenchmarkResponse)
async def get_benchmarks(model_id: str):
    """Get benchmark statistics for a model"""
    return {
        "model_id": model_id,
        "elo_estimate": 1200,
        "move_accuracy": 0.85,
        "total_games": 50,
        "wins": 20,
        "losses": 15,
        "draws": 15,
    }


@app.get("/api/benchmarks/rankings", response_model=List[BenchmarkResponse])
async def get_rankings():
    """Get overall model rankings"""
    return [
        {
            "model_id": "model-1",
            "elo_estimate": 1500,
            "total_games": 100,
            "rank": 1,
        },
        {
            "model_id": "model-2",
            "elo_estimate": 1450,
            "total_games": 80,
            "rank": 2,
        },
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
