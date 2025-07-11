"""
Autonomous AI Storyteller
Handles the full storyteller role with minimal human intervention
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

# Import will be handled dynamically to avoid torch dependency during testing
# from .local_deepseek_storyteller import LocalDeepSeekStoryteller
from ..core.game_state import GamePhase, GameState, Player
from ..speech.speech_handler import SpeechHandler


@dataclass
class InformationGiven:
    """Track information given to players"""

    player_name: str
    character: str
    info_type: str  # "fortune_teller", "empath", "washerwoman", etc.
    information: str
    was_true: bool
    context: str
    timestamp: datetime
    night_number: int


@dataclass
class PlayerAction:
    """Track player actions and speech"""

    player_name: str
    action_type: str  # "choose_targets", "nominate", "vote", "discussion"
    details: Dict[str, Any]
    timestamp: datetime
    phase: str


class GameContext:
    """Maintains full game context for AI decisions"""

    def __init__(self):
        self.information_history: List[InformationGiven] = []
        self.player_actions: List[PlayerAction] = []
        self.game_events: List[str] = []
        self.current_suspicions: Dict[str, List[str]] = {}  # who suspects whom
        self.voting_patterns: Dict[str, List[str]] = {}  # voting history

    def add_information(self, info: InformationGiven):
        """Record information given to a player"""
        self.information_history.append(info)

    def add_action(self, action: PlayerAction):
        """Record a player action"""
        self.player_actions.append(action)

    def get_context_summary(self, game_state: GameState) -> str:
        """Create a comprehensive summary for AI decision-making"""

        context = f"""
BLOOD ON THE CLOCKTOWER - GAME CONTEXT SUMMARY

=== BASIC INFO ===
Night: {game_state.day_number}
Phase: {game_state.phase.value}
Players Alive: {len([p for p in game_state.players if p.is_alive()])}
Script: {game_state.script_name}

