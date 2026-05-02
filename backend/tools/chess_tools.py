"""
Agentic Chess Tools for Checkmark Platform.

Tools exposed to AI agents for interacting with chess games.
Each tool validates moves against the current board state and
returns structured responses with legal alternatives on failure.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from services.chess_engine import ChessEngine
from services.match_service import MatchService


class ToolType(str, Enum):
    """Types of chess tools."""

    GET_BOARD_STATE = "get_board_state"
    GET_LEGAL_MOVES = "get_legal_moves"
    MAKE_MOVE = "make_move"
    UNDO_MOVE = "undo_move"
    GET_GAME_STATUS = "get_game_status"


@dataclass
class ToolResponse:
    """Standard response for all tools."""

    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "success": self.success,
            "message": self.message,
        }
        if self.data is not None:
            result["data"] = self.data
        if self.error is not None:
            result["error"] = self.error
        return result


class GetBoardStateTool:
    """Tool to get current board state."""

    def __init__(self, match_id: str, match_service: MatchService):
        self.match_id = match_id
        self.match_service = match_service

    def call(self, side: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current board state.

        Args:
            side: Optional side to focus on ('white' or 'black').

        Returns:
            Dict with board state information.
        """
        match = self.match_service.get_match(self.match_id)
        if not match:
            return ToolResponse(
                success=False,
                message="Match not found",
                error="MATCH_NOT_FOUND",
            ).to_dict()

        engine = ChessEngine()
        fen = match["board_fen"]
        board = engine.parse_fen(fen)

        piece_positions = self._get_piece_positions(board)
        game_status = engine.get_game_status(board)

        return ToolResponse(
            success=True,
            message="Board state retrieved successfully",
            data={
                "fen": fen,
                "turn": "white" if board.turn else "black",
                "piece_positions": piece_positions,
                "game_status": game_status,
            },
        ).to_dict()

    def _get_piece_positions(self, board) -> Dict[str, List[str]]:
        """Get positions of all piece types."""
        positions: Dict[str, List[str]] = {
            "white_king": [],
            "black_king": [],
            "white_pawns": [],
            "black_pawns": [],
            "white_rooks": [],
            "black_rooks": [],
            "white_knights": [],
            "black_knights": [],
            "white_bishops": [],
            "black_bishops": [],
            "white_queens": [],
            "black_queens": [],
            "white_pieces": [],
            "black_pieces": [],
            "all_pieces": [],
        }

        piece_type_map = {
            1: "pawns",
            2: "knights",
            3: "bishops",
            4: "rooks",
            5: "queens",
            6: "king",
        }

        for square_idx in board.square_indices():
            piece = board.piece_at(square_idx)
            if piece:
                square = board.square_at(square_idx).name
                piece_type = piece.piece_type
                piece_color = piece.color

                type_name = piece_type_map.get(piece_type, f"piece_{piece_type}")

                if piece_color == 0:  # WHITE
                    positions[f"white_{type_name}"].append(square)
                    positions["white_pieces"].append(square)
                else:  # BLACK
                    positions[f"black_{type_name}"].append(square)
                    positions["black_pieces"].append(square)

                positions["all_pieces"].append({
                    "square": square,
                    "piece": piece.piece_name,
                    "color": piece_color,
                })

        return positions


class GetLegalMovesTool:
    """Tool to get all legal moves."""

    def __init__(self, match_id: str, match_service: MatchService):
        self.match_id = match_id
        self.match_service = match_service

    def call(self) -> Dict[str, Any]:
        """
        Get all legal moves from current position.

        Returns:
            Dict with list of legal moves in SAN notation.
        """
        match = self.match_service.get_match(self.match_id)
        if not match:
            return ToolResponse(
                success=False,
                message="Match not found",
                error="MATCH_NOT_FOUND",
            ).to_dict()

        engine = ChessEngine()
        board = engine.parse_fen(match["board_fen"])
        legal_moves = engine.get_all_legal_moves_san(board)

        return ToolResponse(
            success=True,
            message=f"Found {len(legal_moves)} legal moves",
            data={"legal_moves": legal_moves},
        ).to_dict()


