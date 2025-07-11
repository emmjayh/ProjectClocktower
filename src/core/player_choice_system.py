"""
Player Choice System for Night Actions
Handles capturing player decisions during night phases
"""

import asyncio
from dataclasses import dataclass
from typing import Dict, List, Optional, Union, Callable, Any
from enum import Enum

from .game_state import Player


class ChoiceType(Enum):
    SINGLE_TARGET = "single_target"  # Choose 1 player
    DUAL_TARGET = "dual_target"  # Choose 2 players
    NO_CHOICE = "no_choice"  # No choice needed
    YES_NO = "yes_no"  # Yes/No decision


@dataclass
class ChoiceRequest:
    """A request for a player to make a choice"""

    player_name: str
    character: str
    choice_type: ChoiceType
    prompt: str
    valid_targets: List[str] = None
    timeout_seconds: int = 30

    def __post_init__(self):
        if self.valid_targets is None:
            self.valid_targets = []


@dataclass
class ChoiceResult:
    """Result of a player choice"""

    player_name: str
    character: str
    choice_type: ChoiceType
    targets: List[str] = None
    yes_no_answer: Optional[bool] = None
    is_valid: bool = True
    error_message: str = ""

    def __post_init__(self):
        if self.targets is None:
            self.targets = []


class PlayerChoiceSystem:
    """Manages player choices during night actions"""

    def __init__(self):
        self.pending_choices: Dict[str, ChoiceRequest] = {}
        self.choice_results: Dict[str, ChoiceResult] = {}
        self.choice_callbacks: Dict[str, Callable] = {}

    def request_choice(
        self,
        request: ChoiceRequest,
        callback: Optional[Callable[[ChoiceResult], None]] = None,
    ) -> str:
        """Request a choice from a player"""

        choice_id = (
            f"{request.player_name}_{request.character}_{len(self.pending_choices)}"
        )

        self.pending_choices[choice_id] = request
        if callback:
            self.choice_callbacks[choice_id] = callback

        return choice_id

    def submit_choice(self, choice_id: str, **kwargs) -> bool:
        """Submit a choice for a pending request"""

        if choice_id not in self.pending_choices:
            return False

        request = self.pending_choices[choice_id]
        result = self._validate_choice(request, kwargs)

        self.choice_results[choice_id] = result

        # Call callback if provided
        if choice_id in self.choice_callbacks:
            self.choice_callbacks[choice_id](result)
            del self.choice_callbacks[choice_id]

        # Remove pending choice
        del self.pending_choices[choice_id]

        return result.is_valid

    def _validate_choice(
        self, request: ChoiceRequest, choice_data: Dict[str, Any]
    ) -> ChoiceResult:
        """Validate a player's choice"""

        result = ChoiceResult(
            player_name=request.player_name,
            character=request.character,
            choice_type=request.choice_type,
        )

        if request.choice_type == ChoiceType.SINGLE_TARGET:
            target = choice_data.get("target")
            if not target:
                result.is_valid = False
                result.error_message = "No target selected"
            elif target not in request.valid_targets:
                result.is_valid = False
                result.error_message = f"Invalid target: {target}"
            else:
                result.targets = [target]

        elif request.choice_type == ChoiceType.DUAL_TARGET:
            target1 = choice_data.get("target1")
            target2 = choice_data.get("target2")

            if not target1 or not target2:
                result.is_valid = False
                result.error_message = "Must select 2 targets"
            elif target1 == target2:
                result.is_valid = False
                result.error_message = "Cannot select same target twice"
            elif (
                target1 not in request.valid_targets
                or target2 not in request.valid_targets
            ):
                result.is_valid = False
                result.error_message = "Invalid target selected"
            else:
                result.targets = [target1, target2]

        elif request.choice_type == ChoiceType.YES_NO:
            answer = choice_data.get("answer")
            if answer is None:
                result.is_valid = False
                result.error_message = "Must provide yes/no answer"
            else:
                result.yes_no_answer = bool(answer)

        elif request.choice_type == ChoiceType.NO_CHOICE:
            # No validation needed
            pass

        return result

    def get_pending_choices(self) -> List[ChoiceRequest]:
        """Get all pending choice requests"""
        return list(self.pending_choices.values())

    def clear_completed_choices(self):
        """Clear completed choice results"""
        self.choice_results.clear()


