"""
Speech-Integrated Game Controller for Blood on the Clocktower
Combines MVP game engine with speech recognition for real-time voice-controlled gameplay
"""

import asyncio
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from ..speech.speech_handler import SpeechConfig, SpeechHandler
from .mvp_game_controller import MVPGameController
from .player_choice_system import ChoiceRequest, ChoiceResult, ChoiceType


class SpeechCommandParser:
    """Parses speech commands for game actions"""

    def __init__(self, player_names: List[str]):
        self.player_names = player_names
        self.logger = logging.getLogger(__name__)

        # Common command patterns
        self.nomination_patterns = [
            r"i nominate (\w+)",
            r"nominate (\w+)",
            r"(\w+) nominates (\w+)",
        ]

        self.vote_patterns = [
            r"(\w+) votes? yes",
            r"(\w+) votes? aye",
            r"(\w+) votes? no",
            r"i vote yes",
            r"i vote no",
            r"yes",
            r"no",
            r"aye",
        ]

        self.night_action_patterns = [
            r"i choose (\w+)",
            r"i select (\w+)",
            r"(\w+) and (\w+)",  # For dual targets
            r"target (\w+)",
        ]

    def parse_nomination(self, command: str) -> Optional[Dict[str, str]]:
        """Parse nomination from speech command"""
        command = command.lower().strip()

        for pattern in self.nomination_patterns:
            match = re.search(pattern, command)
            if match:
                if len(match.groups()) == 1:
                    nominee = self._find_player_name(match.group(1))
                    if nominee:
                        return {
                            "nominee": nominee,
                            "nominator": "Unknown",  # Will be identified by voice later
                            "command": command,
                        }
                elif len(match.groups()) == 2:
                    nominator = self._find_player_name(match.group(1))
                    nominee = self._find_player_name(match.group(2))
                    if nominator and nominee:
                        return {
                            "nominee": nominee,
                            "nominator": nominator,
                            "command": command,
                        }
        return None

    def parse_vote(self, command: str) -> Optional[Dict[str, Any]]:
        """Parse vote from speech command"""
        command = command.lower().strip()

        for pattern in self.vote_patterns:
            match = re.search(pattern, command)
            if match:
                if "yes" in command or "aye" in command:
                    vote_value = True
                elif "no" in command:
                    vote_value = False
                else:
                    continue

                voter = None
                if len(match.groups()) >= 1:
                    voter = self._find_player_name(match.group(1))

                return {
                    "voter": voter or "Unknown",
                    "vote": vote_value,
                    "command": command,
                }
        return None

    def parse_night_action(self, command: str) -> Optional[Dict[str, Any]]:
        """Parse night action from speech command"""
        command = command.lower().strip()

        # Check for dual target pattern first
        dual_match = re.search(r"(\w+) and (\w+)", command)
        if dual_match:
            target1 = self._find_player_name(dual_match.group(1))
            target2 = self._find_player_name(dual_match.group(2))
            if target1 and target2:
                return {
                    "type": "dual_target",
                    "target1": target1,
                    "target2": target2,
                    "command": command,
                }

        # Single target patterns
        for pattern in self.night_action_patterns:
            match = re.search(pattern, command)
            if match and len(match.groups()) == 1:
                target = self._find_player_name(match.group(1))
                if target:
                    return {
                        "type": "single_target",
                        "target": target,
                        "command": command,
                    }
        return None

    def _find_player_name(self, name_fragment: str) -> Optional[str]:
        """Find closest matching player name"""
        name_fragment = name_fragment.lower()

        # Exact match first
        for name in self.player_names:
            if name.lower() == name_fragment:
                return name

        # Partial match
        for name in self.player_names:
            if name.lower().startswith(name_fragment):
                return name

        return None


