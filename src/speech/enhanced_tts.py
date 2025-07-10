"""
Enhanced Text-to-Speech with OpenAI TTS support
Provides higher quality speech synthesis options
"""

import asyncio
import io
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

# Optional dependencies
try:
    import pygame
except ImportError:
    pygame = None

try:
    import requests
except ImportError:
    requests = None


class OpenAITTS:
    """OpenAI Text-to-Speech API integration"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.logger = logging.getLogger(__name__)

        # Available voices
        self.voices = {
            "alloy": "Neutral, balanced voice",
            "echo": "Male voice with clarity",
            "fable": "British accent, expressive",
            "onyx": "Deep male voice",
            "nova": "Young female voice",
            "shimmer": "Soft female voice",
        }

        # Initialize pygame mixer for audio playback
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        except pygame.error as e:
            self.logger.warning(f"Could not initialize pygame mixer: {e}")

    def is_available(self) -> bool:
        """Check if OpenAI TTS is available"""
        return self.api_key is not None

    async def speak(self, text: str, voice: str = "alloy", speed: float = 1.0) -> bool:
        """Generate speech using OpenAI TTS"""
        if not self.is_available():
            self.logger.error("OpenAI API key not available")
            return False

        try:
            self.logger.info(f"Generating speech with OpenAI TTS: {text[:50]}...")

            # Call OpenAI TTS API
            response = await self._generate_speech(text, voice, speed)

            if response:
                # Play the audio
                await self._play_audio_bytes(response)
                return True

        except Exception as e:
            self.logger.error(f"OpenAI TTS failed: {e}")

        return False

    async def _generate_speech(
        self, text: str, voice: str, speed: float
    ) -> Optional[bytes]:
        """Generate speech audio bytes"""
        url = "https://api.openai.com/v1/audio/speech"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": "tts-1-hd",  # High quality model
            "input": text,
            "voice": voice,
            "speed": speed,
        }

        try:
            # Make async request
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, lambda: requests.post(url, headers=headers, json=data, timeout=30)
            )

            if response.status_code == 200:
                return response.content
            else:
                self.logger.error(
                    f"OpenAI API error: {response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            return None

    async def _play_audio_bytes(self, audio_bytes: bytes):
        """Play audio from bytes using pygame"""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                temp_file.write(audio_bytes)
                temp_path = temp_file.name

            try:
                # Load and play with pygame
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.play()

                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.1)

            finally:
                # Clean up
                try:
                    pygame.mixer.music.stop()
                    os.unlink(temp_path)
                except:
                    pass

        except Exception as e:
            self.logger.error(f"Audio playback failed: {e}")


class EnhancedNominationHandler:
    """Enhanced nomination handling with better speech processing"""

    def __init__(
        self, use_openai_tts: bool = False, openai_api_key: Optional[str] = None
    ):
        self.logger = logging.getLogger(__name__)
        self.use_openai_tts = use_openai_tts

        # Initialize TTS
        if use_openai_tts:
            self.tts = OpenAITTS(openai_api_key)
            if not self.tts.is_available():
                self.logger.warning("OpenAI TTS not available, falling back to Piper")
                self.use_openai_tts = False

        # Nomination patterns for better recognition
        self.nomination_patterns = [
            r"i nominate (\w+)",
            r"nominate (\w+)",
            r"i vote to nominate (\w+)",
            r"(\w+) is my nomination",
            r"my nomination is (\w+)",
        ]

        # Response templates
        self.responses = {
            "nomination_received": [
                "{nominator} nominates {nominee}.",
                "{nominee} has been nominated by {nominator}.",
                "We have a nomination: {nominator} nominates {nominee}.",
            ],
            "invalid_nomination": [
                "That nomination is not valid.",
                "Sorry, {nominee} cannot be nominated right now.",
                "That player is not available for nomination.",
            ],
            "call_for_nominations": [
                "Nominations are now open. Who would you like to nominate?",
                "The nomination phase begins now. Please make your nominations.",
                "Time for nominations. Speak up if you wish to nominate someone.",
            ],
        }

    async def process_nomination_speech(
        self, speech_text: str, active_players: list
    ) -> Dict[str, Any]:
        """Process speech for nomination commands with improved parsing"""
        import re

        speech_lower = speech_text.lower().strip()
        self.logger.info(f"Processing nomination speech: '{speech_text}'")

        # Try different patterns
        for pattern in self.nomination_patterns:
            match = re.search(pattern, speech_lower)
            if match:
                nominee_name = match.group(1).title()

                # Find closest matching player name
                nominee = self._find_closest_player(nominee_name, active_players)

                if nominee:
                    return {
                        "type": "nomination",
                        "nominee": nominee,
                        "nominator": "Unknown",  # Would need speaker ID
                        "raw_text": speech_text,
                        "confidence": 0.8,  # Could be improved with better matching
                    }

        return {"type": "unknown", "raw_text": speech_text}

    def _find_closest_player(
        self, spoken_name: str, active_players: list
    ) -> Optional[str]:
        """Find the closest matching player name"""
        from difflib import SequenceMatcher

        best_match = None
        best_score = 0.6  # Minimum similarity threshold

        for player in active_players:
            if not isinstance(player, str):
                player_name = player.get("name", str(player))
            else:
                player_name = player

            # Check exact match first
            if spoken_name.lower() == player_name.lower():
                return player_name

            # Check similarity
            similarity = SequenceMatcher(
                None, spoken_name.lower(), player_name.lower()
            ).ratio()
            if similarity > best_score:
                best_score = similarity
                best_match = player_name

        return best_match

    async def announce_nomination(
        self, nominator: str, nominee: str, voice: str = "alloy"
    ):
        """Announce a nomination with enhanced TTS"""
        import random

        template = random.choice(self.responses["nomination_received"])
        message = template.format(nominator=nominator, nominee=nominee)

        if self.use_openai_tts and self.tts.is_available():
            self.logger.info(f"Using OpenAI TTS for: {message}")
            success = await self.tts.speak(message, voice=voice, speed=0.9)
            if success:
                return True

        # Fallback to basic announcement
        self.logger.info(f"Announcement: {message}")
        return False

    async def call_for_nominations(self, voice: str = "alloy"):
        """Call for nominations with enhanced TTS"""
        import random

        message = random.choice(self.responses["call_for_nominations"])

        if self.use_openai_tts and self.tts.is_available():
            success = await self.tts.speak(message, voice=voice, speed=0.9)
            if success:
                return True

        # Fallback
        self.logger.info(f"Call for nominations: {message}")
        return False


# Example usage and testing
async def test_enhanced_nominations():
    """Test the enhanced nomination system"""
    # Test without OpenAI (fallback mode)
    handler = EnhancedNominationHandler(use_openai_tts=False)

    test_players = ["Alice", "Bob", "Charlie", "Diana", "Edward"]

    test_speeches = [
        "I nominate Alice",
        "nominate bob please",
        "I vote to nominate charlie",
        "Diana is my nomination",
        "my nomination is ed",  # Should match "Edward"
        "let's vote for alice",  # Should not match
    ]

    print("Testing nomination speech processing:")
    for speech in test_speeches:
        result = await handler.process_nomination_speech(speech, test_players)
        print(f"'{speech}' -> {result}")

    # Test announcements
    await handler.call_for_nominations()
    await handler.announce_nomination("Alice", "Bob")


if __name__ == "__main__":
    asyncio.run(test_enhanced_nominations())
