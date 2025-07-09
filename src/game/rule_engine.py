"""
Rule Enforcement Engine for Blood on the Clocktower
Implements all game rules and mechanics from rules.md
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from ..core.game_state import GameState, Player, PlayerStatus, Team, GamePhase, Nomination


class RuleViolation(Exception):
    """Exception raised when a game rule is violated"""
    pass


class ActionType(Enum):
    NOMINATION = "nomination"
    VOTE = "vote"
    EXECUTION = "execution"
    NIGHT_ACTION = "night_action"
    ABILITY_USE = "ability_use"
    PHASE_CHANGE = "phase_change"


@dataclass
class RuleValidation:
    is_valid: bool
    reason: str
    suggested_action: Optional[str] = None


class RuleEngine:
    """Core rule enforcement engine following rules.md specifications"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Rule tracking
        self.active_restrictions = {}
        self.pending_effects = []
        
    def validate_nomination(self, nominator: str, nominee: str, game_state: GameState) -> RuleValidation:
        """Validate nomination according to rules.md section 3"""
        
        # Get players
        nominator_player = game_state.get_player_by_name(nominator)
        nominee_player = game_state.get_player_by_name(nominee)
        
        # Basic existence checks
        if not nominator_player:
            return RuleValidation(False, f"Player '{nominator}' not found")
        if not nominee_player:
            return RuleValidation(False, f"Player '{nominee}' not found")
            
        # Phase check
        if game_state.phase not in [GamePhase.DAY, GamePhase.VOTING]:
            return RuleValidation(False, "Nominations only allowed during day phase")
            
        # Alive checks
        if not nominator_player.is_alive():
            return RuleValidation(False, "Dead players cannot nominate")
        if not nominee_player.is_alive():
            return RuleValidation(False, "Dead players cannot be nominated")
            
        # Already nominated today check
        today_nominees = [n.nominee for n in game_state.nominations if n.timestamp.date() == datetime.now().date()]
        if nominee in today_nominees:
            return RuleValidation(False, f"{nominee} has already been nominated today")
            
        # Nominator already nominated check
        today_nominators = [n.nominator for n in game_state.nominations if n.timestamp.date() == datetime.now().date()]
        if nominator in today_nominators:
            return RuleValidation(False, f"{nominator} has already made a nomination today")
            
        # Character-specific restrictions
        char_validation = self._validate_character_nomination_restrictions(nominator_player, nominee_player, game_state)
        if not char_validation.is_valid:
            return char_validation
            
        return RuleValidation(True, "Valid nomination")
        
    def validate_vote(self, voter: str, nominee: str, game_state: GameState) -> RuleValidation:
        """Validate vote according to rules.md section 6"""
        
        voter_player = game_state.get_player_by_name(voter)
        nominee_player = game_state.get_player_by_name(nominee)
        
        if not voter_player:
            return RuleValidation(False, f"Voter '{voter}' not found")
        if not nominee_player:
            return RuleValidation(False, f"Nominee '{nominee}' not found")
            
        # Phase check
        if game_state.phase != GamePhase.VOTING:
            return RuleValidation(False, "Voting only allowed during voting phase")
            
        # Find current nomination
        current_nomination = None
        for nom in reversed(game_state.nominations):
            if nom.nominee == nominee and nom.timestamp.date() == datetime.now().date():
                current_nomination = nom
                break
                
        if not current_nomination:
            return RuleValidation(False, f"No active nomination for {nominee}")
            
        # Alive voter check (with ghost vote exception)
        if not voter_player.is_alive():
            if voter_player.ghost_vote_used:
                return RuleValidation(False, "Ghost vote already used")
            # Ghost vote is allowed once
            
        # Already voted check
        if voter in current_nomination.voters:
            return RuleValidation(False, f"{voter} has already voted on this nomination")
            
        # Character-specific voting restrictions
        char_validation = self._validate_character_voting_restrictions(voter_player, nominee_player, game_state)
        if not char_validation.is_valid:
            return char_validation
            
        return RuleValidation(True, "Valid vote")
        
    def validate_execution(self, nominee: str, vote_count: int, game_state: GameState) -> RuleValidation:
        """Validate execution according to rules.md section 6"""
        
        nominee_player = game_state.get_player_by_name(nominee)
        if not nominee_player:
            return RuleValidation(False, f"Nominee '{nominee}' not found")
            
        # Check vote threshold
        threshold = game_state.calculate_vote_threshold()
        if vote_count < threshold:
            return RuleValidation(False, f"Insufficient votes: {vote_count}/{threshold} required")
            
        # Check if already executed someone today
        if game_state.executions_today >= 1:
            return RuleValidation(False, "Maximum one execution per day")
            
        # Character-specific execution restrictions
        char_validation = self._validate_character_execution_restrictions(nominee_player, game_state)
        if not char_validation.is_valid:
            return char_validation
            
        return RuleValidation(True, "Valid execution")
        
    def validate_night_action(self, character: str, player: Player, target: Optional[str], game_state: GameState) -> RuleValidation:
        """Validate night action according to character abilities"""
        
        # Phase check
        if game_state.phase not in [GamePhase.FIRST_NIGHT, GamePhase.NIGHT]:
            return RuleValidation(False, "Night actions only allowed during night phase")
            
        # Player must be alive (unless specified otherwise)
        if not player.is_alive() and not self._character_acts_when_dead(character):
            return RuleValidation(False, f"{player.name} is dead and cannot act")
            
        # Player must not be drunk/poisoned (unless ability specifies otherwise)
        if (player.is_drunk or player.is_poisoned) and not self._character_acts_when_drunk_poisoned(character):
            return RuleValidation(False, f"{player.name} is drunk/poisoned and cannot act normally")
            
        # Check if character has night ability on this night
        is_first_night = game_state.phase == GamePhase.FIRST_NIGHT
        if not self._character_has_night_ability(character, is_first_night):
            return RuleValidation(False, f"{character} has no night ability this night")
            
        # Check if already acted this night
        if self._has_acted_this_night(player, game_state):
            return RuleValidation(False, f"{player.name} has already acted this night")
            
        # Validate target if required
        if target:
            target_validation = self._validate_night_action_target(character, player, target, game_state)
            if not target_validation.is_valid:
                return target_validation
                
        return RuleValidation(True, "Valid night action")
        
    def validate_win_condition(self, game_state: GameState) -> Tuple[bool, Optional[str], Optional[str]]:
        """Check win conditions according to rules.md section 7"""
        
        # Get alive players
        alive_players = game_state.get_alive_players()
        alive_count = len(alive_players)
        
        # Check good team victory conditions
        good_wins, good_reason = self._check_good_victory_conditions(game_state, alive_players)
        if good_wins:
            return True, "good", good_reason
            
        # Check evil team victory conditions
        evil_wins, evil_reason = self._check_evil_victory_conditions(game_state, alive_players)
        if evil_wins:
            return True, "evil", evil_reason
            
        # Game continues
        return False, None, None
        
    def apply_execution(self, nominee: str, game_state: GameState) -> List[str]:
        """Apply execution and return list of effects/deaths"""
        effects = []
        
        nominee_player = game_state.get_player_by_name(nominee)
        if not nominee_player:
            return effects
            
        # Mark as dead
        nominee_player.status = PlayerStatus.DEAD
        game_state.executions_today += 1
        
        effects.append(f"{nominee} has been executed")
        
        # Trigger death-related abilities
        death_effects = self._trigger_death_abilities(nominee_player, game_state, "execution")
        effects.extend(death_effects)
        
        # Check for special execution effects
        special_effects = self._apply_special_execution_effects(nominee_player, game_state)
        effects.extend(special_effects)
        
        return effects
        
    def apply_demon_kill(self, demon_player: Player, target: str, game_state: GameState) -> List[str]:
        """Apply demon kill and return list of effects"""
        effects = []
        
        target_player = game_state.get_player_by_name(target)
        if not target_player:
            return effects
            
        # Check for protection
        if self._is_protected_from_demon(target_player, game_state):
            effects.append(f"{target} was protected from the demon")
            return effects
            
        # Apply kill
        target_player.status = PlayerStatus.DEAD
        effects.append(f"{target} died in the night")
        
        # Trigger death abilities
        death_effects = self._trigger_death_abilities(target_player, game_state, "demon")
        effects.extend(death_effects)
        
        return effects
        
    def _validate_character_nomination_restrictions(self, nominator: Player, nominee: Player, game_state: GameState) -> RuleValidation:
        """Check character-specific nomination restrictions"""
        
        # Butler restriction
        if nominator.character == "Butler":
            master = self._get_butler_master(nominator, game_state)
            if master and not self._has_master_nominated_today(master, game_state):
                return RuleValidation(False, "Butler must wait for their Master to nominate first")
                
        return RuleValidation(True, "No character restrictions")
        
    def _validate_character_voting_restrictions(self, voter: Player, nominee: Player, game_state: GameState) -> RuleValidation:
        """Check character-specific voting restrictions"""
        
        # Butler restriction - can only vote if master votes
        if voter.character == "Butler":
            master = self._get_butler_master(voter, game_state)
            if master:
                current_nomination = self._get_current_nomination(nominee.name, game_state)
                if current_nomination and master.name not in current_nomination.voters:
                    return RuleValidation(False, "Butler can only vote if their Master votes")
                    
        # Organ Grinder - all votes are secret
        if any(p.character == "Organ Grinder" and p.is_alive() for p in game_state.players):
            # Special handling needed for secret voting
            pass
            
        return RuleValidation(True, "No voting restrictions")
        
    def _validate_character_execution_restrictions(self, nominee: Player, game_state: GameState) -> RuleValidation:
        """Check character-specific execution restrictions"""
        
        # Saint - good team loses if Saint is executed
        if nominee.character == "Saint" and nominee.team == Team.GOOD:
            return RuleValidation(True, "WARNING: Executing the Saint will cause good team to lose!", "confirm_saint_execution")
            
        return RuleValidation(True, "No execution restrictions")
        
    def _check_good_victory_conditions(self, game_state: GameState, alive_players: List[Player]) -> Tuple[bool, Optional[str]]:
        """Check if good team has won"""
        
        # Primary: Demon is dead
        demons = [p for p in game_state.players if self._is_demon(p.character) and p.status == PlayerStatus.DEAD]
        if demons:
            return True, "The demon has been slain!"
            
        # Mayor special condition: 3 alive at day end with no execution
        if len(alive_players) == 3 and game_state.executions_today == 0:
            mayor = next((p for p in alive_players if p.character == "Mayor"), None)
            if mayor:
                return True, "Mayor saves the day with no execution!"
                
        return False, None
        
    def _check_evil_victory_conditions(self, game_state: GameState, alive_players: List[Player]) -> Tuple[bool, Optional[str]]:
        """Check if evil team has won"""
        
        # Primary: 2 or fewer players alive (excluding Travelers)
        non_traveler_alive = [p for p in alive_players if p.status != PlayerStatus.TRAVELER]
        if len(non_traveler_alive) <= 2:
            return True, "Evil overwhelms the town!"
            
        # All remaining players are evil
        if all(p.team == Team.EVIL for p in alive_players):
            return True, "Evil has taken control!"
            
        return False, None
        
    def _trigger_death_abilities(self, dead_player: Player, game_state: GameState, death_type: str) -> List[str]:
        """Trigger abilities that activate on death"""
        effects = []
        
        character = dead_player.character
        
        # Ravenkeeper - learns character of killer
        if character == "Ravenkeeper" and death_type == "demon":
            # Would need to determine who the demon is
            effects.append(f"Ravenkeeper learns information about their killer")
            
        # Other death-triggered abilities...
        
        return effects
        
    def _apply_special_execution_effects(self, executed_player: Player, game_state: GameState) -> List[str]:
        """Apply special effects from executing certain characters"""
        effects = []
        
        character = executed_player.character
        
        # Saint execution causes good loss
        if character == "Saint" and executed_player.team == Team.GOOD:
            effects.append("GAME OVER: Good team loses by executing the Saint!")
            
        return effects
        
    def _is_protected_from_demon(self, target: Player, game_state: GameState) -> bool:
        """Check if player is protected from demon kill"""
        
        # Soldier is immune to demon
        if target.character == "Soldier":
            return True
            
        # Monk protection
        for player in game_state.players:
            if player.character == "Monk" and player.is_alive():
                # Check if Monk protected this player
                for token in target.reminder_tokens:
                    if token.token_type == "protected_by_monk" and token.is_active:
                        return True
                        
        return False
        
    def _character_has_night_ability(self, character: str, is_first_night: bool) -> bool:
        """Check if character has night ability on given night"""
        
        # Characters with first night abilities
        first_night_characters = [
            "Librarian", "Investigator", "Chef", "Empath", "Fortune Teller", 
            "Washerwoman", "Steward", "Butler", "Drunk"
        ]
        
        # Characters with ongoing night abilities
        ongoing_night_characters = [
            "Fortune Teller", "Undertaker", "Ravenkeeper", "Imp", "Poisoner", "Spy"
        ]
        
        if is_first_night:
            return character in first_night_characters or character in ongoing_night_characters
        else:
            return character in ongoing_night_characters
            
    def _character_acts_when_dead(self, character: str) -> bool:
        """Check if character can act when dead"""
        
        # Ravenkeeper acts when dying
        return character == "Ravenkeeper"
        
    def _character_acts_when_drunk_poisoned(self, character: str) -> bool:
        """Check if character acts normally when drunk/poisoned"""
        
        # Most characters act but get false information
        # Only a few are completely disabled
        return True
        
    def _has_acted_this_night(self, player: Player, game_state: GameState) -> bool:
        """Check if player has already acted this night"""
        
        current_night = game_state.night_number
        
        for action in game_state.night_actions:
            if (action.player_id == player.id and 
                action.timestamp.date() == datetime.now().date()):
                return True
                
        return False
        
    def _validate_night_action_target(self, character: str, player: Player, target: str, game_state: GameState) -> RuleValidation:
        """Validate target for night action"""
        
        target_player = game_state.get_player_by_name(target)
        if not target_player:
            return RuleValidation(False, f"Target '{target}' not found")
            
        # Most abilities can't target self
        if target == player.name and character not in ["Fortune Teller"]:
            return RuleValidation(False, "Cannot target yourself")
            
        # Most abilities require alive targets
        if not target_player.is_alive() and character not in ["Undertaker"]:
            return RuleValidation(False, "Cannot target dead players")
            
        return RuleValidation(True, "Valid target")
        
    def _is_demon(self, character: str) -> bool:
        """Check if character is a demon"""
        demons = ["Imp", "Fang Gu", "Vigormortis", "No Dashii", "Vortox", "Zombuul"]
        return character in demons
        
    def _get_butler_master(self, butler: Player, game_state: GameState) -> Optional[Player]:
        """Get the Butler's master"""
        for token in butler.reminder_tokens:
            if token.token_type == "butler_master":
                return game_state.get_player_by_name(token.description)
        return None
        
    def _has_master_nominated_today(self, master: Player, game_state: GameState) -> bool:
        """Check if master has nominated today"""
        today_nominators = [n.nominator for n in game_state.nominations if n.timestamp.date() == datetime.now().date()]
        return master.name in today_nominators
        
    def _get_current_nomination(self, nominee: str, game_state: GameState) -> Optional[Nomination]:
        """Get current active nomination"""
        for nom in reversed(game_state.nominations):
            if nom.nominee == nominee and nom.timestamp.date() == datetime.now().date():
                return nom
        return None


