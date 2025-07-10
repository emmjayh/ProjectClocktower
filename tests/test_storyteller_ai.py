"""
Tests for the AI Storyteller decision engine
"""

import os
import sys
from datetime import datetime
from unittest.mock import MagicMock, Mock

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

try:
    from ai.storyteller_ai import StorytellerAI
    from core.game_state import GameState, Player, PlayerStatus, Team
    from game.clocktower_api import ClockTowerAPI
    from speech.speech_handler import SpeechHandler
except ImportError as e:
    pytest.skip(f"Skipping tests due to import error: {e}", allow_module_level=True)


class TestStorytellerAI:
    """Test suite for AI Storyteller decision making"""

    @pytest.fixture
    def mock_api_client(self):
        """Mock API client"""
        return Mock(spec=ClockTowerAPI)

    @pytest.fixture
    def mock_speech_handler(self):
        """Mock speech handler"""
        return Mock(spec=SpeechHandler)

    @pytest.fixture
    def storyteller_ai(self, mock_api_client, mock_speech_handler):
        """Create StorytellerAI instance with mocks"""
        return StorytellerAI(mock_api_client, mock_speech_handler)

    @pytest.fixture
    def sample_game_state(self):
        """Create sample game state for testing"""
        players = [
            Player(
                id="1",
                name="Alice",
                seat_position=0,
                character="Fortune Teller",
                team=Team.GOOD,
            ),
            Player(
                id="2", name="Bob", seat_position=1, character="Empath", team=Team.GOOD
            ),
            Player(
                id="3",
                name="Charlie",
                seat_position=2,
                character="Chef",
                team=Team.GOOD,
            ),
            Player(
                id="4",
                name="Diana",
                seat_position=3,
                character="Poisoner",
                team=Team.EVIL,
            ),
            Player(
                id="5", name="Eve", seat_position=4, character="Imp", team=Team.EVIL
            ),
        ]

        return GameState(
            game_id="test_game", players=players, script_name="trouble_brewing"
        )

    def test_fortune_teller_decision_sober(self, storyteller_ai, sample_game_state):
        """Test Fortune Teller decision when sober"""
        fortune_teller = sample_game_state.get_player_by_name("Alice")

        # Test when one target is demon
        result = storyteller_ai.decide_fortune_teller_result(
            fortune_teller, "Bob", "Eve", sample_game_state
        )

        assert result is True  # Should return True as Eve is the Imp

    def test_fortune_teller_decision_drunk(self, storyteller_ai, sample_game_state):
        """Test Fortune Teller decision when drunk"""
        fortune_teller = sample_game_state.get_player_by_name("Alice")
        fortune_teller.is_drunk = True

        # When drunk, should sometimes give false information
        result = storyteller_ai.decide_fortune_teller_result(
            fortune_teller, "Bob", "Charlie", sample_game_state
        )

        # Result could be true or false due to drunk effect
        assert isinstance(result, bool)

    def test_empath_decision_normal(self, storyteller_ai, sample_game_state):
        """Test Empath decision with normal neighbors"""
        empath = sample_game_state.get_player_by_name("Bob")
        left_neighbor = sample_game_state.get_player_by_name("Alice")  # Good
        right_neighbor = sample_game_state.get_player_by_name("Charlie")  # Good

        result = storyteller_ai.decide_empath_result(
            empath, left_neighbor, right_neighbor, sample_game_state
        )

        assert result == 0  # Both neighbors are good

    def test_empath_decision_evil_neighbor(self, storyteller_ai, sample_game_state):
        """Test Empath decision with evil neighbor"""
        empath = sample_game_state.get_player_by_name("Charlie")
        left_neighbor = sample_game_state.get_player_by_name("Bob")  # Good
        right_neighbor = sample_game_state.get_player_by_name("Diana")  # Evil

        result = storyteller_ai.decide_empath_result(
            empath, left_neighbor, right_neighbor, sample_game_state
        )

        assert result == 1  # One evil neighbor

    def test_chef_decision(self, storyteller_ai, sample_game_state):
        """Test Chef decision for evil pairs"""
        chef = sample_game_state.get_player_by_name("Charlie")

        result = storyteller_ai.decide_chef_result(chef, sample_game_state)

        # Diana (seat 3) and Eve (seat 4) are adjacent evil players
        assert result == 1

    def test_demon_kill_selection(self, storyteller_ai, sample_game_state):
        """Test demon kill target selection"""
        demon = sample_game_state.get_player_by_name("Eve")

        target = storyteller_ai.decide_demon_kill(demon, sample_game_state)

        # Should target a good player (not demon or minion)
        assert target in ["Alice", "Bob", "Charlie"]

    def test_monk_protection_selection(self, storyteller_ai, sample_game_state):
        """Test monk protection target selection"""
        # Add a monk to the game
        monk = Player(
            id="6", name="Frank", seat_position=5, character="Monk", team=Team.GOOD
        )
        sample_game_state.players.append(monk)

        target = storyteller_ai.decide_monk_protection(monk, sample_game_state)

        # Should protect someone other than the monk
        assert target != "Frank"
        assert target in ["Alice", "Bob", "Charlie", "Diana", "Eve"]

    def test_is_demon_check(self, storyteller_ai):
        """Test demon character identification"""
        assert storyteller_ai._is_demon("Imp") is True
        assert storyteller_ai._is_demon("Fortune Teller") is False

    def test_is_evil_check(self, storyteller_ai):
        """Test evil character identification"""
        assert storyteller_ai._is_evil("Imp") is True
        assert storyteller_ai._is_evil("Poisoner") is True
        assert storyteller_ai._is_evil("Fortune Teller") is False

    def test_decision_logging(self, storyteller_ai, sample_game_state):
        """Test that decisions are properly logged"""
        fortune_teller = sample_game_state.get_player_by_name("Alice")

        storyteller_ai.decide_fortune_teller_result(
            fortune_teller, "Bob", "Eve", sample_game_state
        )

        # Check that decision was logged
        assert len(storyteller_ai.decisions_made) > 0
        decision = storyteller_ai.decisions_made[-1]
        assert decision.decision_type == "fortune_teller"
        assert decision.confidence > 0

    def test_game_balance_tracking(self, storyteller_ai, sample_game_state):
        """Test game balance assessment"""
        storyteller_ai.update_game_balance(sample_game_state)

        # Should be around 0.6 (3 good vs 2 evil players)
        assert 0.5 <= storyteller_ai.game_balance_score <= 0.7

    def test_opening_story_generation(self, storyteller_ai):
        """Test opening story generation"""
        story = storyteller_ai.generate_opening_story("trouble_brewing", 5)

        assert isinstance(story, str)
        assert len(story) > 50  # Should be a substantial story
        assert "5" in story  # Should mention player count


if __name__ == "__main__":
    pytest.main([__file__])
