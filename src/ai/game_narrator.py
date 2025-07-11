"""
Game Narrator - Manages AI storytelling without making player decisions
This replaces the old decision-making AI with a proper storyteller
"""

import logging
from typing import Dict, List, Optional

from ..core.game_state import GameState, Player
from .deepseek_openai_client import DeepSeekClient


class GameNarrator:
    """AI Narrator that provides atmosphere without making player decisions"""

    def __init__(self, deepseek_client: Optional[DeepSeekClient] = None):
        self.ai_client = deepseek_client
        self.logger = logging.getLogger(__name__)
        self.use_ai = deepseek_client is not None

    async def narrate_game_start(self, player_count: int, script: str) -> str:
        """Narrate the beginning of a new game"""

        if self.use_ai:
            try:
                return await self.ai_client.narrate(
                    "game_start", {"players": player_count, "script": script}
                )
            except Exception as e:
                self.logger.error(f"AI narration failed: {e}")

        # Fallback narration
        return f"Welcome to Blood on the Clocktower. {player_count} souls gather as darkness falls..."

    async def narrate_night_start(self, night_number: int, alive_count: int) -> str:
        """Narrate the beginning of night phase"""

        if self.use_ai:
            try:
                return await self.ai_client.narrate(
                    "night_phase", {"night": night_number, "alive": alive_count}
                )
            except Exception as e:
                self.logger.error(f"AI narration failed: {e}")

        # Fallback
        if night_number == 1:
            return "The first night begins. Everyone, close your eyes..."
        else:
            return f"Night {night_number} falls upon the town. Close your eyes..."

    async def announce_deaths(self, deaths: List[str]) -> str:
        """Announce deaths at dawn"""

        if self.use_ai:
            try:
                return await self.ai_client.narrate(
                    "death_announcement", {"deaths": deaths}
                )
            except Exception as e:
                self.logger.error(f"AI narration failed: {e}")

        # Fallback
        if not deaths:
            return "The sun rises. Miraculously, everyone survived the night."
        elif len(deaths) == 1:
            return f"Dawn breaks. {deaths[0]} was found dead."
        else:
            return f"Dawn reveals tragedy. {', '.join(deaths)} have died in the night."

    async def narrate_nomination(self, nominator: str, nominee: str) -> str:
        """Narrate a nomination"""

        if self.use_ai:
            try:
                return await self.ai_client.narrate(
                    "nomination", {"nominator": nominator, "nominee": nominee}
                )
            except Exception as e:
                self.logger.error(f"AI narration failed: {e}")

        # Fallback
        return f"{nominator} nominates {nominee}. The town holds its breath..."

    async def narrate_execution(
        self, player_name: str, character: Optional[str] = None
    ) -> str:
        """Narrate an execution"""

        if self.use_ai:
            try:
                return await self.ai_client.narrate(
                    "execution", {"player": player_name, "character": character}
                )
            except Exception as e:
                self.logger.error(f"AI narration failed: {e}")

        # Fallback
        return f"{player_name} meets their fate at the hands of the town."

    async def announce_victory(self, winning_team: str, reason: str) -> str:
        """Announce game victory"""

        if self.use_ai:
            try:
                return await self.ai_client.narrate(
                    "victory", {"team": winning_team, "reason": reason}
                )
            except Exception as e:
                self.logger.error(f"AI narration failed: {e}")

        # Fallback
        if winning_team == "good":
            return f"Good triumphs! {reason}"
        else:
            return f"Evil prevails! {reason}"

    async def answer_rule_question(self, question: str) -> str:
        """Answer a player's rule question"""

        if self.use_ai:
            try:
                return await self.ai_client.answer_question(question)
            except Exception as e:
                self.logger.error(f"AI question answering failed: {e}")

        # Fallback
        return "Please refer to the rulebook or ask the human storyteller for clarification."

    async def describe_character_ability(self, character: str) -> str:
        """Describe a character's ability"""

        if self.use_ai:
            try:
                return await self.ai_client.describe_character(character)
            except Exception as e:
                self.logger.error(f"AI character description failed: {e}")

        # Fallback descriptions
        descriptions = {
            "Fortune Teller": "Each night, choose 2 players: you learn if either is the Demon.",
            "Empath": "Each night, you learn how many of your alive neighbors are evil.",
            "Washerwoman": "You start knowing that 1 of 2 players is a Townsfolk.",
            "Librarian": "You start knowing that 1 of 2 players is an Outsider.",
            "Investigator": "You start knowing that 1 of 2 players is a Minion.",
            "Chef": "You start knowing how many pairs of evil players there are.",
            "Virgin": "The 1st time you are nominated, if the nominator is a Townsfolk, they are executed immediately.",
            "Slayer": "Once per game, during the day, publicly choose a player: if they are the Demon, they die.",
            "Soldier": "You are safe from the Demon.",
            "Mayor": "If only 3 players live & no execution occurs, your team wins.",
            "Imp": "Each night, choose a player: they die. If you kill yourself this way, a Minion becomes the Imp.",
            "Poisoner": "Each night, choose a player: they are poisoned tonight and tomorrow day.",
            "Spy": "Each night, you see the Grimoire.",
            "Baron": "There are extra Outsiders in play.",
            "Scarlet Woman": "If there are 5 or more players alive & the Demon dies, you become the Demon.",
            "Drunk": "You do not know you are the Drunk. You think you are a Townsfolk, but your ability malfunctions.",
            "Butler": "Each night, choose a player (not yourself): tomorrow, you may only vote if they are voting too.",
            "Recluse": "You might register as evil & as a Minion or Demon, even if dead.",
            "Saint": "If you die by execution, your team loses.",
        }

        return descriptions.get(
            character, f"The {character} has a unique ability in this game."
        )

    # Helper method to check if AI is available
    def is_ai_enabled(self) -> bool:
        """Check if AI narration is available"""
        return self.use_ai and self.ai_client is not None
