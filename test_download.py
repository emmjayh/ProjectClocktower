#!/usr/bin/env python3
"""Test script to debug model downloads"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.speech.speech_handler import ModelDownloader

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


async def test_download():
    """Test the download process with detailed logging"""

    # Create models directory if it doesn't exist
    models_dir = Path(__file__).parent / "models"
    models_dir.mkdir(exist_ok=True)

    print(f"Models directory: {models_dir}")
    print(f"Models directory exists: {models_dir.exists()}")

    # Create downloader
    downloader = ModelDownloader(str(models_dir))

    # Check what's already in models directory
    print("\nChecking existing files in models directory:")
    if models_dir.exists():
        for item in models_dir.iterdir():
            print(f"  - {item.name}")
    else:
        print("  Models directory doesn't exist yet")

    # Test Whisper download
    print("\n=== Testing Whisper Download ===")

    def whisper_progress(msg, percent=None):
        if percent is not None:
            print(f"[{percent:3.0f}%] {msg}")
        else:
            print(f"[---] {msg}")

    try:
        # Check if whisper model already exists
        whisper_dir = models_dir / "whisper_base"
        print(f"Whisper directory: {whisper_dir}")
        print(f"Whisper directory exists: {whisper_dir.exists()}")

        if whisper_dir.exists():
            print("Contents of whisper directory:")
            for item in whisper_dir.iterdir():
                print(f"  - {item.name} ({item.stat().st_size / 1024 / 1024:.1f} MB)")

        success = await downloader.download_whisper_model("base", whisper_progress)
        print(f"Whisper download success: {success}")

    except Exception as e:
        print(f"Whisper download error: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()

    # Test Piper download
    print("\n=== Testing Piper Download ===")

    def piper_progress(msg, percent=None):
        if percent is not None:
            print(f"[{percent:3.0f}%] {msg}")
        else:
            print(f"[---] {msg}")

    try:
        # Check if piper voice already exists
        voice_name = "en_US-lessac-medium"
        piper_dir = models_dir / "piper" / voice_name
        print(f"Piper voice directory: {piper_dir}")
        print(f"Piper voice directory exists: {piper_dir.exists()}")

        if piper_dir.exists():
            print("Contents of piper voice directory:")
            for item in piper_dir.iterdir():
                print(f"  - {item.name} ({item.stat().st_size / 1024 / 1024:.1f} MB)")

        success = await downloader.download_piper_voice(voice_name, piper_progress)
        print(f"Piper download success: {success}")

    except Exception as e:
        print(f"Piper download error: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()

    # Check final state
    print("\n=== Final State ===")
    print("Contents of models directory:")
    for item in models_dir.iterdir():
        print(f"  - {item.name}")
        if item.is_dir():
            for subitem in item.iterdir():
                print(f"    - {subitem.name}")


if __name__ == "__main__":
    asyncio.run(test_download())
