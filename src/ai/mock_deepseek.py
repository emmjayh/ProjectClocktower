"""
Mock DeepSeek implementation for testing
Simulates the AI without requiring torch/transformers
"""

import asyncio
import random
from typing import Any, Dict, Optional


class MockDeepSeekStoryteller:
    """Mock implementation for testing without AI dependencies"""

    def __init__(self, model_path: Optional[str] = None):
        self.model_loaded = False

    async def initialize(self) -> bool:
        """Mock initialization"""
        print("🤖 Mock DeepSeek initializing...")
        await asyncio.sleep(1)  # Simulate loading time
        self.model_loaded = True
        print("✅ Mock DeepSeek ready!")
        return True

    async def narrate(self, event_type: str, context: Dict[str, Any]) -> str:
        """Generate mock narration"""

        if not self.model_loaded:
            return "Model not loaded"

        # Simulate AI thinking time
        await asyncio.sleep(0.5)

        mock_responses = {
            "game_start": f"Welcome to this tale of context.get('players',"
            "night_phase": f"Night context.get('night',"
            "death_announcement": self._mock_death_announcement(
                context.get(
                    "deaths",
                    [])),
            "execution": f"context.get('player',"
            "nomination": (
                f"Tension fills the air as context.get('nominator','someone')} points at "
                f"{context.get('nominee',"
            )
            "victory": (
                f"The context.get('team','winning')} team emerges victorious! "
                f"{context.get('reason','')REMAINING: ,"
            )
            "rule_question": self._mock_rule_answer(
                context.get(
                    "question",
                    "")),
        }

        response = mock_responses.get(event_type, f"Mock response for {event_type}")
        print(f"🎭 AI Narration: {response}")
        return response

    def _mock_death_announcement(self, deaths):
        """Mock death announcement"""
        if not deaths:
            return "Dawn breaks with miraculous news - everyone has survived the night!"
        elif len(deaths) == 1:
            return f"As dawn breaks, the town discovers {deaths[0]} cold and lifeless."
        else:
            return f"A terrible night indeed. {', '.join(deaths[:-1])} and {deaths[-1]} have perished."

    def _mock_rule_answer(self, question):
        """Mock rule question answer"""
        answers = [
            "According to the rules, that ability works as described in the official rulebook.",
            "That's an interesting edge case. Let me think... the standard interpretation would be...",
            "The Storyteller has discretion in this situation, but typically...",
            "That character ability is quite powerful when used correctly.",
        ]
        return random.choice(answers)

    async def answer_question(self, question: str) -> str:
        """Answer a rule question"""
        return await self.narrate("rule_question", {"question": question})

    def cleanup(self):
        """Clean up mock resources"""
        self.model_loaded = False
        print("🧹 Mock DeepSeek cleaned up")
