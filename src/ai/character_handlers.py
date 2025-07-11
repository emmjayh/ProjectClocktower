"""
Character Ability Handlers for Autonomous Storyteller
Handles all character abilities and information decisions
"""

import random
from datetime import datetime
from typing import List, Dict, Any, Optional

from .autonomous_storyteller import InformationGiven, GameContext
from ..core.game_state import GameState, Player


class CharacterAbilityHandler:
    """Handles all character abilities and AI decision-making for information"""
    
    def __init__(self, ai_storyteller, game_context: GameContext):
        self.ai_storyteller = ai_storyteller
        self.game_context = game_context
        
        # Character data for decision making
        self.character_data = {
            "Fortune Teller": {"team": "good", "type": "townsfolk", "info_type": "detection"},
            "Empath": {"team": "good", "type": "townsfolk", "info_type": "numeric"},
            "Washerwoman": {"team": "good", "type": "townsfolk", "info_type": "first_night"},
            "Librarian": {"team": "good", "type": "townsfolk", "info_type": "first_night"},
            "Investigator": {"team": "good", "type": "townsfolk", "info_type": "first_night"},
            "Chef": {"team": "good", "type": "townsfolk", "info_type": "first_night"},
            "Undertaker": {"team": "good", "type": "townsfolk", "info_type": "reactive"},
            "Imp": {"team": "evil", "type": "demon", "kills": True},
            "Poisoner": {"team": "evil", "type": "minion", "affects_info": True},
            "Spy": {"team": "evil", "type": "minion", "sees_grimoire": True},
            "Drunk": {"team": "good", "type": "outsider", "malfunctions": True},
        }
        
    async def handle_fortune_teller(self, player: Player, targets: List[str], game_state: GameState) -> str:
        """Handle Fortune Teller ability"""
        
        if len(targets) != 2:
            return "Fortune Teller must choose exactly 2 players."
            
        # Get context for AI decision
        context_summary = self.game_context.get_context_summary(game_state)
        
        # Check actual truth
        target_players = [p for p in game_state.players if p.name in targets]
        actual_demon_present = any(self._is_demon(p.character) for p in target_players)
        
        # Check if Fortune Teller is drunk/poisoned
        give_false_info = player.is_drunk or player.is_poisoned
        
        # AI decision prompt
        prompt = f"""
STORYTELLER DECISION - Fortune Teller Information

{context_summary}

CURRENT SITUATION:
- {player.name} (Fortune Teller) is asking about {targets[0]} and {targets[1]}
- Fortune Teller status: {'DRUNK' if player.is_drunk else 'POISONED' if player.is_poisoned else 'HEALTHY'}
- Actual truth: {'One of them IS the demon' if actual_demon_present else 'Neither is the demon'}

As an experienced Storyteller, what information should I give?

Options:
1. "YES" (tell them one is the demon)
2. "NO" (tell them neither is the demon)

Consider game balance, story drama, and whether to give true or false information.
Respond with just: YES or NO
"""

        try:
            ai_response = await self.ai_storyteller.narrate("rule_question", {"question": prompt})
            result = "YES" if "yes" in ai_response.lower() else "NO"
            
            # Determine if this was truthful
            was_truthful = (result == "YES") == actual_demon_present
            
            # If drunk/poisoned, maybe override with false info
            if give_false_info and random.random() < 0.7:  # 70% chance of false info
                result = "YES" if result == "NO" else "NO"
                was_truthful = False
                
        except Exception:
            # Fallback decision
            result = "YES" if actual_demon_present else "NO"
            was_truthful = True
            
        # Record information given
        info = InformationGiven(
            player_name=player.name,
            character="Fortune Teller",
            info_type="fortune_teller",
            information=f"Asked about {targets[0]} and {targets[1]}: {result}",
            was_true=was_truthful,
            context=f"Actual: {'demon present' if actual_demon_present else 'no demon'}",
            timestamp=datetime.now(),
            night_number=game_state.day_number
        )
        
        self.game_context.add_information(info)
        
        return f"You learn: {result}"
        
    async def handle_empath(self, player: Player, game_state: GameState) -> str:
        """Handle Empath ability"""
        
        # Find neighbors
        players = sorted(game_state.get_alive_players(), key=lambda p: p.seat_position)
        player_index = next(i for i, p in enumerate(players) if p.name == player.name)
        
        left_neighbor = players[(player_index - 1) % len(players)]
        right_neighbor = players[(player_index + 1) % len(players)]
        
        # Count actual evil neighbors
        actual_evil_count = 0
        if self._is_evil(left_neighbor.character):
            actual_evil_count += 1
        if self._is_evil(right_neighbor.character):
            actual_evil_count += 1
            
        # AI decision for what to tell them
        context_summary = self.game_context.get_context_summary(game_state)
        
        prompt = f"""
STORYTELLER DECISION - Empath Information

{context_summary}

CURRENT SITUATION:
- {player.name} (Empath) is checking their neighbors
- Left neighbor: {left_neighbor.name} ({left_neighbor.character})
- Right neighbor: {right_neighbor.name} ({right_neighbor.character})
- Actual evil neighbors: {actual_evil_count}
- Empath status: {'DRUNK' if player.is_drunk else 'POISONED' if player.is_poisoned else 'HEALTHY'}

What number should I tell the Empath? Consider game balance and their drunk/poisoned status.
Respond with just a number: 0, 1, or 2
"""

        try:
            ai_response = await self.ai_storyteller.narrate("rule_question", {"question": prompt})
            # Extract number from response
            result = int(''.join(filter(str.isdigit, ai_response))[:1] or "0")
            result = max(0, min(2, result))  # Ensure valid range
        except Exception:
            result = actual_evil_count  # Fallback to truth
            
        # Check if information was truthful
        was_truthful = (result == actual_evil_count)
        
        # Record information
        info = InformationGiven(
            player_name=player.name,
            character="Empath",
            info_type="empath",
            information=f"Evil neighbors: {result}",
            was_true=was_truthful,
            context=f"Actual: {actual_evil_count}, Neighbors: {left_neighbor.name}, {right_neighbor.name}",
            timestamp=datetime.now(),
            night_number=game_state.day_number
        )
        
        self.game_context.add_information(info)
        
        return f"You learn: {result}"
        
    async def handle_washerwoman(self, player: Player, game_state: GameState) -> str:
        """Handle Washerwoman first night info"""
        
        # Get all townsfolk
        townsfolk = [p for p in game_state.players if self._is_townsfolk(p.character)]
        
        if not townsfolk:
            return "You learn: No townsfolk information available."
            
        # AI chooses which townsfolk to reveal and what false character to show
        context_summary = self.game_context.get_context_summary(game_state)
        
        prompt = f"""
STORYTELLER DECISION - Washerwoman Information

{context_summary}

AVAILABLE TOWNSFOLK:
{chr(10).join([f"- {p.name} ({p.character})" for p in townsfolk])}

As Storyteller, choose:
1. Which townsfolk to show (pick one from the list above)
2. Which other player to pair them with  
3. What townsfolk character to claim one of them is

Example response: "Alice is the Chef, or Bob is the Chef"

Generate the Washerwoman information:
"""

        try:
            ai_response = await self.ai_storyteller.narrate("rule_question", {"question": prompt})
            
            # For now, use a simple selection method
            chosen_townsfolk = random.choice(townsfolk)
            other_players = [p for p in game_state.players if p.name != chosen_townsfolk.name]
            other_player = random.choice(other_players)
            
            result = f"{chosen_townsfolk.name} is the {chosen_townsfolk.character}, or {other_player.name} is the {chosen_townsfolk.character}"
            
        except Exception:
            # Fallback
            chosen_townsfolk = random.choice(townsfolk)
            other_players = [p for p in game_state.players if p.name != chosen_townsfolk.name]
            other_player = random.choice(other_players)
            result = f"{chosen_townsfolk.name} is the {chosen_townsfolk.character}, or {other_player.name} is the {chosen_townsfolk.character}"
            
        # Record information
        info = InformationGiven(
            player_name=player.name,
            character="Washerwoman",
            info_type="washerwoman",
            information=result,
            was_true=True,  # Washerwoman info is always technically true
            context="First night information",
            timestamp=datetime.now(),
            night_number=game_state.day_number
        )
        
        self.game_context.add_information(info)
        
        return f"You learn: {result}"
        
    async def handle_chef(self, player: Player, game_state: GameState) -> str:
        """Handle Chef first night info"""
        
        # Count actual evil pairs
        players = sorted(game_state.players, key=lambda p: p.seat_position)
        actual_pairs = 0
        
        for i in range(len(players)):
            current = players[i]
            next_player = players[(i + 1) % len(players)]
            
            if self._is_evil(current.character) and self._is_evil(next_player.character):
                actual_pairs += 1
                
        # AI decision for what number to give
        context_summary = self.game_context.get_context_summary(game_state)
        
        prompt = f"""
STORYTELLER DECISION - Chef Information

{context_summary}

EVIL PAIR ANALYSIS:
- Actual evil pairs sitting together: {actual_pairs}
- Chef status: {'DRUNK' if player.is_drunk else 'POISONED' if player.is_poisoned else 'HEALTHY'}

What number should I tell the Chef? Consider game balance.
Respond with just a number: 0, 1, 2, etc.
"""

        try:
            ai_response = await self.ai_storyteller.narrate("rule_question", {"question": prompt})
            result = int(''.join(filter(str.isdigit, ai_response))[:1] or str(actual_pairs))
        except Exception:
            result = actual_pairs
            
        # Record information
        info = InformationGiven(
            player_name=player.name,
            character="Chef",
            info_type="chef",
            information=f"Evil pairs: {result}",
            was_true=(result == actual_pairs),
            context=f"Actual pairs: {actual_pairs}",
            timestamp=datetime.now(),
            night_number=game_state.day_number
        )
        
        self.game_context.add_information(info)
        
        return f"You learn: {result}"
        
    async def handle_undertaker(self, player: Player, executed_player: Player, game_state: GameState) -> str:
        """Handle Undertaker learning about executed player"""
        
        # Undertaker learns the character of the executed player
        actual_character = executed_player.character
        
        # AI decision - should we tell the truth?
        context_summary = self.game_context.get_context_summary(game_state)
        
        prompt = f"""
STORYTELLER DECISION - Undertaker Information

{context_summary}

SITUATION:
- {executed_player.name} was executed today
- Their actual character: {actual_character}
- Undertaker ({player.name}) status: {'DRUNK' if player.is_drunk else 'POISONED' if player.is_poisoned else 'HEALTHY'}

Should I tell the truth or give false information? If false, what character?
Respond with the character name to tell the Undertaker.
"""

        try:
            ai_response = await self.ai_storyteller.narrate("rule_question", {"question": prompt})
            # Extract character name from response
            result = actual_character  # For now, default to truth
        except Exception:
            result = actual_character
            
        # Record information
        info = InformationGiven(
            player_name=player.name,
            character="Undertaker",
            info_type="undertaker",
            information=f"{executed_player.name} was the {result}",
            was_true=(result == actual_character),
            context=f"Executed: {executed_player.name}, Actual: {actual_character}",
            timestamp=datetime.now(),
            night_number=game_state.day_number
        )
        
        self.game_context.add_information(info)
        
        return f"You learn: {executed_player.name} was the {result}"
        
    def _is_demon(self, character: str) -> bool:
        """Check if character is demon"""
        demons = ["Imp", "Vigormortis", "No Dashii", "Vortox", "Fang Gu", "Shabaloth"]
        return character in demons
        
    def _is_minion(self, character: str) -> bool:
        """Check if character is minion"""
        minions = ["Poisoner", "Spy", "Scarlet Woman", "Baron", "Witch", "Cerenovus"]
        return character in minions
        
    def _is_evil(self, character: str) -> bool:
        """Check if character is evil"""
        return self._is_demon(character) or self._is_minion(character)
        
    def _is_townsfolk(self, character: str) -> bool:
        """Check if character is townsfolk"""
        townsfolk = ["Washerwoman", "Librarian", "Investigator", "Chef", "Empath", 
                    "Fortune Teller", "Undertaker", "Monk", "Ravenkeeper", "Virgin", 
                    "Slayer", "Soldier", "Mayor"]
        return character in townsfolk