"""
Complete Autonomous Storyteller Integration Example
Shows how all components work together for hands-off operation
"""

import asyncio
import logging
from typing import List

from .autonomous_storyteller import AutonomousStoryteller, GameContext, SpeechParser
from .character_handlers import CharacterAbilityHandler
from .local_deepseek_storyteller import LocalDeepSeekStoryteller
from ..core.game_state import GameState, Player, GamePhase, PlayerStatus
from ..speech.speech_handler import SpeechHandler, SpeechConfig


class FullyAutonomousGame:
    """Complete autonomous game management"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.speech_config = SpeechConfig(
            whisper_model="base",  # Good balance of speed/accuracy
            tts_voice="en_US-lessac-medium",
            vad_threshold=0.01
        )
        
        self.speech_handler = SpeechHandler(self.speech_config)
        self.autonomous_storyteller = AutonomousStoryteller(self.speech_handler)
        
        # Game state
        self.game_state = None
        
    async def start_game(self, player_names: List[str], script: str = "trouble_brewing"):
        """Start a fully autonomous game"""
        
        self.logger.info(f"Starting autonomous game with {len(player_names)} players")
        
        # Initialize storyteller
        await self.autonomous_storyteller.initialize()
        
        # Create game state
        self.game_state = self._create_game_state(player_names, script)
        
        # Start autonomous operation
        await self.autonomous_storyteller.start_autonomous_operation(self.game_state)
        
        # Initial game setup narration
        await self._narrate_game_start()
        
        self.logger.info("Autonomous game started - AI is now in control")
        
    def _create_game_state(self, player_names: List[str], script: str) -> GameState:
        """Create initial game state with character assignments"""
        
        # Create players
        players = []
        for i, name in enumerate(player_names):
            player = Player(
                id=f"player_{i}",
                name=name,
                seat_position=i,
                status=PlayerStatus.ALIVE
            )
            players.append(player)
            
        # Assign characters (this would be more sophisticated in real implementation)
        characters = self._get_character_distribution(len(player_names), script)
        
        for i, character in enumerate(characters):
            if i < len(players):
                players[i].character = character
                
        # Set some players as drunk/poisoned for testing
        if len(players) > 5:
            players[2].is_drunk = True  # Make someone drunk for testing
            
        game_state = GameState(
            players=players,
            phase=GamePhase.FIRST_NIGHT,
            day_number=1,
            script_name=script
        )
        
        return game_state
        
    def _get_character_distribution(self, player_count: int, script: str) -> List[str]:
        """Get character distribution for the game"""
        
        # Simplified character assignment for Trouble Brewing
        if script == "trouble_brewing":
            if player_count == 5:
                return ["Fortune Teller", "Empath", "Washerwoman", "Drunk", "Imp"]
            elif player_count == 6:
                return ["Fortune Teller", "Empath", "Washerwoman", "Chef", "Drunk", "Imp"]
            elif player_count == 7:
                return ["Fortune Teller", "Empath", "Washerwoman", "Chef", "Drunk", "Poisoner", "Imp"]
            elif player_count >= 8:
                return ["Fortune Teller", "Empath", "Washerwoman", "Chef", "Undertaker", 
                       "Drunk", "Butler", "Poisoner", "Imp"][:player_count]
                       
        # Default fallback
        return ["Fortune Teller", "Empath", "Washerwoman"] + ["Drunk"] * (player_count - 4) + ["Imp"]
        
    async def _narrate_game_start(self):
        """Narrate the game beginning"""
        
        # Create dramatic opening
        opening = await self.autonomous_storyteller.ai_storyteller.narrate("game_start", {
            "players": len(self.game_state.players),
            "script": self.game_state.script_name
        })
        
        await self.autonomous_storyteller._speak(opening)
        
        # Announce setup
        await asyncio.sleep(3)
        await self.autonomous_storyteller._speak(
            "I am your AI Storyteller. I will listen for your actions and guide the game. "
            "Speak clearly when making choices."
        )
        
    async def run_example_game_flow(self):
        """Run through an example game flow to demonstrate the system"""
        
        # Start with a test game
        test_players = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace"]
        await self.start_game(test_players)
        
        # Simulate some game events
        await self._simulate_first_night()
        await self._simulate_first_day()
        
    async def _simulate_first_night(self):
        """Simulate first night events for demonstration"""
        
        self.logger.info("Simulating first night...")
        
        # Night phase announcement
        await self.autonomous_storyteller._speak("The first night begins. Everyone close your eyes.")
        
        # Simulate character abilities
        await asyncio.sleep(2)
        
        # Fortune Teller
        ft_player = next(p for p in self.game_state.players if p.character == "Fortune Teller")
        await self.autonomous_storyteller._speak(f"{ft_player.name}, Fortune Teller, wake up.")
        await asyncio.sleep(1)
        await self.autonomous_storyteller._speak("Choose two players to learn about.")
        
        # Simulate Fortune Teller choice
        targets = ["Bob", "Charlie"]
        await self._simulate_fortune_teller_choice(ft_player, targets)
        
        # Empath
        empath_player = next(p for p in self.game_state.players if p.character == "Empath")
        await self.autonomous_storyteller._speak(f"{empath_player.name}, Empath, wake up.")
        
        # Handle Empath ability
        handler = CharacterAbilityHandler(
            self.autonomous_storyteller.ai_storyteller,
            self.autonomous_storyteller.game_context
        )
        
        empath_info = await handler.handle_empath(empath_player, self.game_state)
        await self.autonomous_storyteller._speak_privately(empath_player.name, empath_info)
        
        await self.autonomous_storyteller._speak("Empath, close your eyes.")
        
    async def _simulate_fortune_teller_choice(self, player: Player, targets: List[str]):
        """Simulate Fortune Teller making a choice"""
        
        # Use character handler
        handler = CharacterAbilityHandler(
            self.autonomous_storyteller.ai_storyteller,
            self.autonomous_storyteller.game_context
        )
        
        result = await handler.handle_fortune_teller(player, targets, self.game_state)
        await self.autonomous_storyteller._speak_privately(player.name, result)
        
        await self.autonomous_storyteller._speak("Fortune Teller, close your eyes.")
        
    async def _simulate_first_day(self):
        """Simulate first day for demonstration"""
        
        self.logger.info("Simulating first day...")
        
        # Day phase
        self.game_state.phase = GamePhase.DAY
        
        # Dawn announcement (no deaths on first night typically)
        dawn_announcement = await self.autonomous_storyteller.ai_storyteller.narrate(
            "death_announcement", {"deaths": []}
        )
        
        await self.autonomous_storyteller._speak(dawn_announcement)
        
        # Allow discussion
        await asyncio.sleep(3)
        await self.autonomous_storyteller._speak(
            "The town may now discuss and nominate for execution."
        )
        
    def get_game_summary(self) -> str:
        """Get a summary of the current game state"""
        
        if not self.game_state:
            return "No game in progress"
            
        summary = f"""
