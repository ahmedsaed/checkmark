"""
Comprehensive tests for the ChessEngine service.

Tests cover:
- Board initialization
- Legal move generation (SAN notation)
- Move validation
- Game status detection (checkmate, stalemate, draw)
- FEN serialization/deserialization
- Move execution and undo
"""

import pytest
from chess import Board, WHITE, BLACK

from services.chess_engine import ChessEngine


@pytest.fixture
def engine():
    """Create a ChessEngine instance for testing."""
    return ChessEngine()


@pytest.fixture
def initial_board(engine):
    """Create an initial board state."""
    return engine.initialize_board()


class TestBoardInitialization:
    """Tests for board initialization."""

    def test_initialize_board_returns_board(self, engine):
        """Test that initialize_board returns a Board object."""
        board = engine.initialize_board()
        assert isinstance(board, Board)

    def test_initial_board_has_correct_fen(self, engine):
        """Test that the initial board has the correct FEN string."""
        board = engine.initialize_board()
        fen = engine.get_board_fen(board)
        assert fen == "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


class TestLegalMoves:
    """Tests for legal move generation."""

    def test_initial_position_has_20_legal_moves(self, initial_board, engine):
        """Test that the initial position has exactly 20 legal moves."""
        legal_moves = engine.get_all_legal_moves_san(initial_board)
        assert len(legal_moves) == 20

    def test_legal_moves_are_in_san_notation(self, initial_board, engine):
        """Test that legal moves are returned in SAN notation."""
        legal_moves = engine.get_all_legal_moves_san(initial_board)
        # All moves should be valid SAN notation
        for move in legal_moves:
            # SAN moves are typically 2-4 characters (e.g., "e4", "Nf3", "O-O")
            assert 2 <= len(move) <= 4

    def test_legal_moves_include_pawn_moves(self, initial_board, engine):
        """Test that pawn moves are included in legal moves."""
        legal_moves = engine.get_all_legal_moves_san(initial_board)
        pawn_moves = [m for m in legal_moves if m[0].isdigit()]
        assert len(pawn_moves) == 16  # 16 pawn moves (e2, d2, c2, b2, a2, f2, g2, h2 each with 1 or 2 squares)

    def test_legal_moves_include_knight_moves(self, initial_board, engine):
        """Test that knight moves are included in legal moves."""
        legal_moves = engine.get_all_legal_moves_san(initial_board)
        knight_moves = [m for m in legal_moves if m.startswith("N")]
        assert len(knight_moves) == 4  # Nb1, Nf1, Nb8, Nf8

    def test_legal_moves_after_some_moves(self, initial_board, engine):
        """Test legal moves after some moves have been made."""
        # Play e4 e5
        board = engine.push_san(initial_board, "e4")
        board = engine.push_san(board, "e5")
        
        legal_moves = engine.get_all_legal_moves_san(board)
        # After e4 e5, there should be 44 legal moves
        assert len(legal_moves) == 44


class TestMoveValidation:
    """Tests for move validation."""

    def test_valid_move_is_valid(self, initial_board, engine):
        """Test that a valid move is correctly identified."""
        is_valid, legal_moves = engine.validate_move(initial_board, "e4")
        assert is_valid is True
        assert legal_moves is None

    def test_invalid_move_is_invalid(self, initial_board, engine):
        """Test that an invalid move is correctly identified."""
        is_valid, legal_moves = engine.validate_move(initial_board, "h5")
        assert is_valid is False
        assert legal_moves is not None
        assert len(legal_moves) > 0

    def test_invalid_san_notation_is_invalid(self, initial_board, engine):
        """Test that invalid SAN notation is correctly identified."""
        is_valid, legal_moves = engine.validate_move(initial_board, "xyz")
        assert is_valid is False
        assert legal_moves is not None

    def test_invalid_move_returns_legal_alternatives(self, initial_board, engine):
        """Test that invalid moves return a list of legal alternatives."""
        is_valid, legal_moves = engine.validate_move(initial_board, "h5")
        assert is_valid is False
        assert isinstance(legal_moves, list)
        assert len(legal_moves) == 20  # Should return all 20 legal moves

    def test_knight_move_validation(self, initial_board, engine):
        """Test knight move validation."""
        # Knight on b1 can move to a3 or c3
        is_valid, _ = engine.validate_move(initial_board, "Na3")
        assert is_valid is False  # Na3 is not legal from b1
        
        is_valid, _ = engine.validate_move(initial_board, "Nc3")
        assert is_valid is True  # Nc3 is legal from b1