=== PLAYER STATUS ===
"""

        for player in game_state.players:
            status = "ALIVE" if player.is_alive() else "DEAD"
            modifiers = []
            if player.is_drunk:
                modifiers.append("DRUNK")
            if player.is_poisoned:
                modifiers.append("POISONED")

            context += f"{player.name} ({player.character}): {status}"
            if modifiers:
                context += f" [{', '.join(modifiers)}]"
            context += "\n"

        context += "\n=== INFORMATION GIVEN ===\n"

        for info in self.information_history[-10:]:  # Last 10 pieces of info
            context += f"Night {
                info.night_number}: {
                info.player_name} ({
                info.character}) learned: {
                info.information}"
            context += f" [{'TRUE' if info.was_true else 'FALSE'}]\n"

        context += "\n=== RECENT PLAYER ACTIONS ===\n"

        for action in self.player_actions[-15:]:  # Last 15 actions
            context += (
                f"{action.player_name}: {action.action_type} - {action.details}\n"
            )

        context += "\n=== SUSPICION PATTERNS ===\n"

        for suspector, targets in self.current_suspicions.items():
            if targets:
                context += f"{suspector} suspects: {', '.join(targets)}\n"

        return context


class SpeechParser:
    """Parse player speech into game actions"""

    def __init__(self):
        self.patterns = {
            "fortune_teller": [
                r"(?i)fortune teller.*(?:choose|pick|select).*?([A-Za-z]+).*?(?:and|,).*?([A-Za-z]+)",
                r"(?i)i choose ([A-Za-z]+) and ([A-Za-z]+)",
                r"(?i)i pick ([A-Za-z]+) and ([A-Za-z]+)",
            ],
            "empath": [
                r"(?i)empath.*neighbors",
                r"(?i)how many.*evil.*neighbors"],
            "washerwoman": [
                r"(?i)washerwoman.*townsfolk",
                r"(?i)which.*townsfolk"],
            "nomination": [
                r"(?i)i nominate ([A-Za-z]+)",
                r"(?i)nominate ([A-Za-z]+)"],
            "vote": [
                r"(?i)i vote (yes|no|aye)",
                r"(?i)(yes|no|aye)"],
            "question": [
                r"(?i)storyteller.*\?",
                r"(?i)how does.*work",
                r"(?i)what happens if",
            ],
        }

    def parse_speech(
        self, text: str, speaker: str, game_state: GameState
    ) -> Optional[PlayerAction]:
        """Parse speech into a structured action"""

        text = text.strip()

        # Check each pattern type
        for action_type, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    return self._create_action(
                        action_type, match, text, speaker, game_state
                    )

        # Default to discussion
        return PlayerAction(
            player_name=speaker,
            action_type="discussion",
            details={"text": text},
            timestamp=datetime.now(),
            phase=game_state.phase.value,
        )

    def _create_action(
        self, action_type: str, match, text: str, speaker: str, game_state: GameState
    ) -> PlayerAction:
        """Create action from regex match"""

        details = {"text": text}

        if action_type == "fortune_teller":
            if len(match.groups()) >= 2:
                details["targets"] = [match.group(1).title(), match.group(2).title()]
        elif action_type == "nomination":
            details["nominee"] = match.group(1).title()
        elif action_type == "vote":
            details["vote"] = match.group(1).lower()

        return PlayerAction(
            player_name=speaker,
            action_type=action_type,
            details=details,
            timestamp=datetime.now(),
            phase=game_state.phase.value,
        )


class AutonomousStoryteller:
    """Fully autonomous AI Storyteller"""

    def __init__(
        self, speech_handler: Optional[SpeechHandler] = None, ai_storyteller=None
    ):
        self.speech_handler = speech_handler
        self.ai_storyteller = ai_storyteller  # Can be injected for testing
        self.game_context = GameContext()
        self.speech_parser = SpeechParser()
        self.logger = logging.getLogger(__name__)

        self.game_state: Optional[GameState] = None
        self.is_running = False
        self.pending_actions = asyncio.Queue()

    async def initialize(self) -> bool:
        """Initialize the autonomous storyteller"""

        # Initialize AI model if available
        if self.ai_storyteller:
            ai_success = await self.ai_storyteller.initialize()
            if not ai_success:
                self.logger.warning(
                    "AI model failed to load - using fallback decisions"
                )
        else:
            self.logger.warning("No AI storyteller provided - using fallback decisions")

        # Initialize speech if available
        if self.speech_handler:
            speech_success = await self.speech_handler.initialize()
            if not speech_success:
                self.logger.error("Speech handler failed - cannot operate autonomously")
                return False
        else:
            self.logger.warning(
                "No speech handler provided - operating without speech recognition"
            )

        return True

    async def start_autonomous_operation(self, game_state: GameState):
        """Start autonomous storyteller operation"""

        self.game_state = game_state
        self.is_running = True

        # Start background tasks
        asyncio.create_task(self._speech_listener())
        asyncio.create_task(self._action_processor())
        asyncio.create_task(self._phase_manager())

        self.logger.info("Autonomous storyteller started")

    async def _speech_listener(self):
        """Continuously listen for player speech"""

        while self.is_running:
            try:
                # Listen for speech
                keywords = ["storyteller", "choose", "nominate", "vote"]
                speech_text = await self.speech_handler.listen_for_command(
                    keywords=keywords, timeout=10.0
                )

                if speech_text:
                    self.logger.info(f"Heard: {speech_text}")

                    # Parse into action
                    action = self.speech_parser.parse_speech(
                        speech_text, "Unknown", self.game_state
                    )

                    if action:
                        await self.pending_actions.put(action)

            except Exception as e:
                self.logger.error(f"Speech listening error: {e}")
                await asyncio.sleep(1)

    async def _action_processor(self):
        """Process queued player actions"""

        while self.is_running:
            try:
                # Wait for action
                action = await self.pending_actions.get()

                # Add to context
                self.game_context.add_action(action)

                # Process based on action type
                if action.action_type == "fortune_teller":
                    await self._handle_fortune_teller(action)
                elif action.action_type == "empath":
                    await self._handle_empath(action)
                elif action.action_type == "nomination":
                    await self._handle_nomination(action)
                elif action.action_type == "question":
                    await self._handle_question(action)

            except Exception as e:
                self.logger.error(f"Action processing error: {e}")

    async def _handle_fortune_teller(self, action: PlayerAction):
        """Handle Fortune Teller information request"""

        targets = action.details.get("targets", [])
        if len(targets) != 2:
            await self._speak("Fortune Teller, please choose exactly 2 players.")
            return

        # Use AI to decide what information to give
        context_summary = self.game_context.get_context_summary(self.game_state)

        prompt = f"""
{context_summary}

