"""
Agentic Chess Tools for Checkmark Platform
Tools exposed to AI agents for interacting with chess games
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json

from services.chess_engine import ChessEngine, board as default_board
from services.match_service import Match, MatchService, MatchStatus


class ToolType(str, Enum):
    """Types of chess tools"""
    GET_BOARD_STATE = "get_board_state"
    GET_LEGAL_MOVES = "get_legal_moves"
    MAKE_MOVE = "make_move"
    UNDO_MOVE = "undo_move"
    GET_GAME_STATUS = "get_game_status"


@dataclass
class ToolResponse:
    """Standard response for all tools"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class BoardState:
    """Board state information"""
    fen: str
    piece_positions: Dict[str, List[str]]  # piece_type -> [squares]
    turn: str  # 'white' or 'black'
    castling_rights: str
    en_passant_target: Optional[str]
    fullmove_number: int
    halfmove_clock: int


class GetBoardStateTool:
    """Tool to get current board state"""

    def __init__(self, match_id: str, match_service: MatchService):
        self.match_id = match_id
        self.match_service = match_service

    def call(self, side: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current board state.
        
        Args:
            side: Optional side to focus on ('white' or 'black')
            
        Returns:
            Dict with board state information
        """
        match = self.match_service.get_match(self.match_id)
        if not match:
            return ToolResponse(
                success=False,
                message="Match not found",
                error="MATCH_NOT_FOUND",
            ).to_dict()

        engine = ChessEngine()
        fen = match.board_fen
        board = engine.parse_fen(fen)

        piece_positions = self._get_piece_positions(board)
        game_status = engine.get_game_status(board)

        return ToolResponse(
            success=True,
            message="Board state retrieved successfully",
            data=BoardState(
                fen=fen,
                piece_positions=piece_positions,
                turn="white" if board.turn == 1 else "black",
                castling_rights=board.castling_rights,
                en_passant_target=board.ep_square if board.ep_square else None,
                fullmove_number=board.fullmove_number,
                halfmove_clock=board.halfmove_clock,
            ).to_dict(),
            data={
                "fen": fen,
                "turn": game_status.get("winner") or "active",
                "piece_positions": piece_positions,
                "game_status": game_status,
            },
        ).to_dict()

    def _get_piece_positions(self, board) -> Dict[str, List[str]]:
        """Get positions of all piece types"""
        positions = {
            "white_king": [],
            "black_king": [],
            "white_pawns": [],
            "black_pawns": [],
            "white_pieces": [],
            "black_pieces": [],
            "all_pieces": [],
        }

        for square_idx in board.square_indices():
            piece = board.piece_at(square_idx)
            if piece:
                square = board.square_at(square_idx).name
                piece_type = piece.piece_type
                piece_color = piece.color
                
                if piece_color == "white":
                    positions[f"white_{piece_type}s"].append(square)
                    positions["white_pieces"].append(square)
                else:
                    positions[f"black_{piece_type}s"].append(square)
                    positions["black_pieces"].append(square)
                
                positions["all_pieces"].append({
                    "square": square,
                    "piece": piece.piece_name,
                    "color": piece_color,
                })

        return positions


class GetLegalMovesTool:
    """Tool to get all legal moves"""

    def __init__(self, match_id: str, match_service: MatchService):
        self.match_id = match_id
        self.match_service = match_service

    def call(self) -> Dict[str, Any]:
        """
        Get all legal moves from current position.
        
        Returns:
            Dict with list of legal moves in SAN notation
        """
        match = self.match_service.get_match(self.match_id)
        if not match:
            return ToolResponse(
                success=False,
                message="Match not found",
                error="MATCH_NOT_FOUND",
            ).to_dict()

        engine = ChessEngine()
        legal_moves = engine.get_all_legal_moves_san(engine.parse_fen(match.board_fen))

        return ToolResponse(
            success=True,
            message=f"Found {len(legal_moves)} legal moves",
            data={"legal_moves": legal_moves},
        ).to_dict()


class MakeMoveTool:
    """Tool to make a move in the game"""

    def __init__(self, match_id: str, match_service: MatchService):
        self.match_id = match_id
        self.match_service = match_service

    def call(self, move_san: str, is_white_move: bool = True) -> Dict[str, Any]:
        """
        Make a move in the game.
        
        Args:
            move_san: Move in SAN notation (e.g., "e4", "Nf3", "Qxf7+")
            is_white_move: Whether this is white's move (default: True)
            
        Returns:
            Dict with success status and board state
        """
        match = self.match_service.get_match(self.match_id)
        if not match:
            return ToolResponse(
                success=False,
                message="Match not found",
                error="MATCH_NOT_FOUND",
            ).to_dict()

        # Check if it's the correct player's turn
        current_player = match.get_current_player()
        if is_white_move:
            expected_player = match.white_model
        else:
            expected_player = match.black_model

        if current_player != expected_player:
            return ToolResponse(
                success=False,
                message=f"It's {current_player}'s turn, not {expected_player}",
                error="WRONG_PLAYER_TURN",
            ).to_dict()

        # Validate the move
        engine = ChessEngine()
        is_valid, legal_moves = engine.validate_move(engine.parse_fen(match.board_fen), move_san)

        if not is_valid:
            # Return error with legal alternatives
            return ToolResponse(
                success=False,
                message=f"Invalid move: {move_san} is not legal",
                error="INVALID_MOVE",
                data={
                    "legal_moves": legal_moves,
                    "suggestion": f"Try one of these legal moves: {', '.join(legal_moves[:5])}...",
                },
            ).to_dict()

        # Execute the move
        board = engine.push_san(match.board_fen, move_san)
        match.board_fen = engine.get_board_fen(board)
        
        # Update game status
        game_status = engine.get_game_status(board)
        if game_status['status'] != 'active':
            match.status = MatchStatus.FINISHED
            match.ended_at = match.ended_at or "completed"

        return ToolResponse(
            success=True,
            message=f"Move {move_san} executed successfully",
            data={
                "move_number": match.total_moves + 1,
                "board_fen": match.board_fen,
                "is_check": game_status.get("is_check", False),
                "is_checkmate": game_status.get("is_checkmate", False),
                "is_stalemate": game_status.get("is_stalemate", False),
            },
        ).to_dict()


class UndoMoveTool:
    """Tool to undo the last move"""

    def __init__(self, match_id: str, match_service: MatchService):
        self.match_id = match_id
        self.match_service = match_service

    def call(self) -> Dict[str, Any]:
        """
        Undo the last move.
        
        Returns:
            Dict with previous board state
        """
        match = self.match_service.get_match(self.match_id)
        if not match:
            return ToolResponse(
                success=False,
                message="Match not found",
                error="MATCH_NOT_FOUND",
            ).to_dict()

        if match.total_moves <= 0:
            return ToolResponse(
                success=False,
                message="No moves to undo",
                error="NO_MOVES_TO_UNDO",
            ).to_dict()

        engine = ChessEngine()
        board = engine.parse_fen(match.board_fen)
        board = engine.pop_move(board)
        previous_fen = engine.get_board_fen(board)

        return ToolResponse(
            success=True,
            message="Move undone successfully",
            data={
                "previous_fen": previous_fen,
                "total_moves": match.total_moves - 1,
            },
        ).to_dict()


class GetGameStatusTool:
    """Tool to get current game status"""

    def __init__(self, match_id: str, match_service: MatchService):
        self.match_id = match_id
        self.match_service = match_service

    def call(self) -> Dict[str, Any]:
        """
        Get current game status.
        
        Returns:
            Dict with game status information
        """
        match = self.match_service.get_match(self.match_id)
        if not match:
            return ToolResponse(
                success=False,
                message="Match not found",
                error="MATCH_NOT_FOUND",
            ).to_dict()

        engine = ChessEngine()
        game_status = engine.get_game_status(engine.parse_fen(match.board_fen))

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
        match_id: ID of the match
        match_service: Match service instance
        
    Returns:
        Dict mapping tool types to tool instances
    """
    return {
        ToolType.GET_BOARD_STATE: GetBoardStateTool(match_id, match_service),
        ToolType.GET_LEGAL_MOVES: GetLegalMovesTool(match_id, match_service),
        ToolType.MAKE_MOVE: MakeMoveTool(match_id, match_service),
        ToolType.UNDO_MOVE: UndoMoveTool(match_id, match_service),
        ToolType.GET_GAME_STATUS: GetGameStatusTool(match_id, match_service),
    }