class SpeechPlayerChoices:
    """Speech-based player choice system for night actions"""

    def __init__(
        self, speech_handler: SpeechHandler, command_parser: SpeechCommandParser
    ):
        self.speech_handler = speech_handler
        self.command_parser = command_parser
        self.logger = logging.getLogger(__name__)

    async def request_choice_async(self, request: ChoiceRequest) -> ChoiceResult:
        """Request a choice through speech recognition"""

        self.logger.info(
            f"Requesting speech choice from {request.player_name} ({request.character})"
        )

        # Announce to the player
        await self.speech_handler.speak_to_player(request.player_name, request.prompt)

        if request.choice_type == ChoiceType.SINGLE_TARGET:
            return await self._get_single_target_speech(request)
        elif request.choice_type == ChoiceType.DUAL_TARGET:
            return await self._get_dual_target_speech(request)
        elif request.choice_type == ChoiceType.YES_NO:
            return await self._get_yes_no_speech(request)
        else:
            # No choice needed
            await asyncio.sleep(1)
            return ChoiceResult(
                player_name=request.player_name,
                character=request.character,
                choice_type=request.choice_type,
                is_valid=True,
            )

    async def _get_single_target_speech(self, request: ChoiceRequest) -> ChoiceResult:
        """Get single target choice via speech"""

        # Listen for target selection
        for attempt in range(3):  # Max 3 attempts
            command = await self.speech_handler.listen_for_command(
                keywords=["choose", "select", "target"] + request.valid_targets,
                timeout=request.timeout_seconds,
            )

            if command:
                action = self.command_parser.parse_night_action(command)
                if action and action["type"] == "single_target":
                    target = action["target"]
                    if target in request.valid_targets:
                        await self.speech_handler.speak_to_player(
                            request.player_name, f"You choose {target}"
                        )
                        return ChoiceResult(
                            player_name=request.player_name,
                            character=request.character,
                            choice_type=request.choice_type,
                            targets=[target],
                            is_valid=True,
                        )
                    else:
                        await self.speech_handler.speak_to_player(
                            request.player_name, f"Invalid target. Try again."
                        )
                else:
                    await self.speech_handler.speak_to_player(
                        request.player_name, "I didn't understand. Please try again."
                    )
            else:
                await self.speech_handler.speak_to_player(
                    request.player_name, "No response heard. Try again."
                )

        # Failed to get valid choice
        return ChoiceResult(
            player_name=request.player_name,
            character=request.character,
            choice_type=request.choice_type,
            is_valid=False,
            error_message="Failed to get valid speech input",
        )

    async def _get_dual_target_speech(self, request: ChoiceRequest) -> ChoiceResult:
        """Get dual target choice via speech"""

        for attempt in range(3):
            command = await self.speech_handler.listen_for_command(
                keywords=["choose", "select"] + request.valid_targets + ["and"],
                timeout=request.timeout_seconds,
            )

            if command:
                action = self.command_parser.parse_night_action(command)
                if action and action["type"] == "dual_target":
                    target1, target2 = action["target1"], action["target2"]
                    if (
                        target1 in request.valid_targets
                        and target2 in request.valid_targets
                        and target1 != target2
                    ):
                        await self.speech_handler.speak_to_player(
                            request.player_name, f"You choose {target1} and {target2}"
                        )
                        return ChoiceResult(
                            player_name=request.player_name,
                            character=request.character,
                            choice_type=request.choice_type,
                            targets=[target1, target2],
                            is_valid=True,
                        )
                    else:
                        await self.speech_handler.speak_to_player(
                            request.player_name, "Invalid targets. Try again."
                        )
                else:
                    await self.speech_handler.speak_to_player(
                        request.player_name,
                        "Please say two names with 'and' between them.",
                    )
            else:
                await self.speech_handler.speak_to_player(
                    request.player_name, "No response heard. Try again."
                )

        return ChoiceResult(
            player_name=request.player_name,
            character=request.character,
            choice_type=request.choice_type,
            is_valid=False,
            error_message="Failed to get valid dual target input",
        )

    async def _get_yes_no_speech(self, request: ChoiceRequest) -> ChoiceResult:
        """Get yes/no choice via speech"""

        for attempt in range(3):
            command = await self.speech_handler.listen_for_command(
                keywords=["yes", "no", "aye"], timeout=request.timeout_seconds
            )

            if command:
                command_lower = command.lower()
                if "yes" in command_lower or "aye" in command_lower:
                    answer = True
                elif "no" in command_lower:
                    answer = False
                else:
                    await self.speech_handler.speak_to_player(
                        request.player_name, "Please say yes or no."
                    )
                    continue

                response_text = "Yes" if answer else "No"
                await self.speech_handler.speak_to_player(
                    request.player_name, f"You answered {response_text}"
                )

                return ChoiceResult(
                    player_name=request.player_name,
                    character=request.character,
                    choice_type=request.choice_type,
                    yes_no_answer=answer,
                    is_valid=True,
                )
            else:
                await self.speech_handler.speak_to_player(
                    request.player_name, "No response heard. Try again."
                )

        return ChoiceResult(
            player_name=request.player_name,
            character=request.character,
            choice_type=request.choice_type,
            is_valid=False,
            error_message="Failed to get valid yes/no input",
        )


