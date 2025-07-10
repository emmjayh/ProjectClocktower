"""
Speech Recognition and Text-to-Speech Handler
Manages local Whisper STT and Piper TTS with automated model downloads
"""

import asyncio
import logging
import os
import subprocess
import sys
import tempfile
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import audio dependencies gracefully
from .audio_dependencies import pyaudio, requests, whisper


@dataclass
class SpeechConfig:
    whisper_model: str = "large"
    tts_voice: str = "en_US-lessac-medium"
    sample_rate: int = 16000
    chunk_size: int = 1024
    channels: int = 1
    device_index: Optional[int] = None
    vad_threshold: float = 0.01
    silence_duration: float = 2.0


class ModelDownloader:
    """Handles automated download of Whisper and Piper models"""

    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)

        # Model URLs and configurations
        self.whisper_models = {
            "tiny": "39kb",
            "base": "142mb",
            "small": "461mb",
            "medium": "1.5gb",
            "large": "2.9gb",
        }

        self.piper_voices = {
            "en_US-lessac-medium": {
                "url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx",
                "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json",
            },
            "en_US-amy-medium": {
                "url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx",
                "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx.json",
            },
            "en_US-ryan-medium": {
                "url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/ryan/medium/en_US-ryan-medium.onnx",
                "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json",
            },
        }

    async def download_whisper_model(
        self, model_size: str = "base", progress_callback: callable = None
    ) -> bool:
        """Download Whisper model if not exists"""
        try:
            self.logger.info(f"Checking Whisper {model_size} model...")

            if progress_callback:
                progress_callback("Checking dependencies...", 0)

            # Check if whisper is available
            if whisper is None:
                error_msg = "Whisper library not available - install with: pip install openai-whisper"
                self.logger.error(error_msg)
                if progress_callback:
                    progress_callback(f"Error: {error_msg}")
                return False

            # Show immediate progress
            if progress_callback:
                progress_callback("Initializing Whisper download...", 5)

            # Whisper models are downloaded automatically by the library
            # Just trigger the download by loading the model
            model_path = self.models_dir / f"whisper_{model_size}"
            model_path.mkdir(exist_ok=True)

            # Test load to trigger download
            self.logger.info(
                f"Loading Whisper {model_size} model (downloading if needed)..."
            )
            if progress_callback:
                progress_callback(f"Loading Whisper {model_size} model (this may take a few minutes)...", 20)

            # This will download the model if it doesn't exist
            model = whisper.load_model(model_size, download_root=str(model_path))

            if progress_callback:
                progress_callback("Whisper model ready!", 100)

            self.logger.info(f"Whisper {model_size} model ready")
            return True

        except Exception as e:
            error_msg = f"Failed to download Whisper model: {e}"
            self.logger.error(error_msg)
            if progress_callback:
                progress_callback(f"Error: {error_msg}")
            return False

    async def download_piper_voice(
        self,
        voice_name: str = "en_US-lessac-medium",
        progress_callback: callable = None,
    ) -> bool:
        """Download Piper TTS voice model"""
        try:
            if progress_callback:
                progress_callback("Checking Piper voice requirements...", 0)

            # Check if requests is available
            if requests is None:
                error_msg = "Requests library not available - install with: pip install requests"
                self.logger.error(error_msg)
                if progress_callback:
                    progress_callback(f"Error: {error_msg}")
                return False

            if voice_name not in self.piper_voices:
                error_msg = f"Unknown voice: {voice_name}"
                self.logger.error(error_msg)
                if progress_callback:
                    progress_callback(f"Error: {error_msg}")
                return False

            if progress_callback:
                progress_callback("Initializing Piper download...", 10)

            voice_info = self.piper_voices[voice_name]
            voice_dir = self.models_dir / "piper" / voice_name
            voice_dir.mkdir(parents=True, exist_ok=True)

            model_path = voice_dir / f"{voice_name}.onnx"
            config_path = voice_dir / f"{voice_name}.onnx.json"

            # Download model file
            if not model_path.exists():
                self.logger.info(f"Downloading Piper voice model: {voice_name}")
                if progress_callback:
                    progress_callback(f"Downloading Piper voice model...", 30)
                    
                # Create a wrapper that converts the progress to percentage
                def model_progress_wrapper(message):
                    if "%" in message:
                        try:
                            percent = float(message.split(":")[1].split("%")[0].strip())
                            final_percent = 30 + (percent * 0.5)  # 30-80%
                            progress_callback(message, final_percent)
                        except:
                            progress_callback(message, 50)
                    else:
                        progress_callback(message, 50)
                        
                await self._download_file(
                    voice_info["url"], model_path, model_progress_wrapper
                )

            # Download config file
            if not config_path.exists():
                self.logger.info(f"Downloading Piper voice config: {voice_name}")
                if progress_callback:
                    progress_callback(f"Downloading Piper voice config...", 85)
                await self._download_file(
                    voice_info["config_url"], config_path, 
                    lambda msg: progress_callback(msg, 90)
                )

            if progress_callback:
                progress_callback("Piper voice ready!", 100)

            self.logger.info(f"Piper voice {voice_name} ready")
            return True

        except Exception as e:
            error_msg = f"Failed to download Piper voice: {e}"
            self.logger.error(error_msg)
            if progress_callback:
                progress_callback(f"Error: {error_msg}")
            return False

    async def _download_file(
        self, url: str, path: Path, progress_callback: callable = None
    ) -> None:
        """Download file with progress"""
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            with open(path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            if progress_callback:
                                # Support both old and new callback formats
                                try:
                                    # Try new format with percentage parameter
                                    progress_callback(
                                        f"Downloading {path.name}: {progress:.1f}%", progress
                                    )
                                except TypeError:
                                    # Fall back to old format
                                    progress_callback(
                                        f"Downloading {path.name}: {progress:.1f}%"
                                    )
                            else:
                                print(
                                    f"\rDownloading {path.name}: {progress:.1f}%",
                                    end="",
                                    flush=True,
                                )
                        elif progress_callback:
                            # If no content-length, show bytes downloaded
                            mb_downloaded = downloaded / (1024 * 1024)
                            try:
                                progress_callback(
                                    f"Downloading {path.name}: {mb_downloaded:.1f} MB", 
                                    min(90, mb_downloaded * 10)  # Rough estimate
                                )
                            except TypeError:
                                progress_callback(
                                    f"Downloading {path.name}: {mb_downloaded:.1f} MB"
                                )

            if not progress_callback:
                print()  # New line after progress

        except Exception as e:
            error_msg = f"Download failed for {url}: {e}"
            if progress_callback:
                progress_callback(f"Error: {error_msg}")
            else:
                print(f"Error: {error_msg}")
            raise

    async def install_dependencies(self) -> bool:
        """Install required system dependencies"""
        try:
            self.logger.info("Installing system dependencies...")

            # Install Piper TTS
            if not self._check_piper_installed():
                await self._install_piper()

            # Install PyAudio dependencies
            if not self._check_pyaudio_installed():
                await self._install_pyaudio_deps()

            return True

        except Exception as e:
            self.logger.error(f"Failed to install dependencies: {e}")
            return False

    def _check_piper_installed(self) -> bool:
        """Check if Piper is installed"""
        try:
            subprocess.run(["piper", "--version"], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _check_pyaudio_installed(self) -> bool:
        """Check if PyAudio is available"""
        try:
            import pyaudio

            return True
        except ImportError:
            return False

    async def _install_piper(self) -> None:
        """Install Piper TTS"""
        self.logger.info("Installing Piper TTS...")

        # Download Piper binary for Linux
        piper_url = "https://github.com/rhasspy/piper/releases/latest/download/piper_linux_x86_64.tar.gz"
        piper_dir = self.models_dir / "piper_bin"
        piper_dir.mkdir(exist_ok=True)

        # Download and extract
        subprocess.run(
            ["wget", "-O", str(piper_dir / "piper.tar.gz"), piper_url], check=True
        )

        subprocess.run(
            ["tar", "-xzf", str(piper_dir / "piper.tar.gz"), "-C", str(piper_dir)],
            check=True,
        )

        # Add to PATH (for this session)
        piper_path = piper_dir / "piper"
        if piper_path.exists():
            os.environ["PATH"] = f"{piper_path.parent}:{os.environ.get('PATH', '')}"

    async def _install_pyaudio_deps(self) -> None:
        """Install PyAudio system dependencies"""
        self.logger.info("Installing PyAudio dependencies...")

        # For Ubuntu/Debian
        try:
            subprocess.run(
                [
                    "apt-get",
                    "update",
                    "&&",
                    "apt-get",
                    "install",
                    "-y",
                    "portaudio19-dev",
                    "python3-pyaudio",
                ],
                shell=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            self.logger.warning("Could not install system dependencies automatically")


class SpeechHandler:
    """Main speech recognition and TTS handler"""

    def __init__(self, config: SpeechConfig = None):
        self.config = config or SpeechConfig()
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.downloader = ModelDownloader()
        self.whisper_model = None
        self.audio = None
        self.is_listening = False

        # Audio stream
        self.stream = None

    async def initialize(self) -> bool:
        """Initialize speech handler with model downloads"""
        try:
            self.logger.info("Initializing speech handler...")

            # Check if dependencies are available
            if whisper is None:
                self.logger.error(
                    "Whisper not available - install with: pip install openai-whisper"
                )
                return False

            if pyaudio is None:
                self.logger.error(
                    "PyAudio not available - install with: pip install pyaudio"
                )
                return False

            # Install dependencies
            await self.downloader.install_dependencies()

            # Download models
            await self.downloader.download_whisper_model(self.config.whisper_model)
            await self.downloader.download_piper_voice(self.config.tts_voice)

            # Load Whisper model
            self.logger.info("Loading Whisper model...")
            self.whisper_model = whisper.load_model(
                self.config.whisper_model,
                download_root=str(
                    self.downloader.models_dir / f"whisper_{self.config.whisper_model}"
                ),
            )

            # Initialize PyAudio
            self.audio = pyaudio.PyAudio()

            self.logger.info("Speech handler initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize speech handler: {e}")
            return False

    async def listen_for_command(
        self, keywords: List[str] = None, timeout: float = 30.0
    ) -> Optional[str]:
        """Listen for speech and return transcription"""
        try:
            self.logger.info("Listening for speech...")

            # Record audio
            audio_data = await self._record_audio(timeout)
            if not audio_data:
                return None

            # Transcribe with Whisper
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                self._save_audio_to_file(audio_data, temp_file.name)

                result = self.whisper_model.transcribe(temp_file.name)
                text = result["text"].strip()

                os.unlink(temp_file.name)

            self.logger.info(f"Transcribed: {text}")

            # Filter by keywords if provided
            if keywords:
                if not any(keyword.lower() in text.lower() for keyword in keywords):
                    return None

            return text

        except Exception as e:
            self.logger.error(f"Error in speech recognition: {e}")
            return None

    async def speak(self, text: str) -> bool:
        """Convert text to speech and play"""
        try:
            self.logger.info(f"Speaking: {text[:50]}...")

            # Generate audio with Piper
            voice_path = (
                self.downloader.models_dir
                / "piper"
                / self.config.tts_voice
                / f"{self.config.tts_voice}.onnx"
            )

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                # Use Piper to generate speech
                process = subprocess.run(
                    [
                        "piper",
                        "--model",
                        str(voice_path),
                        "--output_file",
                        temp_file.name,
                    ],
                    input=text,
                    text=True,
                    capture_output=True,
                )

                if process.returncode == 0:
                    await self._play_audio_file(temp_file.name)
                    os.unlink(temp_file.name)
                    return True
                else:
                    self.logger.error(f"Piper TTS failed: {process.stderr}")

        except Exception as e:
            self.logger.error(f"Error in text-to-speech: {e}")

        return False

    async def speak_to_player(self, player_name: str, text: str) -> bool:
        """Speak directly to a specific player (private information)"""
        # For now, just prepend player name
        full_text = f"{player_name}, {text}"
        return await self.speak(full_text)

    async def collect_votes(self, players: List[Any]) -> List[str]:
        """Collect votes through speech recognition"""
        voters = []

        # Listen for vote commands
        for _ in range(10):  # Max 10 seconds to collect votes
            command = await self.listen_for_command(["vote", "yes", "aye"], timeout=1.0)

            if command:
                # Parse player name from command
                player_name = self._extract_player_name(command, players)
                if player_name and player_name not in voters:
                    voters.append(player_name)
                    await self.speak(f"{player_name} votes")

        return voters

    async def parse_nomination(self, command: str) -> Dict[str, str]:
        """Parse nomination from speech command"""
        # Simple parsing - can be enhanced with NLP
        words = command.lower().split()

        nominate_idx = -1
        for i, word in enumerate(words):
            if "nominate" in word:
                nominate_idx = i
                break

        if nominate_idx >= 0 and nominate_idx + 1 < len(words):
            nominee = words[nominate_idx + 1].title()
            nominator = "Unknown"  # Would need speaker identification

            return {"nominator": nominator, "nominee": nominee, "command": command}

        return {}

    async def _record_audio(self, timeout: float) -> Optional[bytes]:
        """Record audio until silence or timeout"""
        try:
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=self.config.channels,
                rate=self.config.sample_rate,
                input=True,
                frames_per_buffer=self.config.chunk_size,
            )

            frames = []
            silence_count = 0
            max_silence = int(
                self.config.silence_duration
                * self.config.sample_rate
                / self.config.chunk_size
            )

            start_time = asyncio.get_event_loop().time()

            while (asyncio.get_event_loop().time() - start_time) < timeout:
                data = stream.read(self.config.chunk_size, exception_on_overflow=False)
                frames.append(data)

                # Simple voice activity detection
                audio_level = max(data) if data else 0
                if audio_level < self.config.vad_threshold * 32768:
                    silence_count += 1
                else:
                    silence_count = 0

                if silence_count > max_silence and len(frames) > 10:
                    break

                await asyncio.sleep(0.01)

            stream.stop_stream()
            stream.close()

            return b"".join(frames) if frames else None

        except Exception as e:
            self.logger.error(f"Error recording audio: {e}")
            return None

    def _save_audio_to_file(self, audio_data: bytes, filename: str) -> None:
        """Save audio data to WAV file"""
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(self.config.channels)
            wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.config.sample_rate)
            wf.writeframes(audio_data)

    async def _play_audio_file(self, filename: str) -> None:
        """Play audio file"""
        try:
            # Simple audio playback - can be enhanced
            subprocess.run(["aplay", filename], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            # Fallback to other players
            try:
                subprocess.run(["paplay", filename], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                self.logger.warning("Could not play audio file")

    def _extract_player_name(self, command: str, players: List[Any]) -> Optional[str]:
        """Extract player name from command"""
        words = command.lower().split()
        player_names = [p.name.lower() for p in players]

        for word in words:
            if word in player_names:
                return next(p.name for p in players if p.name.lower() == word)

        return None

    def cleanup(self) -> None:
        """Cleanup resources"""
        if self.stream:
            self.stream.close()
        if self.audio:
            self.audio.terminate()
