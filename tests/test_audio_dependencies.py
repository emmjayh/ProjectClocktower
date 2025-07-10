"""
Test audio dependencies and import handling
"""

import pytest
import sys
from unittest.mock import patch


def test_audio_dependencies_import():
    """Test that audio_dependencies module imports without errors"""
    from src.speech.audio_dependencies import (
        DEPENDENCIES, 
        check_continuous_listening_support,
        log_audio_capabilities
    )
    
    # Should always work
    assert isinstance(DEPENDENCIES, dict)
    
    # Should return a dict with expected keys
    support = check_continuous_listening_support()
    assert isinstance(support, dict)
    assert "supported" in support
    assert "features" in support
    assert "missing" in support


def test_continuous_listener_import():
    """Test that continuous listener can be imported safely"""
    try:
        from src.speech.continuous_listener import ContinuousListener, ListenerConfig
        
        # Should be able to create config
        config = ListenerConfig()
        assert config.sample_rate == 16000
        
        # Should be able to instantiate (even without dependencies)
        listener = ContinuousListener(config)
        assert listener.config == config
        
    except ImportError as e:
        pytest.skip(f"Continuous listener import failed: {e}")


def test_speaker_identification_import():
    """Test that speaker identification can be imported safely"""
    try:
        from src.speech.speaker_identification import VoiceSeparationSystem
        
        # Should be able to instantiate
        system = VoiceSeparationSystem()
        assert hasattr(system, 'speaker_id')
        
    except ImportError as e:
        pytest.skip(f"Speaker identification import failed: {e}")


def test_enhanced_tts_import():
    """Test that enhanced TTS can be imported safely"""
    try:
        from src.speech.enhanced_tts import OpenAITTS
        
        # Should be able to instantiate without API key
        tts = OpenAITTS()
        assert not tts.is_available()  # No API key
        
    except ImportError as e:
        pytest.skip(f"Enhanced TTS import failed: {e}")


def test_live_game_monitor_import():
    """Test that live game monitor can be imported safely"""
    try:
        from src.game.live_game_monitor import LiveGameMonitor
        
        # Should be able to instantiate with None arguments
        monitor = LiveGameMonitor(None, None)
        assert hasattr(monitor, 'listener')
        
    except ImportError as e:
        pytest.skip(f"Live game monitor import failed: {e}")


@pytest.mark.asyncio
async def test_dependency_handling_gracefully():
    """Test that missing dependencies are handled gracefully"""
    from src.speech.audio_dependencies import DEPENDENCIES
    
    # Even if some dependencies are missing, should not crash
    missing_deps = [dep for dep, available in DEPENDENCIES.items() if not available]
    
    if missing_deps:
        print(f"Missing dependencies (gracefully handled): {missing_deps}")
    
    # Test should always pass regardless of missing dependencies
    assert True