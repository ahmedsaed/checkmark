"""Move validation middleware for Checkmark backend.

This middleware intercepts all move-related API requests and validates them
against the current board state before they reach the business logic layer.
Invalid moves return structured errors with legal alternatives.
"""

import json
from typing import Dict, Any, Optional, List
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
import anyio
import logging

from services.chess_engine import ChessEngine
from services.match_service import MatchService
from utils.mongo_db import get_database

logger = logging.getLogger(__name__)


class MoveValidationMiddleware(BaseHTTPMiddleware):
    """Validates all move-related API requests before they reach handlers."""

    def __init__(self, app, chess_engine: ChessEngine = None):
        super().__init__(app)
        self.chess_engine = chess_engine or ChessEngine()

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Only validate POST /api/matches/{match_id}/moves
        if (
            request.method == "POST"
            and "/api/matches/" in request.url.path
            and "/moves" in request.url.path
        ):
            return await self._validate_move_request(request, call_next)
        return await call_next(request)

    async def _validate_move_request(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Validate a move request before passing it to the handler."""
        try:
            # Extract match_id from path
            path_parts = request.url.path.split("/")
            if len(path_parts) < 5:
                return await call_next(request)

            match_id = path_parts[3]  # /api/matches/{match_id}/moves

            # Parse request body and re-attach it so the handler can read it too
            body_bytes = await request.body()
            body = json.loads(body_bytes) if body_bytes else {}
            move_san = body.get("move_san", "")

            # Re-attach the body so downstream handlers can read it
            await request._receive({"type": "http.request", "body": body_bytes})

            if not move_san:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "message": "move_san is required",
                        "error": "MISSING_MOVE_SAN",
                    },
                )

            # Get current board state
            db = await get_database()
            matches_col = db["matches"]
            match_doc = await matches_col.find_one({"_id": match_id})

            if not match_doc:
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "message": f"Match {match_id} not found",
                        "error": "MATCH_NOT_FOUND",
                    },
                )

            if match_doc.get("status") != "active":
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "message": f"Match is not active (status: {match_doc.get('status')})",
                        "error": "MATCH_NOT_ACTIVE",
                    },
                )

            # Validate the move
            board = self.chess_engine.parse_fen(match_doc["board_fen"])
            is_valid, legal_moves = self.chess_engine.validate_move(board, move_san)

            if not is_valid:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "message": f"Invalid move: '{move_san}' is not legal",
                        "error": "INVALID_MOVE",
                        "data": {
                            "legal_moves": legal_moves[:20],
                            "suggestion": f"Try one of these: {', '.join(legal_moves[:5])}...",
                        },
                    },
                )

            # Move is valid - proceed with the request
            return await call_next(request)

        except Exception as e:
            logger.error(f"Move validation error: {e}")
            # If validation fails, let the request proceed (fail open)
            return await call_next(request)