class MakeMoveTool:
    """Tool to make a move in the game."""

    def __init__(self, match_id: str, match_service: MatchService):
        self.match_id = match_id
        self.match_service = match_service

    def call(self, move_san: str, thinking_time_ms: Optional[int] = None) -> Dict[str, Any]:
        """
        Make a move in the game.

        Args:
            move_san: Move in SAN notation (e.g., "e4", "Nf3", "Qxf7+").
            thinking_time_ms: Optional thinking time in milliseconds.

        Returns:
            Dict with success status and board state.
        """
        match = self.match_service.get_match(self.match_id)
        if not match:
            return ToolResponse(
                success=False,
                message="Match not found",
                error="MATCH_NOT_FOUND",
            ).to_dict()

        if match["status"] != "active":
            return ToolResponse(
                success=False,
                message=f"Match is not active (status: {match['status']})",
                error="MATCH_NOT_ACTIVE",
            ).to_dict()

        # Validate the move
        engine = ChessEngine()
        board = engine.parse_fen(match["board_fen"])
        is_valid, legal_moves = engine.validate_move(board, move_san)

        if not is_valid:
            return ToolResponse(
                success=False,
                message=f"Invalid move: '{move_san}' is not legal",
                error="INVALID_MOVE",
                data={
                    "legal_moves": legal_moves[:20],
                    "suggestion": f"Try one of these: {', '.join(legal_moves[:5])}...",
                },
            ).to_dict()

        # Execute the move via MatchService (persists to MongoDB)
        try:
            result = self.match_service.make_move(
                match_id=self.match_id,
                san=move_san,
                thinking_time_ms=thinking_time_ms,
            )
            return ToolResponse(
                success=True,
                message=f"Move {move_san} executed successfully",
                data=result,
            ).to_dict()
        except ValueError as e:
            return ToolResponse(
                success=False,
                message=str(e),
                error="MOVE_FAILED",
            ).to_dict()


class UndoMoveTool:
    """Tool to undo the last move."""

    def __init__(self, match_id: str, match_service: MatchService):
        self.match_id = match_id
        self.match_service = match_service

    def call(self) -> Dict[str, Any]:
        """
        Undo the last move.

        Returns:
            Dict with previous board state.
        """
        match = self.match_service.get_match(self.match_id)
        if not match:
            return ToolResponse(
                success=False,
                message="Match not found",
                error="MATCH_NOT_FOUND",
            ).to_dict()

        if match["total_moves"] <= 0:
            return ToolResponse(
                success=False,
                message="No moves to undo",
                error="NO_MOVES_TO_UNDO",
            ).to_dict()

        engine = ChessEngine()
        board = engine.parse_fen(match["board_fen"])
        board = engine.pop_move(board)
        previous_fen = engine.get_board_fen(board)

        # Persist the undone state
        self.match_service.update_match(
            self.match_id,
            {
                "board_fen": previous_fen,
                "total_moves": match["total_moves"] - 1,
            },
        )

        return ToolResponse(
            success=True,
            message="Move undone successfully",
            data={
                "previous_fen": previous_fen,
                "total_moves": match["total_moves"] - 1,
            },
        ).to_dict()


class GetGameStatusTool:
    """Tool to get current game status."""

    def __init__(self, match_id: str, match_service: MatchService):
        self.match_id = match_id
        self.match_service = match_service

    def call(self) -> Dict[str, Any]:
        """
        Get current game status.

        Returns:
            Dict with game status information.
        """
        match = self.match_service.get_match(self.match_id)
        if not match:
            return ToolResponse(
                success=False,
                message="Match not found",
                error="MATCH_NOT_FOUND",
            ).to_dict()

        engine = ChessEngine()
        game_status = engine.get_game_status(engine.parse_fen(match["board_fen"]))

        return ToolResponse(
            success=True,
            message="Game status retrieved",
            data={
                "status": game_status.get("status", "active"),
                "is_checkmate": game_status.get("is_checkmate", False),
                "is_stalemate": game_status.get("is_stalemate", False),
                "is_insufficient_material": game_status.get("is_insufficient_material", False),
                "move_count": game_status.get("move_count", 0),
                "winner": game_status.get("winner"),
            },
        ).to_dict()


# Tool factory for creating all tools
def create_tools(match_id: str, match_service: MatchService) -> Dict[ToolType, Any]:
    """
    Create all chess tools for a match.

    Args:
        match_id: ID of the match.
        match_service: Match service instance.

    Returns:
        Dict mapping tool types to tool instances.
    """
    return {
        ToolType.GET_BOARD_STATE: GetBoardStateTool(match_id, match_service),
        ToolType.GET_LEGAL_MOVES: GetLegalMovesTool(match_id, match_service),
        ToolType.MAKE_MOVE: MakeMoveTool(match_id, match_service),
        ToolType.UNDO_MOVE: UndoMoveTool(match_id, match_service),
        ToolType.GET_GAME_STATUS: GetGameStatusTool(match_id, match_service),
    }
