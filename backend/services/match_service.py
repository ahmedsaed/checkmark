"""
Match Service for Checkmark Platform
Handles match creation, game loop orchestration, and turn management
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import uuid

from chess_engine import ChessEngine, board


class MatchStatus(str, Enum):
    ACTIVE = "active"
    FINISHED = "finished"
    ABANDONED = "abandoned"


@dataclass
class Match:
    """Represents a match between two AI models"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    model_a_id: str = ""
    model_b_id: str = ""
    mode: str = "rapid"
    time_control: int = 10
    white_side: str = ""  # Which model plays white
    board_fen: str = field(default_factory=lambda: ChessEngine().get_board_fen(board()))
    status: MatchStatus = MatchStatus.ACTIVE
    winner_id: Optional[str] = None
    total_moves: int = 0
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None

    def __post_init__(self):
        """Initialize board to standard position"""
        if self.board_fen == "":
            self.board_fen = ChessEngine().get_board_fen(board())

    @property
    def white_model(self) -> str:
        """Get the ID of the model playing white"""
        return self.white_side or self.model_a_id

    @property
    def black_model(self) -> str:
        """Get the ID of the model playing black"""
        return self.model_b_id

    def get_current_player(self) -> str:
        """
        Determine whose turn it is based on total_moves count.
        White plays moves 1, 3, 5... (odd)
        Black plays moves 2, 4, 6... (even)
        """
        if self.total_moves % 2 == 0:
            return self.white_model
        return self.black_model

    def advance_turn(self) -> bool:
        """
        Advance the turn counter.
        
        Returns:
            True if turn was advanced successfully, False if game is over
        """
        game_status = ChessEngine().get_game_status(self.board_fen)
        if game_status['status'] in ['checkmate', 'stalemate', 'draw']:
            return False
        
        self.total_moves += 1
        return True

    def is_game_over(self) -> bool:
        """Check if the game has ended"""
        game_status = ChessEngine().get_game_status(self.board_fen)
        return game_status['status'] != 'active'

    def set_winner(self, winner_id: str):
        """Set the winner of the match"""
        self.winner_id = winner_id
        self.status = MatchStatus.FINISHED
        self.ended_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert match to dictionary"""
        return {
            'id': self.id,
            'model_a_id': self.model_a_id,
            'model_b_id': self.model_b_id,
            'mode': self.mode,
            'time_control': self.time_control,
            'white_side': self.white_side,
            'status': self.status.value,
            'winner_id': self.winner_id,
            'total_moves': self.total_moves,
            'board_fen': self.board_fen,
            'started_at': self.started_at.isoformat(),
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
        }


class MatchService:
    """Service for managing chess matches"""

    def __init__(self, chess_engine: ChessEngine):
        self.chess_engine = chess_engine
        self.matches: Dict[str, Match] = {}

    def create_match(
        self,
        model_a: str,
        model_b: str,
        mode: str = "rapid",
        time_control: int = 10,
        white_side: Optional[str] = None,
    ) -> Match:
        """
        Create a new match between two models.
        
        Args:
            model_a: ID of first model
            model_b: ID of second model
            mode: Match mode (best_of, rapid, blitz, bullet)
            time_control: Time control in minutes
            white_side: Optional model ID that plays white
            
        Returns:
            Match: Created match object
        """
        match = Match(
            model_a_id=model_a,
            model_b_id=model_b,
            mode=mode,
            time_control=time_control,
            white_side=white_side,
        )
        self.matches[match.id] = match
        return match

    def get_match(self, match_id: str) -> Optional[Match]:
        """Get a match by ID"""
        return self.matches.get(match_id)

    def get_current_move_maker(self, match_id: str) -> str:
        """
        Get the ID of the model whose turn it is.
        
        Args:
            match_id: ID of the match
            
        Returns:
            str: ID of model whose turn it is
        """
        match = self.get_match(match_id)
        if not match:
            raise ValueError(f"Match {match_id} not found")
        return match.get_current_player()

    def advance_turn(self, match_id: str) -> bool:
        """
        Advance the turn for a match.
        
        Args:
            match_id: ID of the match
            
        Returns:
            bool: True if turn was advanced, False if game is over
        """
        match = self.get_match(match_id)
        if not match:
            raise ValueError(f"Match {match_id} not found")
        
        if match.status != MatchStatus.ACTIVE:
            raise ValueError(f"Match {match_id} is not active")
        
        return match.advance_turn()

    def complete_match(self, match_id: str, winner_id: str):
        """
        Mark a match as finished and set winner.
        
        Args:
            match_id: ID of the match
            winner_id: ID of the winning model
        """
        match = self.get_match(match_id)
        if not match:
            raise ValueError(f"Match {match_id} not found")
        
        match.set_winner(winner_id)

    def get_active_matches(self) -> List[Match]:
        """Get all active matches"""
        return [m for m in self.matches.values() if m.status == MatchStatus.ACTIVE]

    def to_dict(self) -> Dict[str, Any]:
        """Convert all matches to dictionaries"""
        return {
            match_id: match.to_dict()
            for match_id, match in self.matches.items()
        }