The Fortune Teller {action.player_name} is asking about {targets[0]} and {targets[1]}.

As the Storyteller, decide what information to give. Consider:
- Are either of them actually the Demon?
- Is the Fortune Teller drunk or poisoned?
- Game balance - what's best for the story?

Respond with just: "YES" or "NO"
"""

        try:
            ai_response = await self.ai_storyteller.narrate(
                "rule_question", {"question": prompt}
            )

            # Parse AI decision
            result = "YES" if "yes" in ai_response.lower() else "NO"

            # Record information given
            info = InformationGiven(
                player_name=action.player_name,
                character="Fortune Teller",
                info_type="fortune_teller",
                information=f"Asked about {targets[0]} and {targets[1]}: {result}",
                was_true=self._is_fortune_teller_info_true(targets, result),
                context=context_summary,
                timestamp=datetime.now(),
                night_number=self.game_state.day_number,
            )

            self.game_context.add_information(info)

            # Speak to Fortune Teller privately
            await self._speak_privately(
                action.player_name,
                f"You learn: {result} - one of {targets[0]} or {targets[1]} is the Demon.",
            )

        except Exception as e:
            self.logger.error(f"Fortune Teller decision error: {e}")
            await self._speak_privately(action.player_name, "You learn: NO")

    def _is_fortune_teller_info_true(self, targets: List[str], result: str) -> bool:
        """Check if the Fortune Teller information was accurate"""

        # Find the targets in game state
        target_players = [p for p in self.game_state.players if p.name in targets]

        # Check if either is actually a demon
        actual_demon_count = len(
            [p for p in target_players if self._is_demon(p.character)]
        )

        if result == "YES":
            return actual_demon_count > 0
        else:
            return actual_demon_count == 0

    def _is_demon(self, character: str) -> bool:
        """Check if character is a demon"""
        demons = ["Imp", "Vigormortis", "No Dashii", "Vortox"]  # Add more as needed
        return character in demons

    async def _speak(self, message: str):
        """Speak publicly"""
        await self.speech_handler.speak(message)

    async def _speak_privately(self, player_name: str, message: str):
        """Speak privately to a player"""
        await self.speech_handler.speak_to_player(player_name, message)

    async def _phase_manager(self):
        """Manage game phases autonomously"""

        while self.is_running:
            if self.game_state.phase == GamePhase.NIGHT:
                await self._run_night_phase()
            elif self.game_state.phase == GamePhase.DAY:
                await self._run_day_phase()

            await asyncio.sleep(5)  # Check every 5 seconds

    async def _run_night_phase(self):
        """Run the night phase autonomously"""

        # Announce night
        narration = await self.ai_storyteller.narrate(
            "night_phase", {"night": self.game_state.day_number}
        )
        await self._speak(narration)

        # Process each character in wake order
        wake_order = ["Poisoner", "Fortune Teller", "Empath", "Imp"]  # Add full order

        for character in wake_order:
            players_with_char = [
                p
                for p in self.game_state.players
                if p.character == character and p.is_alive()
            ]

            if players_with_char:
                await self._wake_character(character, players_with_char[0])

        # Move to day
        self.game_state.phase = GamePhase.DAY

    async def _wake_character(self, character: str, player: Player):
        """Wake a specific character for their night action"""

        await self._speak(f"{character}, wake up.")

        # Wait for their action based on character type
        if character == "Fortune Teller":
            await self._speak("Choose two players to learn about.")
            # Wait for Fortune Teller to make choice
            await asyncio.sleep(30)  # Give them time

        await self._speak(f"{character}, go back to sleep.")

    async def _run_day_phase(self):
        """Run the day phase"""

        # Announce dawn and deaths
        deaths = []  # Would be determined by night actions

        if deaths:
            death_announcement = await self.ai_storyteller.narrate(
                "death_announcement", {"deaths": deaths}
            )
        else:
            death_announcement = await self.ai_storyteller.narrate(
                "death_announcement", {"deaths": []}
            )

        await self._speak(death_announcement)

        # Allow discussion and nominations
        # This would continue until execution or no execution

    def stop_autonomous_operation(self):
        """Stop autonomous operation"""
        self.is_running = False
