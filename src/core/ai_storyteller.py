"""
Blood on the Clocktower AI Storyteller - Core Implementation
Central AI system that manages game flow, narration, and rule enforcement
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

class GamePhase(Enum):
    SETUP = "setup"
    FIRST_NIGHT = "first_night"
    DAY = "day"
    NIGHT = "night"
    GAME_OVER = "game_over"

class PlayerStatus(Enum):
    ALIVE = "alive"
    DEAD = "dead"
    TRAVELER = "traveler"

@dataclass
class Player:
    id: str
    name: str
    seat_position: int
    character: Optional[str] = None
    status: PlayerStatus = PlayerStatus.ALIVE
    is_drunk: bool = False
    is_poisoned: bool = False
    ghost_vote_used: bool = False
    reminder_tokens: List[str] = None
    
    def __post_init__(self):
        if self.reminder_tokens is None:
            self.reminder_tokens = []

@dataclass
class GameState:
    players: List[Player]
    phase: GamePhase = GamePhase.SETUP
    day_number: int = 0
    current_night_order: List[str] = None
    nominations: List[Dict] = None
    executions_today: int = 0
    demon_bluffs: List[str] = None
    script_name: str = "trouble_brewing"
    
    def __post_init__(self):
        if self.current_night_order is None:
            self.current_night_order = []
        if self.nominations is None:
            self.nominations = []
        if self.demon_bluffs is None:
            self.demon_bluffs = []

class AIStoryteller:
    """Main AI Storyteller class that orchestrates the game"""
    
    def __init__(self, llm_client, speech_handler, character_data):
        self.llm_client = llm_client
        self.speech_handler = speech_handler
        self.character_data = character_data
        self.game_state = None
        self.logger = logging.getLogger(__name__)
        
        # Core AI systems
        self.rule_enforcer = RuleEnforcer(character_data)
        self.narrator = NarrativeAI(llm_client)
        self.game_balancer = GameBalancer()
        
    async def start_new_game(self, player_names: List[str]) -> None:
        """Initialize a new game with given players"""
        self.logger.info(f"Starting new game with {len(player_names)} players")
        
        # Initialize players
        players = [
            Player(id=f"player_{i}", name=name, seat_position=i)
            for i, name in enumerate(player_names)
        ]
        
        self.game_state = GameState(players=players)
        
        # Setup phase
        await self._setup_game()
        await self._distribute_characters()
        await self._begin_first_night()
    
    async def _setup_game(self) -> None:
        """Handle pre-game setup according to rules.md section 1"""
        self.game_state.phase = GamePhase.SETUP
        
        # Generate opening narrative
        intro_text = await self.narrator.generate_opening_story(
            len(self.game_state.players),
            self.game_state.script_name
        )
        
        await self.speech_handler.speak(intro_text)
        await self.speech_handler.speak("Players, please take your seats in a circle.")
        
    async def _distribute_characters(self) -> None:
        """Distribute characters following official rules"""
        player_count = len(self.game_state.players)
        
        # Get character distribution for player count
        characters = self.character_data.get_distribution(player_count, self.game_state.script_name)
        
        # Assign characters
        for player, character in zip(self.game_state.players, characters):
            player.character = character
            
        # Generate demon bluffs
        self.game_state.demon_bluffs = self.character_data.get_demon_bluffs(
            characters, self.game_state.script_name
        )
        
        await self.speech_handler.speak("Characters have been distributed. Check your tokens quietly.")
        
    async def _begin_first_night(self) -> None:
        """Execute first night according to rules.md section 1"""
        self.game_state.phase = GamePhase.FIRST_NIGHT
        
        await self.speech_handler.speak("Night falls on the town. Everyone close your eyes.")
        
        # First night order from rules.md
        await self._wake_minions()
        await self._wake_demon()
        await self._process_first_night_abilities()
        
        await self._transition_to_day()
        
    async def _wake_minions(self) -> None:
        """Wake minions and show them the demon"""
        minions = [p for p in self.game_state.players if self.character_data.is_minion(p.character)]
        demon = next(p for p in self.game_state.players if self.character_data.is_demon(p.character))
        
        if minions:
            minion_names = [p.name for p in minions]
            await self.speech_handler.speak(f"Minions: {', '.join(minion_names)}, wake up.")
            await asyncio.sleep(2)
            await self.speech_handler.speak(f"This is your demon: {demon.name}")
            await asyncio.sleep(3)
            await self.speech_handler.speak("Minions, go back to sleep.")
            
    async def _wake_demon(self) -> None:
        """Wake demon and show minions + bluffs"""
        demon = next(p for p in self.game_state.players if self.character_data.is_demon(p.character))
        minions = [p for p in self.game_state.players if self.character_data.is_minion(p.character)]
        
        await self.speech_handler.speak(f"{demon.name}, wake up.")
        await asyncio.sleep(2)
        
        if minions:
            minion_names = [p.name for p in minions]
            await self.speech_handler.speak(f"These are your minions: {', '.join(minion_names)}")
            
        bluff_text = f"Your bluff characters are: {', '.join(self.game_state.demon_bluffs)}"
        await self.speech_handler.speak(bluff_text)
        await asyncio.sleep(5)
        await self.speech_handler.speak(f"{demon.name}, go back to sleep.")
        
    async def _process_first_night_abilities(self) -> None:
        """Process first night abilities in order"""
        night_order = self.character_data.get_first_night_order()
        
        for character_name in night_order:
            players_with_character = [p for p in self.game_state.players if p.character == character_name]
            
            for player in players_with_character:
                if not player.is_drunk and not player.is_poisoned:
                    await self._execute_night_ability(player, character_name, is_first_night=True)
                    
    async def _execute_night_ability(self, player: Player, character: str, is_first_night: bool = False) -> None:
        """Execute a character's night ability"""
        ability_handler = self.character_data.get_ability_handler(character)
        
        if ability_handler.has_night_ability(is_first_night):
            await self.speech_handler.speak(f"{player.name}, wake up.")
            
            # Get ability result using AI decision making
            ability_result = await ability_handler.execute(
                player, self.game_state, self.llm_client, self.game_balancer
            )
            
            # Process result and give information
            if ability_result.requires_information:
                await self._give_information(player, ability_result)
                
            await self.speech_handler.speak(f"{player.name}, go back to sleep.")
            
    async def _give_information(self, player: Player, ability_result) -> None:
        """Give information to player based on ability result"""
        info_text = ability_result.information_text
        
        # Apply drunk/poisoned modifications
        if player.is_drunk or player.is_poisoned:
            info_text = await self.game_balancer.modify_information_for_drunk_poisoned(
                info_text, player, self.game_state
            )
            
        await self.speech_handler.speak_to_player(player.name, info_text)
        
    async def _transition_to_day(self) -> None:
        """Transition from night to day phase"""
        self.game_state.phase = GamePhase.DAY
        self.game_state.day_number += 1
        
        # Announce deaths
        deaths = self._calculate_deaths()
        if deaths:
            death_text = await self.narrator.generate_death_announcement(deaths, self.game_state.day_number)
            await self.speech_handler.speak(death_text)
        else:
            await self.speech_handler.speak("Dawn breaks. No one died in the night.")
            
        # Check win conditions
        if await self._check_win_conditions():
            return
            
        # Begin day discussion
        await self._begin_day_phase()
        
    async def _begin_day_phase(self) -> None:
        """Begin day phase discussion and nominations"""
        await self.speech_handler.speak("The town wakes. You may now discuss freely.")
        
        # Allow discussion time
        await asyncio.sleep(300)  # 5 minutes base discussion
        
        await self.speech_handler.speak("Nominations are now open. Who would you like to nominate?")
        
        # Handle nominations through speech recognition
        await self._handle_nominations()
        
    async def _handle_nominations(self) -> None:
        """Process nominations and voting"""
        while True:
            # Listen for nomination commands
            command = await self.speech_handler.listen_for_command([
                "nominate", "I nominate", "close nominations", "end day"
            ])
            
            if "close" in command or "end" in command:
                break
                
            # Process nomination
            nomination = await self._process_nomination(command)
            if nomination:
                await self._conduct_vote(nomination)
                
        await self._transition_to_night()
        
    async def _process_nomination(self, command: str) -> Optional[Dict]:
        """Process a nomination command"""
        # Extract nominator and nominee from speech
        nomination_data = await self.speech_handler.parse_nomination(command)
        
        if self.rule_enforcer.validate_nomination(nomination_data, self.game_state):
            self.game_state.nominations.append(nomination_data)
            
            nominator = nomination_data['nominator']
            nominee = nomination_data['nominee']
            
            await self.speech_handler.speak(f"{nominator} nominates {nominee}.")
            return nomination_data
            
        return None
        
    async def _conduct_vote(self, nomination: Dict) -> None:
        """Conduct voting on a nomination"""
        nominee = nomination['nominee']
        
        await self.speech_handler.speak(f"Voting on {nominee}. Raise your hand to vote.")
        
        # Collect votes through speech/gesture recognition
        votes = await self.speech_handler.collect_votes(self.game_state.players)
        
        vote_count = len(votes)
        required_votes = len([p for p in self.game_state.players if p.status == PlayerStatus.ALIVE]) // 2 + 1
        
        await self.speech_handler.speak(f"{vote_count} votes. {required_votes} required.")
        
        if vote_count >= required_votes:
            await self._execute_player(nominee)
            
    async def _execute_player(self, player_name: str) -> None:
        """Execute a player and check win conditions"""
        player = next(p for p in self.game_state.players if p.name == player_name)
        player.status = PlayerStatus.DEAD
        
        execution_text = await self.narrator.generate_execution_story(player, self.game_state)
        await self.speech_handler.speak(execution_text)
        
        # Check for immediate win conditions
        await self._check_win_conditions()
        
    async def _check_win_conditions(self) -> bool:
        """Check if game should end based on win conditions from rules.md"""
        # Good wins if demon is dead
        demon = next(p for p in self.game_state.players if self.character_data.is_demon(p.character))
        if demon.status == PlayerStatus.DEAD:
            await self._end_game("good", "The demon has been slain!")
            return True
            
        # Evil wins if only 2 players remain
        alive_players = [p for p in self.game_state.players if p.status == PlayerStatus.ALIVE]
        if len(alive_players) <= 2:
            await self._end_game("evil", "Evil overwhelms the town!")
            return True
            
        return False
        
    async def _end_game(self, winner: str, reason: str) -> None:
        """End the game with winner announcement"""
        self.game_state.phase = GamePhase.GAME_OVER
        
        ending_story = await self.narrator.generate_ending_story(winner, reason, self.game_state)
        await self.speech_handler.speak(ending_story)
        
    def _calculate_deaths(self) -> List[Player]:
        """Calculate which players died during the night"""
        # This will be implemented based on demon abilities and protective roles
        # For now, return empty list
        return []
        
    async def handle_player_question(self, question: str) -> str:
        """Handle player questions about rules or game state"""
        return await self.narrator.answer_player_question(question, self.game_state)