class MVPChoiceTemplates:
    """Pre-defined choice templates for MVP characters"""

    @staticmethod
    def fortune_teller_choice(
        player: Player, valid_targets: List[str]
    ) -> ChoiceRequest:
        """Fortune Teller choice template"""
        return ChoiceRequest(
            player_name=player.name,
            character="Fortune Teller",
            choice_type=ChoiceType.DUAL_TARGET,
            prompt="Choose 2 players to learn about:",
            valid_targets=valid_targets,
            timeout_seconds=45,
        )

    @staticmethod
    def empath_choice(player: Player) -> ChoiceRequest:
        """Empath choice template (no choice needed)"""
        return ChoiceRequest(
            player_name=player.name,
            character="Empath",
            choice_type=ChoiceType.NO_CHOICE,
            prompt="Learning about your neighbors...",
            timeout_seconds=5,
        )

    @staticmethod
    def poisoner_choice(player: Player, valid_targets: List[str]) -> ChoiceRequest:
        """Poisoner choice template"""
        return ChoiceRequest(
            player_name=player.name,
            character="Poisoner",
            choice_type=ChoiceType.SINGLE_TARGET,
            prompt="Choose a player to poison:",
            valid_targets=valid_targets,
            timeout_seconds=30,
        )

    @staticmethod
    def imp_choice(player: Player, valid_targets: List[str]) -> ChoiceRequest:
        """Imp choice template"""
        return ChoiceRequest(
            player_name=player.name,
            character="Imp",
            choice_type=ChoiceType.SINGLE_TARGET,
            prompt="Choose a player to kill (or yourself to starpass):",
            valid_targets=valid_targets,
            timeout_seconds=30,
        )


# Simple implementation for MVP (command-line interface)
class SimpleCommandLineChoices:
    """Simple command-line interface for player choices"""

    def __init__(self):
        self.choice_system = PlayerChoiceSystem()

    async def request_choice_async(self, request: ChoiceRequest) -> ChoiceResult:
        """Request a choice with command-line interface"""

        print(f"\n=== {request.player_name} ({request.character}) ===")
        print(request.prompt)

        if request.choice_type == ChoiceType.SINGLE_TARGET:
            return await self._get_single_target(request)
        elif request.choice_type == ChoiceType.DUAL_TARGET:
            return await self._get_dual_target(request)
        elif request.choice_type == ChoiceType.YES_NO:
            return await self._get_yes_no(request)
        else:
            return ChoiceResult(
                player_name=request.player_name,
                character=request.character,
                choice_type=request.choice_type,
                is_valid=True,
            )

    async def _get_single_target(self, request: ChoiceRequest) -> ChoiceResult:
        """Get single target choice"""

        print("Valid targets:", ", ".join(request.valid_targets))

        while True:
            target = input(f"Choose target: ").strip()

            if target in request.valid_targets:
                return ChoiceResult(
                    player_name=request.player_name,
                    character=request.character,
                    choice_type=request.choice_type,
                    targets=[target],
                    is_valid=True,
                )
            else:
                print(f"Invalid target '{target}'. Try again.")

    async def _get_dual_target(self, request: ChoiceRequest) -> ChoiceResult:
        """Get dual target choice"""

        print("Valid targets:", ", ".join(request.valid_targets))

        while True:
            target1 = input("Choose first target: ").strip()
            target2 = input("Choose second target: ").strip()

            if target1 not in request.valid_targets:
                print(f"Invalid first target '{target1}'. Try again.")
                continue
            if target2 not in request.valid_targets:
                print(f"Invalid second target '{target2}'. Try again.")
                continue
            if target1 == target2:
                print("Cannot choose same target twice. Try again.")
                continue

            return ChoiceResult(
                player_name=request.player_name,
                character=request.character,
                choice_type=request.choice_type,
                targets=[target1, target2],
                is_valid=True,
            )

    async def _get_yes_no(self, request: ChoiceRequest) -> ChoiceResult:
        """Get yes/no choice"""

        while True:
            answer = input("(y/n): ").strip().lower()

            if answer in ["y", "yes", "true", "1"]:
                return ChoiceResult(
                    player_name=request.player_name,
                    character=request.character,
                    choice_type=request.choice_type,
                    yes_no_answer=True,
                    is_valid=True,
                )
            elif answer in ["n", "no", "false", "0"]:
                return ChoiceResult(
                    player_name=request.player_name,
                    character=request.character,
                    choice_type=request.choice_type,
                    yes_no_answer=False,
                    is_valid=True,
                )
            else:
                print("Please enter y/n")


