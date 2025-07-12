"""
Enhanced Speech Interface for Night Phase Character Abilities
Provides sophisticated voice interaction for character abilities during night phases
"""

import asyncio
import logging
from typing import List, Optional, Tuple

from ..speech.speech_handler import SpeechHandler
from .game_state import GamePhase, Player
from .mvp_character_abilities import AbilityDispatcher
from .player_choice_system import MVPChoiceTemplates
from .speech_integrated_controller import SpeechIntegratedController


class EnhancedNightSpeechInterface:
    """Enhanced speech interface for night phase interactions"""

    def __init__(
        self, speech_handler: SpeechHandler, ability_dispatcher: AbilityDispatcher
    ):
        self.speech_handler = speech_handler
        self.ability_dispatcher = ability_dispatcher
        self.logger = logging.getLogger(__name__)

        # Night phase state
        self.current_character = None
        self.current_player = None
        self.wake_phrases = {
            "Fortune Teller": [
                "Fortune Teller, wake up.",
                "You may choose two players to learn about.",
                "Point to your first choice... now your second choice.",
            ],
            "Empath": [
                "Empath, wake up.",
                "You learn how many evil neighbors you have.",
            ],
            "Washerwoman": [
                "Washerwoman, wake up.",
                "You learn information about townsfolk in play.",
            ],
            "Chef": ["Chef, wake up.", "You learn about evil player pairs."],
            "Poisoner": [
                "Poisoner, wake up.",
                "Choose a player to poison tonight and tomorrow.",
            ],
            "Imp": [
                "Imp, wake up.",
                "Choose a player to kill, or choose yourself to pass the demon token.",
            ],
        }

    async def handle_enhanced_night_phase(
        self, game_controller: SpeechIntegratedController
    ):
        """Handle night phase with enhanced speech interactions"""

        await self.speech_handler.speak("🌙 Night falls upon the town...")
        await asyncio.sleep(2)
        await self.speech_handler.speak("Everyone, close your eyes and sleep soundly.")
        await asyncio.sleep(3)

        # Get night order
        is_first_night = (
            game_controller.engine.game_state.phase == GamePhase.FIRST_NIGHT
        )
        night_order = game_controller.engine.get_night_order(is_first_night)

        self.logger.info(f"Night order: {night_order}")

        for character in night_order:
            await self._wake_character_enhanced(
                character, game_controller, is_first_night
            )

        await self.speech_handler.speak("🌅 Dawn breaks. Everyone may open their eyes.")

    async def _wake_character_enhanced(
        self,
        character: str,
        game_controller: SpeechIntegratedController,
        is_first_night: bool,
    ):
        """Wake character with enhanced speech interaction"""

        # Find players with this character
        players_with_char = [
            p
            for p in game_controller.engine.game_state.players
            if p.character == character and p.is_alive()
        ]

        if not players_with_char:
            return

        player = players_with_char[0]
        self.current_character = character
        self.current_player = player

        # Enhanced wake sequence
        await self._deliver_wake_sequence(character, player)

        # Handle character-specific action
        await self._handle_enhanced_character_action(
            player, game_controller, is_first_night
        )

        # Enhanced sleep sequence
        await self._deliver_sleep_sequence(character, player)

    async def _deliver_wake_sequence(self, character: str, player: Player):
        """Deliver enhanced wake sequence with dramatic timing"""

        if character in self.wake_phrases:
            phrases = self.wake_phrases[character]

            for i, phrase in enumerate(phrases):
                if i == 0:  # First phrase (wake up)
                    await self.speech_handler.speak(phrase)
                    await asyncio.sleep(2)  # Give time to wake
                else:
                    await self.speech_handler.speak_to_player(player.name, phrase)
                    await asyncio.sleep(1.5)
        else:
            await self.speech_handler.speak(f"{character}, wake up.")
            await asyncio.sleep(2)

    async def _deliver_sleep_sequence(self, character: str, player: Player):
        """Deliver enhanced sleep sequence"""

        await asyncio.sleep(1)
        await self.speech_handler.speak(f"{character}, close your eyes.")
        await asyncio.sleep(1)

    async def _handle_enhanced_character_action(
        self,
        player: Player,
        game_controller: SpeechIntegratedController,
        is_first_night: bool,
    ):
        """Handle character action with enhanced speech prompts"""

        character = player.character

        if character == "Fortune Teller":
            await self._handle_enhanced_fortune_teller(player, game_controller)
        elif character == "Empath":
            await self._handle_enhanced_empath(player, game_controller)
        elif character == "Washerwoman" and is_first_night:
            await self._handle_enhanced_washerwoman(player, game_controller)
        elif character == "Chef" and is_first_night:
            await self._handle_enhanced_chef(player, game_controller)
        elif character == "Poisoner":
            await self._handle_enhanced_poisoner(player, game_controller)
        elif character == "Imp":
            await self._handle_enhanced_imp(player, game_controller)
        else:
            await self.speech_handler.speak_to_player(
                player.name, "You have no action tonight."
            )
            await asyncio.sleep(2)

    async def _handle_enhanced_fortune_teller(
        self, player: Player, game_controller: SpeechIntegratedController
    ):
        """Enhanced Fortune Teller interaction"""

        valid_targets = [
            p.name
            for p in game_controller.engine.get_alive_players()
            if p.name != player.name
        ]

        if len(valid_targets) < 2:
            await self.speech_handler.speak_to_player(
                player.name, "Not enough players to choose from."
            )
            return

        # Enhanced prompting
        await self.speech_handler.speak_to_player(
            player.name, "Choose two players. You will learn if either is the demon."
        )

        await asyncio.sleep(1)

        player_list = ", ".join(valid_targets[:-1]) + f", or {valid_targets[-1]}"
        await self.speech_handler.speak_to_player(
            player.name, f"Your choices are: {player_list}. Say both names clearly."
        )

        # Get choice using speech
        choice_request = MVPChoiceTemplates.fortune_teller_choice(player, valid_targets)
        choice_result = await game_controller.speech_choices.request_choice_async(
            choice_request
        )

        if choice_result.is_valid:
            # Execute ability
            ability_result = game_controller.ability_dispatcher.execute_ability(
                "Fortune Teller",
                player,
                target1=choice_result.targets[0],
                target2=choice_result.targets[1],
            )

            # Enhanced information delivery
            await asyncio.sleep(1)
            await self.speech_handler.speak_to_player(
                player.name,
                f"You peer into their souls and learn: {ability_result.information.split(': ')[1]}",
            )

            game_controller.ability_results.append(ability_result)
        else:
            await self.speech_handler.speak_to_player(
                player.name, "You struggle to focus and learn nothing tonight."
            )

    async def _handle_enhanced_empath(
        self, player: Player, game_controller: SpeechIntegratedController
    ):
        """Enhanced Empath interaction"""

        await self.speech_handler.speak_to_player(
            player.name, "You sense the evil in your immediate neighbors."
        )

        await asyncio.sleep(2)

        # Execute ability
        ability_result = game_controller.ability_dispatcher.execute_ability(
            "Empath", player
        )

        # Enhanced information delivery
        count = ability_result.information.split(": ")[1]
        if count == "0":
            message = "You feel surrounded by goodness. You sense no evil neighbors."
        elif count == "1":
            message = "You sense a dark presence. One of your neighbors harbors evil."
        else:
            message = f"The evil is strong. You sense {count} evil neighbors."

        await self.speech_handler.speak_to_player(player.name, message)
        game_controller.ability_results.append(ability_result)

    async def _handle_enhanced_washerwoman(
        self, player: Player, game_controller: SpeechIntegratedController
    ):
        """Enhanced Washerwoman interaction"""

        await self.speech_handler.speak_to_player(
            player.name, "You investigate the town's residents..."
        )

        await asyncio.sleep(2)

        ability_result = game_controller.ability_dispatcher.execute_ability(
            "Washerwoman", player
        )

        # Enhanced information delivery
        info_parts = ability_result.information.split(": ")[1]
        await self.speech_handler.speak_to_player(
            player.name, f"You discover: {info_parts}"
        )

        game_controller.ability_results.append(ability_result)

    async def _handle_enhanced_chef(
        self, player: Player, game_controller: SpeechIntegratedController
    ):
        """Enhanced Chef interaction"""

        await self.speech_handler.speak_to_player(
            player.name, "You observe who sits together at meals..."
        )

        await asyncio.sleep(2)

        ability_result = game_controller.ability_dispatcher.execute_ability(
            "Chef", player
        )

        # Enhanced information delivery
        count = ability_result.information.split(": ")[1]
        if count == "0":
            message = "You notice no evil pairs sitting together."
        elif count == "1":
            message = "You spot one pair of evil players sitting next to each other."
        else:
            message = f"You observe {count} pairs of evil players sitting together."

        await self.speech_handler.speak_to_player(player.name, message)
        game_controller.ability_results.append(ability_result)

    async def _handle_enhanced_poisoner(
        self, player: Player, game_controller: SpeechIntegratedController
    ):
        """Enhanced Poisoner interaction"""

        valid_targets = [p.name for p in game_controller.engine.get_alive_players()]

        await self.speech_handler.speak_to_player(
            player.name, "Choose someone to poison. Their abilities will malfunction."
        )

        await asyncio.sleep(1)

        choice_request = MVPChoiceTemplates.poisoner_choice(player, valid_targets)
        choice_result = await game_controller.speech_choices.request_choice_async(
            choice_request
        )

        if choice_result.is_valid:
            ability_result = game_controller.ability_dispatcher.execute_ability(
                "Poisoner", player, target=choice_result.targets[0]
            )

            await self.speech_handler.speak_to_player(
                player.name,
                f"You slip poison to {choice_result.targets[0]}. They will be poisoned until dusk.",
            )

            game_controller.ability_results.append(ability_result)
        else:
            await self.speech_handler.speak_to_player(
                player.name, "You cannot decide who to poison tonight."
            )

    async def _handle_enhanced_imp(
        self, player: Player, game_controller: SpeechIntegratedController
    ):
        """Enhanced Imp interaction"""

        valid_targets = [p.name for p in game_controller.engine.get_alive_players()]

        await self.speech_handler.speak_to_player(
            player.name,
            "Choose a victim for tonight, or target yourself to pass your demonic power.",
        )

        await asyncio.sleep(1)

        choice_request = MVPChoiceTemplates.imp_choice(player, valid_targets)
        choice_result = await game_controller.speech_choices.request_choice_async(
            choice_request
        )

        if choice_result.is_valid:
            target = choice_result.targets[0]
            ability_result = game_controller.ability_dispatcher.execute_ability(
                "Imp", player, target=target
            )

            if target == player.name:
                await self.speech_handler.speak_to_player(
                    player.name, "You sacrifice yourself, passing your evil to another."
                )
            else:
                await self.speech_handler.speak_to_player(
                    player.name,
                    f"You mark {target} for death. They will not see tomorrow's dawn.",
                )

            game_controller.ability_results.append(ability_result)
        else:
            await self.speech_handler.speak_to_player(
                player.name, "You decide not to kill anyone tonight."
            )