class TestMoveExecution:
    """Tests for move execution."""

    def test_push_san_executes_move(self, initial_board, engine):
        """Test that push_san correctly executes a move."""
        board = engine.push_san(initial_board, "e4")
        fen = engine.get_board_fen(board)
        assert "P" in fen  # White pawn should be on e4
        assert "e4" in fen.lower() or "E4" in fen

    def test_push_san_updates_fen(self, initial_board, engine):
        """Test that push_san updates the FEN string."""
        board = engine.push_san(initial_board, "e4")
        fen = engine.get_board_fen(board)
        assert fen != engine.get_board_fen(initial_board)

    def test_push_san_invalid_move_raises(self, initial_board, engine):
        """Test that push_san raises ValueError for invalid moves."""
        with pytest.raises(ValueError):
            engine.push_san(initial_board, "h5")

    def test_make_move_executes_move(self, initial_board, engine):
        """Test that make_move correctly executes a move."""
        from chess import Move
        # Get the first legal move
        legal_moves = engine.get_legal_moves(initial_board)
        assert len(legal_moves) > 0
        move = legal_moves[0]
        
        board = engine.make_move(initial_board, move)
        assert board != initial_board

    def test_move_number_tracking(self, initial_board, engine):
        """Test that move numbers are tracked correctly."""
        board = initial_board
        board = engine.push_san(board, "e4")  # White move 1
        board = engine.push_san(board, "e5")  # Black move 1
        board = engine.push_san(board, "Nf3")  # White move 2
        
        status = engine.get_game_status(board)
        assert status["move_count"] == 3


class TestMoveUndo:
    """Tests for move undo."""

    def test_undo_move_reverts_board(self, initial_board, engine):
        """Test that undo_move correctly reverts the board."""
        board = engine.push_san(initial_board, "e4")
        board = engine.pop_move(board)
        fen = engine.get_board_fen(board)
        assert fen == engine.get_board_fen(initial_board)

    def test_undo_multiple_moves(self, initial_board, engine):
        """Test undoing multiple moves."""
        board = engine.push_san(initial_board, "e4")
        board = engine.push_san(board, "e5")
        board = engine.push_san(board, "Nf3")
        board = engine.push_san(board, "Nc6")
        
        # Undo all moves
        board = engine.pop_move(board)
        board = engine.pop_move(board)
        board = engine.pop_move(board)
        board = engine.pop_move(board)
        
        fen = engine.get_board_fen(board)
        assert fen == engine.get_board_fen(initial_board)

    def test_undo_from_initial_raises(self, initial_board, engine):
        """Test that undoing from initial position raises ValueError."""
        with pytest.raises(IndexError):
            engine.pop_move(initial_board)


