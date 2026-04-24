"""
AI Model Service for Checkmark Platform
Handles AI model integration with LiteLLM/OpenRouter
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import litellm
from litellm import completion
import os
import json
from datetime import datetime


@dataclass
class ModelConfig:
    """Configuration for an AI model"""
    name: str
    provider: str = "openrouter"
    model_id: str
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
    """Service for interacting with AI models via LiteLLM/OpenRouter"""

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
        # Try to get API key from environment
        self.api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("LITELLM_API_KEY")
        
        if not self.api_key:
            # Use test mode with mock responses
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

    def get_model_config(self, model_name: str) -> ModelConfig:
        """
        Get configuration for a specific model.
        
        Args:
            model_name: Model identifier (e.g., "openrouter/anthropic/claude-3.5")
            
        Returns:
            ModelConfig: Configuration for the model
        """
        # Parse model name
        if "/" in model_name:
            provider, model_id = model_name.split("/", 1)
        else:
            provider = "openrouter"
            model_id = model_name
        
        # Map common model IDs
        model_specs = {
            "anthropic/claude-3.5": {
                "temperature": 0.7,
                "max_tokens": 1024,
            },
            "google/gemini-1.5-pro": {
                "temperature": 0.7,
                "max_tokens": 2048,
            },
            "mistralai/mistral-7b": {
                "temperature": 0.7,
                "max_tokens": 512,
            },
            "openai/gpt-4o": {
                "temperature": 0.7,
                "max_tokens": 1024,
            },
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
    ) -> Optional[MoveSuggestion]:
        """
        Get AI's move suggestion for a given position.
        
        Args:
            board_fen: FEN string of current position
            match_id: ID of the match (for context)
            model_name: Name of the model to use
            
        Returns:
            MoveSuggestion: AI's suggested move
        """
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
            
            # Parse JSON response
            try:
                result = json.loads(response.choices[0].message.content)
                return MoveSuggestion(
                    move_san=result.get("move", ""),
                    reasoning=result.get("reasoning", ""),
                    evaluation=result.get("evaluation", ""),
                )
            except json.JSONDecodeError:
                # Try to extract move from unstructured response
                return self._extract_move_from_text(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Error generating move suggestion: {e}")
            return None

    def _prepare_move_prompt(self, board_fen: str, match_id: str) -> str:
        """Prepare the move suggestion prompt"""
        turn = "White" if board_fen.count("w") % 2 == 0 else "Black"
        return self.MOVE_SUGGESTION_PROMPT.format(fen=board_fen, turn=turn)

    def _mock_move_suggestion(self) -> MoveSuggestion:
        """Mock move suggestion for development"""
        return MoveSuggestion(
            move_san="e4",
            reasoning="Opening principle: control the center",
            evaluation="Equal position",
            is_legal=True,
            confidence=0.85,
        )

    def _extract_move_from_text(self, text: str) -> Optional[MoveSuggestion]:
        """Extract move from unstructured text response"""
        # Look for move patterns in text
        import re
        move_patterns = [
            r'"move"[^\]]*:\s*"([^"]+)"',
            r'\"move\"[^\]]*:\s*\"([^\"]+)\"',
            r'Move:\s*([a-h][1-8][a-h][1-8]|[A-Za-z][a-h][=x#?])',
            r'\(([a-h][1-8][a-h][1-8]|[A-Za-z][a-h][=x#?])\)',
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
    ) -> Optional[Dict[str, Any]]:
        """
        Get AI's evaluation of a chess position.
        
        Args:
            board_fen: FEN string of current position
            model_name: Name of the model to use
            
        Returns:
            Dict with evaluation data
        """
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
            
            # Parse JSON response
            try:
                result = json.loads(response.choices[0].message.content)
                return result
            except json.JSONDecodeError:
                return None
            
        except Exception as e:
            print(f"Error evaluating position: {e}")
            return None

    def _mock_evaluation(self) -> Dict[str, Any]:
        """Mock position evaluation"""
        return {
            "material_balance": "Equal",
            "positional_assessment": "Open position with chances for both sides",
            "recommended_plan": "Control the center and develop pieces",
            "evaluation_cents": 0,
        }


# Singleton instance
_ai_model_service = None


def get_ai_model_service() -> AIModelService:
    """Get the singleton AIModelService instance"""
    global _ai_model_service
    if _ai_model_service is None:
        _ai_model_service = AIModelService()
    return _ai_model_service