class CharacterAbilityValidator:
    """Validates specific character abilities and interactions"""
    
    def __init__(self):
        self.ability_rules = self._load_ability_rules()
        
    def _load_ability_rules(self) -> Dict[str, Dict]:
        """Load character-specific ability rules"""
        
        return {
            "Librarian": {
                "night_ability": True,
                "first_night_only": True,
                "learns": "outsider_or_type",
                "targets": 2
            },
            "Investigator": {
                "night_ability": True,
                "first_night_only": True,
                "learns": "minion_or_type",
                "targets": 2
            },
            "Chef": {
                "night_ability": True,
                "first_night_only": True,
                "learns": "evil_neighbors",
                "targets": 0
            },
            "Empath": {
                "night_ability": True,
                "ongoing": True,
                "learns": "evil_neighbors",
                "targets": 0
            },
            "Fortune Teller": {
                "night_ability": True,
                "ongoing": True,
                "learns": "demon_detection",
                "targets": 2,
                "can_target_self": True
            },
            "Butler": {
                "voting_restriction": True,
                "nomination_restriction": True,
                "master_dependent": True
            },
            "Monk": {
                "night_ability": True,
                "ongoing": True,
                "protects": True,
                "targets": 1,
                "cannot_target_self": True
            },
            "Soldier": {
                "passive": True,
                "demon_immune": True
            },
            "Mayor": {
                "passive": True,
                "win_condition": "no_execution_3_alive"
            }
        }
        
    def validate_ability_use(self, character: str, ability_context: Dict) -> RuleValidation:
        """Validate use of character ability"""
        
        if character not in self.ability_rules:
            return RuleValidation(False, f"Unknown character: {character}")
            
        rules = self.ability_rules[character]
        
        # Check if ability can be used at this time
        if rules.get("first_night_only") and not ability_context.get("is_first_night"):
            return RuleValidation(False, f"{character} ability only works on first night")
            
        # Check target count
        expected_targets = rules.get("targets", 0)
        actual_targets = len(ability_context.get("targets", []))
        
        if actual_targets != expected_targets:
            return RuleValidation(False, f"{character} requires exactly {expected_targets} targets")
            
        return RuleValidation(True, "Valid ability use")