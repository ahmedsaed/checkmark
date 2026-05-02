"""
Tests for Pydantic schemas and models.

Tests cover:
- Match schemas (create, response, list)
- Move schemas (create, response, list)
- Model schemas (create, response, list)
- Benchmark schemas (create, response, ranking)
- Game status schema
- Generic API response
- PyObjectId validation
"""

import pytest
from bson import ObjectId

from schemas import (
    MatchCreate,
    MatchResponse,
    MatchListResponse,
    MoveCreate,
    MoveResponse,
    MoveListResponse,
    ModelCreate,
    ModelResponse,
    ModelListResponse,
    BenchmarkCreate,
    BenchmarkResponse,
    BenchmarkRankingResponse,
    GameStatusResponse,
    APIResponse,
)
from models import (
    PyObjectId,
    MatchMode,
    MatchStatus,
    GameOutcome,
    ModelStats,
    ModelDocument,
    MatchDocument,
    MoveDocument,
    BenchmarkDocument,
    MatchCreateRequest,
    MoveCreateRequest,
    ModelCreateRequest,
    BenchmarkCreateRequest,
)


class TestMatchSchemas:
    """Tests for match-related schemas."""

    def test_match_create_defaults(self):
        """Test MatchCreate with default values."""
        data = MatchCreate(
            model_a_id="507f1f77bcf86cd799439011",
            model_b_id="507f1f77bcf86cd799439012",
        )
        assert data.mode == "rapid"
        assert data.time_control == 10
        assert data.white_side is None

    def test_match_create_explicit_values(self):
        """Test MatchCreate with explicit values."""
        data = MatchCreate(
            model_a_id="507f1f77bcf86cd799439011",
            model_b_id="507f1f77bcf86cd799439012",
            mode="blitz",
            time_control=3,
            white_side="507f1f77bcf86cd799439011",
        )
        assert data.mode == "blitz"
        assert data.time_control == 3
        assert data.white_side == "507f1f77bcf86cd799439011"

    def test_match_create_invalid_mode(self):
        """Test MatchCreate with invalid mode."""
        with pytest.raises(ValueError):
            MatchCreate(
                model_a_id="507f1f77bcf86cd799439011",
                model_b_id="507f1f77bcf86cd799439012",
                mode="invalid",
            )

    def test_match_create_invalid_time_control(self):
        """Test MatchCreate with invalid time control."""
        with pytest.raises(ValueError):
            MatchCreate(
                model_a_id="507f1f77bcf86cd799439011",
                model_b_id="507f1f77bcf86cd799439012",
                time_control=0,
            )

    def test_match_response_defaults(self):
        """Test MatchResponse with default values."""
        from datetime import datetime
        data = MatchResponse(
            id="507f1f77bcf86cd799439011",
            model_a_id="507f1f77bcf86cd799439012",
            model_b_id="507f1f77bcf86cd799439013",
            mode="rapid",
            time_control=10,
            started_at=datetime.utcnow(),
        )
        assert data.status == "active"
        assert data.winner_id is None
        assert data.total_moves == 0
        assert data.board_fen is None
        assert data.ended_at is None

    def test_match_list_response(self):
        """Test MatchListResponse."""
        from datetime import datetime
        matches = [
            MatchResponse(
                id="507f1f77bcf86cd799439011",
                model_a_id="507f1f77bcf86cd799439012",
                model_b_id="507f1f77bcf86cd799439013",
                mode="rapid",
                time_control=10,
                started_at=datetime.utcnow(),
            ),
        ]
        data = MatchListResponse(matches=matches, total=1)
        assert len(data.matches) == 1
        assert data.total == 1


class TestMoveSchemas:
    """Tests for move-related schemas."""

    def test_move_create_defaults(self):
        """Test MoveCreate with default values."""
        data = MoveCreate(
            move_san="e4",
            match_id="507f1f77bcf86cd799439011",
        )
        assert data.white_move is True

    def test_move_create_explicit(self):
        """Test MoveCreate with explicit values."""
        data = MoveCreate(
            move_san="Nf3",
            match_id="507f1f77bcf86cd799439011",
            white_move=False,
        )
        assert data.white_move is False

    def test_move_response_defaults(self):
        """Test MoveResponse with default values."""
        from datetime import datetime
        data = MoveResponse(
            success=True,
            move_number=1,
            timestamp=datetime.utcnow(),
        )
        assert data.move_from is None
        assert data.move_to is None
        assert data.promotion is None
        assert data.is_check is False
        assert data.is_checkmate is False
        assert data.is_stalemate is False
        assert data.board_fen is None

    def test_move_list_response(self):
        """Test MoveListResponse."""
        from datetime import datetime
        moves = [
            MoveResponse(
                success=True,
                move_number=1,
                timestamp=datetime.utcnow(),
            ),
        ]
        data = MoveListResponse(moves=moves, total=1)
        assert len(data.moves) == 1
        assert data.total == 1


