"""
AI Model Service for Checkmark Platform
Handles AI model integration with LiteLLM/OpenRouter and MongoDB persistence.
Supports tool-calling agents for chess move generation.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import os
import json
import logging
import asyncio
from datetime import datetime
from bson import ObjectId
import litellm

logger = logging.getLogger("checkmark")


@dataclass
class ModelConfig:
    """Configuration for an AI model"""
    name: str
    model_id: str
    provider: str = "openrouter"
    temperature: float = 0.7
    max_tokens: int = 1024
    supports_chess: bool = True


@dataclass
class MoveSuggestion:
    """AI model's move suggestion"""
    move_san: str
    confidence: float = 0.0
    reasoning: str = ""
    is_legal: bool = True
    evaluation: str = ""


# System prompt for chess AI agents
CHESS_SYSTEM_PROMPT = """You are a chess playing AI. You play by calling tools to interact with the chess board.

Available Tools:
1. get_board_state() - Get the current board position
   Input: No arguments
   Returns: { "fen": "...", "turn": "white" or "black" }

2. make_move(move: str) - Make a move in SAN notation (e.g., "e4", "Nf3", "O-O")
   Input: One string argument - the move in SAN notation
   Returns: { "success": true, "new_fen": "...", "turn": "black" }
   OR: { "success": false, "error": "Illegal move: e5 is not legal" }

Rules:
- Always call get_board_state() first to see the position and whose turn it is
- Call make_move() with a legal SAN notation move
- If make_move() returns success: false, analyze the error and try a different move
- You have a maximum of 20 tool calls per turn
- Don't repeat the same illegal moves
- The move MUST be in SAN notation (Standard Algebraic Notation)
- Examples of valid moves: "e4", "Nf3", "O-O", "Bxd5+", "Qxf7#"
"""