AUTONOMOUS GAME SUMMARY

Players: {len(self.game_state.players)}
Phase: {self.game_state.phase.value}
Day: {self.game_state.day_number}

PLAYERS:
"""
        
        for player in self.game_state.players:
            status = "ALIVE" if player.is_alive() else "DEAD"
            modifiers = []
            if player.is_drunk: modifiers.append("DRUNK")
            if player.is_poisoned: modifiers.append("POISONED")
            
            summary += f"  {player.name} ({player.character}): {status}"
            if modifiers:
                summary += f" [{', '.join(modifiers)}]"
            summary += "\n"
            
        # Add information history
        summary += "\nINFORMATION GIVEN:\n"
        for info in self.autonomous_storyteller.game_context.information_history:
            summary += f"  Night {info.night_number}: {info.player_name} learned: {info.information}\n"
            
        return summary
        

# Example usage
async def demo_autonomous_storyteller():
    """Demonstrate the autonomous storyteller system"""
    
    print("🎭 Blood on the Clocktower - Autonomous AI Storyteller Demo")
    print("=" * 60)
    
    # Create autonomous game
    game = FullyAutonomousGame()
    
    print("Initializing autonomous storyteller...")
    
    try:
        # Run example game flow
        await game.run_example_game_flow()
        
        # Let it run for a bit
        await asyncio.sleep(30)
        
        # Print game summary
        print("\nGame Summary:")
        print(game.get_game_summary())
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"Demo error: {e}")
    finally:
        game.autonomous_storyteller.stop_autonomous_operation()
        print("Autonomous storyteller stopped")


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the demo
    asyncio.run(demo_autonomous_storyteller())