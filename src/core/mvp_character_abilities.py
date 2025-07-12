"""
MVP Character Ability Implementations
Core character abilities for the 7-player Trouble Brewing MVP
"""

import random
from dataclasses import dataclass
from typing import List, Optional, Tuple

from .game_state import GameState, Player


@dataclass
class AbilityResult:
    """Result of a character ability"""

    character: str
    player_name: str
    information: str
    is_successful: bool = True
    is_true_info: bool = True
    targets: List[str] = None

    def __post_init__(self):
        if self.targets is None:
            self.targets = []


class MVPCharacterAbilities:
    """Character ability implementations for MVP"""

    def __init__(self, game_state: GameState):
        self.game_state = game_state

    # === TOWNSFOLK ABILITIES ===

    def fortune_teller_ability(
        self, player: Player, target1: str, target2: str
    ) -> AbilityResult:
        """Fortune Teller: Choose 2 players, learn if either is the Demon"""

        # Find target players
        t1 = self._get_player_by_name(target1)
        t2 = self._get_player_by_name(target2)

        if not t1 or not t2:
            return AbilityResult(
                character="Fortune Teller",
                player_name=player.name,
                information="Invalid targets selected",
                is_successful=False,
            )

        # Check if either target is actually the demon
        actual_result = self._is_demon(t1.character) or self._is_demon(t2.character)

        # Determine what information to give
        told_result = self._get_fortune_teller_info(player, actual_result)

        info_text = f"You learn: {'YES' if told_result else 'NO'}"

        return AbilityResult(
            character="Fortune Teller",
            player_name=player.name,
            information=info_text,
            is_true_info=(told_result == actual_result),
            targets=[target1, target2],
        )

    def empath_ability(self, player: Player) -> AbilityResult:
        """Empath: Learn how many evil neighbors you have"""

        # Find neighbors
        left_neighbor, right_neighbor = self._get_neighbors(player)

        if not left_neighbor or not right_neighbor:
            return AbilityResult(
                character="Empath",
                player_name=player.name,
                information="Cannot determine neighbors",
                is_successful=False,
            )

        # Count actual evil neighbors
        actual_count = 0
        if self._is_evil(left_neighbor.character):
            actual_count += 1
        if self._is_evil(right_neighbor.character):
            actual_count += 1

        # Determine what number to give
        told_count = self._get_empath_info(player, actual_count)

        info_text = f"You learn: {told_count}"

        return AbilityResult(
            character="Empath",
            player_name=player.name,
            information=info_text,
            is_true_info=(told_count == actual_count),
            targets=[left_neighbor.name, right_neighbor.name],
        )

    def washerwoman_ability(self, player: Player) -> AbilityResult:
        """Washerwoman: Learn that 1 of 2 players is a particular Townsfolk"""

        # Find all townsfolk in play
        townsfolk = [
            p for p in self.game_state.players if self._is_townsfolk(p.character)
        ]

        if len(townsfolk) < 1:
            return AbilityResult(
                character="Washerwoman",
                player_name=player.name,
                information="No townsfolk to detect",
                is_successful=False,
            )

        # Choose a townsfolk to reveal
        chosen_townsfolk = random.choice(townsfolk)

        # Choose another player to pair with
        other_players = [
            p for p in self.game_state.players if p.name != chosen_townsfolk.name
        ]
        other_player = random.choice(other_players)

        # Determine what information to give (drunk/poisoned affects this)
        told_character = self._get_washerwoman_info(player, chosen_townsfolk.character)

        info_text = (
            f"You learn: One of {chosen_townsfolk.name} or "
            f"{other_player.name} is the {told_character}"
        )

        return AbilityResult(
            character="Washerwoman",
            player_name=player.name,
            information=info_text,
            is_true_info=(told_character == chosen_townsfolk.character),
            targets=[chosen_townsfolk.name, other_player.name],
        )

    def chef_ability(self, player: Player) -> AbilityResult:
        """Chef: Learn how many pairs of evil players sit next to each other"""

        # Count actual evil pairs
        actual_pairs = self._count_evil_pairs()

        # Determine what number to give
        told_pairs = self._get_chef_info(player, actual_pairs)

        info_text = f"You learn: {told_pairs}"

        return AbilityResult(
            character="Chef",
            player_name=player.name,
            information=info_text,
            is_true_info=(told_pairs == actual_pairs),
        )

    # === MINION ABILITIES ===

    def poisoner_ability(self, player: Player, target: str) -> AbilityResult:
        """Poisoner: Choose a player to poison tonight and tomorrow day"""

        target_player = self._get_player_by_name(target)
        if not target_player:
            return AbilityResult(
                character="Poisoner",
                player_name=player.name,
                information="Invalid target",
                is_successful=False,
            )

        # Apply poison effect
        target_player.is_poisoned = True

        info_text = f"You poison {target}"

        return AbilityResult(
            character="Poisoner",
            player_name=player.name,
            information=info_text,
            targets=[target],
        )

    # === DEMON ABILITIES ===

    def imp_ability(self, player: Player, target: str) -> AbilityResult:
        """Imp: Choose a player to kill (or yourself to pass on the demon)"""

        target_player = self._get_player_by_name(target)
        if not target_player:
            return AbilityResult(
                character="Imp",
                player_name=player.name,
                information="Invalid target",
                is_successful=False,
            )

        # Check for self-kill (starpass)
        if target_player.name == player.name:
            return self._handle_imp_starpass(player)

        # Normal kill
        target_player.kill()

        info_text = f"You kill {target}"

        return AbilityResult(
            character="Imp",
            player_name=player.name,
            information=info_text,
            targets=[target],
        )

    # === HELPER METHODS ===

    def _get_player_by_name(self, name: str) -> Optional[Player]:
        """Get player by name (case insensitive)"""
        for player in self.game_state.players:
            if player.name.lower() == name.lower():
                return player
        return None

    def _get_neighbors(
        self, player: Player
    ) -> Tuple[Optional[Player], Optional[Player]]:
        """Get left and right neighbors of a player"""

        alive_players = [p for p in self.game_state.players if p.is_alive()]
        alive_players.sort(key=lambda p: p.seat_position)

        try:
            player_index = next(
                i for i, p in enumerate(alive_players) if p.name == player.name
            )
        except StopIteration:
            return None, None

        left_neighbor = alive_players[(player_index - 1) % len(alive_players)]
        right_neighbor = alive_players[(player_index + 1) % len(alive_players)]

        return left_neighbor, right_neighbor

    def _is_demon(self, character: str) -> bool:
        """Check if character is a demon"""
        return character in ["Imp", "Vigormortis", "No Dashii", "Vortox"]

    def _is_minion(self, character: str) -> bool:
        """Check if character is a minion"""
        return character in ["Poisoner", "Spy", "Scarlet Woman", "Baron"]

    def _is_evil(self, character: str) -> bool:
        """Check if character is evil (demon or minion)"""
        return self._is_demon(character) or self._is_minion(character)

    def _is_townsfolk(self, character: str) -> bool:
        """Check if character is townsfolk"""
        townsfolk = [
            "Washerwoman",
            "Librarian",
            "Investigator",
            "Chef",
            "Empath",
            "Fortune Teller",
            "Undertaker",
            "Monk",
            "Ravenkeeper",
            "Virgin",
            "Slayer",
            "Soldier",
            "Mayor",
        ]
        return character in townsfolk

    def _count_evil_pairs(self) -> int:
        """Count pairs of evil players sitting next to each other"""

        players = sorted(self.game_state.players, key=lambda p: p.seat_position)
        pairs = 0

        for i in range(len(players)):
            current = players[i]
            next_player = players[(i + 1) % len(players)]

            if self._is_evil(current.character) and self._is_evil(
                next_player.character
            ):
                pairs += 1

        return pairs

    def _handle_imp_starpass(self, imp_player: Player) -> AbilityResult:
        """Handle Imp killing themselves (starpass to minion)"""

        # Find a living minion to become the Imp
        minions = [
            p
            for p in self.game_state.players
            if self._is_minion(p.character) and p.is_alive()
        ]

        if minions:
            new_imp = random.choice(minions)
            new_imp.character = "Imp"

        # Kill the original Imp
        imp_player.kill()

        info_text = f"You kill yourself. {new_imp.name if minions else 'No one'} becomes the Imp"

        return AbilityResult(
            character="Imp",
            player_name=imp_player.name,
            information=info_text,
            targets=[imp_player.name],
        )

    # === INFORMATION DECISION METHODS ===

    def _get_fortune_teller_info(self, player: Player, actual_result: bool) -> bool:
        """Decide what information to give Fortune Teller"""

        # If drunk or poisoned, give false info sometimes
        if player.is_drunk or player.is_poisoned:
            if random.random() < 0.3:  # 30% chance of true info when drunk/poisoned
                return actual_result
            else:
                return not actual_result

        # Otherwise, give true information (MVP simplification)
        return actual_result

    def _get_empath_info(self, player: Player, actual_count: int) -> int:
        """Decide what number to give Empath"""

        # If drunk or poisoned, give false info sometimes
        if player.is_drunk or player.is_poisoned:
            if random.random() < 0.3:  # 30% chance of true info
                return actual_count
            else:
                # Give random number 0-2
                return random.randint(0, 2)

        return actual_count

    def _get_washerwoman_info(self, player: Player, actual_character: str) -> str:
        """Decide what character to tell Washerwoman"""

        # If drunk or poisoned, might give wrong character
        if player.is_drunk or player.is_poisoned:
            if random.random() < 0.3:  # 30% chance of true info
                return actual_character
            else:
                # Give random townsfolk character
                townsfolk_chars = [
                    "Washerwoman",
                    "Chef",
                    "Empath",
                    "Fortune Teller",
                    "Monk",
                ]
                return random.choice(townsfolk_chars)

        return actual_character

    def _get_chef_info(self, player: Player, actual_pairs: int) -> int:
        """Decide what number to give Chef"""

        # If drunk or poisoned, give false info sometimes
        if player.is_drunk or player.is_poisoned:
            if random.random() < 0.3:  # 30% chance of true info
                return actual_pairs
            else:
                # Give random number 0-3
                return random.randint(0, 3)

        return actual_pairs


