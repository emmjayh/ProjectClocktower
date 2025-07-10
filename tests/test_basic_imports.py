"""
Test basic imports work without heavy dependencies
"""

import pytest


def test_core_imports():
    """Test that core modules can be imported"""
    # These should always work
    from src.core import ai_storyteller, game_state

    # Basic game modules
    from src.game import clocktower_api, rule_engine

    # GUI modules require tkinter which isn't available in CI
    # Test them only if tkinter is available
    try:
        import tkinter

        from src.gui import main_window
    except ImportError:
        # Skip GUI tests in environments without tkinter
        pass

    assert True  # If we get here, imports worked


def test_speech_dependencies_module():
    """Test that audio dependencies module works safely"""
    from src.speech.audio_dependencies import (
        DEPENDENCIES,
        check_continuous_listening_support,
    )

    # Should always work regardless of available dependencies
    assert isinstance(DEPENDENCIES, dict)

    support = check_continuous_listening_support()
    assert isinstance(support, dict)
    assert "supported" in support


def test_audio_modules_safe_import():
    """Test that audio modules can be imported safely even without dependencies"""
    # These should not fail even if audio dependencies are missing
    from src.game import live_game_monitor
    from src.speech import continuous_listener, enhanced_tts, speaker_identification

    # Basic instantiation should work (even if features are disabled)
    config = continuous_listener.ListenerConfig()
    assert config.sample_rate == 16000


def test_async_functionality():
    """Test basic async functionality"""
    import asyncio

    async def dummy_async_function():
        """Dummy async function for testing"""
        return "test"

    # Simple async test
    result = asyncio.run(dummy_async_function())
    assert result == "test"
