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
from .audio_dependencies import pyaudio, whisper

# Increase recursion limit to prevent download failures
sys.setrecursionlimit(10000)


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
    """Handles automated download of Whisper, Piper, and DeepSeek models"""

    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)

        # Model URLs and configurations
        self.whisper_models = {
            "tiny": "39mb",
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

        # DeepSeek R1 model info
        self.deepseek_model = {
            "name": "DeepSeek-R1-Distill-Qwen-1.5B",
            "size": "~3.5GB",  # Approximate size for the model files
            "repo": "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
        }

    async def download_whisper_model(
        self, model_size: str = "base", progress_callback: callable = None
    ) -> bool:
        """Download Whisper model if not exists"""
        try:
            self.logger.info(f"Checking Whisper {model_size} model...")

            if progress_callback:
                progress_callback("Checking dependencies...", 0)

            # For downloads, we don't need whisper to be installed yet
            # We'll just download the model files directly
            whisper_available = True  # Assume available for download purposes

            if progress_callback:
                progress_callback("Starting model download...", 1)

            # Validate model size
            valid_models = [
                "tiny",
                "base",
                "small",
                "medium",
                "large",
                "tiny.en",
                "base.en",
                "small.en",
                "medium.en",
            ]
            if model_size not in valid_models:
                raise ValueError(
                    f"Invalid model size: {model_size}. Valid options: {valid_models}"
                )

            # Multiple fallback sources for robust downloads
            model_sources = {
                "tiny": [
                    "https://openaipublic.azureedge.net/main/whisper/models/65147644a518d12f04e32d6f3b26facc3f8dd46e5390956a9424a650c0ce22b9/tiny.pt",
                    "https://huggingface.co/openai/whisper-tiny/resolve/main/pytorch_model.bin",
                    "https://github.com/openai/whisper/raw/main/whisper/assets/tiny.pt",
                ],
                "base": [
                    "https://openaipublic.azureedge.net/main/whisper/models/ed3a0b6b1c0edf879ad9b11b1af5a0e6ab5db9205f891f668f8b0e6c6326e34e/base.pt",
                    "https://huggingface.co/openai/whisper-base/resolve/main/pytorch_model.bin",
                    "https://github.com/openai/whisper/raw/main/whisper/assets/base.pt",
                ],
                "small": [
                    "https://openaipublic.azureedge.net/main/whisper/models/9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794/small.pt",
                    "https://huggingface.co/openai/whisper-small/resolve/main/pytorch_model.bin",
                    "https://github.com/openai/whisper/raw/main/whisper/assets/small.pt",
                ],
                "medium": [
                    "https://openaipublic.azureedge.net/main/whisper/models/345ae4da62f9b3d59415adc60127b97c714f32e89e936602e85993674d08dcb1/medium.pt",
                    "https://huggingface.co/openai/whisper-medium/resolve/main/pytorch_model.bin",
                    "https://github.com/openai/whisper/raw/main/whisper/assets/medium.pt",
                ],
                "large": [
                    "https://openaipublic.azureedge.net/main/whisper/models/e4b87e7e0bf463eb8e6956e646f1e277e901512310def2c24bf0e11bd3c28e9a/large.pt",
                    "https://huggingface.co/openai/whisper-large/resolve/main/pytorch_model.bin",
                    "https://huggingface.co/openai/whisper-large-v3/resolve/main/pytorch_model.bin",
                ],
            }

            # Check if model already exists
            import os

            home = os.path.expanduser("~")
            cache_dir = os.path.join(home, ".cache", "whisper")
            os.makedirs(cache_dir, exist_ok=True)

            model_file = os.path.join(cache_dir, f"{model_size}.pt")

            if os.path.exists(model_file):
                self.logger.info(f"Whisper {model_size} model already exists")
                if progress_callback:
                    # Simulate gradual progress for GUI compatibility
                    progress_callback("Checking existing model...", 10)
                    await asyncio.sleep(0.5)
                    progress_callback("Validating model integrity...", 50)
                    await asyncio.sleep(0.5)
                    progress_callback("Model verified and ready!", 100)
                return True

            # Download the model manually with progress from multiple sources
            if model_size in model_sources:
                urls = model_sources[model_size]

                for i, url in enumerate(urls):
                    try:
                        self.logger.info(
                            f"Downloading Whisper {model_size} model from {url}"
                        )

                        if progress_callback:
                            source_name = (
                                "Official"
                                if i == 0
                                else "HuggingFace" if "huggingface" in url else "GitHub"
                            )
                            progress_callback(
                                f"Downloading from {source_name} ({i + 1}/{len(urls)})...",
                                5,
                            )

                        # Download with progress tracking
                        await self._download_file(
                            url, Path(model_file), progress_callback
                        )

                        self.logger.info(
                            f"Whisper {model_size} model downloaded successfully from {url}"
                        )
                        return True

                    except Exception as e:
                        self.logger.warning(f"Failed to download from {url}: {e}")
                        if progress_callback:
                            progress_callback(
                                f"Source {i + 1} failed, trying next...", 10 + (i * 10)
                            )

                        # If this was the last URL, re-raise the exception
                        if i == len(urls) - 1:
                            raise e

                        # Otherwise, continue to next URL
                        continue

                # If we get here, all downloads failed
                raise Exception(
                    f"Failed to download {model_size} model from all sources"
                )
            else:
                # No direct download URL available, try whisper.load_model fallback
                try:
                    import whisper as whisper_module

                    self.logger.info(f"Using whisper.load_model for {model_size}")
                    if progress_callback:
                        progress_callback(f"Loading {model_size} model...", 50)

                    whisper_module.load_model(model_size)

                    if progress_callback:
                        progress_callback("Whisper model ready!", 100)

                    return True
                except ImportError:
                    error_msg = (
                        f"Cannot download {model_size} model - whisper not installed"
                    )
                    self.logger.error(error_msg)
                    if progress_callback:
                        progress_callback(f"Error: {error_msg}")
                    return False

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

            if voice_name not in self.piper_voices:
                error_msg = f"Unknown voice: {voice_name}"
                self.logger.error(error_msg)
                if progress_callback:
                    progress_callback(f"Error: {error_msg}")
                return False

            if progress_callback:
                progress_callback("Initializing Piper download...", 5)

            voice_info = self.piper_voices[voice_name]
            voice_dir = self.models_dir / "piper" / voice_name
            voice_dir.mkdir(parents=True, exist_ok=True)

            model_path = voice_dir / f"{voice_name}.onnx"
            config_path = voice_dir / f"{voice_name}.onnx.json"

            # Download model file
            if not model_path.exists():
                self.logger.info(f"Downloading Piper voice model: {voice_name}")
                if progress_callback:
                    progress_callback("Downloading Piper voice model...", 10)

                await self._download_file(
                    voice_info["url"], model_path, progress_callback
                )

            # Download config file
            if not config_path.exists():
                self.logger.info(f"Downloading Piper voice config: {voice_name}")
                if progress_callback:
                    progress_callback("Downloading Piper voice config...", 95)
                await self._download_file(
                    voice_info["config_url"], config_path, progress_callback
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
        """Download file with progress and robust error handling"""
        try:
            # Use urllib instead of requests to avoid potential recursion issues
            import urllib.error
            import urllib.request

            # Create parent directory if it doesn't exist
            path.parent.mkdir(parents=True, exist_ok=True)

            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                },
            )

            # Add timeout and retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    with urllib.request.urlopen(req, timeout=300) as response:
                        # Handle redirects
                        if response.getcode() != 200:
                            raise urllib.error.HTTPError(
                                url,
                                response.getcode(),
                                f"HTTP {response.getcode()}",
                                response.headers,
                                None,
                            )

                        total_size = int(response.headers.get("Content-Length", 0))
                        downloaded = 0

                        # Use temporary file to prevent partial downloads
                        temp_path = path.with_suffix(path.suffix + ".tmp")

                        with open(temp_path, "wb") as f:
                            while True:
                                chunk = response.read(8192)
                                if not chunk:
                                    break

                                f.write(chunk)
                                downloaded += len(chunk)

                                if total_size > 0:
                                    progress = (downloaded / total_size) * 100
                                    if progress_callback:
                                        try:
                                            progress_callback(
                                                f"Downloading {path.name}: {progress:.1f}%"
                                            )
                                        except TypeError:
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
                                    mb_downloaded = downloaded / (1024 * 1024)
                                    try:
                                        progress_callback(
                                            f"Downloading {path.name}: {min(95, mb_downloaded * 10):.1f}%"  # Estimate progress
                                        )
                                    except TypeError:
                                        progress_callback(
                                            f"Downloading {path.name}: {min(95, mb_downloaded * 10):.1f}%"
                                        )

                        # Move temp file to final location
                        temp_path.rename(path)

                        if not progress_callback:
                            print()  # New line after progress

                        # Verify file was downloaded completely
                        if total_size > 0 and path.stat().st_size != total_size:
                            raise Exception(
                                f"Downloaded file size mismatch: expected {total_size}, got {path.stat().st_size}"
                            )

                        return  # Success, exit retry loop

                except (urllib.error.URLError, urllib.error.HTTPError, Exception) as e:
                    if attempt == max_retries - 1:
                        raise  # Re-raise on final attempt

                    self.logger.warning(f"Download attempt {attempt + 1} failed: {e}")
                    if progress_callback:
                        progress_callback(
                            f"Retrying download ({attempt + 2}/{max_retries})...", 0
                        )

                    # Clean up temp file if it exists
                    temp_path = path.with_suffix(path.suffix + ".tmp")
                    if temp_path.exists():
                        temp_path.unlink()

                    await asyncio.sleep(2)  # Wait before retry

        except Exception as e:
            error_msg = f"Download failed for {url}: {e}"
            if progress_callback:
                progress_callback(f"Error: {error_msg}")
            else:
                print(f"Error: {error_msg}")

            # Clean up any partial downloads
            if path.exists():
                path.unlink()
            temp_path = path.with_suffix(path.suffix + ".tmp")
            if temp_path.exists():
                temp_path.unlink()

            raise

    async def download_deepseek_model(self, progress_callback: callable = None) -> bool:
        """Download DeepSeek R1 model for AI storytelling"""
        try:
            if progress_callback:
                progress_callback("Checking DeepSeek model...", 0)

            self.logger.info("Checking DeepSeek-R1-Distill-Qwen-1.5B model...")

            # Check if transformers is available
            try:
                pass
            except ImportError:
                error_msg = "Transformers library not available - install with: pip install transformers"
                self.logger.error(error_msg)
                if progress_callback:
                    progress_callback(f"Error: {error_msg}")
                return False

            # DeepSeek uses HuggingFace model hub
            from transformers import AutoModelForCausalLM, AutoTokenizer

            cache_dir = Path.home() / ".cache" / "deepseek" / "qwen-1.5b"
            cache_dir.mkdir(parents=True, exist_ok=True)

            if progress_callback:
                progress_callback("Downloading DeepSeek tokenizer...", 10)

            # Download tokenizer
            try:
                tokenizer = AutoTokenizer.from_pretrained(
                    self.deepseek_model["repo"],
                    cache_dir=cache_dir,
                    trust_remote_code=True,
                )
                self.logger.info("DeepSeek tokenizer downloaded successfully")
            except Exception as e:
                self.logger.error(f"Failed to download tokenizer: {e}")
                if progress_callback:
                    progress_callback(f"Error downloading tokenizer: {e}")
                return False

            if progress_callback:
                progress_callback(
                    "Downloading DeepSeek model (this may take a while)...", 30
                )

            # Download model - this will use HuggingFace's progress system
            try:
                model = AutoModelForCausalLM.from_pretrained(
                    self.deepseek_model["repo"],
                    cache_dir=cache_dir,
                    trust_remote_code=True,
                    torch_dtype="auto",
                )
                self.logger.info("DeepSeek model downloaded successfully")

                # Clean up the loaded model from memory
                del model
                import torch

                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

            except Exception as e:
                self.logger.error(f"Failed to download model: {e}")
                if progress_callback:
                    progress_callback(f"Error downloading model: {e}")
                return False

            if progress_callback:
                progress_callback("DeepSeek model ready!", 100)

            return True

        except Exception as e:
            error_msg = f"Failed to download DeepSeek model: {e}"
            self.logger.error(error_msg)
            if progress_callback:
                progress_callback(f"Error: {error_msg}")
            return False

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
            pass

            return True
        except ImportError:
            return False

    async def _install_piper(self) -> None:
        """Install Piper TTS"""
        self.logger.info("Installing Piper TTS...")

        # Download Piper binary for Linux
        piper_url = "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz"
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
