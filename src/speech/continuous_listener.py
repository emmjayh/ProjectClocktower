"""
Continuous Audio Monitoring System
Real-time detection of game commands during active conversation
"""

import asyncio
import collections
import logging
import os
import queue
import tempfile
import threading
import time
import wave
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

# Import dependencies through dependency checker
from .audio_dependencies import check_continuous_listening_support, np, pyaudio, whisper


@dataclass
class ListenerConfig:
    """Configuration for continuous listener"""

    sample_rate: int = 16000
    chunk_size: int = 1024
    channels: int = 1

    # Continuous listening settings
    window_duration: float = 3.0  # Seconds per processing window
    overlap_duration: float = 1.0  # Overlap between windows
    max_buffer_duration: float = 30.0  # Max audio buffer

    # Voice activity detection
    vad_threshold: float = 0.02
    min_speech_duration: float = 0.5
    max_silence_gap: float = 0.3

    # Wake word detection
    wake_words: List[str] = field(
        default_factory=lambda: [
            "nominate",
            "i nominate",
            "vote",
            "execution",
            "storyteller",
            "demon",
            "minion",
            "outsider",
            "townsfolk",
        ]
    )

    # Processing settings
    whisper_model: str = "large"
    confidence_threshold: float = 0.7


class AudioBuffer:
    """Circular buffer for continuous audio data"""

    def __init__(self, max_duration: float, sample_rate: int):
        self.max_samples = int(max_duration * sample_rate)
        self.buffer = collections.deque(maxlen=self.max_samples)
        self.sample_rate = sample_rate
        self.lock = threading.Lock()

    def add_chunk(self, chunk: bytes):
        """Add audio chunk to buffer"""
        with self.lock:
            # Convert bytes to numpy array
            audio_data = np.frombuffer(chunk, dtype=np.int16)
            self.buffer.extend(audio_data)

    def get_window(self, duration: float, offset: float = 0.0) -> Any:
        """Get audio window of specified duration"""
        with self.lock:
            samples_needed = int(duration * self.sample_rate)
            offset_samples = int(offset * self.sample_rate)

            if len(self.buffer) < samples_needed + offset_samples:
                return np.array([], dtype=np.int16)

            start_idx = len(self.buffer) - samples_needed - offset_samples
            end_idx = len(self.buffer) - offset_samples

            return np.array(list(self.buffer)[start_idx:end_idx], dtype=np.int16)


class VoiceActivityDetector:
    """Real-time voice activity detection"""

    def __init__(self, config: ListenerConfig):
        self.config = config
        self.energy_threshold = config.vad_threshold * 32768
        self.min_speech_frames = int(
            config.min_speech_duration * config.sample_rate / config.chunk_size
        )
        self.max_silence_frames = int(
            config.max_silence_gap * config.sample_rate / config.chunk_size
        )

        self.speech_frames = 0
        self.silence_frames = 0
        self.is_speaking = False

    def process_chunk(self, chunk: bytes) -> bool:
        """Process audio chunk and return if speech is detected"""
        audio_data = np.frombuffer(chunk, dtype=np.int16)
        energy = np.mean(np.abs(audio_data))

        if energy > self.energy_threshold:
            self.speech_frames += 1
            self.silence_frames = 0

            if self.speech_frames >= self.min_speech_frames:
                self.is_speaking = True
        else:
            self.silence_frames += 1

            if self.silence_frames >= self.max_silence_frames:
                self.speech_frames = 0
                if self.is_speaking:
                    self.is_speaking = False
                    return True  # End of speech detected

        return False