class TestModelSchemas:
    """Tests for model-related schemas."""

    def test_model_create_defaults(self):
        """Test ModelCreate with default values."""
        data = ModelCreate(
            name="Claude 3.5",
            model_id="anthropic/claude-3.5",
        )
        assert data.provider == "openrouter"
        assert data.capabilities == {}

    def test_model_create_explicit(self):
        """Test ModelCreate with explicit values."""
        data = ModelCreate(
            name="GPT-4o",
            provider="openai",
            model_id="openai/gpt-4o",
            capabilities={"supports_chess": True},
        )
        assert data.provider == "openai"
        assert data.capabilities == {"supports_chess": True}

    def test_model_response(self):
        """Test ModelResponse."""
        from datetime import datetime
        data = ModelResponse(
            id="507f1f77bcf86cd799439011",
            name="Claude 3.5",
            provider="openrouter",
            model_id="anthropic/claude-3.5",
            capabilities={"supports_chess": True},
            benchmark_stats={"wins": 10, "losses": 5, "draws": 2, "total_games": 17},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert data.id == "507f1f77bcf86cd799439011"
        assert data.name == "Claude 3.5"

    def test_model_list_response(self):
        """Test ModelListResponse."""
        from datetime import datetime
        models = [
            ModelResponse(
                id="507f1f77bcf86cd799439011",
                name="Claude 3.5",
                provider="openrouter",
                model_id="anthropic/claude-3.5",
                capabilities={},
                benchmark_stats={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
        ]
        data = ModelListResponse(models=models, total=1)
        assert len(data.models) == 1
        assert data.total == 1


class TestBenchmarkSchemas:
    """Tests for benchmark-related schemas."""

    def test_benchmark_create(self):
        """Test BenchmarkCreate."""
        data = BenchmarkCreate(
            model_id="507f1f77bcf86cd799439011",
            match_id="507f1f77bcf86cd799439012",
            elo_estimate=1500.0,
            move_accuracy=0.85,
            thinking_time_avg=5000.0,
        )
        assert data.elo_estimate == 1500.0
        assert data.move_accuracy == 0.85

    def test_benchmark_create_invalid_accuracy(self):
        """Test BenchmarkCreate with invalid accuracy."""
        with pytest.raises(ValueError):
            BenchmarkCreate(
                model_id="507f1f77bcf86cd799439011",
                match_id="507f1f77bcf86cd799439012",
                elo_estimate=1500.0,
                move_accuracy=1.5,  # > 1.0
                thinking_time_avg=5000.0,
            )

    def test_benchmark_response_defaults(self):
        """Test BenchmarkResponse with default values."""
        from datetime import datetime
        data = BenchmarkResponse(
            model_id="507f1f77bcf86cd799439011",
            match_id="507f1f77bcf86cd799439012",
            elo_estimate=1500.0,
            move_accuracy=0.85,
            average_depth=20.0,
            thinking_time_avg=5000.0,
            timestamp=datetime.utcnow(),
        )
        assert data.wins == 0
        assert data.losses == 0
        assert data.draws == 0
        assert data.total_games == 0

    def test_benchmark_ranking_response(self):
        """Test BenchmarkRankingResponse."""
        data = BenchmarkRankingResponse(
            model_id="507f1f77bcf86cd799439011",
            model_name="Claude 3.5",
            elo_estimate=1500.0,
            total_games=100,
            wins=60,
            losses=30,
            draws=10,
            win_rate=60.0,
            rank=1,
        )
        assert data.model_name == "Claude 3.5"
        assert data.rank == 1
        assert data.win_rate == 60.0


class TestGameStatusSchema:
    """Tests for game status schema."""

    def test_game_status_active(self):
        """Test GameStatusResponse for active game."""
        data = GameStatusResponse(
            status="active",
            move_count=12,
        )
        assert data.status == "active"
        assert data.winner is None
        assert data.is_checkmate is False
        assert data.is_stalemate is False
        assert data.is_insufficient_material is False
        assert data.move_count == 12

    def test_game_status_finished(self):
        """Test GameStatusResponse for finished game."""
        data = GameStatusResponse(
            status="finished",
            winner="white",
            is_checkmate=True,
            move_count=40,
        )
        assert data.status == "finished"
        assert data.winner == "white"
        assert data.is_checkmate is True


class TestAPIResponse:
    """Tests for generic API response."""

    def test_api_response_defaults(self):
        """Test APIResponse with default values."""
        data = APIResponse()
        assert data.success is True
        assert data.message == "OK"
        assert data.data is None

    def test_api_response_custom(self):
        """Test APIResponse with custom values."""
        data = APIResponse(
            success=False,
            message="Error occurred",
            data={"error": "invalid_move"},
        )
        assert data.success is False
        assert data.message == "Error occurred"
        assert data.data == {"error": "invalid_move"}

    def test_api_response_ok_classmethod(self):
        """Test APIResponse.ok() classmethod."""
        data = APIResponse.ok(data={"key": "value"}, message="Success")
        assert data.success is True
        assert data.message == "Success"
        assert data.data == {"key": "value"}

    def test_api_response_error_classmethod(self):
        """Test APIResponse.error() classmethod."""
        data = APIResponse.error(message="Something went wrong")
        assert data.success is False
        assert data.message == "Something went wrong"
        assert data.data is None


class TestPyObjectId:
    """Tests for PyObjectId custom type."""

    def test_pyobjectid_from_string(self):
        """Test creating PyObjectId from string."""
        oid_str = "507f1f77bcf86cd799439011"
        oid = PyObjectId.validate(oid_str)
        assert isinstance(oid, ObjectId)
        assert str(oid) == oid_str

    def test_pyobjectid_from_objectid(self):
        """Test creating PyObjectId from ObjectId."""
        original = ObjectId()
        oid = PyObjectId.validate(original)
        assert oid == original

    def test_pyobjectid_invalid_string(self):
        """Test PyObjectId with invalid string."""
        with pytest.raises(ValueError):
            PyObjectId.validate("invalid")

    def test_pyobjectid_invalid_hex(self):
        """Test PyObjectId with invalid hex string."""
        with pytest.raises(ValueError):
            PyObjectId.validate("x" * 24)

    def test_pyobjectid_json_schema(self):
        """Test PyObjectId JSON schema generation."""
        from pydantic import BaseModel
        from typing import Any
        
        class TestModel(BaseModel):
            id: PyObjectId
        
        schema = TestModel.model_json_schema()
        assert "properties" in schema
        assert "id" in schema["properties"]


class TestModelStats:
    """Tests for ModelStats."""

    def test_model_stats_defaults(self):
        """Test ModelStats with default values."""
        stats = ModelStats()
        assert stats.wins == 0
        assert stats.losses == 0
        assert stats.draws == 0
        assert stats.total_games == 0
        assert stats.win_rate == 0.0

    def test_model_stats_win_rate(self):
        """Test ModelStats win rate calculation."""
        stats = ModelStats(wins=30, losses=15, draws=5, total_games=50)
        assert stats.win_rate == 60.0

    def test_model_stats_zero_games(self):
        """Test ModelStats win rate with zero games."""
        stats = ModelStats(total_games=0)
        assert stats.win_rate == 0.0


class TestModelDocument:
    """Tests for ModelDocument."""

    def test_model_document_defaults(self):
        """Test ModelDocument with default values."""
        doc = ModelDocument(
            name="Claude 3.5",
            provider="openrouter",
            model_id="anthropic/claude-3.5",
        )
        assert doc.benchmark_stats.wins == 0
        assert doc.created_at is not None
        assert doc.updated_at is not None

    def test_model_document_with_stats(self):
        """Test ModelDocument with benchmark stats."""
        from datetime import datetime
        doc = ModelDocument(
            name="GPT-4o",
            provider="openai",
            model_id="openai/gpt-4o",
            benchmark_stats=ModelStats(wins=25, losses=15, draws=5, total_games=45),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert doc.benchmark_stats.wins == 25
        assert doc.benchmark_stats.win_rate == 55.56


class TestMatchDocument:
    """Tests for MatchDocument."""

    def test_match_document_defaults(self):
        """Test MatchDocument with default values."""
        doc = MatchDocument(
            model_a_id=ObjectId(),
            model_b_id=ObjectId(),
        )
        assert doc.mode == MatchMode.RAPID
        assert doc.time_control == 10
        assert doc.status == MatchStatus.ACTIVE
        assert doc.board_fen == "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        assert doc.total_moves == 0

    def test_match_document_white_model_id(self):
        """Test MatchDocument white_model_id property."""
        model_a = ObjectId()
        model_b = ObjectId()
        doc = MatchDocument(
            model_a_id=model_a,
            model_b_id=model_b,
        )
        assert doc.white_model_id == model_a
        assert doc.black_model_id == model_b

    def test_match_document_white_side_override(self):
        """Test MatchDocument white_model_id with white_side override."""
        model_a = ObjectId()
        model_b = ObjectId()
        doc = MatchDocument(
            model_a_id=model_a,
            model_b_id=model_b,
            white_side=model_b,
        )
        assert doc.white_model_id == model_b
        assert doc.black_model_id == model_a


class TestMoveDocument:
    """Tests for MoveDocument."""

    def test_move_document_defaults(self):
        """Test MoveDocument with default values."""
        doc = MoveDocument(
            match_id=ObjectId(),
            move_number=1,
            san="e4",
            uci="e2e4",
            from_square="e2",
            to_square="e4",
        )
        assert doc.promotion is None
        assert doc.is_check is False
        assert doc.is_checkmate is False
        assert doc.is_castling is False
        assert doc.is_en_passant is False
        assert doc.thinking_time_ms is None

    def test_move_document_with_promotion(self):
        """Test MoveDocument with promotion."""
        doc = MoveDocument(
            match_id=ObjectId(),
            move_number=10,
            san="Qxf7+",
            uci="f7f8q",
            from_square="f7",
            to_square="f8",
            promotion="q",
            is_check=True,
            thinking_time_ms=5000,
        )
        assert doc.promotion == "q"
        assert doc.is_check is True
        assert doc.thinking_time_ms == 5000


class TestBenchmarkDocument:
    """Tests for BenchmarkDocument."""

    def test_benchmark_document_defaults(self):
        """Test BenchmarkDocument with default values."""
        doc = BenchmarkDocument(
            model_id=ObjectId(),
            match_id=ObjectId(),
            elo_estimate=1500.0,
            move_accuracy=0.85,
        )
        assert doc.average_depth == 0
        assert doc.thinking_time_avg == 0
        assert doc.wins == 0
        assert doc.losses == 0
        assert doc.draws == 0
        assert doc.total_games == 0

    def test_benchmark_document_with_stats(self):
        """Test BenchmarkDocument with stats."""
        doc = BenchmarkDocument(
            model_id=ObjectId(),
            match_id=ObjectId(),
            elo_estimate=1500.0,
            move_accuracy=0.85,
            average_depth=20.0,
            thinking_time_avg=5000.0,
            wins=1,
            losses=0,
            draws=0,
            total_games=1,
        )
        assert doc.average_depth == 20.0
        assert doc.thinking_time_avg == 5000.0
        assert doc.wins == 1


class TestRequestSchemas:
    """Tests for API request schemas."""

    def test_match_create_request(self):
        """Test MatchCreateRequest."""
        data = MatchCreateRequest(
            model_a_id="507f1f77bcf86cd799439011",
            model_b_id="507f1f77bcf86cd799439012",
        )
        assert data.mode == MatchMode.RAPID
        assert data.time_control == 10

    def test_move_create_request(self):
        """Test MoveCreateRequest."""
        data = MoveCreateRequest(
            move_san="e4",
            thinking_time_ms=5000,
        )
        assert data.move_uci is None
        assert data.thinking_time_ms == 5000

    def test_model_create_request(self):
        """Test ModelCreateRequest."""
        data = ModelCreateRequest(
            name="Claude 3.5",
            model_id="anthropic/claude-3.5",
        )
        assert data.provider == "openrouter"
        assert data.capabilities == {}

    def test_benchmark_create_request(self):
        """Test BenchmarkCreateRequest."""
        data = BenchmarkCreateRequest(
            model_id="507f1f77bcf86cd799439011",
            match_id="507f1f77bcf86cd799439012",
            elo_estimate=1500.0,
            move_accuracy=0.85,
        )
        assert data.thinking_time_avg == 0
        assert data.average_depth == 0