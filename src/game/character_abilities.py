"""
Character Ability System for Blood on the Clocktower
Comprehensive implementation of all character abilities and interactions
"""

import asyncio
import logging
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional

from ..core.game_state import GameState, Player


class TriggerType(Enum):
    """When abilities trigger"""

    FIRST_NIGHT = auto()
    EACH_NIGHT = auto()
    FIRST_DAY = auto()
    EACH_DAY = auto()
    ON_DEATH = auto()
    ON_EXECUTION = auto()
    ON_NOMINATION = auto()
    PASSIVE = auto()


class AbilityResult(Enum):
    """Result of ability execution"""

    SUCCESS = auto()
    FAILED = auto()
    BLOCKED = auto()
    POISONED = auto()
    NO_EFFECT = auto()


@dataclass
class AbilityExecution:
    """Record of ability execution"""

    character: str
    player_name: str
    trigger: TriggerType
    result: AbilityResult
    targets: List[str] = field(default_factory=list)
    effects: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0
    night_number: int = 0


class CharacterAbility(ABC):
    """Base class for all character abilities"""

    def __init__(self, character_name: str, team: str):
        self.character_name = character_name
        self.team = team
        self.logger = logging.getLogger(f"{__name__}.{character_name}")

    @abstractmethod
    def get_triggers(self) -> List[TriggerType]:
        """Get when this ability triggers"""

    @abstractmethod
    async def execute(
        self, player: Player, game_state: GameState, targets: List[str] = None, **kwargs
    ) -> AbilityExecution:
        """Execute the ability"""

    def is_poisoned(self, player: Player) -> bool:
        """Check if player is poisoned (ability has no effect)"""
        return hasattr(player, "poisoned") and player.poisoned

    def is_drunk(self, player: Player) -> bool:
        """Check if player is drunk (ability malfunctions)"""
        return hasattr(player, "drunk") and player.drunk


# DEMON ABILITIES


class ImpAbility(CharacterAbility):
    """Imp demon ability"""

    def __init__(self):
        super().__init__("Imp", "evil")

    def get_triggers(self) -> List[TriggerType]:
        return [TriggerType.EACH_NIGHT]

    async def execute(
        self, player: Player, game_state: GameState, targets: List[str] = None, **kwargs
    ) -> AbilityExecution:
        """Imp kills a player each night"""
        result = AbilityExecution(
            character=self.character_name,
            player_name=player.name,
            trigger=TriggerType.EACH_NIGHT,
            result=AbilityResult.SUCCESS,
        )

        if self.is_poisoned(player):
            result.result = AbilityResult.POISONED
            return result

        if targets and len(targets) > 0:
            target_name = targets[0]
            target_player = game_state.get_player_by_name(target_name)

            if target_player and target_player.is_alive():
                # Check for protection
                if hasattr(target_player, "protected") and target_player.protected:
                    result.result = AbilityResult.BLOCKED
                    result.effects["protection_blocked"] = True
                    self.logger.info(f"Imp kill blocked by protection on {target_name}")
                else:
                    # Schedule kill for dawn
                    setattr(target_player, "demon_kill_pending", True)
                    result.targets = [target_name]
                    result.effects["kill_scheduled"] = True
                    self.logger.info(f"Imp scheduled kill on {target_name}")

        return result


class ScarletWomanAbility(CharacterAbility):
    """Scarlet Woman minion ability"""

    def __init__(self):
        super().__init__("Scarlet Woman", "evil")

    def get_triggers(self) -> List[TriggerType]:
        return [TriggerType.EACH_NIGHT, TriggerType.PASSIVE]

    async def execute(
        self, player: Player, game_state: GameState, targets: List[str] = None, **kwargs
    ) -> AbilityExecution:
        """Becomes Imp if Imp dies"""
        result = AbilityExecution(
            character=self.character_name,
            player_name=player.name,
            trigger=TriggerType.EACH_NIGHT,
            result=AbilityResult.NO_EFFECT,
        )

        # Check if Imp is dead
        imp_alive = any(
            p.character == "Imp" and p.is_alive() for p in game_state.players
        )

        if not imp_alive and player.is_alive():
            # Scarlet Woman becomes the Imp
            player.character = "Imp"
            result.result = AbilityResult.SUCCESS
            result.effects["becomes_imp"] = True
            self.logger.info(f"{player.name} becomes the Imp (Scarlet Woman)")

            # Can now kill like an Imp
            if targets and len(targets) > 0:
                target_name = targets[0]
                target_player = game_state.get_player_by_name(target_name)

                if target_player and target_player.is_alive():
                    setattr(target_player, "demon_kill_pending", True)
                    result.targets = [target_name]
                    result.effects["kill_scheduled"] = True

        return result


