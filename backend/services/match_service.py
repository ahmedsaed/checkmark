"""
Match Service for Checkmark Platform
Handles match creation, game loop orchestration, and turn management.

Uses MongoDB for persistent storage.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from bson import ObjectId

from services.chess_engine import ChessEngine


class MatchService:
    """Service for managing chess matches with MongoDB persistence."""

    def __init__(self, chess_engine: ChessEngine):
        self.chess_engine = chess_engine

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _ensure_object_id(value: str) -> ObjectId:
        """Convert a string to ObjectId, raising ValueError if invalid."""
        if not ObjectId.is_valid(value):
            raise ValueError(f"Invalid ObjectId: {value}")
        return ObjectId(value)

    @staticmethod
    def _match_to_response(match_doc: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a MongoDB match document to an API response dict."""
        return {
            "id": str(match_doc["_id"]),
            "model_a_id": str(match_doc["model_a_id"]),
            "model_b_id": str(match_doc["model_b_id"]),
            "mode": match_doc["mode"],
            "time_control": match_doc["time_control"],
            "white_side": str(match_doc["white_side"]) if match_doc.get("white_side") else None,
            "status": match_doc["status"],
            "winner_id": str(match_doc["winner_id"]) if match_doc.get("winner_id") else None,
            "total_moves": match_doc.get("total_moves", 0),
            "board_fen": match_doc.get("board_fen"),
            "started_at": match_doc["started_at"],
            "ended_at": match_doc.get("ended_at"),
        }

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------

    async def create_match(
        self,
        model_a_id: str,
        model_b_id: str,
        mode: str = "rapid",
        time_control: int = 10,
        white_side: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new match and persist it to MongoDB."""
        db = await self._get_db()
        matches_col = db["matches"]

        # Validate ObjectIds
        self._ensure_object_id(model_a_id)
        self._ensure_object_id(model_b_id)
        if white_side:
            self._ensure_object_id(white_side)

        match_doc = {
            "model_a_id": ObjectId(model_a_id),
            "model_b_id": ObjectId(model_b_id),
            "mode": mode,
            "time_control": time_control,
            "white_side": ObjectId(white_side) if white_side else None,
            "board_fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "status": "active",
            "winner_id": None,
            "total_moves": 0,
            "started_at": datetime.utcnow(),
            "ended_at": None,
        }

        result = await matches_col.insert_one(match_doc)
        match_doc["_id"] = result.inserted_id
        return self._match_to_response(match_doc)

    async def get_match(self, match_id: str) -> Optional[Dict[str, Any]]:
        """Get a single match by ID."""
        db = await self._get_db()
        matches_col = db["matches"]

        try:
            match_doc = await matches_col.find_one({"_id": ObjectId(match_id)})
        except Exception:
            return None

        if not match_doc:
            return None

        return self._match_to_response(match_doc)

    async def list_matches(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List matches, optionally filtered by status."""
        db = await self._get_db()
        matches_col = db["matches"]

        query = {}
        if status:
            query["status"] = status

        cursor = matches_col.find(query).sort("started_at", -1)
        matches = []
        async for doc in cursor:
            matches.append(self._match_to_response(doc))
        return matches

    async def update_match(self, match_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update fields on an existing match."""
        db = await self._get_db()
        matches_col = db["matches"]

        # Filter out None values
        updates = {k: v for k, v in updates.items() if v is not None}
        if not updates:
            return None

        result = await matches_col.update_one(
            {"_id": ObjectId(match_id)},
            {"$set": updates},
        )
        if result.matched_count == 0:
            return None

        return await self.get_match(match_id)

    async def complete_match(
        self,
        match_id: str,
        winner_id: str,
        outcome: str = "1-0",
    ) -> Optional[Dict[str, Any]]:
        """Mark a match as finished with a winner."""
        return await self.update_match(
            match_id,
            {
                "status": "finished",
                "winner_id": ObjectId(winner_id),
                "outcome": outcome,
                "ended_at": datetime.utcnow(),
            },
        )

    # ------------------------------------------------------------------
    # Move handling
    # ------------------------------------------------------------------

    async def make_move(
        self,
        match_id: str,
        san: str,
        white_move: bool = True,
        thinking_time_ms: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Validate and record a move for a match.

        Returns a MoveResponse-style dict.
        """
        db = await self._get_db()
        matches_col = db["matches"]
        moves_col = db["moves"]

        # Fetch match
        match_doc = await matches_col.find_one({"_id": ObjectId(match_id)})
        if not match_doc:
            raise ValueError(f"Match {match_id} not found")

        if match_doc["status"] != "active":
            raise ValueError(f"Match {match_id} is not active (status: {match_doc['status']})")

        # Parse FEN and validate move
        board = self.chess_engine.parse_fen(match_doc["board_fen"])
        is_valid, legal_moves = self.chess_engine.validate_move(board, san)

        if not is_valid:
            raise ValueError(
                f"Invalid move: '{san}' is not legal. "
                f"Legal moves: {legal_moves[:10]}"
            )

        # Execute move
        board = self.chess_engine.push_san(board, san)
        new_fen = self.chess_engine.get_board_fen(board)

        # Extract move details
        move_obj = board.parse_san(san)
        from_square = self.chess_engine.square_to_str(move_obj.from_square)
        to_square = self.chess_engine.square_to_str(move_obj.to_square)
        uci = move_obj.uci()
        promotion = move_obj.promotion

        # Game status
        status_info = self.chess_engine.get_game_status(board)

        # Determine move number (white moves are odd, black are even)
        move_number = match_doc["total_moves"] + 1

        # Create move document
        move_doc = {
            "match_id": ObjectId(match_id),
            "move_number": move_number,
            "san": san,
            "uci": uci,
            "from_square": from_square,
            "to_square": to_square,
            "promotion": chr(promotion) if promotion else None,
            "is_check": status_info["is_check"],
            "is_checkmate": status_info["is_checkmate"],
            "is_stalemate": status_info["is_stalemate"],
            "is_castling": board.is_castling(move_obj),
            "is_en_passant": board.is_en_passant(move_obj),
            "thinking_time_ms": thinking_time_ms,
            "timestamp": datetime.utcnow(),
        }
        await moves_col.insert_one(move_doc)

        # Update match
        updates = {
            "board_fen": new_fen,
            "total_moves": move_number,
        }

        if status_info["is_checkmate"]:
            winner_side = "white" if board.turn == 0 else "black"  # 0=white, 1=black
            updates["status"] = "finished"
            updates["outcome"] = "1-0" if winner_side == "white" else "0-1"
            updates["ended_at"] = datetime.utcnow()
            # Determine winner_id based on whose turn it is (the loser just moved)
            loser_is_white = board.turn == 0  # black just moved, so white is winner
            if loser_is_white:
                updates["winner_id"] = match_doc["model_a_id"] if match_doc.get("white_side") == match_doc["model_a_id"] else match_doc["model_b_id"]
            else:
                updates["winner_id"] = match_doc["model_b_id"] if match_doc.get("white_side") == match_doc["model_a_id"] else match_doc["model_a_id"]

        elif status_info["is_stalemate"] or status_info.get("is_insufficient_material") or status_info["status"] == "draw":
            updates["status"] = "finished"
            updates["outcome"] = "1/2-1/2"
            updates["ended_at"] = datetime.utcnow()

        await matches_col.update_one(
            {"_id": ObjectId(match_id)},
            {"$set": updates},
        )

        return {
            "success": True,
            "move_number": move_number,
            "move_from": from_square,
            "move_to": to_square,
            "promotion": chr(promotion) if promotion else None,
            "is_check": status_info["is_check"],
            "is_checkmate": status_info["is_checkmate"],
            "is_stalemate": status_info["is_stalemate"],
            "board_fen": new_fen,
            "timestamp": datetime.utcnow(),
        }

    async def get_moves(self, match_id: str) -> List[Dict[str, Any]]:
        """Get all moves for a match."""
        db = await self._get_db()
        moves_col = db["moves"]

        cursor = moves_col.find({"match_id": ObjectId(match_id)}).sort("move_number", 1)
        moves = []
        async for doc in cursor:
            moves.append({
                "id": str(doc["_id"]),
                "match_id": str(doc["match_id"]),
                "move_number": doc["move_number"],
                "san": doc["san"],
                "uci": doc["uci"],
                "from_square": doc["from_square"],
                "to_square": doc["to_square"],
                "promotion": doc.get("promotion"),
                "is_check": doc.get("is_check", False),
                "is_checkmate": doc.get("is_checkmate", False),
                "thinking_time_ms": doc.get("thinking_time_ms"),
                "timestamp": doc["timestamp"],
            })
        return moves

    # ------------------------------------------------------------------
    # DB access
    # ------------------------------------------------------------------

    async def _get_db(self):
        """Get the MongoDB database instance."""
        from utils.mongo_db import get_database
        return await get_database()