# Ability dispatcher for easy access
class AbilityDispatcher:
    """Dispatches character abilities by name"""

    def __init__(self, game_state: GameState):
        self.abilities = MVPCharacterAbilities(game_state)

    def execute_ability(
        self, character: str, player: Player, **kwargs
    ) -> AbilityResult:
        """Execute a character ability"""

        method_map = {
            "Fortune Teller": self.abilities.fortune_teller_ability,
            "Empath": self.abilities.empath_ability,
            "Washerwoman": self.abilities.washerwoman_ability,
            "Chef": self.abilities.chef_ability,
            "Poisoner": self.abilities.poisoner_ability,
            "Imp": self.abilities.imp_ability,
        }

        if character not in method_map:
            return AbilityResult(
                character=character,
                player_name=player.name,
                information=f"{character} ability not implemented",
                is_successful=False,
            )

        try:
            method = method_map[character]

            # Handle different ability signatures
            if character == "Fortune Teller":
                return method(player, kwargs.get("target1"), kwargs.get("target2"))
            elif character in ["Empath", "Washerwoman", "Chef"]:
                return method(player)
            elif character in ["Poisoner", "Imp"]:
                return method(player, kwargs.get("target"))
            else:
                return method(player, **kwargs)

        except Exception as e:
            return AbilityResult(
                character=character,
                player_name=player.name,
                information=f"Error executing ability: {str(e)}",
                is_successful=False,
            )