class SpeechIntegratedController(MVPGameController):
    """Speech-integrated game controller that handles voice commands"""

    def __init__(self, speech_config: SpeechConfig = None):
        super().__init__(use_mock_choices=False)  # Don't use mock choices

        # Initialize speech systems
        self.speech_config = speech_config or SpeechConfig()
        self.speech_handler = SpeechHandler(self.speech_config)
        self.command_parser: Optional[SpeechCommandParser] = None
        self.speech_choices: Optional[SpeechPlayerChoices] = None

        # Speech integration state
        self.is_speech_initialized = False
        self.listening_active = False

    async def setup_game(self, player_names: List[str]) -> bool:
        """Setup game with speech integration"""

        print("=== Setting up Speech-Integrated Blood on the Clocktower ===")

        try:
            # Initialize speech systems
            if not await self._initialize_speech():
                print("Failed to initialize speech systems")
                return False

            # Initialize command parser with player names
            self.command_parser = SpeechCommandParser(player_names)
            self.speech_choices = SpeechPlayerChoices(
                self.speech_handler, self.command_parser
            )

            # Use speech choice system instead of mock
            self.choice_system = self.speech_choices

            # Setup the game using parent method
            success = await super().setup_game(player_names)

            if success:
                await self.speech_handler.speak(
                    "Speech recognition is active. Players may now use voice commands."
                )

            return success

        except Exception as e:
            print(f"Failed to setup speech-integrated game: {e}")
            return False

    async def _initialize_speech(self) -> bool:
        """Initialize speech recognition and TTS"""
        if self.is_speech_initialized:
            return True

        try:
            print("Initializing speech recognition and text-to-speech...")
            success = await self.speech_handler.initialize()

            if success:
                self.is_speech_initialized = True
                print("✅ Speech systems ready!")

                # Test speech synthesis
                await self.speech_handler.speak("Speech systems are now online.")

            return success

        except Exception as e:
            print(f"Speech initialization failed: {e}")
            return False

    async def _announce_game_setup(self, game_state):
        """Announce game setup with speech synthesis"""

        await super()._announce_game_setup(game_state)

        # Additional speech announcement
        await self.speech_handler.speak(
            f"Welcome to Blood on the Clocktower with {len(game_state.players)} players."
        )

        # Announce player names
        player_list = ", ".join([p.name for p in game_state.players])
        await self.speech_handler.speak(f"Players are: {player_list}")

    async def _run_day_phase(self):
        """Run day phase with speech-controlled nominations and voting"""

        print(f"\n☀️ DAY {self.engine.game_state.day_number}")
        await self.speech_handler.speak(
            f"Good morning everyone! It is day {self.engine.game_state.day_number}. "
            "The town may now discuss and nominate players for execution."
        )

        alive_players = self.engine.get_alive_players()

        if len(alive_players) < 3:
            await self.speech_handler.speak("Not enough players alive for nominations.")
            return

        # Extended discussion period
        await self.speech_handler.speak(
            "You have 3 minutes for discussion before nominations begin."
        )
        await asyncio.sleep(180)  # 3 minutes discussion

        # Handle speech-controlled nominations
        executed_player = await self._handle_speech_nominations_and_voting()

        if executed_player:
            self.engine.execute_player(executed_player)
            await self.speech_handler.speak(f"{executed_player} has been executed!")

            # Dramatic pause
            await asyncio.sleep(3)

            # Check if it was demon
            executed = self.engine.get_player_by_name(executed_player)
            if executed and executed.character in ["Imp"]:
                await self.speech_handler.speak("The demon falls! Good team wins!")
        else:
            await self.speech_handler.speak(
                "No execution today. The town remains divided."
            )

    async def _handle_speech_nominations_and_voting(self) -> Optional[str]:
        """Handle nominations and voting through speech recognition"""

        await self.speech_handler.speak(
            "Nominations are now open. Say 'I nominate [player name]' to make a nomination."
        )

        nominations = []
        nomination_timeout = 120  # 2 minutes for nominations
        start_time = asyncio.get_event_loop().time()

        while (asyncio.get_event_loop().time() - start_time) < nomination_timeout:
            # Listen for nomination commands
            command = await self.speech_handler.listen_for_command(
                keywords=["nominate", "I nominate", "close nominations"], timeout=5.0
            )

            if command:
                if "close" in command.lower():
                    break

                # Parse nomination
                nomination = self.command_parser.parse_nomination(command)
                if nomination and nomination["nominee"]:
                    nominee = nomination["nominee"]

                    # Check if nominee already nominated
                    if nominee not in [n["nominee"] for n in nominations]:
                        nominations.append(nomination)
                        await self.speech_handler.speak(
                            f"{nominee} has been nominated for execution."
                        )
                    else:
                        await self.speech_handler.speak(
                            f"{nominee} has already been nominated today."
                        )
                else:
                    await self.speech_handler.speak(
                        "I didn't understand that nomination."
                    )

        if not nominations:
            await self.speech_handler.speak("No nominations were made today.")
            return None

        # Conduct voting on each nomination
        for nomination in nominations:
            executed_player = await self._conduct_speech_vote(nomination["nominee"])
            if executed_player:
                return executed_player

        return None

    async def _conduct_speech_vote(self, nominee: str) -> Optional[str]:
        """Conduct voting on a nominee through speech"""

        await self.speech_handler.speak(
            f"Voting on {nominee}. Say 'yes' or 'aye' to vote for execution, 'no' to vote against."
        )

        alive_players = self.engine.get_alive_players()
        votes = []
        vote_timeout = 30  # 30 seconds for voting

        await self.speech_handler.speak("Voting begins now.")

        start_time = asyncio.get_event_loop().time()
        while (asyncio.get_event_loop().time() - start_time) < vote_timeout:
            command = await self.speech_handler.listen_for_command(
                keywords=["yes", "no", "aye"], timeout=2.0
            )

            if command:
                vote_data = self.command_parser.parse_vote(command)
                if vote_data:
                    vote_data["voter"]
                    vote_value = vote_data["vote"]

                    # For now, accept votes without strict voter identification
                    if len(votes) < len(alive_players):
                        votes.append(vote_value)
                        response = "Yes" if vote_value else "No"
                        await self.speech_handler.speak(f"Vote recorded: {response}")

        yes_votes = sum(1 for v in votes if v)
        no_votes = len(votes) - yes_votes
        threshold = (len(alive_players) + 1) // 2

        await self.speech_handler.speak(
            f"Vote results: {yes_votes} yes, {no_votes} no. "
            f"Threshold for execution: {threshold}."
        )

        if yes_votes >= threshold:
            await self.speech_handler.speak(f"{nominee} will be executed!")
            return nominee
        else:
            await self.speech_handler.speak(f"{nominee} survives the vote.")
            return None

    async def _announce_victory(self, win_result: Tuple[str, str]):
        """Announce victory with dramatic speech synthesis"""

        winning_team, reason = win_result

        # Enhanced victory announcement
        if winning_team == "good":
            await self.speech_handler.speak(
                "🎉 The forces of good have triumphed! The town is saved!"
            )
        else:
            await self.speech_handler.speak(
                "💀 Evil has consumed the town! Darkness reigns supreme!"
            )

        await asyncio.sleep(2)
        await self.speech_handler.speak(reason)

        # Call parent for character reveals
        await super()._announce_victory(win_result)

        # Final speech
        await self.speech_handler.speak(
            "Thank you for playing Blood on the Clocktower! Game ended."
        )

    def cleanup(self):
        """Cleanup speech resources"""
        if self.speech_handler:
            self.speech_handler.cleanup()


# Example usage
async def run_speech_integrated_game():
    """Run a complete speech-integrated game"""

    controller = SpeechIntegratedController()

    # Setup game
    player_names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace"]
    success = await controller.setup_game(player_names)

    if success:
        try:
            # Run game
            result = await controller.run_game()
            print(f"\n🎮 Game completed: {result}")
        except KeyboardInterrupt:
            print("\n🛑 Game interrupted by user")
        finally:
            controller.cleanup()
    else:
        print("❌ Failed to setup speech-integrated game")


if __name__ == "__main__":
    # Run the speech-integrated game
    asyncio.run(run_speech_integrated_game())
