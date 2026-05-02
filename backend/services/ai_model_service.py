"""
AI Model Service for Checkmark Platform
Handles AI model integration with LiteLLM/OpenRouter and MongoDB persistence.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import litellm
from litellm import completion
import os
import json
from datetime import datetime
from bson import ObjectId


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


class AIModelService:
    """Service for interacting with AI models via LiteLLM/OpenRouter with MongoDB persistence."""

    # Prompt templates for chess reasoning
    MOVE_SUGGESTION_PROMPT = """You are a chess playing AI. Analyze the following chess position and suggest the best move.

Current Position (FEN): {fen}
Whose Turn: {turn}

Please analyze the position and provide:
1. The best move in SAN notation (e.g., "e4", "Nf3", "Qxf7+")
2. A brief reasoning for your choice
3. Your evaluation of the position

IMPORTANT: The move MUST be legal. Do not suggest illegal moves.

Format your response as JSON:
{{
  "move": "SAN notation of the move",
  "reasoning": "Brief explanation",
  "evaluation": "Position evaluation"
}}
"""

    POSITION_EVALUATION_PROMPT = """You are a chess evaluation AI. Analyze the following position and provide an evaluation.

Current Position (FEN): {fen}

Provide:
1. Material balance (if any)
2. Positional assessment
3. Recommended plan
4. Your evaluation in centipawns (positive = advantage for White, negative = advantage for Black)

Format your response as JSON:
{{
  "material_balance": "Material assessment",
  "positional_assessment": "Positional evaluation",
  "recommended_plan": "Strategic recommendations",
  "evaluation_cents": 0
}}
"""

    def __init__(self):
        """Initialize AI model service with API configuration"""
        self.api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("LITELLM_API_KEY")
        
        if not self.api_key:
            self.use_mock = True
        else:
            self.use_mock = False
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
    # AI move suggestion (LiteLLM/OpenRouter)
    # ------------------------------------------------------------------

    def get_model_config(self, model_name: str) -> ModelConfig:
        """Get configuration for a specific model."""
        if "/" in model_name:
            provider, model_id = model_name.split("/", 1)
        else:
            provider = "openrouter"
            model_id = model_name

        model_specs = {
            "anthropic/claude-3.5": {"temperature": 0.7, "max_tokens": 1024},
            "google/gemini-1.5-pro": {"temperature": 0.7, "max_tokens": 2048},
            "mistralai/mistral-7b": {"temperature": 0.7, "max_tokens": 512},
            "openai/gpt-4o": {"temperature": 0.7, "max_tokens": 1024},
        }

        specs = model_specs.get(model_id, {})
        return ModelConfig(
            name=model_name,
            provider=provider,
            model_id=model_id,
            temperature=specs.get("temperature", 0.7),
            max_tokens=specs.get("max_tokens", 1024),
        )

    def generate_move_suggestion(
        self,
        board_fen: str,
        match_id: str,
        model_name: str = "openrouter/anthropic/claude-3.5",
        max_retries: int = 3,
    ) -> Optional[MoveSuggestion]:
        """Get AI's move suggestion for a given position with retry logic.

        Args:
            board_fen: Current board FEN string.
            match_id: ID of the match.
            model_name: Model to use for move suggestion.
            max_retries: Maximum number of retry attempts (default 3).

        Returns:
            MoveSuggestion or None if all retries fail.
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                if self.use_mock:
                    return self._mock_move_suggestion()

                config = self.get_model_config(model_name)
                prompt = self._prepare_move_prompt(board_fen, match_id)

                response = completion(
                    model=config.model_id,
                    messages=[
                        {"role": "system", "content": "You are a chess expert AI. Provide your response as valid JSON."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                )

                try:
                    result = json.loads(response.choices[0].message.content)
                    return MoveSuggestion(
                        move_san=result.get("move", ""),
                        reasoning=result.get("reasoning", ""),
                        evaluation=result.get("evaluation", ""),
                    )
                except json.JSONDecodeError:
                    return self._extract_move_from_text(response.choices[0].message.content)

            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    import time
                    time.sleep(2 ** attempt)
                    continue
                break

        print(f"Error generating move suggestion after {max_retries} attempts: {last_error}")
        return None

    def _prepare_move_prompt(self, board_fen: str, match_id: str) -> str:
        """Prepare the move suggestion prompt."""
        # FEN format: last character after the board is 'w' (white) or 'b' (black)
        parts = board_fen.split()
        turn = parts[1] if len(parts) > 1 else "w"
        turn_name = "White" if turn == "w" else "Black"
        return self.MOVE_SUGGESTION_PROMPT.format(fen=board_fen, turn=turn_name)

    def _mock_move_suggestion(self) -> MoveSuggestion:
        """Mock move suggestion for development."""
        return MoveSuggestion(
            move_san="e4",
            reasoning="Opening principle: control the center",
            evaluation="Equal position",
            is_legal=True,
            confidence=0.85,
        )

    def _extract_move_from_text(self, text: str) -> Optional[MoveSuggestion]:
        """Extract move from unstructured text response."""
        import re
        move_patterns = [
            r'"move"[^\]]*:\s*"([^"]+)"',
            r'Move:\s*([a-h][1-8][a-h][1-8]|[A-Za-z][a-h][=x#?])',
        ]

        for pattern in move_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                move = match.group(1)
                return MoveSuggestion(
                    move_san=move,
                    reasoning="Extracted from model response",
                    is_legal=True,
                    confidence=0.5,
                )

        return None

    def evaluate_position(
        self,
        board_fen: str,
        model_name: str = "openrouter/anthropic/claude-3.5",
        max_retries: int = 3,
    ) -> Optional[Dict[str, Any]]:
        """Get AI's evaluation of a chess position with retry logic.

        Args:
            board_fen: Current board FEN string.
            model_name: Model to use for evaluation.
            max_retries: Maximum number of retry attempts (default 3).

        Returns:
            Dict with evaluation or None if all retries fail.
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                if self.use_mock:
                    return self._mock_evaluation()

                config = self.get_model_config(model_name)
                prompt = self.POSITION_EVALUATION_PROMPT.format(fen=board_fen)

                response = completion(
                    model=config.model_id,
                    messages=[
                        {"role": "system", "content": "You are a chess expert AI. Provide your response as valid JSON."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                )

                try:
                    result = json.loads(response.choices[0].message.content)
                    return result
                except json.JSONDecodeError:
                    return None

            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)
                    continue
                break

        print(f"Error evaluating position after {max_retries} attempts: {last_error}")
        return None

    def _mock_evaluation(self) -> Dict[str, Any]:
        """Mock position evaluation."""
        return {
            "material_balance": "Equal",
            "positional_assessment": "Open position with chances for both sides",
            "recommended_plan": "Control the center and develop pieces",
            "evaluation_cents": 0,
        }

    # ------------------------------------------------------------------
    # DB access
    # ------------------------------------------------------------------

    async def _get_db(self):
        """Get the MongoDB database instance."""
        from utils.mongo_db import get_database
        return await get_database()