if __name__ == "__main__":
    # Test character abilities
    from .game_state import GamePhase, GameState, PlayerStatus

    # Create test game state
    players = [
        Player("1", "Alice", 0, "Fortune Teller", PlayerStatus.ALIVE),
        Player("2", "Bob", 1, "Empath", PlayerStatus.ALIVE),
        Player("3", "Charlie", 2, "Chef", PlayerStatus.ALIVE),
        Player("4", "Diana", 3, "Washerwoman", PlayerStatus.ALIVE),
        Player("5", "Eve", 4, "Drunk", PlayerStatus.ALIVE),
        Player("6", "Frank", 5, "Poisoner", PlayerStatus.ALIVE),
        Player("7", "Grace", 6, "Imp", PlayerStatus.ALIVE),
    ]

    game_state = GameState(
        players=players,
        phase=GamePhase.FIRST_NIGHT,
        day_number=1,
        script_name="trouble_brewing",
    )

    dispatcher = AbilityDispatcher(game_state)

    print("=== Testing Character Abilities ===")

    # Test Fortune Teller
    ft_result = dispatcher.execute_ability(
        "Fortune Teller", players[0], target1="Grace", target2="Frank"
    )
    print(f"Fortune Teller: {ft_result.information} (True: {ft_result.is_true_info})")

    # Test Empath
    empath_result = dispatcher.execute_ability("Empath", players[1])
    print(f"Empath: {empath_result.information} (True: {empath_result.is_true_info})")

    # Test Chef
    chef_result = dispatcher.execute_ability("Chef", players[2])
    print(f"Chef: {chef_result.information} (True: {chef_result.is_true_info})")

    # Test Washerwoman
    ww_result = dispatcher.execute_ability("Washerwoman", players[3])
    print(f"Washerwoman: {ww_result.information} (True: {ww_result.is_true_info})")
