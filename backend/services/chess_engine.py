"""
Chess Engine Service for Checkmark Platform
Implements core chess logic using python-chess library
"""

from chess import Board, Square, Move, COLOR_WHITE, COLOR_BLACK
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import uuid


@dataclass
class ChessEngine:
    """
    Chess engine providing board state management, move validation,
    and game status detection using python-chess library.
    """

    def initialize_board(self) -> Board:
        """
        Create a new standard chess game board.
        
        Returns:
            Board: New game board in initial position
        """
        return Board()

    def get_legal_moves(self, board: Board, square: Square = None) -> List[Move]:
        """
        Get all legal moves from the current position, or from a specific square.
        
        Args:
            board: Current board state
            square: Optional square to get moves from
            
        Returns:
            List of legal Move objects (UCI format internally)
        """
        if square:
            return list(board.legal_moves(square))
        return list(board.legal_moves)

    def make_move(self, board: Board, move: Move) -> Board:
        """
        Execute a move on the board.
        
        Args:
            board: Current board state
            move: Move to execute (can be UCI or SAN notation)
            
        Returns:
            Board: New board state after move
        """
        return board.push(move)

    def push_san(self, board: Board, san: str) -> Board:
        """
        Parse SAN notation and execute the move.
        
        Args:
            board: Current board state
            san: Move in SAN notation (e.g., 'e4', 'Nf3', 'Qxf7+')
            
        Returns:
            Board: New board state after move
        """
        return board.push_san(san)

    def pop_move(self, board: Board) -> Board:
        """
        Undo the last move.
        
        Args:
            board: Current board state
            
        Returns:
            Board: Board state before last move
        """
        return board.pop()

    def get_board_fen(self, board: Board) -> str:
        """
        Get FEN string representation of board state.
        
        Args:
            board: Current board state
            
        Returns:
            str: FEN string representation
        """
        return board.fen()

    def parse_fen(self, fen: str) -> Board:
        """
        Parse FEN string to create board state.
        
        Args:
            fen: FEN string representation
            
        Returns:
            Board: Board state from FEN
        """
        return Board(fen)

    def get_game_status(self, board: Board) -> Dict[str, Any]:
        """
        Check current game status.
        
        Args:
            board: Current board state
            
        Returns:
            Dict with game status information:
                - status: 'active', 'checkmate', 'stalemate', 'draw', or 'game_over'
                - is_check: Whether current player is in check
                - is_checkmate: Whether it's checkmate
                - is_stalemate: Whether it's stalemate
                - is_insufficient_material: Whether it's a draw due to insufficient material
                - winner: 'white' or 'black' if game is over
        """
        is_check = board.is_check()
        is_checkmate = board.is_checkmate()
        is_stalemate = board.is_stalemate()
        is_insufficient = board.is_insufficient_material()
        is_draw = board.is_draw()
        
        if is_checkmate:
            winner = 'white' if board.turn == COLOR_BLACK else 'black'
            return {
                'status': 'checkmate',
                'is_check': True,
                'is_checkmate': True,
                'is_stalemate': False,
                'is_insufficient_material': False,
                'winner': winner,
                'move_count': board.turn_count
            }
        elif is_stalemate:
            return {
                'status': 'stalemate',
                'is_check': False,
                'is_checkmate': False,
                'is_stalemate': True,
                'is_insufficient_material': False,
                'winner': None,
                'move_count': board.turn_count
            }
        elif is_insufficient:
            return {
                'status': 'draw',
                'is_check': False,
                'is_checkmate': False,
                'is_stalemate': False,
                'is_insufficient_material': True,
                'winner': None,
                'move_count': board.turn_count
            }
        elif is_draw:
            return {
                'status': 'draw',
                'is_check': False,
                'is_checkmate': False,
                'is_stalemate': False,
                'is_insufficient_material': False,
                'winner': None,
                'move_count': board.turn_count
            }
        else:
            return {
                'status': 'active',
                'is_check': is_check,
                'is_checkmate': False,
                'is_stalemate': False,
                'is_insufficient_material': False,
                'winner': None,
                'move_count': board.turn_count
            }

    def validate_move(self, board: Board, san: str) -> tuple[bool, Optional[List[str]]]:
        """
        Validate if a move is legal.
        
        Args:
            board: Current board state
            san: Move in SAN notation to validate
            
        Returns:
            Tuple of (is_valid, legal_moves) where legal_moves is a list
            of all legal moves from current position if move is invalid
        """
        try:
            move = board.parse_san(san)
            if move in board.legal_moves:
                return True, None
            return False, [str(m) for m in board.legal_moves]
        except ValueError:
            # Invalid SAN notation
            return False, [str(m) for m in board.legal_moves]

    def get_all_legal_moves_san(self, board: Board) -> List[str]:
        """
        Get all legal moves in SAN notation.
        
        Args:
            board: Current board state
            
        Returns:
            List of legal moves in SAN notation
        """
        return [str(move) for move in board.legal_moves]

    def get_piece_at(self, board: Board, square: Square) -> Optional[str]:
        """
        Get piece at a given square.
        
        Args:
            board: Current board state
            square: Square to check
            
        Returns:
            Piece character (e.g., 'K', 'q', 'P') or None if empty
        """
        return board.piece_at(square)

    def get_piece_square(self, board: Board, piece_type: str = None) -> Optional[str]:
        """
        Get square for a piece of given type.
        
        Args:
            board: Current board state
            piece_type: Optional piece type filter (e.g., 'K', 'N', 'P')
            
        Returns:
            Square in UCI notation or None if not found
        """
        for square in board.square_indices():
            piece = board.piece_at(square)
            if piece and (piece_type is None or piece.piece_type == piece_type):
                return str(square)
        return None

    def convert_uci_to_san(self, uci: str) -> str:
        """
        Convert UCI move notation to SAN.
        
        Args:
            uci: Move in UCI notation (e.g., 'e2e4', 'g1f3')
            
        Returns:
            Move in SAN notation
        """
        move = board.parse_uci(uci)
        return str(move) if move else uci


# Global board instance for convenience
board = None
