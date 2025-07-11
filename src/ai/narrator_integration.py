"""
Integration layer for AI narrator - handles both local DeepSeek and fallback narration
"""

import logging
from typing import Optional

from .local_deepseek_storyteller import LocalDeepSeekStoryteller


class AIGameNarrator:
    """
    Main narrator class that integrates local DeepSeek for storytelling
    Falls back to scripted narration if model unavailable
    """

    def __init__(self, use_ai: bool = True):
        self.logger = logging.getLogger(__name__)
        self.use_ai = use_ai
        self.ai_storyteller = None

        if self.use_ai:
            self.ai_storyteller = LocalDeepSeekStoryteller()

    async def initialize(self) -> bool:
        """Initialize the AI narrator"""
        if self.use_ai and self.ai_storyteller:
            success = await self.ai_storyteller.initialize()
            if not success:
                self.logger.warning(
                    "Failed to initialize AI - using fallback narration"
                )
                self.use_ai = False
            return success
        return True

    async def narrate_game_start(
        self, player_count: int, script: str = "Trouble Brewing"
    ) -> str:
        """Narrate the beginning of a new game"""
        context = {"players": player_count, "script": script}

        if self.use_ai and self.ai_storyteller:
            return await self.ai_storyteller.narrate("game_start", context)

        # Fallback narration
        return f"Welcome to Blood on the Clocktower. {player_count} souls gather in the town square as darkness approaches. Evil has infiltrated your peaceful community..."

    async def narrate_night_phase(self, night_number: int, alive_count: int) -> str:
        """Narrate the beginning of night"""
        context = {"night": night_number, "alive": alive_count}

        if self.use_ai and self.ai_storyteller:
            return await self.ai_storyteller.narrate("night_phase", context)

        # Fallback
        if night_number == 1:
            return (
                "The first night descends upon the town. Everyone, close your eyes..."
            )
        else:
            return f"Night {night_number} falls. The remaining {alive_count} townspeople close their eyes..."

    async def announce_deaths(self, deaths: list[str]) -> str:
        """Announce who died in the night"""
        context = {"deaths": deaths}

        if self.use_ai and self.ai_storyteller:
            return await self.ai_storyteller.narrate("death_announcement", context)

        # Fallback
        if not deaths:
            return "The sun rises on a miraculous morning - everyone has survived the night!"
        elif len(deaths) == 1:
            return f"As dawn breaks, the town discovers {
                deaths[0]} has met a terrible fate."
        else:
            return f"Dawn reveals a night of horror. {', '.join(deaths[:-1])} and {deaths[-1]} have died."

    async def narrate_nomination(self, nominator: str, nominee: str) -> str:
        """Narrate a nomination"""
        context = {"nominator": nominator, "nominee": nominee}

        if self.use_ai and self.ai_storyteller:
            return await self.ai_storyteller.narrate("nomination", context)

        # Fallback
        return f"{nominator} stands and points an accusing finger at {nominee}. The town holds its breath..."

    async def narrate_execution(
        self, player_name: str, character: Optional[str] = None
    ) -> str:
        """Narrate an execution"""
        context = {"player": player_name, "character": character}

        if self.use_ai and self.ai_storyteller:
            return await self.ai_storyteller.narrate("execution", context)

        # Fallback
        return f"The town has spoken. {player_name} meets their fate at the gallows."

    async def announce_victory(self, winning_team: str, reason: str) -> str:
        """Announce game victory"""
        context = {"team": winning_team, "reason": reason}

        if self.use_ai and self.ai_storyteller:
            return await self.ai_storyteller.narrate("victory", context)

        # Fallback
        if winning_team.lower() == "good":
            return (
                f"Light banishes darkness! The forces of good have triumphed. {reason}"
            )
        else:
            return f"Shadows consume the town! Evil reigns supreme. {reason}"

    async def answer_rule_question(self, question: str) -> str:
        """Answer a player's question about the rules"""
        if self.use_ai and self.ai_storyteller:
            return await self.ai_storyteller.answer_question(question)

        # Fallback
        return "Please consult the rulebook or ask the human storyteller for clarification on rules."

    async def describe_character(self, character: str) -> str:
        """Describe a character's ability"""
        context = {"character": character}

        if self.use_ai and self.ai_storyteller:
            instruction = f"Briefly describe the {character} character's ability in Blood on the Clocktower."
            return await self.ai_storyteller.narrate(
                "character_description", {"question": instruction}
            )

        # Fallback to basic descriptions
        descriptions = {
            "Fortune Teller": "Each night, choose 2 players: you learn if either is the Demon.",
            "Empath": "Each night, you learn how many of your alive neighbors are evil.",
            "Washerwoman": "You start knowing that 1 of 2 players is a Townsfolk.",
            "Imp": "Each night, choose a player: they die. If you kill yourself, a Minion becomes the Imp.",
            # Add more as needed
        }

        return descriptions.get(
            character, f"The {character} has a unique ability in this game."
        )

    def cleanup(self):
        """Clean up resources"""
        if self.ai_storyteller:
            self.ai_storyteller.cleanup()


# Example usage
async def demo_narrator():
    """Demo the AI narrator"""
    narrator = AIGameNarrator(use_ai=True)

    # Initialize
    await narrator.initialize()

    # Game start
    intro = await narrator.narrate_game_start(10, "Trouble Brewing")
    print(f"Storyteller: {intro}")

    # Night phase
    night = await narrator.narrate_night_phase(1, 10)
    print(f"Storyteller: {night}")

    # Deaths (determined by player actions, not AI!)
    deaths_announcement = await narrator.announce_deaths(["Alice", "Bob"])
    print(f"Storyteller: {deaths_announcement}")

    # Cleanup
    narrator.cleanup()


if __name__ == "__main__":
    import asyncio

    asyncio.run(demo_narrator())
