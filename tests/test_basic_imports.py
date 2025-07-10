"""
Test basic imports work without heavy dependencies
"""

import pytest


def test_core_imports():
    """Test that core modules can be imported"""
    # These should always work
    from src.core import game_state
    from src.core import ai_storyteller
    
    # Basic game modules
    from src.game import rule_engine
    from src.game import clocktower_api
    
    # GUI modules
    from src.gui import main_window
    
    assert True  # If we get here, imports worked


def test_speech_dependencies_module():
    """Test that audio dependencies module works safely"""
    from src.speech.audio_dependencies import DEPENDENCIES, check_continuous_listening_support
    
    # Should always work regardless of available dependencies
    assert isinstance(DEPENDENCIES, dict)
    
    support = check_continuous_listening_support()
    assert isinstance(support, dict)
    assert "supported" in support


def test_audio_modules_safe_import():
    """Test that audio modules can be imported safely even without dependencies"""
    # These should not fail even if audio dependencies are missing
    from src.speech import continuous_listener
    from src.speech import speaker_identification
    from src.speech import enhanced_tts
    from src.game import live_game_monitor
    
    # Basic instantiation should work (even if features are disabled)
    config = continuous_listener.ListenerConfig()
    assert config.sample_rate == 16000


@pytest.mark.asyncio
async def test_async_functionality():
    """Test basic async functionality"""
    # Simple async test
    result = await dummy_async_function()
    assert result == "test"


async def dummy_async_function():
    """Dummy async function for testing"""
    return "test"