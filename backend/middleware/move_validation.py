"""Move validation middleware for Checkmark backend.

This middleware intercepts all move-related API requests and validates them
against the current board state before they reach the business logic layer.
Invalid moves return structured errors with legal alternatives.

Uses a proper ASGI middleware (not BaseHTTPMiddleware) to avoid request body
stream consumption issues in newer Starlette versions.
"""

import json
from typing import Any, Dict, List, Optional, Callable, Awaitable
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send
import logging

from services.chess_engine import ChessEngine
from utils.mongo_db import get_database

logger = logging.getLogger(__name__)


class MoveValidationMiddleware:
    """ASGI middleware that validates move requests before they reach handlers."""

    def __init__(self, app: ASGIApp, chess_engine: ChessEngine = None):
        self.app = app
        self.chess_engine = chess_engine or ChessEngine()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # Only intercept POST /api/matches/{match_id}/moves
        if (
            scope["type"] == "http"
            and scope["method"] == "POST"
            and "/api/matches/" in scope["path"]
            and "/moves" in scope["path"]
        ):
            await self._validate_move_request(scope, receive, send)
        else:
            await self.app(scope, receive, send)

    async def _validate_move_request(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        """Validate a move request before passing it to the app."""
        try:
            # Extract match_id from path
            path_parts = scope["path"].split("/")
            if len(path_parts) < 5:
                await self.app(scope, receive, send)
                return

            match_id = path_parts[3]  # /api/matches/{match_id}/moves

            # Read the request body
            body_bytes = b""
            more_body = True
            while more_body:
                message = await receive()
                body_bytes += message.get("body", b"")
                more_body = message.get("more_body", False)

            body = json.loads(body_bytes) if body_bytes else {}
            move_san = body.get("move_san", "")

            # Create a new receive that returns the body bytes
            async def new_receive() -> Message:
                return {"type": "http.request", "body": body_bytes}

            # Create a new send that wraps the original send
            response_sent = False

            async def new_send(message: Message) -> None:
                nonlocal response_sent
                response_sent = True
                await send(message)

            if not move_san:
                response = JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "message": "move_san is required",
                        "error": "MISSING_MOVE_SAN",
                    },
                )
                await response(scope, new_receive, new_send)
                return

            # Get current board state
            db = await get_database()
            matches_col = db["matches"]
            match_doc = await matches_col.find_one({"_id": match_id})

            if not match_doc:
                response = JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "message": f"Match {match_id} not found",
                        "error": "MATCH_NOT_FOUND",
                    },
                )
                await response(scope, new_receive, new_send)
                return

            if match_doc.get("status") != "active":
                response = JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "message": f"Match is not active (status: {match_doc.get('status')})",
                        "error": "MATCH_NOT_ACTIVE",
                    },
                )
                await response(scope, new_receive, new_send)
                return

            # Validate the move
            board = self.chess_engine.parse_fen(match_doc["board_fen"])
            is_valid, legal_moves = self.chess_engine.validate_move(board, move_san)

            if not is_valid:
                response = JSONResponse(
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
                await response(scope, new_receive, new_send)
                return

            # Move is valid - pass to the app with the body re-attached
            scope["body"] = body_bytes
            await self.app(scope, new_receive, new_send)

        except Exception as e:
            logger.error(f"Move validation error: {e}")
            # If validation fails, let the request proceed (fail open)
            await self.app(scope, receive, send)
