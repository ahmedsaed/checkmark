"""
Match Service for Checkmark Platform
Handles match creation, game loop orchestration, and turn management.

Uses MongoDB for persistent storage.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from bson import ObjectId

from services.chess_engine import ChessEngine
from services.ai_model_service import AIModelService
import litellm

logger = logging.getLogger("checkmark")


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
            "time_control": match_doc.get("time_control"),
            "white_side": str(match_doc["white_side"]) if match_doc.get("white_side") else None,
            "status": match_doc["status"],
            "winner_id": str(match_doc["winner_id"]) if match_doc.get("winner_id") else None,
            "total_moves": match_doc.get("total_moves", 0),
            "board_fen": match_doc.get("board_fen"),
            "started_at": match_doc.get("started_at"),
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
        max_moves: int = 100,
    ) -> Dict[str, Any]:
        """Create a new match and persist it to MongoDB."""
        db = await self._get_db()
        matches_col = db["matches"]
        models_col = db["models"]

        # Validate ObjectIds
        self._ensure_object_id(model_a_id)
        self._ensure_object_id(model_b_id)

        # Validate that models exist in the database
        model_a = await models_col.find_one({"_id": ObjectId(model_a_id)})
        if not model_a:
            raise ValueError(f"Model {model_a_id} not found")

        model_b = await models_col.find_one({"_id": ObjectId(model_b_id)})
        if not model_b:
            raise ValueError(f"Model {model_b_id} not found")

        match_doc = {
            "model_a_id": ObjectId(model_a_id),
            "model_b_id": ObjectId(model_b_id),
            "mode": mode,
            "max_moves": max_moves,
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

        # Extract move details BEFORE pushing to board
        move_obj = board.parse_san(san)
        from_square = self.chess_engine.square_to_str(move_obj.from_square)
        to_square = self.chess_engine.square_to_str(move_obj.to_square)
        uci = move_obj.uci()
        promotion = move_obj.promotion

        # Execute move
        board = self.chess_engine.push_san(board, san)
        new_fen = self.chess_engine.get_board_fen(board)

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

    # ------------------------------------------------------------------
    # Helpers for auto-play
    # ------------------------------------------------------------------

    def _build_move_prompt(self, fen: str, white: bool) -> str:
        """Build a prompt for move generation."""
        side = "White" if white else "Black"
        return (
            f"Current position (FEN): {fen}\n"
            f"You are {side}. Generate the best move for this position.\n"
            f"Return ONLY the move in SAN notation (e.g., 'e4' or 'Nf3').\n"
            f"No other text, no quotes."
        )

   

    async def _get_ai_move(self, match_id: str, model_id: str, fen: str, white: bool) -> str:
        """Generate a move using AI with tool-calling."""
        ai_service = AIModelService()
        move_san = await ai_service.generate_move_with_tools(match_id, model_id)
        if move_san:
            return move_san
        else:
            raise ValueError(f"AI failed to generate move for {model_id}")

    async def _execute_move(self, match_id: str, san: str, white: bool) -> None:
        """Validate turn and check game status after move has been recorded."""
        # Fetch match
        match_doc = await self.get_match(match_id)
        if not match_doc:
            raise ValueError(f"Match {match_id} not found")

        if match_doc["status"] != "active":
            raise ValueError(f"Match {match_id} is not active")

        # Parse FEN and validate turn
        board = self.chess_engine.parse_fen(match_doc["board_fen"])
        expected_turn = 0 if white else 1

        if board.turn != expected_turn:
            raise ValueError(
                f"Turn mismatch for {match_id}: expected {white}, got {not white}"
            )

        # Move was already executed by AI service via make_move()
        # Just check for game end
        status = self.chess_engine.get_game_status(board)
        if status["status"] in ["checkmate", "stalemate", "draw"]:
            await self._finalize_match(match_id, {"status": "finished"})

    async def _check_game_status(self, match_id: str) -> dict:
        """Get current game status."""
        match_doc = await self.get_match(match_id)
        if not match_doc:
            return {"status": "active"}

        board = self.chess_engine.parse_fen(match_doc["board_fen"])
        return self.chess_engine.get_game_status(board)

    async def _finalize_match(
        self, match_id: str, game_status: dict, reached_max_moves: bool = False, error: str = None
    ):
        """Finalize a match: update status, winner, and model stats."""
        match = await self.get_match(match_id)

        # Determine winner
        winner_id = None
        game_status_status = game_status.get("status", "unknown")
        if game_status_status == "checkmate":
            winner_side = game_status.get("winner", "unknown")
            if winner_side == "white":
                winner_id = match["model_a_id"]
            else:
                winner_id = match["model_b_id"]

        # Update match
        updates = {
            "status": "finished" if not reached_max_moves and not error else game_status_status,
        }
        if winner_id:
            outcome = "1-0" if winner_id == match["model_a_id"] else "0-1"
            updates["winner_id"] = winner_id
            updates["outcome"] = outcome
        if game_status_status in ["checkmate", "stalemate", "draw"]:
            updates["ended_at"] = datetime.utcnow()

        await self.update_match(match_id, updates)

        # Update model stats
        await self._update_model_stats(match_id, winner_id, reached_max_moves, error)

    async def _update_model_stats(
        self, match_id: str, winner_id: str, reached_max_moves: bool = False, error: str = None
    ):
        """Update benchmark stats for models."""
        match = await self.get_match(match_id)

        if reached_max_moves:
            # Draw for both
            await self._increment_model_stat(match["model_a_id"], "draws")
            await self._increment_model_stat(match["model_b_id"], "draws")
        elif winner_id:
            # Winner gets a win
            await self._increment_model_stat(match["model_a_id"], "wins")
            await self._increment_model_stat(match["model_b_id"], "losses")
        else:
            # Draw or other outcome
            await self._increment_model_stat(match["model_a_id"], "draws")
            await self._increment_model_stat(match["model_b_id"], "draws")

        # Increment total_games for both
        await self._increment_model_stat(match["model_a_id"], "total_games")
        await self._increment_model_stat(match["model_b_id"], "total_games")

    async def _increment_model_stat(self, model_id: str, stat: str) -> None:
        """Increment a stat for a model."""
        db = await self._get_db()
        models_col = db["models"]
        result = await models_col.update_one(
            {"_id": ObjectId(model_id)},
            {"$inc": {f"benchmark_stats.{stat}": 1}},
        )
        if result.matched_count == 0:
            logger.warning(f"Model {model_id} not found for stats update")

    async def auto_play_match(self, match_id: str, max_moves: int = 100):
        """
        Auto-play a match between two models in the background.
        Runs until game ends, max_moves reached, or error occurs.
        """
        try:
            logger.info(f"Starting auto-play for match {match_id}")

            # Get match details
            match = await self.get_match(match_id)
            if not match:
                raise ValueError(f"Match {match_id} not found")

            game_status = None
            # Auto-play loop
            while match["status"] == "active":
                # Check max moves
                if match["total_moves"] >= max_moves:
                    logger.info(f"Match {match_id} reached max moves ({max_moves})")
                    game_status = self._check_game_status(match_id)
                    await self._finalize_match(match_id, game_status=game_status, reached_max_moves=True)
                    break

                # White's move (model_a)
                try:
                    logger.info(f"Match {match_id}: White's turn (move {match['total_moves'] + 1})")
                    move_white = await self._get_ai_move(
                        match_id, match["model_a_id"], match["board_fen"], white=True
                    )
                    await self._execute_move(match_id, move_white, white=True)
                except Exception as e:
                    logger.error(f"White move failed for match {match_id}: {e}")
                    await self._finalize_match(match_id, {"status": "abandoned"}, error=str(e))
                    break

                # Check game status
                game_status = await self._check_game_status(match_id)
                if game_status["status"] != "active":
                    logger.info(f"Match {match_id} ended: {game_status['status']}")
                    await self._finalize_match(match_id, game_status=game_status)
                    break

                # Black's move (model_b)
                try:
                    logger.info(f"Match {match_id}: Black's turn (move {match['total_moves'] + 1})")
                    move_black = await self._get_ai_move(
                        match_id, match["model_b_id"], match["board_fen"], white=False
                    )
                    await self._execute_move(match_id, move_black, white=False)
                except Exception as e:
                    logger.error(f"Black move failed for match {match_id}: {e}")
                    await self._finalize_match(match_id, {"status": "abandoned"}, error=str(e))
                    break

                # Check game status
                game_status = await self._check_game_status(match_id)
                if game_status["status"] != "active":
                    logger.info(f"Match {match_id} ended: {game_status['status']}")
                    await self._finalize_match(match_id, game_status=game_status)
                    break

            logger.info(f"Match {match_id} auto-play completed: status={game_status['status'] if game_status else 'unknown'}")

        except Exception as e:
            logger.error(f"Auto-play failed for match {match_id}: {e}")
            game_status = {"status": "abandoned"}
            await self._finalize_match(match_id, game_status=game_status, error=str(e))