class AIModelService:
    """Service for interacting with AI models via LiteLLM/OpenRouter with MongoDB persistence."""

    def __init__(self):
        """Initialize AI model service with API configuration"""
        self.api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("LITELLM_API_KEY")
        
        if self.api_key:
            litellm.api_key = self.api_key
            litellm.model_list = [
                {
                    "model": "openrouter/anthropic/claude-3.5",
                    "litellm_model": "anthropic/claude-3.5"
                },
                {
                    "model": "openrouter/google/gemini-1.5-pro",
                    "litellm_model": "google/gemini-1.5-pro"
                },
                {
                    "model": "openrouter/mistralai/mistral-7b-instruct",
                    "litellm_model": "mistralai/mistral-7b-instruct"
                },
            ]

    # ------------------------------------------------------------------
    # Model CRUD
    # ------------------------------------------------------------------

    async def create_model(
        self,
        name: str,
        model_id: str,
        provider: str = "openrouter",
        capabilities: Optional[dict] = None,
    ) -> Dict[str, Any]:
        """Register a new AI model in MongoDB."""
        db = await self._get_db()
        models_col = db["models"]

        model_doc = {
            "name": name,
            "provider": provider,
            "model_id": model_id,
            "capabilities": capabilities or {},
            "benchmark_stats": {
                "wins": 0,
                "losses": 0,
                "draws": 0,
                "total_games": 0,
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        result = await models_col.insert_one(model_doc)
        model_doc["_id"] = result.inserted_id
        return self._model_to_response(model_doc)

    async def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get a model by ID."""
        db = await self._get_db()
        models_col = db["models"]

        try:
            model_doc = await models_col.find_one({"_id": ObjectId(model_id)})
        except Exception:
            return None

        if not model_doc:
            return None

        return self._model_to_response(model_doc)

    async def list_models(self) -> List[Dict[str, Any]]:
        """List all registered models."""
        db = await self._get_db()
        models_col = db["models"]

        cursor = models_col.find().sort("benchmark_stats.total_games", -1)
        models = []
        async for doc in cursor:
            models.append(self._model_to_response(doc))
        return models

    async def update_model(self, model_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a model's fields."""
        db = await self._get_db()
        models_col = db["models"]

        updates["updated_at"] = datetime.utcnow()
        result = await models_col.update_one(
            {"_id": ObjectId(model_id)},
            {"$set": updates},
        )
        if result.matched_count == 0:
            return None
        return await self.get_model(model_id)

    @staticmethod
    def _model_to_response(model_doc: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a MongoDB model document to an API response dict."""
        stats = model_doc.get("benchmark_stats", {})
        return {
            "id": str(model_doc["_id"]),
            "name": model_doc["name"],
            "provider": model_doc["provider"],
            "model_id": model_doc["model_id"],
            "capabilities": model_doc.get("capabilities", {}),
            "benchmark_stats": {
                "wins": stats.get("wins", 0),
                "losses": stats.get("losses", 0),
                "draws": stats.get("draws", 0),
                "total_games": stats.get("total_games", 0),
            },
            "created_at": model_doc["created_at"],
            "updated_at": model_doc["updated_at"],
        }

    # ------------------------------------------------------------------
    # Benchmark CRUD
    # ------------------------------------------------------------------

    async def create_benchmark(
        self,
        model_id: str,
        match_id: str,
        elo_estimate: float,
        move_accuracy: float,
        thinking_time_avg: float = 0,
        average_depth: float = 0,
    ) -> Dict[str, Any]:
        """Record benchmark data for a model."""
        db = await self._get_db()
        benchmarks_col = db["benchmarks"]

        benchmark_doc = {
            "model_id": ObjectId(model_id),
            "match_id": ObjectId(match_id),
            "elo_estimate": elo_estimate,
            "move_accuracy": move_accuracy,
            "thinking_time_avg": thinking_time_avg,
            "average_depth": average_depth,
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "total_games": 0,
            "timestamp": datetime.utcnow(),
        }

        result = await benchmarks_col.insert_one(benchmark_doc)
        benchmark_doc["_id"] = result.inserted_id
        return self._benchmark_to_response(benchmark_doc)

    async def get_benchmark(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get benchmark statistics for a model (latest)."""
        db = await self._get_db()
        benchmarks_col = db["benchmarks"]

        try:
            benchmark_doc = await benchmarks_col.find_one(
                {"model_id": ObjectId(model_id)},
                sort=[("timestamp", -1)],
            )
        except Exception:
            return None

        if not benchmark_doc:
            return None

        return self._benchmark_to_response(benchmark_doc)

    async def get_rankings(self) -> List[Dict[str, Any]]:
        """Get overall model rankings based on ELO."""
        db = await self._get_db()
        models_col = db["models"]

        cursor = models_col.find().sort("benchmark_stats.elo_estimate", -1)
        rankings = []
        rank = 1
        async for doc in cursor:
            stats = doc.get("benchmark_stats", {})
            rankings.append({
                "model_id": str(doc["_id"]),
                "model_name": doc["name"],
                "elo_estimate": stats.get("elo_estimate", 0),
                "total_games": stats.get("total_games", 0),
                "wins": stats.get("wins", 0),
                "losses": stats.get("losses", 0),
                "draws": stats.get("draws", 0),
                "win_rate": stats.get("win_rate", 0),
                "rank": rank,
            })
            rank += 1
        return rankings

    @staticmethod
    def _benchmark_to_response(benchmark_doc: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a MongoDB benchmark document to an API response dict."""
        return {
            "id": str(benchmark_doc["_id"]),
            "model_id": str(benchmark_doc["model_id"]),
            "match_id": str(benchmark_doc["match_id"]),
            "elo_estimate": benchmark_doc["elo_estimate"],
            "move_accuracy": benchmark_doc["move_accuracy"],
            "thinking_time_avg": benchmark_doc.get("thinking_time_avg", 0),
            "average_depth": benchmark_doc.get("average_depth", 0),
            "wins": benchmark_doc.get("wins", 0),
            "losses": benchmark_doc.get("losses", 0),
            "draws": benchmark_doc.get("draws", 0),
            "total_games": benchmark_doc.get("total_games", 0),
            "timestamp": benchmark_doc["timestamp"],
        }

    # ------------------------------------------------------------------
    # Tool definitions
    # ------------------------------------------------------------------

    def get_chess_tools(self) -> List[Dict[str, Any]]:
        """Define the chess tools for the AI agent."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_board_state",
                    "description": "Get the current chess board position and whose turn it is.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "make_move",
                    "description": "Make a chess move in SAN notation (e.g., 'e4', 'Nf3', 'O-O'). Returns success/failure.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "move": {
                                "type": "string",
                                "description": "The move in SAN notation (e.g., 'e4', 'Nf3', 'O-O', 'Bxd5+')",
                            },
                        },
                        "required": ["move"],
                    },
                },
            },
        ]

    # ------------------------------------------------------------------
    # Tool execution (called by match_service during auto-play)
    # ------------------------------------------------------------------

    async def execute_get_board_state(self, match_id: str) -> Dict[str, Any]:
        """Execute the get_board_state tool.

        Args:
            match_id: ID of the match.

        Returns:
            Dict with fen and turn information.
        """
        db = await self._get_db()
        matches_col = db["matches"]
        
        match_doc = await matches_col.find_one({"_id": ObjectId(match_id)})
        if not match_doc:
            return {"error": f"Match {match_id} not found"}
        
        fen = match_doc.get("board_fen", "")
        # Parse FEN to determine turn (w=white, b=black)
        turn = "white" if fen.split()[1] == "w" else "black"
        
        return {"fen": fen, "turn": turn}

    async def execute_make_move(self, match_id: str, move: str) -> Dict[str, Any]:
        """Execute the make_move tool.

        Args:
            match_id: ID of the match.
            move: The move in SAN notation.

        Returns:
            Dict with success status and new board state.
        """
        try:
            from services.match_service import MatchService
            from services.chess_engine import ChessEngine
            
            chess_engine = ChessEngine()
            match_service = MatchService(chess_engine)
            
            # Execute the move (this validates and records it)
            result = await match_service.make_move(match_id, move)
            
            if result.get("success"):
                new_fen = result.get("board_fen", "")
                # Determine next turn
                move_number = result.get("move_number", 0)
                next_turn = "black" if move_number % 2 == 1 else "white"
                
                return {
                    "success": True,
                    "new_fen": new_fen,
                    "turn": next_turn,
                    "move_number": move_number,
                }
            else:
                return {
                    "success": False,
                    "error": "Unknown error occurred",
                }
                
        except ValueError as e:
            # Illegal move
            return {
                "success": False,
                "error": str(e),
            }
        except Exception as e:
            logger.error(f"Error executing make_move tool: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": f"Tool execution error: {str(e)}",
            }

    # ------------------------------------------------------------------
    # Tool-calling move generation
    # ------------------------------------------------------------------

    async def generate_move_with_tools(
        self,
        match_id: str,
        model_id: str,
        max_tool_calls: int = 20,
    ) -> Optional[str]:
        """Generate a move using tool-calling with LiteLLM.

        This method implements a tool-calling agent loop where:
        1. The AI agent calls tools to get board state and make moves
        2. We execute the tools and return results to the agent
        3. The agent continues until it makes a valid move or max_tool_calls is reached
        4. Empty/non-tool responses get a nudge and don't count against the limit

        Args:
            match_id: ID of the match.
            model_id: Model ID to use for move generation (UUID stored in DB).
            max_tool_calls: Maximum number of tool calls allowed per turn (default 20).

        Returns:
            The SAN notation of the move if successful, None otherwise.
        """
        # Look up the model to get its configuration
        db = await self._get_db()
        models_col = db["models"]
        model = await models_col.find_one({"_id": ObjectId(model_id)})
        
        if not model:
            logger.error(f"Model {model_id} not found in database")
            return None
        
        model_name = model.get("name", model_id)
        provider = model.get("provider", "openrouter")
        model_id_str = model.get("model_id", model_id)
        api_base = model.get("api_base")
        api_key = model.get("api_key")
        
        logger.info(f"Model {model_name} ({model_id_str}) starting tool-calling turn for match {match_id}")
        
        # Build litellm model string based on provider
        if provider == "llama-swap":
            # llama-swap is OpenAI-compatible at /v1
            litellm_model = f"openai/{model_id_str}"
            litellm_kwargs = {
                "api_base": "http://localhost:8080/v1",
                "api_key": "not-needed",
            }
        else:
            # OpenRouter and other providers
            litellm_model = f"{provider}/{model_id_str}" if "/" not in model_id_str else model_id_str
            litellm_kwargs = {}
        
        if api_base:
            litellm_kwargs["api_base"] = api_base
        if api_key:
            litellm_kwargs["api_key"] = api_key
        
        # Initialize conversation history
        messages = [
            {"role": "system", "content": CHESS_SYSTEM_PROMPT},
            {"role": "user", "content": "It's your turn. Please call get_board_state() to see the position."},
        ]
        
        tool_calls_count = 0
        
        while tool_calls_count < max_tool_calls:
            try:
                result = await self._generate_move_with_litellm_tools(
                    match_id, messages, litellm_model, litellm_kwargs, tool_calls_count
                )
                
                if result["move"]:
                    return result["move"]
                elif result["nudge"]:
                    # Model didn't make a tool call - add nudge and retry (doesn't count)
                    messages.append({
                        "role": "user",
                        "content": "[INTERNAL NOTE] You must use the get_board_state() tool to see the current board position, then use make_move() to make a move. Both tools are required to play.",
                    })
                elif result["invalid_move"]:
                    # Model made an invalid move - loop continues (doesn't count as wasted)
                    pass
                else:
                    # Exception occurred
                    messages.append({
                        "role": "user",
                        "content": "[INTERNAL NOTE] An error occurred. Please try again with get_board_state() and make_move().",
                    })
                    
            except Exception as e:
                logger.error(f"Error in tool-calling loop (tool calls: {tool_calls_count}/{max_tool_calls}): {e}")
                messages.append({
                    "role": "user",
                    "content": f"[INTERNAL NOTE] An error occurred: {str(e)}. Please try again with get_board_state() and make_move().",
                })
        
        # Max tool calls reached
        logger.error(f"⚠️ Model {model_name} exceeded max tool calls ({max_tool_calls}) for match {match_id}")
        return None

    async def _generate_move_with_litellm_tools(
        self,
        match_id: str,
        messages: list,
        model_string: str,
        litellm_kwargs: dict,
        current_tool_calls: int,
    ) -> dict:
        """Generate a move using litellm's tool calling API.
        
        Returns a dict with keys:
        - move: the SAN move if successful, else None
        - nudge: True if model needs a nudge (no tool calls made)
        - invalid_move: True if model made an invalid move
        - error: True if an exception occurred
        """
        result = {"move": None, "nudge": False, "invalid_move": False, "error": False}
        
        # Call litellm with tools
        response = litellm.completion(
            model=model_string,
            messages=messages,
            tools=self.get_chess_tools(),
            tool_choice="auto",
            temperature=0.7,
            max_tokens=1024,
            timeout=90,
            **litellm_kwargs,
        )
        
        # Increment tool calls count only when model actually uses tools
        assistant_message = response.choices[0].message
        
        # Check for tool calls
        if assistant_message.tool_calls:
            tool_calls_count = len(assistant_message.tool_calls)
            current_tool_calls += tool_calls_count
            
            messages.append(assistant_message)  # Add assistant's message
            
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                tool_call_id = tool_call.id
                
                logger.debug(f"Tool call #{current_tool_calls}: {function_name}({function_args})")
                current_tool_calls += 1
                
                # Execute the tool
                if function_name == "get_board_state":
                    tool_result = await self.execute_get_board_state(match_id)
                elif function_name == "make_move":
                    move = function_args.get("move", "")
                    tool_result = await self.execute_make_move(match_id, move)
                    
                    # If move was successful, return it
                    if tool_result.get("success"):
                        logger.info(f"✅ Model made valid move: {move}")
                        result["move"] = move
                        return result
                    else:
                        logger.warning(f"❌ Model made invalid move: {move} - {tool_result.get('error')}")
                        result["invalid_move"] = True
                else:
                    tool_result = {"error": f"Unknown function: {function_name}"}
                
                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": json.dumps(tool_result),
                })
            
            return result
        
        # No tool calls - model responded with text or was empty
        if assistant_message.content:
            assistant_content = assistant_message.content
            messages.append(assistant_message)
            
            logger.debug(f"Model responded with text: {assistant_content[:200]}...")
            
            # Try to extract a SAN move from the text
            import re
            san_pattern = r'\b([KQRBN]?[a-h]?[1-8]?x?[a-h][1-8][+#]?)\b'
            matches = re.findall(san_pattern, assistant_content)
            
            if matches:
                # Try the first match
                potential_move = matches[0]
                logger.info(f"Extracted potential move from text: {potential_move}")
                
                # Validate the move by attempting it
                validation_result = await self.execute_make_move(match_id, potential_move)
                if validation_result.get("success"):
                    logger.info(f"✅ Model made valid move: {potential_move}")
                    result["move"] = potential_move
                    return result
                else:
                    logger.warning(f"❌ Extracted move {potential_move} was invalid: {validation_result.get('error')}")
                    result["invalid_move"] = True
                    return result
            
            logger.info(f"Model made no tool calls and no extractable move - will nudge")
        
        else:
            logger.info("Model returned empty response - will nudge")
        
        result["nudge"] = True
        return result

    # ------------------------------------------------------------------
    # DB access
    # ------------------------------------------------------------------

    async def _get_db(self):
        """Get the MongoDB database instance."""
        from utils.mongo_db import get_database
        return await get_database()
