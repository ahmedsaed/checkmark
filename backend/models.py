"""
MongoDB document models for Checkmark Chess Benchmarking Platform.

These Pydantic v2 models represent the actual MongoDB documents,
with ObjectId support and proper type annotations for each collection.
"""

from typing import Optional, Literal, List
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId


# ---------------------------------------------------------------------------
# Custom types
# ---------------------------------------------------------------------------

class PyObjectId(ObjectId):
    """Pydantic-compatible ObjectId that serialises to string."""

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        """Generate JSON schema for ObjectId fields."""
        return {"type": "string", "example": "507f1f77bcf86cd799439011"}

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        """Generate core schema for ObjectId fields."""
        from pydantic_core import core_schema
        return core_schema.with_info_plain_validator_function(
            cls.validate,
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def validate(cls, v, info):
        """Validate that the value is a valid ObjectId."""
        if isinstance(v, str):
            if not ObjectId.is_valid(v):
                raise ValueError("Invalid ObjectId")
            return ObjectId(v)
        elif isinstance(v, ObjectId):
            return v
        else:
            raise ValueError("Invalid ObjectId")


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class MatchMode(str, Enum):
    BEST_OF = "best_of"
    RAPID = "rapid"
    BLITZ = "blitz"
    BULLET = "bullet"


class MatchStatus(str, Enum):
    ACTIVE = "active"
    FINISHED = "finished"
    ABANDONED = "abandoned"


class GameOutcome(str, Enum):
    WHITE_WINS = "1-0"
    BLACK_WINS = "0-1"
    DRAW = "1/2-1/2"
    ONGOING = "*"


# ---------------------------------------------------------------------------
# Models collection
# ---------------------------------------------------------------------------

class ModelStats(BaseModel):
    """Benchmark statistics for an AI model."""

    wins: int = 0
    losses: int = 0
    draws: int = 0
    total_games: int = 0

    @property
    def win_rate(self) -> float:
        if self.total_games == 0:
            return 0.0
        return round(self.wins / self.total_games * 100, 2)


class ModelDocument(BaseModel):
    """Document for the *models* collection."""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    name: str = Field(..., description="Human-readable model name, e.g. 'Claude 3.5'")
    provider: str = Field(default="openrouter", description="AI provider slug")
    model_id: str = Field(..., description="Provider model identifier, e.g. 'anthropic/claude-3.5'")
    capabilities: dict = Field(default_factory=dict)
    benchmark_stats: ModelStats = Field(default_factory=ModelStats)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
        }


# ---------------------------------------------------------------------------
# Matches collection
# ---------------------------------------------------------------------------

class MatchDocument(BaseModel):
    """Document for the *matches* collection."""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    model_a_id: PyObjectId = Field(..., description="Reference to models collection")
    model_b_id: PyObjectId = Field(..., description="Reference to models collection")
    mode: MatchMode = Field(default=MatchMode.RAPID)
    time_control: int = Field(default=10, ge=1, description="Time control in minutes")
    white_side: Optional[PyObjectId] = None  # Override; defaults to model_a
    board_fen: str = Field(
        default="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        description="Current board FEN",
    )
    status: MatchStatus = Field(default=MatchStatus.ACTIVE)
    winner_id: Optional[PyObjectId] = None
    outcome: Optional[GameOutcome] = None
    total_moves: int = 0
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None

    @property
    def white_model_id(self) -> PyObjectId:
        return self.white_side or self.model_a_id

    @property
    def black_model_id(self) -> PyObjectId:
        return self.model_b_id if self.white_model_id == self.model_a_id else self.model_a_id

    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            MatchMode: str,
            MatchStatus: str,
            GameOutcome: str,
        }


# ---------------------------------------------------------------------------
# Moves collection
# ---------------------------------------------------------------------------

class MoveDocument(BaseModel):
    """Document for the *moves* collection."""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    match_id: PyObjectId = Field(..., description="Reference to matches collection")
    move_number: int = Field(..., ge=1, description="Half-move number (1, 2, 3, …)")
    san: str = Field(..., description="Move in Standard Algebraic Notation, e.g. 'e4'")
    uci: str = Field(..., description="Move in UCI notation, e.g. 'e2e4'")
    from_square: str = Field(..., description="Source square, e.g. 'e2'")
    to_square: str = Field(..., description="Destination square, e.g. 'e4'")
    promotion: Optional[str] = None  # Piece letter if promoted, e.g. 'q'
    is_check: bool = False
    is_checkmate: bool = False
    is_stalemate: bool = False
    is_castling: bool = False
    is_en_passant: bool = False
    thinking_time_ms: Optional[int] = None  # How long the AI took to decide
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
        }


# ---------------------------------------------------------------------------
# Benchmarks collection
# ---------------------------------------------------------------------------

class BenchmarkDocument(BaseModel):
    """Document for the *benchmarks* collection."""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    model_id: PyObjectId = Field(..., description="Reference to models collection")
    match_id: PyObjectId = Field(..., description="Reference to matches collection")
    elo_estimate: float = Field(..., ge=0)
    move_accuracy: float = Field(..., ge=0, le=1, description="Fraction of legal moves")
    average_depth: float = Field(default=0, description="Average search depth")
    thinking_time_avg: float = Field(default=0, description="Average thinking time in ms")
    wins: int = 0
    losses: int = 0
    draws: int = 0
    total_games: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
        }


# ---------------------------------------------------------------------------
# API request / response schemas (kept alongside models for convenience)
# ---------------------------------------------------------------------------

class MatchCreateRequest(BaseModel):
    """Request body for creating a match."""

    model_a_id: str = Field(..., description="ObjectId of first model")
    model_b_id: str = Field(..., description="ObjectId of second model")
    mode: MatchMode = Field(default=MatchMode.RAPID)
    time_control: int = Field(default=10, ge=1, description="Time control in minutes")
    white_side: Optional[str] = None  # ObjectId string; defaults to model_a


class MoveCreateRequest(BaseModel):
    """Request body for submitting a move."""

    move_san: str = Field(..., description="Move in SAN notation")
    move_uci: Optional[str] = None  # Optional; backend can derive from SAN
    thinking_time_ms: Optional[int] = None


class ModelCreateRequest(BaseModel):
    """Request body for registering a model."""

    name: str = Field(..., description="Human-readable model name")
    provider: str = Field(default="openrouter")
    model_id: str = Field(..., description="Provider model identifier")
    capabilities: dict = Field(default_factory=dict)


class BenchmarkCreateRequest(BaseModel):
    """Request body for recording benchmark data."""

    model_id: str
    match_id: str
    elo_estimate: float
    move_accuracy: float = Field(..., ge=0, le=1)
    thinking_time_avg: float = 0
    average_depth: float = 0


# ---------------------------------------------------------------------------
# Generic API response wrapper
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