# Mock implementation for testing
class MockPlayerChoices:
    """Mock player choices for automated testing"""

    def __init__(self, mock_choices: Dict[str, Any] = None):
        self.mock_choices = mock_choices or {}
        self.choice_system = PlayerChoiceSystem()

    async def request_choice_async(self, request: ChoiceRequest) -> ChoiceResult:
        """Mock choice request with predefined answers"""

        # Check if we have a mock choice for this player/character
        key = f"{request.player_name}_{request.character}"
        if key in self.mock_choices:
            choice_data = self.mock_choices[key]
            return self.choice_system._validate_choice(request, choice_data)

        # Default choices for testing
        if request.choice_type == ChoiceType.SINGLE_TARGET and request.valid_targets:
            return ChoiceResult(
                player_name=request.player_name,
                character=request.character,
                choice_type=request.choice_type,
                targets=[request.valid_targets[0]],  # Choose first available
                is_valid=True,
            )
        elif (
            request.choice_type == ChoiceType.DUAL_TARGET
            and len(request.valid_targets) >= 2
        ):
            return ChoiceResult(
                player_name=request.player_name,
                character=request.character,
                choice_type=request.choice_type,
                targets=[request.valid_targets[0], request.valid_targets[1]],
                is_valid=True,
            )
        elif request.choice_type == ChoiceType.YES_NO:
            return ChoiceResult(
                player_name=request.player_name,
                character=request.character,
                choice_type=request.choice_type,
                yes_no_answer=True,  # Default to yes
                is_valid=True,
            )
        else:
            return ChoiceResult(
                player_name=request.player_name,
                character=request.character,
                choice_type=request.choice_type,
                is_valid=True,
            )


if __name__ == "__main__":
    # Test the choice system
    import asyncio

    async def test_choices():
        # Create mock players
        players = ["Alice", "Bob", "Charlie", "Diana"]

        # Test Fortune Teller choice
        ft_request = MVPChoiceTemplates.fortune_teller_choice(
            Player("1", "Alice", 0, "Fortune Teller"), players[1:]  # Can't target self
        )

        # Test with mock choices
        mock_system = MockPlayerChoices(
            {"Alice_Fortune Teller": {"target1": "Bob", "target2": "Charlie"}}
        )

        result = await mock_system.request_choice_async(ft_request)
        print(f"Fortune Teller choice: {result.targets} (Valid: {result.is_valid})")

        # Test Poisoner choice
        poisoner_request = MVPChoiceTemplates.poisoner_choice(
            Player("2", "Frank", 5, "Poisoner"), players  # Can target anyone
        )

        result2 = await mock_system.request_choice_async(poisoner_request)
        print(f"Poisoner choice: {result2.targets} (Valid: {result2.is_valid})")

    asyncio.run(test_choices())
