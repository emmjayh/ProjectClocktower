"""
Audio Dependencies Checker
Checks for optional audio processing dependencies and provides fallbacks
"""

import logging
import os
from typing import Dict

logger = logging.getLogger(__name__)

# Track which dependencies are available
DEPENDENCIES = {
    "numpy": False,
    "pyaudio": False,
    "whisper": False,
    "librosa": False,
    "sklearn": False,
    "pygame": False,
    "requests": False,
}

# Check each dependency - skip in test environment

is_testing = any(
    x in os.environ.get("PYTEST_CURRENT_TEST", "") for x in ["test_", "pytest"]
) or "pytest" in os.environ.get("_", "")

if not is_testing:
    # Check each dependency
    try:
        import numpy as np

        DEPENDENCIES["numpy"] = True
    except ImportError:
        np = None

    try:
        import pyaudio

        DEPENDENCIES["pyaudio"] = True
    except ImportError:
        pyaudio = None

    try:
        import whisper

        DEPENDENCIES["whisper"] = True
    except ImportError:
        whisper = None

    try:
        import librosa

        DEPENDENCIES["librosa"] = True
    except ImportError:
        librosa = None

    try:
        from sklearn.cluster import KMeans
        from sklearn.preprocessing import StandardScaler

        DEPENDENCIES["sklearn"] = True
    except ImportError:
        KMeans = None
        StandardScaler = None

    try:
        import pygame

        DEPENDENCIES["pygame"] = True
    except ImportError:
        pygame = None

    try:
        import requests

        DEPENDENCIES["requests"] = True
    except ImportError:
        requests = None
else:
    # In testing - use None for everything
    np = None
    pyaudio = None
    whisper = None
    librosa = None
    KMeans = None
    StandardScaler = None
    pygame = None
    requests = None


def check_continuous_listening_support() -> Dict[str, bool]:
    """Check if continuous listening is supported"""
    required = ["numpy", "whisper"]
    optional = ["pyaudio", "librosa", "sklearn"]

    result = {
        "supported": all(DEPENDENCIES[dep] for dep in required),
        "features": {},
        "missing": [],
    }

    for dep in required + optional:
        result["features"][dep] = DEPENDENCIES[dep]
        if not DEPENDENCIES[dep]:
            result["missing"].append(dep)

    result["features"]["continuous_listening"] = (
        result["supported"] and DEPENDENCIES["pyaudio"]
    )
    result["features"]["speaker_identification"] = (
        result["supported"] and DEPENDENCIES["librosa"] and DEPENDENCIES["sklearn"]
    )
    result["features"]["enhanced_tts"] = (
        DEPENDENCIES["pygame"] and DEPENDENCIES["requests"]
    )

    return result


def log_audio_capabilities():
    """Log available audio capabilities"""
    support = check_continuous_listening_support()

    if support["supported"]:
        logger.info("✅ Audio processing core dependencies available")

        if support["features"]["continuous_listening"]:
            logger.info("✅ Continuous listening supported")
        else:
            logger.warning("⚠️ Continuous listening disabled (missing pyaudio)")

        if support["features"]["speaker_identification"]:
            logger.info("✅ Speaker identification supported")
        else:
            logger.warning(
                "⚠️ Speaker identification disabled (missing librosa/sklearn)"
            )

        if support["features"]["enhanced_tts"]:
            logger.info("✅ Enhanced TTS supported")
        else:
            logger.warning("⚠️ Enhanced TTS disabled (missing pygame/requests)")
    else:
        logger.error("❌ Audio processing not available - missing core dependencies")
        logger.error(f"Missing: {', '.join(support['missing'])}")


def require_dependency(name: str, feature_name: str = None):
    """Decorator to require a specific dependency"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            if not DEPENDENCIES.get(name, False):
                feature = feature_name or name
                raise ImportError(
                    f"{feature} requires {name} - install with: pip install {name}"
                )
            return func(*args, **kwargs)

        return wrapper

    return decorator


# Export available modules
__all__ = [
    "DEPENDENCIES",
    "check_continuous_listening_support",
    "log_audio_capabilities",
    "require_dependency",
    "np",
    "pyaudio",
    "whisper",
    "librosa",
    "pygame",
    "requests",
    "KMeans",
    "StandardScaler",
]
