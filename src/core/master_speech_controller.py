"""
Master Speech-Controlled Blood on the Clocktower Controller
Integrates all speech systems for a complete voice-controlled game experience
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from .enhanced_speech_night_interface import FullySpeechIntegratedController
from ..speech.enhanced_storyteller_tts import DramaticStoryteller
from ..speech.advanced_nlp_processor import AdvancedNLPProcessor, Intent
from ..speech.voice_player_identification import (
    VoicePlayerIdentifier,
    SecureVoiceActions,
)
from ..speech.speech_handler import SpeechHandler, SpeechConfig


class MasterSpeechController(FullySpeechIntegratedController):
    """Master controller with full speech integration"""

    def __init__(self, speech_config: SpeechConfig = None):
        super().__init__(speech_config)

        # Advanced speech systems
        self.dramatic_storyteller: Optional[DramaticStoryteller] = None
        self.nlp_processor: Optional[AdvancedNLPProcessor] = None
        self.voice_identifier: Optional[VoicePlayerIdentifier] = None
        self.secure_actions: Optional[SecureVoiceActions] = None

        # Master controller state
        self.voice_id_enabled = True
        self.nlp_enabled = True
        self.dramatic_narration = True

        # Speech analytics
        self.command_stats = {
            "total_commands": 0,
            "successful_commands": 0,
            "failed_commands": 0,
            "voice_id_successes": 0,
            "voice_id_failures": 0,
        }

    async def setup_game(self, player_names: List[str]) -> bool:
        """Setup game with full speech integration"""

        print("=== Initializing Master Speech-Controlled Blood on the Clocktower ===")

        try:
            # Initialize base speech systems
            success = await super().setup_game(player_names)
            if not success:
                return False

            # Initialize advanced speech systems
            await self._initialize_advanced_speech_systems(player_names)

            # Dramatic game opening
            await self._dramatic_game_opening(player_names)

            return True

        except Exception as e:
            print(f"Failed to setup master speech controller: {e}")
            return False

    async def _initialize_advanced_speech_systems(self, player_names: List[str]):
        """Initialize all advanced speech systems"""

        print("🎭 Initializing dramatic storyteller...")
        self.dramatic_storyteller = DramaticStoryteller(self.speech_handler)

        print("🧠 Initializing natural language processor...")
        self.nlp_processor = AdvancedNLPProcessor(player_names)

        if self.voice_id_enabled:
            print("🎤 Initializing voice identification...")
            self.voice_identifier = VoicePlayerIdentifier(
                self.speech_handler, player_names
            )

            # Train voice profiles
            voice_success = await self.voice_identifier.initialize_voice_profiles()
            if voice_success:
                self.secure_actions = SecureVoiceActions(self.voice_identifier)
                print("✅ Voice identification ready")
            else:
                print("⚠️ Voice identification partially failed - continuing without")
                self.voice_id_enabled = False

        print("🚀 All speech systems initialized!")

    async def _dramatic_game_opening(self, player_names: List[str]):
        """Deliver dramatic game opening"""

        if self.dramatic_storyteller:
            await self.dramatic_storyteller.narrate_game_event(
                "game_start",
                player_count=len(player_names),
                script_name="Trouble Brewing",
            )
        else:
            await self.speech_handler.speak("Welcome to Blood on the Clocktower!")

    async def run_game(self) -> Optional[Tuple[str, str]]:
        """Run the complete game with master speech control"""

        if not self.engine.game_state:
            print("Game not setup!")
            return None

        self.is_running = True

        try:
            # Dramatic first night
            await self._master_first_night()

            # Main game loop with advanced speech
            while self.is_running:
                # Advanced day phase
                await self._master_day_phase()

                # Check win condition
                win_result = self.engine.check_win_condition()
                if win_result:
                    await self._dramatic_victory_announcement(win_result)
                    return win_result

                # Advanced night phase
                await self._master_night_phase()

                # Check win condition after night
                win_result = self.engine.check_win_condition()
                if win_result:
                    await self._dramatic_victory_announcement(win_result)
                    return win_result

        except KeyboardInterrupt:
            await self.speech_handler.speak("Game interrupted by storyteller.")
            self.is_running = False

        except Exception as e:
            await self.speech_handler.speak(
                "A mysterious error has occurred. The game ends."
            )
            print(f"Game error: {e}")
            self.is_running = False

        return None

    async def _master_first_night(self):
        """First night with dramatic narration"""

        if self.dramatic_storyteller:
            await self.dramatic_storyteller.narrate_game_event("first_night")
        else:
            await self.speech_handler.speak("🌙 The first night begins...")

        # Use enhanced night interface
        await super()._run_first_night()

    async def _master_day_phase(self):
        """Day phase with advanced speech processing"""

        print(f"\n☀️ DAY {self.engine.game_state.day_number}")

        if self.dramatic_storyteller:
            await self.dramatic_storyteller.narrate_game_event(
                "phase_change",
                old_phase="night",
                new_phase="day",
                day_number=self.engine.game_state.day_number,
            )
        else:
            await self.speech_handler.speak(
                f"Day {self.engine.game_state.day_number} begins."
            )

        # Extended discussion with NLP monitoring
        await self._advanced_discussion_phase()

        # Advanced nomination system
        executed_player = await self._advanced_nomination_and_voting()

        if executed_player:
            self.engine.execute_player(executed_player)

            # Dramatic execution
            executed = self.engine.get_player_by_name(executed_player)
            if executed and self.dramatic_storyteller:
                await self.dramatic_storyteller.narrate_game_event(
                    "execution",
                    player_name=executed_player,
                    character=executed.character,
                )
            else:
                await self.speech_handler.speak(
                    f"⚰️ {executed_player} has been executed!"
                )
        else:
            await self.speech_handler.speak("🤝 No execution today.")

    async def _advanced_discussion_phase(self):
        """Discussion phase with NLP monitoring"""

        await self.speech_handler.speak(
            "The town may now discuss. I am listening for important information."
        )

        discussion_time = 240  # 4 minutes
        start_time = asyncio.get_event_loop().time()

        interesting_commands = []

        while (asyncio.get_event_loop().time() - start_time) < discussion_time:
            # Listen for any speech
            command = await self.speech_handler.listen_for_command(
                keywords=["storyteller", "question", "nominate", "claim"], timeout=5.0
            )

            if command:
                await self._process_discussion_command(command, interesting_commands)

        # Summarize interesting information
        if interesting_commands and self.dramatic_storyteller:
            await self.speech_handler.speak(
                "Interesting claims and accusations have been made. Let us proceed to nominations."
            )
        else:
            await self.speech_handler.speak(
                "The discussion concludes. Time for nominations."
            )

    async def _process_discussion_command(
        self, command: str, interesting_commands: List[str]
    ):
        """Process commands during discussion"""

        self.command_stats["total_commands"] += 1

        if self.nlp_processor:
            # Get current game state for context
            game_state = {
                "phase": "day",
                "alive_players": [p.name for p in self.engine.get_alive_players()],
                "day_number": self.engine.game_state.day_number,
            }

            parsed = self.nlp_processor.process_speech(command, game_state)

            # Respond based on intent
            if parsed.intent == Intent.QUESTION:
                await self._handle_player_question(command)
            elif parsed.intent == Intent.CLAIM:
                await self._handle_character_claim(parsed)
                interesting_commands.append(command)
            elif parsed.intent == Intent.ACCUSATION:
                await self._handle_accusation(parsed)
                interesting_commands.append(command)
            elif parsed.intent == Intent.NOMINATE:
                await self.speech_handler.speak("Nominations will begin shortly.")

            # Track successful processing
            if parsed.confidence > 0.7:
                self.command_stats["successful_commands"] += 1
            else:
                self.command_stats["failed_commands"] += 1
        else:
            # Fallback without NLP
            if "question" in command.lower():
                await self._handle_player_question(command)

    async def _handle_player_question(self, question: str):
        """Handle player questions intelligently"""

        # Common question responses
        if "rules" in question.lower():
            await self.speech_handler.speak(
                "Ask specific rule questions and I will answer them."
            )
        elif "character" in question.lower():
            await self.speech_handler.speak(
                "Character abilities are described in the rulebook. I cannot reveal secret information."
            )
        elif "vote" in question.lower():
            await self.speech_handler.speak(
                "You need a simple majority to execute. Half the living players plus one."
            )
        else:
            await self.speech_handler.speak(
                "I am here to answer rules questions and guide the game."
            )

    async def _handle_character_claim(self, parsed_command):
        """Handle character claims"""

        entities = parsed_command.entities
        if "claimed_character" in entities:
            character = entities["claimed_character"]
            await self.speech_handler.speak(f"A {character} claim has been noted.")

    async def _handle_accusation(self, parsed_command):
        """Handle accusations"""

        entities = parsed_command.entities
        if "accused" in entities:
            accused = entities["accused"][0] if entities["accused"] else "someone"
            await self.speech_handler.speak(f"Suspicion of {accused} has been noted.")

    async def _advanced_nomination_and_voting(self) -> Optional[str]:
        """Advanced nomination system with voice ID and NLP"""

        await self.speech_handler.speak(
            "🗳️ Nominations are now open. Clearly state 'I nominate [player name]' to make a nomination."
        )

        nominations = []
        nomination_timeout = 180  # 3 minutes
        start_time = asyncio.get_event_loop().time()

        while (asyncio.get_event_loop().time() - start_time) < nomination_timeout:
            command = await self.speech_handler.listen_for_command(
                keywords=["nominate", "I nominate", "close nominations"], timeout=10.0
            )

            if command:
                if "close" in command.lower():
                    break

                # Advanced nomination processing
                nomination_result = await self._process_advanced_nomination(command)
                if nomination_result:
                    nominations.append(nomination_result)

        if not nominations:
            await self.speech_handler.speak("No valid nominations were made.")
            return None

        # Vote on each nomination with voice ID
        for nomination in nominations:
            executed_player = await self._advanced_voting(nomination)
            if executed_player:
                return executed_player

        return None

    async def _process_advanced_nomination(
        self, command: str
    ) -> Optional[Dict[str, str]]:
        """Process nomination with NLP and voice ID"""

        if self.nlp_processor:
            game_state = {
                "phase": "day",
                "alive_players": [p.name for p in self.engine.get_alive_players()],
                "nominations_today": [],  # Track this properly
            }

            parsed = self.nlp_processor.process_speech(command, game_state)

            if parsed.intent == Intent.NOMINATE and "nominee" in parsed.entities:
                nominee = parsed.entities["nominee"]

                # Voice identification for nominator
                if self.voice_id_enabled and self.secure_actions:
                    success, message, nominator = (
                        await self.secure_actions.secure_nomination(nominee)
                    )

                    if success:
                        await self.speech_handler.speak(
                            f"{nominator} nominates {nominee}!"
                        )
                        self.command_stats["voice_id_successes"] += 1
                        return {"nominator": nominator, "nominee": nominee}
                    else:
                        await self.speech_handler.speak(f"Nomination failed: {message}")
                        self.command_stats["voice_id_failures"] += 1
                        return None
                else:
                    # Without voice ID
                    await self.speech_handler.speak(f"{nominee} has been nominated!")
                    return {"nominator": "Unknown", "nominee": nominee}

        return None

    async def _advanced_voting(self, nomination: Dict[str, str]) -> Optional[str]:
        """Advanced voting with voice ID and dramatic announcements"""

        nominee = nomination["nominee"]

        if self.dramatic_storyteller:
            await self.dramatic_storyteller.narrate_game_event(
                "voting", nominee=nominee
            )
        else:
            await self.speech_handler.speak(f"Voting on {nominee}.")

        alive_players = self.engine.get_alive_players()
        votes = []

        # Individual voting with voice ID
        for player in alive_players:
            vote_result = await self._get_individual_vote_with_id(player)
            votes.append(vote_result)

        yes_votes = sum(1 for v in votes if v)
        no_votes = len(votes) - yes_votes
        threshold = (len(alive_players) + 1) // 2
        execute = yes_votes >= threshold

        # Dramatic vote announcement
        if self.dramatic_storyteller:
            await self.dramatic_storyteller.narrate_game_event(
                "vote_results",
                yes_votes=yes_votes,
                no_votes=no_votes,
                threshold=threshold,
                execute=execute,
                nominee=nominee,
            )
        else:
            result = "executed" if execute else "spared"
            await self.speech_handler.speak(f"{nominee} is {result}!")

        return nominee if execute else None

    async def _get_individual_vote_with_id(self, player) -> bool:
        """Get individual vote with optional voice identification"""

        await self.speech_handler.speak(f"{player.name}, how do you vote?")

        if self.voice_id_enabled and self.secure_actions:
            # Try voice identification
            success, message, voter = await self.secure_actions.secure_vote(
                True
            )  # Placeholder

            if success and voter == player.name:
                # Get actual vote
                for attempt in range(2):
                    command = await self.speech_handler.listen_for_command(
                        keywords=["yes", "no", "aye"], timeout=10.0
                    )

                    if command:
                        if "yes" in command.lower() or "aye" in command.lower():
                            await self.speech_handler.speak(f"{player.name} votes yes.")
                            return True
                        elif "no" in command.lower():
                            await self.speech_handler.speak(f"{player.name} votes no.")
                            return False

            # Voice ID failed
            await self.speech_handler.speak(
                f"Could not verify {player.name}'s vote. Abstaining."
            )
            return False
        else:
            # Standard voting without voice ID
            return await self._get_standard_vote(player)

    async def _get_standard_vote(self, player) -> bool:
        """Get vote without voice identification"""

        for attempt in range(3):
            command = await self.speech_handler.listen_for_command(
                keywords=["yes", "no", "aye"], timeout=10.0
            )

            if command:
                if "yes" in command.lower() or "aye" in command.lower():
                    await self.speech_handler.speak(f"{player.name} votes yes.")
                    return True
                elif "no" in command.lower():
                    await self.speech_handler.speak(f"{player.name} votes no.")
                    return False

        await self.speech_handler.speak(f"{player.name} abstains.")
        return False

    async def _master_night_phase(self):
        """Night phase with dramatic narration"""

        if self.dramatic_storyteller:
            await self.dramatic_storyteller.narrate_game_event(
                "phase_change",
                old_phase="day",
                new_phase="night",
                day_number=self.engine.game_state.day_number,
            )
        else:
            await self.speech_handler.speak(
                f"🌙 Night {self.engine.game_state.day_number} begins."
            )

        # Use enhanced night interface
        await super()._run_night_phase()

        # Dramatic dawn announcement
        await self._dramatic_dawn_announcement()

    async def _dramatic_dawn_announcement(self):
        """Dramatic dawn announcement with deaths"""

        # Find deaths from night actions
        deaths = []
        for result in self.ability_results:
            if result.character == "Imp" and result.is_successful:
                target_name = result.targets[0] if result.targets else None
                if target_name:
                    target_player = self.engine.get_player_by_name(target_name)
                    if target_player and not target_player.is_alive():
                        deaths.append(target_name)

        if self.dramatic_storyteller:
            await self.dramatic_storyteller.narrate_game_event("dawn", deaths=deaths)
        else:
            if deaths:
                death_list = ", ".join(deaths)
                await self.speech_handler.speak(f"💀 {death_list} died in the night.")
            else:
                await self.speech_handler.speak("✨ Nobody died last night!")

        self.ability_results.clear()

    async def _dramatic_victory_announcement(self, win_result: Tuple[str, str]):
        """Dramatic victory announcement"""

        winning_team, reason = win_result

        if self.dramatic_storyteller:
            await self.dramatic_storyteller.narrate_game_event(
                "victory", winning_team=winning_team, reason=reason
            )
        else:
            await self.speech_handler.speak(
                f"🏆 {winning_team.upper()} TEAM WINS! {reason}"
            )

        # Show final character reveals
        await self.speech_handler.speak("📋 Final character reveals:")
        for player in self.engine.game_state.players:
            status = "ALIVE" if player.is_alive() else "DEAD"
            await self.speech_handler.speak(
                f"{player.name}: {player.character} ({status})"
            )

        # Game statistics
        await self._announce_game_statistics()

        self.is_running = False

    async def _announce_game_statistics(self):
        """Announce game and speech statistics"""

        total_commands = self.command_stats["total_commands"]
        if total_commands > 0:
            success_rate = (
                self.command_stats["successful_commands"] / total_commands
            ) * 100

            await self.speech_handler.speak(
                f"Game statistics: {total_commands} voice commands processed "
                f"with {success_rate:.1f}% success rate."
            )

        if self.voice_id_enabled:
            voice_attempts = (
                self.command_stats["voice_id_successes"]
                + self.command_stats["voice_id_failures"]
            )
            if voice_attempts > 0:
                voice_rate = (
                    self.command_stats["voice_id_successes"] / voice_attempts
                ) * 100
                await self.speech_handler.speak(
                    f"Voice identification success rate: {voice_rate:.1f}%"
                )

    def cleanup(self):
        """Cleanup all speech resources"""
        super().cleanup()

        # Additional cleanup for advanced systems
        if self.voice_identifier:
            # Save voice profiles if needed
            pass


# Example usage
async def run_master_speech_game():
    """Run a complete master speech-controlled game"""

    controller = MasterSpeechController()

    player_names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace"]
    success = await controller.setup_game(player_names)

    if success:
        try:
            result = await controller.run_game()
            print(f"\n🎮 Master speech game completed: {result}")
        except KeyboardInterrupt:
            print("\n🛑 Game interrupted")
        finally:
            controller.cleanup()
    else:
        print("❌ Failed to setup master speech game")


if __name__ == "__main__":
    asyncio.run(run_master_speech_game())