class TestGameStatus:
    """Tests for game status detection."""

    def test_initial_position_is_active(self, initial_board, engine):
        """Test that the initial position is active."""
        status = engine.get_game_status(initial_board)
        assert status["status"] == "active"
        assert status["is_checkmate"] is False
        assert status["is_stalemate"] is False

    def test_checkmate_detection(self, engine):
        """Test checkmate detection with Scholar's mate."""
        board = engine.initialize_board()
        # Scholar's mate: 1.e4 e5 2.Qh5 Nc6 3.Bc4 Nf6 4.Qxf7#
        board = engine.push_san(board, "e4")
        board = engine.push_san(board, "e5")
        board = engine.push_san(board, "Qh5")
        board = engine.push_san(board, "Nc6")
        board = engine.push_san(board, "Bc4")
        board = engine.push_san(board, "Nf6")
        board = engine.push_san(board, "Qxf7#")
        
        status = engine.get_game_status(board)
        assert status["status"] == "checkmate"
        assert status["is_checkmate"] is True
        assert status["winner"] == "white"

    def test_stalemate_detection(self, engine):
        """Test stalemate detection."""
        board = engine.initialize_board()
        # Simple stalemate position: White: Ka1, Black: Ka8
        # This is a simplified test - real stalemate requires more setup
        board = engine.parse_fen("8/8/8/8/8/k7/7K/8 w - - 0 1")
        status = engine.get_game_status(board)
        assert status["status"] == "stalemate"
        assert status["is_stalemate"] is True

    def test_insufficient_material_detection(self, engine):
        """Test insufficient material detection."""
        board = engine.parse_fen("8/8/8/8/8/k7/7K/8 w - - 0 1")
        status = engine.get_game_status(board)
        # King vs King is insufficient material
        assert status["is_insufficient_material"] is True

    def test_check_detection(self, engine):
        """Test check detection."""
        board = engine.parse_fen("rnbqkbnr/pppppppp/8/8/8/5Q2/PPPPPPPP/RNB1KBNR b KQkq - 0 1")
        status = engine.get_game_status(board)
        assert status["is_check"] is True

    def test_move_count_in_status(self, engine):
        """Test that move count is included in status."""
        board = engine.initialize_board()
        board = engine.push_san(board, "e4")
        board = engine.push_san(board, "e5")
        
        status = engine.get_game_status(board)
        assert status["move_count"] == 2


class TestFENSerialization:
    """Tests for FEN serialization and deserialization."""

    def test_fen_roundtrip(self, initial_board, engine):
        """Test that FEN serialization and deserialization work correctly."""
        fen = engine.get_board_fen(initial_board)
        board = engine.parse_fen(fen)
        new_fen = engine.get_board_fen(board)
        assert fen == new_fen

    def test_parse_custom_fen(self, engine):
        """Test parsing a custom FEN string."""
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
        board = engine.parse_fen(fen)
        assert engine.get_board_fen(board) == fen

    def test_fen_contains_correct_info(self, initial_board, engine):
        """Test that FEN contains all required information."""
        fen = engine.get_board_fen(initial_board)
        parts = fen.split()
        assert len(parts) == 4  # board, turn, castling, en passant


class TestSquareConversion:
    """Tests for square conversion utilities."""

    def test_square_to_str(self, engine):
        """Test converting a Square to string."""
        from chess import parse_square
        square = parse_square("e4")
        result = engine.square_to_str(square)
        assert result == "e4"

    def test_square_to_str_all_squares(self, engine):
        """Test square_to_str for all 64 squares."""
        from chess import square_name
        for file in "abcdefgh":
            for rank in "12345678":
                square_str = file + rank
                from chess import parse_square
                square = parse_square(square_str)
                result = engine.square_to_str(square)
                assert result == square_str


class TestConvertUCIToSAN:
    """Tests for UCI to SAN conversion."""

    def test_uci_to_san_simple(self, initial_board, engine):
        """Test converting UCI to SAN for a simple move."""
        uci = "e2e4"
        san = engine.convert_uci_to_san(uci)
        assert san == "e4"

    def test_uci_to_san_knight(self, initial_board, engine):
        """Test converting UCI to SAN for a knight move."""
        uci = "g1f3"
        san = engine.convert_uci_to_san(uci)
        assert san == "Nf3"

    def test_uci_to_san_invalid(self, initial_board, engine):
        """Test converting invalid UCI notation."""
        uci = "invalid"
        san = engine.convert_uci_to_san(uci)
        assert san == uci  # Returns original if invalid


class TestPieceAtSquare:
    """Tests for piece retrieval."""

    def test_get_piece_at_square(self, initial_board, engine):
        """Test getting a piece at a specific square."""
        from chess import parse_square
        square = parse_square("e2")
        piece = engine.get_piece_at(initial_board, square)
        assert piece is not None
        assert piece.symbol() == "P"  # White pawn

    def test_get_piece_at_empty_square(self, initial_board, engine):
        """Test getting a piece from an empty square."""
        from chess import parse_square
        square = parse_square("e5")
        piece = engine.get_piece_at(initial_board, square)
        assert piece is None