# MINION ABILITIES


class PoisonerAbility(CharacterAbility):
    """Poisoner minion ability"""

    def __init__(self):
        super().__init__("Poisoner", "evil")

    def get_triggers(self) -> List[TriggerType]:
        return [TriggerType.EACH_NIGHT]

    async def execute(
        self, player: Player, game_state: GameState, targets: List[str] = None, **kwargs
    ) -> AbilityExecution:
        """Poison a player's ability"""
        result = AbilityExecution(
            character=self.character_name,
            player_name=player.name,
            trigger=TriggerType.EACH_NIGHT,
            result=AbilityResult.SUCCESS,
        )

        # Clear previous poison
        for p in game_state.players:
            if hasattr(p, "poisoned_by_poisoner"):
                setattr(p, "poisoned", False)
                setattr(p, "poisoned_by_poisoner", False)

        if targets and len(targets) > 0:
            target_name = targets[0]
            target_player = game_state.get_player_by_name(target_name)

            if target_player and target_player.is_alive():
                setattr(target_player, "poisoned", True)
                setattr(target_player, "poisoned_by_poisoner", True)
                result.targets = [target_name]
                result.effects["poisoned"] = True
                self.logger.info(f"Poisoner poisoned {target_name}")

        return result


class SpyAbility(CharacterAbility):
    """Spy minion ability"""

    def __init__(self):
        super().__init__("Spy", "evil")

    def get_triggers(self) -> List[TriggerType]:
        return [TriggerType.FIRST_NIGHT, TriggerType.EACH_NIGHT]

    async def execute(
        self, player: Player, game_state: GameState, targets: List[str] = None, **kwargs
    ) -> AbilityExecution:
        """See the Grimoire and register as good"""
        result = AbilityExecution(
            character=self.character_name,
            player_name=player.name,
            trigger=kwargs.get("trigger", TriggerType.EACH_NIGHT),
            result=AbilityResult.SUCCESS,
        )

        # Spy sees everything - implementation would provide full game state
        grimoire_info = self._generate_grimoire_info(game_state)
        result.effects["grimoire_info"] = grimoire_info

        # Spy registers as good to all abilities
        setattr(player, "registers_as_good", True)

        self.logger.info(f"Spy sees full Grimoire state")
        return result

    def _generate_grimoire_info(self, game_state: GameState) -> Dict[str, Any]:
        """Generate complete game state information"""
        return {
            "players": [
                {
                    "name": p.name,
                    "character": p.character,
                    "team": p.team,
                    "alive": p.is_alive(),
                    "position": p.seat_position,
                }
                for p in game_state.players
            ],
            "demon_bluffs": ["Virgin", "Investigator", "Monk"],  # Example bluffs
            "in_play": [p.character for p in game_state.players],
        }


# TOWNSFOLK ABILITIES


class WasherwomanAbility(CharacterAbility):
    """Washerwoman townsfolk ability"""

    def __init__(self):
        super().__init__("Washerwoman", "good")

    def get_triggers(self) -> List[TriggerType]:
        return [TriggerType.FIRST_NIGHT]

    async def execute(
        self, player: Player, game_state: GameState, targets: List[str] = None, **kwargs
    ) -> AbilityExecution:
        """Learn which of two players is a specific Townsfolk"""
        result = AbilityExecution(
            character=self.character_name,
            player_name=player.name,
            trigger=TriggerType.FIRST_NIGHT,
            result=AbilityResult.SUCCESS,
        )

        if self.is_poisoned(player) or self.is_drunk(player):
            result.result = AbilityResult.POISONED
            # Provide false information
            info = self._generate_false_info(game_state)
        else:
            info = self._generate_true_info(game_state)

        result.effects["information"] = info
        self.logger.info(f"Washerwoman learns: {info}")

        return result

    def _generate_true_info(self, game_state: GameState) -> str:
        """Generate true Washerwoman information"""
        # Find a Townsfolk character in play
        townsfolk = [
            p
            for p in game_state.players
            if p.team == "good" and p.character != "Washerwoman"
        ]

        if not townsfolk:
            return "No Townsfolk information available"

        target_townsfolk = random.choice(townsfolk)

        # Find another player to pair with
        other_players = [p for p in game_state.players if p != target_townsfolk]
        if not other_players:
            return f"{target_townsfolk.name} is the {target_townsfolk.character}"

        other_player = random.choice(other_players)

        return f"Between {target_townsfolk.name} and {other_player.name}, one is the {target_townsfolk.character}."

    def _generate_false_info(self, game_state: GameState) -> str:
        """Generate false information when poisoned/drunk"""
        # Pick two random players and a random Townsfolk character
        players = random.sample(game_state.players, min(2, len(game_state.players)))
        fake_character = random.choice(
            ["Librarian", "Investigator", "Chef", "Empath", "Fortune Teller"]
        )

        if len(players) == 2:
            return f"Between {players[0].name} and {players[1].name}, one is the {fake_character}."
        else:
            return f"{players[0].name} is the {fake_character}."


