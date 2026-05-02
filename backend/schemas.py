"""
Pydantic schemas for Checkmark Chess Benchmarking Platform.

These are the API request/response schemas used by FastAPI endpoints.
MongoDB document models live in models.py.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal, List
from datetime import datetime


# ---------------------------------------------------------------------------
# Match schemas
# ---------------------------------------------------------------------------

class MatchCreate(BaseModel):
    model_a_id: str = Field(..., description="ObjectId of first model")
    model_b_id: str = Field(..., description="ObjectId of second model")
    mode: Literal["best_of", "rapid", "blitz", "bullet"] = "rapid"
    time_control: int = Field(default=10, ge=1, description="Time control in minutes")
    white_side: Optional[str] = None


class MatchResponse(BaseModel):
    id: str
    model_a_id: str
    model_b_id: str
    mode: str
    time_control: int
    white_side: Optional[str]
    status: str = "active"
    winner_id: Optional[str] = None
    total_moves: int = 0
    board_fen: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime] = None


class MatchListResponse(BaseModel):
    matches: List[MatchResponse]
    total: int


# ---------------------------------------------------------------------------
# Move schemas
# ---------------------------------------------------------------------------

class MoveCreate(BaseModel):
    move_san: str = Field(..., description="Move in SAN notation, e.g., 'e4' or 'Nf3'")
    match_id: str = Field(..., description="ID of the match")
    white_move: bool = Field(default=True, description="Is this white's move?")


class MoveResponse(BaseModel):
    success: bool
    move_number: int
    move_from: Optional[str] = None
    move_to: Optional[str] = None
    promotion: Optional[str] = None
    is_check: bool = False
    is_checkmate: bool = False
    is_stalemate: bool = False
    board_fen: Optional[str] = None
    timestamp: datetime


class MoveListResponse(BaseModel):
    moves: List[MoveResponse]
    total: int


# ---------------------------------------------------------------------------
# Model schemas
# ---------------------------------------------------------------------------

class ModelCreate(BaseModel):
    name: str = Field(..., description="Model display name")
    provider: str = Field(default="openrouter", description="AI provider")
    model_id: str = Field(..., description="Model identifier, e.g., 'anthropic/claude-3.5'")
    capabilities: Optional[dict] = Field(default_factory=dict)


class ModelResponse(BaseModel):
    id: str
    name: str
    provider: str
    model_id: str
    capabilities: dict
    benchmark_stats: dict
    created_at: datetime
    updated_at: datetime


class ModelListResponse(BaseModel):
    models: List[ModelResponse]
    total: int


# ---------------------------------------------------------------------------
# Benchmark schemas
# ---------------------------------------------------------------------------

class BenchmarkCreate(BaseModel):
    model_id: str
    match_id: str
    elo_estimate: float
    move_accuracy: float = Field(ge=0, le=1)
    thinking_time_avg: float


class BenchmarkResponse(BaseModel):
    model_id: str
    match_id: str
    elo_estimate: float
    move_accuracy: float
    average_depth: float
    thinking_time_avg: float
    wins: int = 0
    losses: int = 0
    draws: int = 0
    total_games: int = 0
    timestamp: datetime


class BenchmarkRankingResponse(BaseModel):
    model_id: str
    model_name: str
    elo_estimate: float
    total_games: int
    wins: int
    losses: int
    draws: int
    win_rate: float
    rank: int


# ---------------------------------------------------------------------------
# Game status
# ---------------------------------------------------------------------------

class GameStatusResponse(BaseModel):
    status: Literal["active", "finished", "abandoned"]
    winner: Optional[str] = None
    is_checkmate: bool = False
    is_stalemate: bool = False
    is_insufficient_material: bool = False
    move_count: int = 0


# ---------------------------------------------------------------------------
# Generic API response
# ---------------------------------------------------------------------------

class APIResponse(BaseModel):
    """Standard envelope for all API responses."""

    success: bool = True
    message: str = "OK"
    data: Optional[dict] = None

    @classmethod
    def ok(cls, data: dict = None, message: str = "OK") -> "APIResponse":
        return cls(success=True, message=message, data=data)

    @classmethod
    def error(cls, message: str, data: dict = None) -> "APIResponse":
        return cls(success=False, message=message, data=data)
