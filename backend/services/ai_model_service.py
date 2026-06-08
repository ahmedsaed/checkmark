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
        display_name = model.get("model_id", model_id)
        
        logger.info(f"Model {model_name} ({display_name}) starting tool-calling turn for match {match_id}")
        
        # Initialize conversation history
        messages = [
            {"role": "system", "content": CHESS_SYSTEM_PROMPT},
            {"role": "user", "content": "It's your turn. Please call get_board_state() to see the position."},
        ]
        
        tool_calls_count = 0
        last_move_attempted = None
        
        while tool_calls_count < max_tool_calls:
            tool_calls_count += 1
            
            try:
                # Determine the model string for litellm
                if provider == "llama-swap":
                    # For llama-swap, use custom text-completion tool calling
                    move = await self._generate_move_with_llama_swap_tools(match_id, messages, tool_calls_count, max_tool_calls, model_id)
                    if move:
                        return move
                else:
                    # For OpenRouter and other providers, use litellm's tool calling
                    model_string = f"{provider}/{display_name}" if "/" not in display_name else display_name
                    
                    move = await self._generate_move_with_litellm_tools(
                        match_id, messages, model_string, tool_calls_count, max_tool_calls
                    )
                    if move:
                        return move
                    
            except Exception as e:
                logger.error(f"Error in tool-calling loop (attempt {tool_calls_count}/{max_tool_calls}): {e}")
                
                # Add error message to history so model knows
                messages.append({
                    "role": "system",
                    "content": f"Error occurred: {str(e)}. Please try again.",
                })
        
        # Max tool calls reached
        logger.error(f"⚠️ Model {model_name} exceeded max tool calls ({max_tool_calls}) for match {match_id}")
        logger.error(f"Last move attempted: {last_move_attempted}")
        return None

    async def _generate_move_with_litellm_tools(
        self,
        match_id: str,
        messages: list,
        model_string: str,
        current_tool_calls: int,
        max_tool_calls: int,
    ) -> Optional[str]:
        """Generate a move using litellm's tool calling API."""
        last_move = None
        
        # Call litellm with tools
        response = litellm.completion(
            model=model_string,
            messages=messages,
            tools=self.get_chess_tools(),
            tool_choice="auto",
            temperature=0.7,
            max_tokens=1024,
        )
        
        # Check for tool calls
        if response.choices[0].message.tool_calls:
            tool_calls = response.choices[0].message.tool_calls
            messages.append(response.choices[0].message)  # Add assistant's message
            
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                tool_call_id = tool_call.id
                
                logger.debug(f"Tool call #{current_tool_calls}: {function_name}({function_args})")
                
                # Execute the tool
                if function_name == "get_board_state":
                    tool_result = await self.execute_get_board_state(match_id)
                elif function_name == "make_move":
                    move = function_args.get("move", "")
                    last_move = move
                    tool_result = await self.execute_make_move(match_id, move)
                    
                    # If move was successful, return it
                    if tool_result.get("success"):
                        logger.info(f"✅ Model made valid move: {move}")
                        return move
                    else:
                        logger.warning(f"❌ Model made invalid move: {move} - {tool_result.get('error')}")
                else:
                    tool_result = {"error": f"Unknown function: {function_name}"}
                
                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": json.dumps(tool_result),
                })
                
        elif response.choices[0].message.content:
            # Model responded with text (no tool calls)
            assistant_content = response.choices[0].message.content
            messages.append(response.choices[0].message)
            
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
                    return potential_move
                else:
                    logger.warning(f"❌ Extracted move {potential_move} was invalid: {validation_result.get('error')}")
            
            logger.warning(f"Model made no tool calls and no extractable move (attempt {current_tool_calls}/{max_tool_calls})")
            
        else:
            logger.warning(f"Model returned empty response (attempt {current_tool_calls}/{max_tool_calls})")
            
        return None

    async def _generate_move_with_llama_swap_tools(
        self,
        match_id: str,
        messages: list,
        current_tool_calls: int,
        max_tool_calls: int,
        model_id: str = None,
    ) -> Optional[str]:
        """Generate a move using llama-swap's text completion with custom tool parsing.
        
        Since llama-swap doesn't support litellm's tool calling API, we need to parse
        tool calls from the text response manually.
        """
        import requests
        import re
        
        # Look up the model to get its display name
        db = await self._get_db()
        models_col = db["models"]
        model = await models_col.find_one({"_id": ObjectId(model_id)}) if model_id else None
        
        if not model:
            # Fallback to first model
            model = await models_col.find_one()
        
        if not model:
            logger.error("No models found in database")
            return None
        
        model_name = model.get("name", "Unknown")
        display_name = model.get("model_id", "OmniCoder-9B")
        
        # Build a text prompt for the model
        prompt = "You are a chess playing AI.\n\n"
        prompt += CHESS_SYSTEM_PROMPT + "\n\n"
        
        # Add conversation history
        for msg in messages:
            if msg["role"] == "user":
                prompt += f"User: {msg['content']}\n\n"
            elif msg["role"] == "assistant":
                prompt += f"Assistant: {msg['content']}\n\n"
            elif msg["role"] == "tool":
                prompt += f"Tool Result: {msg['content']}\n\n"
            elif msg["role"] == "system":
                continue  # Skip system messages in text mode
        
        prompt += "Assistant: "
        
        try:
            # Call llama-swap
            response = requests.post(
                "http://localhost:8080/completion",
                json={
                    "model": display_name,
                    "prompt": prompt,
                    "stream": False,
                    "max_tokens": 1024,
                    "temperature": 0.7,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            assistant_text = data.get("content", "")
            
            logger.debug(f"Llama-swap response from {model_name}: {assistant_text[:500]}...")
            
            # Parse tool calls from text
            # Look for patterns like "get_board_state()" or "make_move('e4')"
            get_board_match = re.search(r'get_board_state\s*\(\s*\)', assistant_text)
            make_move_match = re.search(r'make_move\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)', assistant_text)
            
            if get_board_match:
                logger.debug(f"Detected get_board_state() call")
                tool_result = await self.execute_get_board_state(match_id)
                messages.append({
                    "role": "assistant",
                    "content": f"I'll call get_board_state().",
                })
                messages.append({
                    "role": "tool",
                    "content": json.dumps(tool_result),
                })
                return None  # Continue the loop
            
            elif make_move_match:
                move = make_move_match.group(1)
                logger.debug(f"Detected make_move('{move}') call")
                tool_result = await self.execute_make_move(match_id, move)
                
                messages.append({
                    "role": "assistant",
                    "content": f"I'll make the move {move}.",
                })
                messages.append({
                    "role": "tool",
                    "content": json.dumps(tool_result),
                })
                
                if tool_result.get("success"):
                    logger.info(f"✅ Model {model_name} made valid move: {move}")
                    return move
                else:
                    logger.warning(f"❌ Model {model_name} made invalid move: {move} - {tool_result.get('error')}")
                    return None  # Continue the loop
            
            else:
                # No tool calls detected, try to extract a move from the text
                san_pattern = r'\b([KQRBN]?[a-h]?[1-8]?x?[a-h][1-8][+#]?)\b'
                matches = re.findall(san_pattern, assistant_text)
                
                if matches:
                    potential_move = matches[0]
                    logger.info(f"Extracted potential move from llama-swap response: {potential_move}")
                    
                    validation_result = await self.execute_make_move(match_id, potential_move)
                    if validation_result.get("success"):
                        logger.info(f"✅ Model {model_name} made valid move: {potential_move}")
                        return potential_move
                    else:
                        logger.warning(f"❌ Extracted move {potential_move} was invalid: {validation_result.get('error')}")
                
                logger.warning(f"No tool calls or extractable moves found (attempt {current_tool_calls}/{max_tool_calls})")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request to llama-swap failed: {e}")
        except Exception as e:
            logger.error(f"Error processing llama-swap response: {e}")
        
        return None

    # ------------------------------------------------------------------
    # DB access
    # ------------------------------------------------------------------

    async def _get_db(self):
        """Get the MongoDB database instance."""
        from utils.mongo_db import get_database
        return await get_database()