class FortunetellAbility(CharacterAbility):
    """Fortune Teller townsfolk ability"""

    def __init__(self):
        super().__init__("Fortune Teller", "good")

    def get_triggers(self) -> List[TriggerType]:
        return [TriggerType.FIRST_NIGHT, TriggerType.EACH_NIGHT]

    async def execute(
        self, player: Player, game_state: GameState, targets: List[str] = None, **kwargs
    ) -> AbilityExecution:
        """Learn if the Demon is one of two chosen players"""
        result = AbilityExecution(
            character=self.character_name,
            player_name=player.name,
            trigger=kwargs.get("trigger", TriggerType.EACH_NIGHT),
            result=AbilityResult.SUCCESS,
        )

        if not targets or len(targets) < 2:
            result.result = AbilityResult.FAILED
            result.effects["error"] = "Need two targets"
            return result

        target1, target2 = targets[0], targets[1]
        result.targets = [target1, target2]

        if self.is_poisoned(player) or self.is_drunk(player):
            result.result = AbilityResult.POISONED
            # Random answer when poisoned
            is_demon = random.choice([True, False])
        else:
            # Check if either target is actually the demon
            demon_characters = ["Imp"]  # Add other demons as needed
            target1_player = game_state.get_player_by_name(target1)
            target2_player = game_state.get_player_by_name(target2)

            is_demon = False
            if target1_player and target1_player.character in demon_characters:
                is_demon = True
            elif target2_player and target2_player.character in demon_characters:
                is_demon = True

        if is_demon:
            info = f"YES - One of {target1} or {target2} is the Demon."
        else:
            info = f"NO - Neither {target1} nor {target2} is the Demon."

        result.effects["information"] = info
        result.effects["demon_present"] = is_demon

        self.logger.info(f"Fortune Teller learns: {info}")
        return result


class MonkAbility(CharacterAbility):
    """Monk townsfolk ability"""

    def __init__(self):
        super().__init__("Monk", "good")

    def get_triggers(self) -> List[TriggerType]:
        return [TriggerType.EACH_NIGHT]

    async def execute(
        self, player: Player, game_state: GameState, targets: List[str] = None, **kwargs
    ) -> AbilityExecution:
        """Protect a player from the demon"""
        result = AbilityExecution(
            character=self.character_name,
            player_name=player.name,
            trigger=TriggerType.EACH_NIGHT,
            result=AbilityResult.SUCCESS,
        )

        # Clear previous protection
        for p in game_state.players:
            if hasattr(p, "protected_by_monk"):
                setattr(p, "protected", False)
                setattr(p, "protected_by_monk", False)

        if self.is_poisoned(player):
            result.result = AbilityResult.POISONED
            return result

        if targets and len(targets) > 0:
            target_name = targets[0]
            target_player = game_state.get_player_by_name(target_name)

            if target_player and target_player.is_alive():
                setattr(target_player, "protected", True)
                setattr(target_player, "protected_by_monk", True)
                result.targets = [target_name]
                result.effects["protected"] = True
                self.logger.info(f"Monk protected {target_name}")

        return result


# OUTSIDER ABILITIES


class ButlerAbility(CharacterAbility):
    """Butler outsider ability"""

    def __init__(self):
        super().__init__("Butler", "good")

    def get_triggers(self) -> List[TriggerType]:
        return [TriggerType.FIRST_NIGHT, TriggerType.PASSIVE]

    async def execute(
        self, player: Player, game_state: GameState, targets: List[str] = None, **kwargs
    ) -> AbilityExecution:
        """Choose master and voting restrictions"""
        result = AbilityExecution(
            character=self.character_name,
            player_name=player.name,
            trigger=kwargs.get("trigger", TriggerType.FIRST_NIGHT),
            result=AbilityResult.SUCCESS,
        )

        if kwargs.get("trigger") == TriggerType.FIRST_NIGHT:
            # Choose master
            if targets and len(targets) > 0:
                master_name = targets[0]
                setattr(player, "butler_master", master_name)
                result.targets = [master_name]
                result.effects["master_chosen"] = master_name
                self.logger.info(f"Butler chose {master_name} as master")

        return result

    def check_voting_restriction(
        self, player: Player, vote_target: str, game_state: GameState
    ) -> bool:
        """Check if Butler can vote based on master's vote"""
        if not hasattr(player, "butler_master"):
            return True

        player.butler_master
        # Implementation would check if master voted for the same target
        # For now, return True (no restriction)
        return True


