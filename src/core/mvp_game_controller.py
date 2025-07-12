"""
MVP Game Controller for Blood on the Clocktower
Orchestrates the complete game flow from setup to completion
"""

import asyncio
from typing import List, Optional, Tuple

from .game_engine import GameEngine
from .game_state import GamePhase, GameState, Player
from .mvp_character_abilities import AbilityDispatcher, AbilityResult
from .player_choice_system import (
    MockPlayerChoices,
    MVPChoiceTemplates,
    SimpleCommandLineChoices,
)
from .voting_system import SimpleMajorityVoting, VoteType


class MVPGameController:
    """Controls the complete flow of an MVP Blood on the Clocktower game"""

    def __init__(self, use_mock_choices: bool = False):
        self.engine = GameEngine()
        self.ability_dispatcher: Optional[AbilityDispatcher] = None
        self.voting_system: Optional[SimpleMajorityVoting] = None
        self.choice_system = (
            MockPlayerChoices() if use_mock_choices else SimpleCommandLineChoices()
        )

        # Game state
        self.is_running = False
        self.ability_results: List[AbilityResult] = []

    async def setup_game(self, player_names: List[str]) -> bool:
        """Setup a new game"""

        print("=== Setting up Blood on the Clocktower MVP ===")

        try:
            # Create game with character distribution
            game_state = self.engine.create_game(player_names)

            # Initialize systems
            self.ability_dispatcher = AbilityDispatcher(game_state)
            self.voting_system = SimpleMajorityVoting(game_state.players)

            # Display setup
            await self._announce_game_setup(game_state)

            return True

        except Exception as e:
            print(f"Failed to setup game: {e}")
            return False

    async def run_game(self) -> Optional[Tuple[str, str]]:
        """Run the complete game from start to finish"""

        if not self.engine.game_state:
            print("Game not setup!")
            return None

        self.is_running = True
        print("\n🎭 Starting Blood on the Clocktower!")

        # Start the game
        self.engine.start_game()

        try:
            # First night
            await self._run_first_night()

            # Game loop: Day -> Night -> Check win condition
            while self.is_running:
                # Day phase
                await self._run_day_phase()

                # Check win condition
                win_result = self.engine.check_win_condition()
                if win_result:
                    await self._announce_victory(win_result)
                    return win_result

                # Night phase (if game continues)
                await self._run_night_phase()

                # Check win condition after night
                win_result = self.engine.check_win_condition()
                if win_result:
                    await self._announce_victory(win_result)
                    return win_result

        except KeyboardInterrupt:
            print("\n🛑 Game interrupted by user")
            self.is_running = False

        except Exception as e:
            print(f"🚨 Game error: {e}")
            self.is_running = False

        return None

    async def _announce_game_setup(self, game_state: GameState):
        """Announce game setup to players"""

        print(f"\n📋 Game Setup Complete!")
        print(f"Players: {len(game_state.players)}")
        print(f"Script: {game_state.script_name.title()}")

        print("\n👥 Player Assignments:")
        for player in game_state.players:
            print(f"  {player.name}: {player.character}")

        if hasattr(game_state, "demon_bluffs"):
            print(f"\n🎭 Demon bluffs: {', '.join(game_state.demon_bluffs)}")

        # Brief pause for dramatic effect
        await asyncio.sleep(2)

    async def _run_first_night(self):
        """Run the first night phase"""

        print("\n🌙 THE FIRST NIGHT BEGINS")
        print("Everyone, close your eyes...")

        self.engine.game_state.phase = GamePhase.FIRST_NIGHT

        # Get night order
        night_order = self.engine.get_night_order(is_first_night=True)

        for character in night_order:
            await self._wake_character(character, is_first_night=True)

        print("🌅 Dawn breaks. Everyone wake up!")
        self.engine.advance_to_day()

    async def _run_night_phase(self):
        """Run a regular night phase"""

        print(f"\n🌙 NIGHT {self.engine.game_state.day_number}")
        print("Everyone, close your eyes...")

        self.engine.advance_to_night()

        # Get night order
        night_order = self.engine.get_night_order(is_first_night=False)

        for character in night_order:
            await self._wake_character(character, is_first_night=False)

        # Apply effects (poison wears off, etc.)
        await self._apply_night_effects()

        print("🌅 Dawn breaks. Time to see what happened...")
        self.engine.advance_to_day()

        # Announce deaths
        await self._announce_deaths()

    async def _wake_character(self, character: str, is_first_night: bool):
        """Wake a specific character for their night action"""

        # Find players with this character who are alive
        players_with_char = [
            p
            for p in self.engine.game_state.players
            if p.character == character and p.is_alive()
        ]

        if not players_with_char:
            return

        player = players_with_char[0]  # Should only be one

        print(f"\n{character}, wake up.")

        # Handle character-specific actions
        await self._handle_character_action(player, is_first_night)

        print(f"{character}, close your eyes.")
        await asyncio.sleep(1)  # Brief pause

    async def _handle_character_action(self, player: Player, is_first_night: bool):
        """Handle a specific character's night action"""

        character = player.character

        if character == "Fortune Teller":
            await self._handle_fortune_teller(player)
        elif character == "Empath":
            await self._handle_empath(player)
        elif character == "Washerwoman" and is_first_night:
            await self._handle_washerwoman(player)
        elif character == "Chef" and is_first_night:
            await self._handle_chef(player)
        elif character == "Poisoner":
            await self._handle_poisoner(player)
        elif character == "Imp":
            await self._handle_imp(player)
        else:
            print(f"  {character} has no action tonight.")

    async def _handle_fortune_teller(self, player: Player):
        """Handle Fortune Teller action"""

        # Get valid targets (everyone except self)
        valid_targets = [
            p.name for p in self.engine.get_alive_players() if p.name != player.name
        ]

        if len(valid_targets) < 2:
            print("  Not enough players to choose from.")
            return

        # Request choice
        choice_request = MVPChoiceTemplates.fortune_teller_choice(player, valid_targets)
        choice_result = await self.choice_system.request_choice_async(choice_request)

        if choice_result.is_valid:
            # Execute ability
            ability_result = self.ability_dispatcher.execute_ability(
                "Fortune Teller",
                player,
                target1=choice_result.targets[0],
                target2=choice_result.targets[1],
            )

            self.ability_results.append(ability_result)
            print(f"  {ability_result.information}")
        else:
            print(f"  Invalid choice: {choice_result.error_message}")

    async def _handle_empath(self, player: Player):
        """Handle Empath action"""

        choice_request = MVPChoiceTemplates.empath_choice(player)
        await self.choice_system.request_choice_async(choice_request)

        # Execute ability
        ability_result = self.ability_dispatcher.execute_ability("Empath", player)
        self.ability_results.append(ability_result)
        print(f"  {ability_result.information}")

    async def _handle_washerwoman(self, player: Player):
        """Handle Washerwoman first night action"""

        ability_result = self.ability_dispatcher.execute_ability("Washerwoman", player)
        self.ability_results.append(ability_result)
        print(f"  {ability_result.information}")

    async def _handle_chef(self, player: Player):
        """Handle Chef first night action"""

        ability_result = self.ability_dispatcher.execute_ability("Chef", player)
        self.ability_results.append(ability_result)
        print(f"  {ability_result.information}")

    async def _handle_poisoner(self, player: Player):
        """Handle Poisoner action"""

        # Get valid targets (anyone)
        valid_targets = [p.name for p in self.engine.get_alive_players()]

        choice_request = MVPChoiceTemplates.poisoner_choice(player, valid_targets)
        choice_result = await self.choice_system.request_choice_async(choice_request)

        if choice_result.is_valid:
            ability_result = self.ability_dispatcher.execute_ability(
                "Poisoner", player, target=choice_result.targets[0]
            )
            self.ability_results.append(ability_result)
            print(f"  You poison {choice_result.targets[0]}")
        else:
            print(f"  Invalid choice: {choice_result.error_message}")

    async def _handle_imp(self, player: Player):
        """Handle Imp action"""

        # Get valid targets (anyone including self for starpass)
        valid_targets = [p.name for p in self.engine.get_alive_players()]

        choice_request = MVPChoiceTemplates.imp_choice(player, valid_targets)
        choice_result = await self.choice_system.request_choice_async(choice_request)

        if choice_result.is_valid:
            ability_result = self.ability_dispatcher.execute_ability(
                "Imp", player, target=choice_result.targets[0]
            )
            self.ability_results.append(ability_result)
            # Don't announce kills until dawn
        else:
            print(f"  Invalid choice: {choice_result.error_message}")

    async def _apply_night_effects(self):
        """Apply end-of-night effects"""

        # Clear poison from previous day
        for player in self.engine.game_state.players:
            player.is_poisoned = False

        # Apply new poison from tonight's Poisoner
        for result in self.ability_results:
            if result.character == "Poisoner" and result.is_successful:
                target_player = self.engine.get_player_by_name(result.targets[0])
                if target_player:
                    target_player.is_poisoned = True

    async def _announce_deaths(self):
        """Announce who died in the night"""

        # Find players who died tonight
        deaths = []
        for result in self.ability_results:
            if result.character == "Imp" and result.is_successful:
                target_name = result.targets[0]
                target_player = self.engine.get_player_by_name(target_name)
                if target_player and not target_player.is_alive():
                    deaths.append(target_name)

        if deaths:
            print(f"💀 The following players died in the night: {', '.join(deaths)}")
        else:
            print("✨ Nobody died last night!")

        # Clear ability results for next night
        self.ability_results.clear()

    async def _run_day_phase(self):
        """Run the day phase with discussion and voting"""

        print(f"\n☀️ DAY {self.engine.game_state.day_number}")
        print("The town may now discuss and vote for execution.")

        alive_players = self.engine.get_alive_players()

        if len(alive_players) < 3:
            print("Not enough players alive for nominations.")
            return

        # Simple nomination process for MVP
        executed_player = await self._handle_nominations_and_voting()

        if executed_player:
            self.engine.execute_player(executed_player)
            print(f"⚰️ {executed_player} has been executed!")
        else:
            print("🤝 No execution today.")

    async def _handle_nominations_and_voting(self) -> Optional[str]:
        """Handle nominations and voting (simplified for MVP)"""

        print("\n--- Nomination Phase ---")
        print("For MVP: automatically nominating a random player")

        # MVP: Simple random nomination for testing
        alive_players = self.engine.get_alive_players()
        if len(alive_players) < 2:
            return None

        # Random nomination for MVP testing
        import random

        nominee = random.choice(alive_players)

        print(f"🎯 {nominee.name} has been nominated for execution!")

        # Start voting
        self.voting_system.start_vote(nominee.name)

        print("\n--- Voting Phase ---")
        print("Players are voting...")

        # MVP: Mock voting for testing
        for player in alive_players:
            vote = VoteType.YES if random.random() > 0.5 else VoteType.NO
            self.voting_system.cast_vote(player.name, vote)

        execute, yes_votes, no_votes = self.voting_system.get_result()

        print(f"Vote result: {yes_votes} yes, {no_votes} no")
        print(f"Threshold: {(len(alive_players) + 1) // 2}")

        self.voting_system.clear_vote()

        return nominee.name if execute else None

    async def _announce_victory(self, win_result: Tuple[str, str]):
        """Announce game victory"""

        winning_team, reason = win_result

        print(f"\n🏆 GAME OVER!")
        print(f"🎉 {winning_team.upper()} TEAM WINS!")
        print(f"📜 {reason}")

        # Show final character reveals
        print(f"\n📋 Final Character Reveals:")
        for player in self.engine.game_state.players:
            status = "ALIVE" if player.is_alive() else "DEAD"
            print(f"  {player.name}: {player.character} ({status})")

        self.is_running = False


# Example usage
async def run_mvp_game():
    """Run a complete MVP game"""

    controller = MVPGameController(use_mock_choices=True)  # Use mock for testing

    # Setup game
    player_names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace"]
    success = await controller.setup_game(player_names)

    if success:
        # Run game
        result = await controller.run_game()
        print(f"\nGame completed: {result}")
    else:
        print("Failed to setup game")


if __name__ == "__main__":
    # Run the MVP game
    asyncio.run(run_mvp_game())
