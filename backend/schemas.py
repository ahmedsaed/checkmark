"""
Pydantic schemas for Checkmark Chess Benchmarking Platform
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


# Match Schemas
class MatchCreate(BaseModel):
    model_a_id: str = Field(..., description="ID of first model")
    model_b_id: str = Field(..., description="ID of second model")
    mode: Literal["best_of", "rapid", "blitz", "bullet"] = "rapid"
    time_control: int = Field(default=10, ge=1, description="Time control in minutes")
    white_side: Optional[str] = None  # Which model plays white


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


# Move Schemas
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


# Model Schemas
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


# Benchmark Schemas
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


# Game Status Response
class GameStatusResponse(BaseModel):
    status: Literal["active", "finished", "abandoned"]
    winner: Optional[str] = None
    is_checkmate: bool = False
    is_stalemate: bool = False
    is_insufficient_material: bool = False
    move_count: int = 0