class VoiceControlledVoting:
    """Enhanced voice-controlled voting system"""

    def __init__(self, speech_handler: SpeechHandler):
        self.speech_handler = speech_handler
        self.logger = logging.getLogger(__name__)

    async def conduct_enhanced_vote(
        self, nominee: str, alive_players: List[Player]
    ) -> Tuple[bool, int, int]:
        """Conduct an enhanced voice-controlled vote"""

        await self.speech_handler.speak(
            f"🗳️ The town will now vote on the execution of {nominee}."
        )

        await asyncio.sleep(2)

        await self.speech_handler.speak(
            "When I call your name, clearly say 'yes' to vote for execution, "
            "or 'no' to vote against execution."
        )

        yes_votes = 0
        no_votes = 0

        # Individual voting for clarity
        for player in alive_players:
            await self._individual_vote(player, yes_votes, no_votes)

        threshold = (len(alive_players) + 1) // 2
        execute = yes_votes >= threshold

        await self._announce_vote_results(
            yes_votes, no_votes, threshold, execute, nominee
        )

        return execute, yes_votes, no_votes

    async def _individual_vote(
        self, player: Player, yes_count: int, no_count: int
    ) -> bool:
        """Get individual player vote"""

        await self.speech_handler.speak(f"{player.name}, how do you vote?")

        for attempt in range(3):
            command = await self.speech_handler.listen_for_command(
                keywords=["yes", "no", "aye"], timeout=10.0
            )

            if command:
                command_lower = command.lower()
                if "yes" in command_lower or "aye" in command_lower:
                    await self.speech_handler.speak(f"{player.name} votes yes.")
                    return True
                elif "no" in command_lower:
                    await self.speech_handler.speak(f"{player.name} votes no.")
                    return False
                else:
                    await self.speech_handler.speak("Please say yes or no clearly.")
            else:
                await self.speech_handler.speak(
                    f"{player.name}, please state your vote."
                )

        # Default to no vote if no clear response
        await self.speech_handler.speak(f"{player.name} abstains.")
        return False

    async def _announce_vote_results(
        self, yes_votes: int, no_votes: int, threshold: int, execute: bool, nominee: str
    ):
        """Announce voting results dramatically"""

        await asyncio.sleep(2)

        await self.speech_handler.speak(
            f"The votes have been counted. {yes_votes} yes, {no_votes} no."
        )

        await asyncio.sleep(1)

        await self.speech_handler.speak(
            f"The threshold for execution is {threshold} votes."
        )

        await asyncio.sleep(2)

        if execute:
            await self.speech_handler.speak(
                f"⚔️ By the will of the town, {nominee} will be executed!"
            )
        else:
            await self.speech_handler.speak(
                f"🛡️ {nominee} survives the vote and lives another day."
            )