class RuleEnforcer:
    """Validates actions against game rules"""
    
    def __init__(self, character_data):
        self.character_data = character_data
        
    def validate_nomination(self, nomination: Dict, game_state: GameState) -> bool:
        """Validate nomination according to rules.md section 3"""
        nominator = nomination['nominator']
        nominee = nomination['nominee']
        
        # Check if nominator is alive
        nominator_player = next((p for p in game_state.players if p.name == nominator), None)
        if not nominator_player or nominator_player.status != PlayerStatus.ALIVE:
            return False
            
        # Check if nominee exists and hasn't been nominated today
        nominee_player = next((p for p in game_state.players if p.name == nominee), None)
        if not nominee_player:
            return False
            
        # Check if nominee already nominated today
        today_nominees = [n['nominee'] for n in game_state.nominations]
        if nominee in today_nominees:
            return False
            
        return True


class NarrativeAI:
    """Generates engaging narratives and stories"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        
    async def generate_opening_story(self, player_count: int, script: str) -> str:
        """Generate opening story for the game"""
        prompt = f"""
        Generate an atmospheric opening for a Blood on the Clocktower game with {player_count} players 
        using the {script} script. Make it dramatic and immersive, setting the scene of a town 
        plagued by evil. Keep it to 2-3 sentences.
        """
        
        response = await self.llm_client.generate(prompt)
        return response.strip()
        
    async def generate_death_announcement(self, deaths: List[Player], day: int) -> str:
        """Generate dramatic death announcements"""
        if not deaths:
            return "The town awakens to find everyone alive and well."
            
        death_names = [p.name for p in deaths]
        prompt = f"""
        Generate a dramatic announcement for day {day} where these players died: {', '.join(death_names)}.
        Make it atmospheric and mysterious. Don't reveal how they died. 2-3 sentences.
        """
        
        response = await self.llm_client.generate(prompt)
        return response.strip()
        
    async def generate_execution_story(self, player: Player, game_state: GameState) -> str:
        """Generate execution story"""
        prompt = f"""
        Generate a dramatic execution scene for {player.name} in a Blood on the Clocktower game.
        Make it atmospheric but not gruesome. Focus on the town's determination to find evil. 
        2-3 sentences.
        """
        
        response = await self.llm_client.generate(prompt)
        return response.strip()
        
    async def generate_ending_story(self, winner: str, reason: str, game_state: GameState) -> str:
        """Generate game ending story"""
        prompt = f"""
        Generate an epic ending for a Blood on the Clocktower game where {winner} team wins.
        Reason: {reason}
        Make it dramatic and satisfying. 3-4 sentences celebrating the victory.
        """
        
        response = await self.llm_client.generate(prompt)
        return response.strip()
        
    async def answer_player_question(self, question: str, game_state: GameState) -> str:
        """Answer player questions about rules or game state"""
        prompt = f"""
        Answer this Blood on the Clocktower question as a knowledgeable storyteller:
        Question: {question}
        
        Current game phase: {game_state.phase.value}
        Day: {game_state.day_number}
        
        Be helpful but don't reveal secret information. Keep response concise.
        """
        
        response = await self.llm_client.generate(prompt)
        return response.strip()


class GameBalancer:
    """Manages game balance and information distribution"""
    
    def __init__(self):
        pass
        
    async def modify_information_for_drunk_poisoned(self, info: str, player: Player, game_state: GameState) -> str:
        """Modify information for drunk/poisoned players per rules.md section 4"""
        # This is where AI can make strategic decisions about false information
        # Generally give misleading info but occasionally correct for balance
        return info  # Placeholder - implement sophisticated false info logic
        
    def should_help_team(self, team: str, game_state: GameState) -> bool:
        """Determine if a team needs subtle help for balance"""
        # Analyze game state and determine if storyteller should subtly help weaker team
        return False  # Placeholder