class ContinuousListener:
    """Continuous audio monitoring and command detection"""

    def __init__(self, config: ListenerConfig = None):
        self.config = config or ListenerConfig()
        self.logger = logging.getLogger(__name__)

        # Check if continuous listening is supported
        self.support = check_continuous_listening_support()
        if not self.support["supported"]:
            self.logger.warning(
                "Continuous listening not fully supported - some features disabled"
            )
            self.logger.warning(
                f"Missing dependencies: {', '.join(self.support['missing'])}"
            )

        # Audio components
        self.audio = None
        self.stream = None
        self.audio_buffer = AudioBuffer(
            self.config.max_buffer_duration, self.config.sample_rate
        )
        self.vad = VoiceActivityDetector(self.config)

        # Processing components
        self.whisper_model = None
        self.processing_queue = queue.Queue()
        self.command_callbacks = {}

        # Control flags
        self.listening = False
        self.processing = False

        # Threads
        self.audio_thread = None
        self.processing_thread = None

    async def initialize(self) -> bool:
        """Initialize the continuous listener"""
        try:
            self.logger.info("Initializing continuous listener...")

            # Initialize Whisper
            self.whisper_model = whisper.load_model(self.config.whisper_model)

            # Initialize PyAudio
            self.audio = pyaudio.PyAudio()

            self.logger.info("Continuous listener initialized")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize continuous listener: {e}")
            return False

    def register_command_callback(self, command_type: str, callback: Callable):
        """Register callback for specific command types"""
        self.command_callbacks[command_type] = callback

    def start_listening(self):
        """Start continuous audio monitoring"""
        if self.listening:
            return

        self.listening = True
        self.processing = True

        # Start audio capture thread
        self.audio_thread = threading.Thread(target=self._audio_capture_loop)
        self.audio_thread.daemon = True
        self.audio_thread.start()

        # Start processing thread
        self.processing_thread = threading.Thread(target=self._processing_loop)
        self.processing_thread.daemon = True
        self.processing_thread.start()

        self.logger.info("Started continuous listening")

    def stop_listening(self):
        """Stop continuous audio monitoring"""
        self.listening = False
        self.processing = False

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        if self.audio_thread:
            self.audio_thread.join(timeout=2.0)

        if self.processing_thread:
            self.processing_thread.join(timeout=2.0)

        self.logger.info("Stopped continuous listening")

    def _audio_capture_loop(self):
        """Main audio capture loop"""
        try:
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=self.config.channels,
                rate=self.config.sample_rate,
                input=True,
                frames_per_buffer=self.config.chunk_size,
                stream_callback=self._audio_callback,
            )

            self.stream.start_stream()

            while self.listening:
                time.sleep(0.1)

        except Exception as e:
            self.logger.error(f"Audio capture error: {e}")

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """PyAudio callback for real-time audio processing"""
        if self.listening:
            # Add to buffer
            self.audio_buffer.add_chunk(in_data)

            # Check for end of speech
            if self.vad.process_chunk(in_data):
                # Queue for processing
                try:
                    audio_window = self.audio_buffer.get_window(
                        self.config.window_duration
                    )
                    if len(audio_window) > 0:
                        self.processing_queue.put(audio_window, block=False)
                except queue.Full:
                    pass  # Skip if queue is full

        return (in_data, pyaudio.paContinue)

    def _processing_loop(self):
        """Main processing loop for speech recognition"""
        while self.processing:
            try:
                # Get audio from queue with timeout
                audio_data = self.processing_queue.get(timeout=1.0)

                # Process with Whisper
                command = self._process_audio_window(audio_data)

                if command:
                    # Handle command
                    asyncio.create_task(self._handle_command(command))

            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Processing error: {e}")

    def _process_audio_window(self, audio_data: Any) -> Optional[Dict[str, Any]]:
        """Process audio window with Whisper"""
        try:
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                self._save_audio_array(audio_data, temp_file.name)

                # Transcribe
                result = self.whisper_model.transcribe(temp_file.name, language="en")

                text = result["text"].strip()
                confidence = result.get("confidence", 0.0)

                os.unlink(temp_file.name)

            if not text or confidence < self.config.confidence_threshold:
                return None

            # Check for wake words
            text_lower = text.lower()
            detected_wake_words = [w for w in self.config.wake_words if w in text_lower]

            if not detected_wake_words:
                return None

            # Parse command
            command = self._parse_command(text, detected_wake_words)

            if command:
                self.logger.info(f"Detected command: {command}")
                return command

        except Exception as e:
            self.logger.error(f"Audio processing error: {e}")

        return None

    def _parse_command(
        self, text: str, wake_words: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Parse recognized text for game commands"""
        text.lower()

        # Nomination detection
        if any(w in ["nominate", "i nominate"] for w in wake_words):
            return self._parse_nomination(text)

        # Vote detection
        if "vote" in wake_words:
            return self._parse_vote(text)

        # Other game commands
        if any(w in ["demon", "minion", "outsider", "townsfolk"] for w in wake_words):
            return {"type": "character_mention", "text": text, "wake_words": wake_words}

        return {"type": "general", "text": text, "wake_words": wake_words}

    def _parse_nomination(self, text: str) -> Dict[str, Any]:
        """Parse nomination from text"""
        import re

        # Try different nomination patterns
        patterns = [
            r"i nominate (\w+)",
            r"nominate (\w+)",
            r"i vote to nominate (\w+)",
            r"(\w+) is my nomination",
            r"my nomination is (\w+)",
        ]

        text_lower = text.lower()

        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                nominee = match.group(1).title()
                return {
                    "type": "nomination",
                    "nominee": nominee,
                    "nominator": "Unknown",  # Would need speaker ID
                    "text": text,
                    "timestamp": time.time(),
                }

        return {"type": "nomination_unclear", "text": text}

    def _parse_vote(self, text: str) -> Dict[str, Any]:
        """Parse voting from text"""
        text_lower = text.lower()

        if any(word in text_lower for word in ["yes", "aye", "vote yes", "i vote"]):
            return {"type": "vote", "vote": "yes", "text": text}
        elif any(word in text_lower for word in ["no", "nay", "vote no", "abstain"]):
            return {"type": "vote", "vote": "no", "text": text}

        return {"type": "vote_unclear", "text": text}

    async def _handle_command(self, command: Dict[str, Any]):
        """Handle detected command"""
        command_type = command.get("type")

        if command_type in self.command_callbacks:
            try:
                callback = self.command_callbacks[command_type]
                if asyncio.iscoroutinefunction(callback):
                    await callback(command)
                else:
                    callback(command)
            except Exception as e:
                self.logger.error(f"Command callback error: {e}")

    def _save_audio_array(self, audio_data: Any, filename: str):
        """Save numpy array as WAV file"""
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(self.config.channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.config.sample_rate)
            wf.writeframes(audio_data.tobytes())


# Example usage and testing
async def test_continuous_listener():
    """Test the continuous listener"""

    async def on_nomination(command):
        print(f"🎯 NOMINATION: {command}")

    async def on_vote(command):
        print(f"🗳️ VOTE: {command}")

    async def on_general(command):
        print(f"💬 GENERAL: {command}")

    # Initialize listener
    config = ListenerConfig(
        window_duration=2.0,
        overlap_duration=0.5,
        wake_words=["nominate", "vote", "storyteller"],
    )

    listener = ContinuousListener(config)

    # Register callbacks
    listener.register_command_callback("nomination", on_nomination)
    listener.register_command_callback("vote", on_vote)
    listener.register_command_callback("general", on_general)

    # Initialize and start
    if await listener.initialize():
        print("🎤 Starting continuous listening...")
        listener.start_listening()

        try:
            # Listen for 30 seconds
            await asyncio.sleep(30)
        finally:
            listener.stop_listening()
    else:
        print("❌ Failed to initialize listener")


if __name__ == "__main__":
    asyncio.run(test_continuous_listener())
