"""
Blood on the Clocktower Game Engine - MVP Implementation
Handles core game logic for a functional 7-player Trouble Brewing game
"""

import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .game_state import GameState, Player, GamePhase, PlayerStatus


@dataclass
class Script:
    """Definition of a game script"""

    name: str
    townsfolk: List[str]
    outsiders: List[str]
    minions: List[str]
    demons: List[str]


class TroubleBrewing:
    """Trouble Brewing script definition"""

    TOWNSFOLK = [
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

    OUTSIDERS = ["Drunk", "Recluse", "Saint", "Butler"]

    MINIONS = ["Poisoner", "Spy", "Scarlet Woman", "Baron"]

    DEMONS = ["Imp"]

    # Character distribution for different player counts
    DISTRIBUTIONS = {
        5: {"townsfolk": 3, "outsiders": 0, "minions": 1, "demons": 1},
        6: {"townsfolk": 3, "outsiders": 1, "minions": 1, "demons": 1},
        7: {"townsfolk": 5, "outsiders": 0, "minions": 1, "demons": 1},
        8: {"townsfolk": 5, "outsiders": 1, "minions": 1, "demons": 1},
        9: {"townsfolk": 5, "outsiders": 2, "minions": 1, "demons": 1},
        10: {"townsfolk": 7, "outsiders": 0, "minions": 2, "demons": 1},
        11: {"townsfolk": 7, "outsiders": 1, "minions": 2, "demons": 1},
        12: {"townsfolk": 7, "outsiders": 2, "minions": 2, "demons": 1},
        13: {"townsfolk": 9, "outsiders": 0, "minions": 3, "demons": 1},
        14: {"townsfolk": 9, "outsiders": 1, "minions": 3, "demons": 1},
        15: {"townsfolk": 9, "outsiders": 2, "minions": 3, "demons": 1},
    }

    # MVP night order (simplified)
    NIGHT_ORDER = [
        "Poisoner",  # Minion poison
        "Imp",  # Demon kill
        "Fortune Teller",  # Information
        "Empath",  # Information
        "Undertaker",  # Information (if execution)
    ]

    # MVP first night order
    FIRST_NIGHT_ORDER = [
        "Poisoner",  # Minion poison
        "Washerwoman",  # First night info
        "Librarian",  # First night info
        "Investigator",  # First night info
        "Chef",  # First night info
        "Fortune Teller",  # Choose 2 players
        "Empath",  # Learn evil neighbors
    ]


class GameEngine:
    """Core game engine for Blood on the Clocktower MVP"""

    def __init__(self):
        self.game_state: Optional[GameState] = None
        self.script = TroubleBrewing()

    def create_game(self, player_names: List[str]) -> GameState:
        """Create a new game with character assignments"""

        if len(player_names) not in TroubleBrewing.DISTRIBUTIONS:
            raise ValueError(f"Player count {len(player_names)} not supported")

        # Get character distribution
        distribution = TroubleBrewing.DISTRIBUTIONS[len(player_names)]

        # Select characters for this game
        characters = self._select_characters(distribution)

        # Create players with character assignments
        players = []
        for i, name in enumerate(player_names):
            player = Player(
                id=f"player_{i}",
                name=name,
                seat_position=i,
                character=characters[i],
                status=PlayerStatus.ALIVE,
            )
            players.append(player)

        # Set up game state
        import uuid

        self.game_state = GameState(
            game_id=str(uuid.uuid4()),
            players=players,
            phase=GamePhase.SETUP,
            day_number=0,
            script_name="trouble_brewing",
        )

        # Assign demon bluffs (3 characters not in play)
        self._assign_demon_bluffs()

        return self.game_state

    def _select_characters(self, distribution: Dict[str, int]) -> List[str]:
        """Select characters based on distribution"""

        selected = []

        # Always include MVP core characters for 7-player game
        if distribution["townsfolk"] >= 4:
            # Core townsfolk for MVP
            core_townsfolk = ["Fortune Teller", "Empath", "Washerwoman", "Chef"]
            selected.extend(core_townsfolk)

            # Add random additional townsfolk if needed
            remaining_townsfolk = distribution["townsfolk"] - len(core_townsfolk)
            if remaining_townsfolk > 0:
                available = [
                    t for t in self.script.TOWNSFOLK if t not in core_townsfolk
                ]
                selected.extend(random.sample(available, remaining_townsfolk))
        else:
            # For smaller games, pick random townsfolk
            selected.extend(
                random.sample(self.script.TOWNSFOLK, distribution["townsfolk"])
            )

        # Outsiders
        if distribution["outsiders"] > 0:
            # Prefer Drunk for MVP
            if "Drunk" in self.script.OUTSIDERS:
                selected.append("Drunk")
                remaining = distribution["outsiders"] - 1
                if remaining > 0:
                    available = [o for o in self.script.OUTSIDERS if o != "Drunk"]
                    selected.extend(random.sample(available, remaining))
            else:
                selected.extend(
                    random.sample(self.script.OUTSIDERS, distribution["outsiders"])
                )

        # Minions
        if distribution["minions"] >= 1:
            # Always include Poisoner for MVP
            selected.append("Poisoner")
            remaining = distribution["minions"] - 1
            if remaining > 0:
                available = [m for m in self.script.MINIONS if m != "Poisoner"]
                selected.extend(random.sample(available, remaining))

        # Demons
        selected.extend(random.sample(self.script.DEMONS, distribution["demons"]))

        # Shuffle the character assignments
        random.shuffle(selected)

        return selected

    def _assign_demon_bluffs(self):
        """Assign 3 character bluffs to the demon"""

        if not self.game_state:
            return

        # Find demon player
        demon_player = None
        characters_in_play = []

        for player in self.game_state.players:
            characters_in_play.append(player.character)
            if player.character in self.script.DEMONS:
                demon_player = player

        if not demon_player:
            return

        # Select 3 bluffs from characters not in play
        all_good_characters = self.script.TOWNSFOLK + self.script.OUTSIDERS
        available_bluffs = [
            c for c in all_good_characters if c not in characters_in_play
        ]

        bluffs = random.sample(available_bluffs, min(3, len(available_bluffs)))

        # Store bluffs (we'll need this for the storyteller)
        if not hasattr(self.game_state, "demon_bluffs"):
            self.game_state.demon_bluffs = bluffs

    def start_game(self) -> bool:
        """Start the game (move to first night)"""

        if not self.game_state:
            return False

        self.game_state.phase = GamePhase.FIRST_NIGHT
        self.game_state.day_number = 1

        return True

    def get_night_order(self, is_first_night: bool = False) -> List[str]:
        """Get the night order for current night"""

        if not self.game_state:
            return []

        order = (
            self.script.FIRST_NIGHT_ORDER if is_first_night else self.script.NIGHT_ORDER
        )

        # Filter to only characters actually in play and alive
        characters_in_play = {
            p.character
            for p in self.game_state.players
            if p.is_alive() and p.character in order
        }

        return [char for char in order if char in characters_in_play]

    def advance_to_day(self) -> bool:
        """Advance from night to day phase"""

        if not self.game_state:
            return False

        if self.game_state.phase == GamePhase.FIRST_NIGHT:
            self.game_state.phase = GamePhase.DAY
        elif self.game_state.phase == GamePhase.NIGHT:
            self.game_state.phase = GamePhase.DAY

        return True

    def advance_to_night(self) -> bool:
        """Advance from day to night phase"""

        if not self.game_state:
            return False

        if self.game_state.phase == GamePhase.DAY:
            self.game_state.phase = GamePhase.NIGHT
            self.game_state.day_number += 1

        return True

    def execute_player(self, player_name: str) -> bool:
        """Execute a player"""

        if not self.game_state:
            return False

        player = self.get_player_by_name(player_name)
        if not player:
            return False

        player.status = PlayerStatus.DEAD
        player.execution_day = self.game_state.day_number

        return True

    def get_player_by_name(self, name: str) -> Optional[Player]:
        """Get player by name"""

        if not self.game_state:
            return None

        for player in self.game_state.players:
            if player.name.lower() == name.lower():
                return player

        return None

    def check_win_condition(self) -> Optional[Tuple[str, str]]:
        """Check if game has ended. Returns (winning_team, reason) or None"""

        if not self.game_state:
            return None

        alive_players = [p for p in self.game_state.players if p.is_alive()]

        # Check if demon is dead
        demon_alive = any(p.character in self.script.DEMONS for p in alive_players)

        if not demon_alive:
            return ("good", "The demon has been eliminated!")

        # Check evil majority (2 or fewer players left)
        if len(alive_players) <= 2:
            return ("evil", "Evil has achieved majority!")

        # Check Saint execution (special loss condition)
        for player in self.game_state.players:
            if (
                player.character == "Saint"
                and player.status == PlayerStatus.DEAD
                and hasattr(player, "execution_day")
                and player.execution_day is not None
            ):
                return ("evil", "The Saint was executed!")

        return None

    def get_alive_players(self) -> List[Player]:
        """Get all alive players"""

        if not self.game_state:
            return []

        return [p for p in self.game_state.players if p.is_alive()]

    def get_evil_players(self) -> List[Player]:
        """Get all evil players (demons and minions)"""

        if not self.game_state:
            return []

        evil_characters = self.script.DEMONS + self.script.MINIONS
        return [p for p in self.game_state.players if p.character in evil_characters]

    def get_good_players(self) -> List[Player]:
        """Get all good players (townsfolk and outsiders)"""

        if not self.game_state:
            return []

        good_characters = self.script.TOWNSFOLK + self.script.OUTSIDERS
        return [p for p in self.game_state.players if p.character in good_characters]

    def is_character_in_play(self, character: str) -> bool:
        """Check if a character is in the current game"""

        if not self.game_state:
            return False

        return any(p.character == character for p in self.game_state.players)


# Example usage and testing
def create_mvp_game() -> GameEngine:
    """Create a sample MVP game for testing"""

    engine = GameEngine()

    # Create 7-player game
    player_names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace"]
    game_state = engine.create_game(player_names)

    print("=== MVP Game Created ===")
    print(f"Players: {len(game_state.players)}")
    print(f"Script: {game_state.script_name}")

    for player in game_state.players:
        print(f"  {player.name}: {player.character}")

    if hasattr(game_state, "demon_bluffs"):
        print(f"Demon bluffs: {game_state.demon_bluffs}")

    return engine


if __name__ == "__main__":
    # Test MVP game creation
    engine = create_mvp_game()

    # Test night order
    engine.start_game()
    print(f"\nFirst night order: {engine.get_night_order(is_first_night=True)}")

    # Test win condition
    win_condition = engine.check_win_condition()
    print(f"Win condition: {win_condition}")