# Enhanced speech-integrated controller that uses the new interfaces
class FullySpeechIntegratedController(SpeechIntegratedController):
    """Fully speech-integrated controller with enhanced night and voting interfaces"""

    def __init__(self, speech_config=None):
        super().__init__(speech_config)
        self.enhanced_night_interface = None
        self.voice_voting = None

    async def setup_game(self, player_names: List[str]) -> bool:
        """Setup with enhanced speech interfaces"""

        success = await super().setup_game(player_names)

        if success:
            # Initialize enhanced interfaces
            self.enhanced_night_interface = EnhancedNightSpeechInterface(
                self.speech_handler, self.ability_dispatcher
            )
            self.voice_voting = VoiceControlledVoting(self.speech_handler)

        return success

    async def _run_first_night(self):
        """Run first night with enhanced interface"""

        if self.enhanced_night_interface:
            await self.enhanced_night_interface.handle_enhanced_night_phase(self)
        else:
            await super()._run_first_night()

        self.engine.advance_to_day()

    async def _run_night_phase(self):
        """Run night phase with enhanced interface"""

        if self.enhanced_night_interface:
            await self.enhanced_night_interface.handle_enhanced_night_phase(self)
        else:
            await super()._run_night_phase()

        # Apply effects and announce deaths
        await self._apply_night_effects()
        await self._announce_deaths()
        self.engine.advance_to_day()

    async def _conduct_speech_vote(self, nominee: str) -> Optional[str]:
        """Use enhanced voting interface"""

        if self.voice_voting:
            alive_players = self.engine.get_alive_players()
            execute, yes_votes, no_votes = (
                await self.voice_voting.conduct_enhanced_vote(nominee, alive_players)
            )
            return nominee if execute else None
        else:
            return await super()._conduct_speech_vote(nominee)


if __name__ == "__main__":
    # Test the enhanced speech interfaces
    async def test_enhanced_speech():
        controller = FullySpeechIntegratedController()

        player_names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace"]
        success = await controller.setup_game(player_names)

        if success:
            try:
                result = await controller.run_game()
                print(f"Enhanced speech game completed: {result}")
            except KeyboardInterrupt:
                print("Game interrupted")
            finally:
                controller.cleanup()
        else:
            print("Failed to setup enhanced speech game")

    asyncio.run(test_enhanced_speech())