class VirginAbility(CharacterAbility):
    """Virgin outsider ability"""

    def __init__(self):
        super().__init__("Virgin", "good")

    def get_triggers(self) -> List[TriggerType]:
        return [TriggerType.ON_NOMINATION]

    async def execute(
        self, player: Player, game_state: GameState, targets: List[str] = None, **kwargs
    ) -> AbilityExecution:
        """If nominated by Townsfolk, nominator dies"""
        result = AbilityExecution(
            character=self.character_name,
            player_name=player.name,
            trigger=TriggerType.ON_NOMINATION,
            result=AbilityResult.SUCCESS,
        )

        nominator_name = kwargs.get("nominator")
        if not nominator_name:
            result.result = AbilityResult.FAILED
            return result

        nominator = game_state.get_player_by_name(nominator_name)
        if not nominator:
            result.result = AbilityResult.FAILED
            return result

        # Check if Virgin ability is still active
        virgin_active = not hasattr(player, "virgin_used") or not player.virgin_used

        if (
            virgin_active
            and nominator.team == "good"
            and nominator.character != "Virgin"
        ):
            # Townsfolk nominated Virgin - nominator dies
            nominator.kill("virgin_power")
            setattr(player, "virgin_used", True)

            result.targets = [nominator_name]
            result.effects["nominator_dies"] = True
            result.effects["virgin_used"] = True

            self.logger.info(
                f"Virgin power: {nominator_name} dies for nominating Virgin"
            )
        else:
            result.result = AbilityResult.NO_EFFECT

        return result


# ABILITY SYSTEM MANAGER


class AbilitySystem:
    """Manages all character abilities and their execution"""

    def __init__(self):
        self.abilities: Dict[str, CharacterAbility] = {}
        self.execution_history: List[AbilityExecution] = []
        self.logger = logging.getLogger(__name__)

        # Register all abilities
        self._register_abilities()

    def _register_abilities(self):
        """Register all character abilities"""
        abilities = [
            # Demons
            ImpAbility(),
            ScarletWomanAbility(),
            # Minions
            PoisonerAbility(),
            SpyAbility(),
            # Townsfolk
            WasherwomanAbility(),
            FortunetellAbility(),
            MonkAbility(),
            # Outsiders
            ButlerAbility(),
            VirginAbility(),
        ]

        for ability in abilities:
            self.abilities[ability.character_name] = ability

        self.logger.info(f"Registered {len(self.abilities)} character abilities")

    async def execute_ability(
        self,
        character: str,
        player: Player,
        game_state: GameState,
        trigger: TriggerType,
        targets: List[str] = None,
        **kwargs,
    ) -> Optional[AbilityExecution]:
        """Execute a character's ability"""
        if character not in self.abilities:
            self.logger.warning(f"No ability registered for {character}")
            return None

        ability = self.abilities[character]

        if trigger not in ability.get_triggers():
            return None

        try:
            kwargs["trigger"] = trigger
            execution = await ability.execute(player, game_state, targets, **kwargs)
            execution.timestamp = asyncio.get_event_loop().time()

            self.execution_history.append(execution)

            # Keep only recent history
            if len(self.execution_history) > 100:
                self.execution_history = self.execution_history[-50:]

            return execution

        except Exception as e:
            self.logger.error(f"Error executing {character} ability: {e}")
            return None

    def get_abilities_for_trigger(self, trigger: TriggerType) -> List[str]:
        """Get all characters that have abilities for this trigger"""
        characters = []
        for character, ability in self.abilities.items():
            if trigger in ability.get_triggers():
                characters.append(character)
        return characters

    def get_execution_history(
        self, character: str = None, limit: int = 10
    ) -> List[AbilityExecution]:
        """Get ability execution history"""
        history = self.execution_history

        if character:
            history = [ex for ex in history if ex.character == character]

        return list(reversed(history))[-limit:]
