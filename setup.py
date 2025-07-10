"""
Setup script for Blood on the Clocktower AI Agent
Handles automated installation and model downloads
"""

import asyncio
import logging
import subprocess
import sys
from pathlib import Path

from src.speech.speech_handler import ModelDownloader, SpeechConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProjectSetup:
    """Handles complete project setup including dependencies and models"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.models_dir = self.project_root / "models"

    async def setup_everything(self):
        """Complete setup process"""
        logger.info("🎭 Setting up Blood on the Clocktower AI Agent")

        try:
            # 1. Install Python dependencies
            await self.install_python_deps()

            # 2. Install system dependencies
            await self.install_system_deps()

            # 3. Download AI models
            await self.download_models()

            # 4. Create necessary directories
            self.create_directories()

            # 5. Test installation
            await self.test_installation()

            logger.info(
                "✅ Setup complete! Ready to run Blood on the Clocktower games."
            )

        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            sys.exit(1)

    async def install_python_deps(self):
        """Install Python dependencies"""
        logger.info("📦 Installing Python dependencies...")

        requirements = [
            "openai-whisper>=20231117",
            "pyaudio>=0.2.11",
            "requests>=2.31.0",
            "asyncio-mqtt>=0.16.1",
            "fastapi>=0.104.0",
            "uvicorn>=0.24.0",
            "pydantic>=2.5.0",
            "sqlite3",  # Usually built-in
            "numpy>=1.24.0",
            "torch>=2.1.0",  # For Whisper
            "torchaudio>=2.1.0",  # For Whisper
        ]

        for req in requirements:
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", req],
                    check=True,
                    capture_output=True,
                )
                logger.info(f"✓ Installed {req}")
            except subprocess.CalledProcessError as e:
                logger.warning(f"⚠️ Failed to install {req}: {e}")

    async def install_system_deps(self):
        """Install system dependencies"""
        logger.info("🔧 Installing system dependencies...")

        # Detect system type
        try:
            # Try apt (Debian/Ubuntu)
            subprocess.run(["which", "apt"], check=True, capture_output=True)
            await self._install_apt_deps()
        except subprocess.CalledProcessError:
            try:
                # Try yum (RHEL/CentOS)
                subprocess.run(["which", "yum"], check=True, capture_output=True)
                await self._install_yum_deps()
            except subprocess.CalledProcessError:
                try:
                    # Try pacman (Arch)
                    subprocess.run(["which", "pacman"], check=True, capture_output=True)
                    await self._install_pacman_deps()
                except subprocess.CalledProcessError:
                    logger.warning("⚠️ Unknown package manager, skipping system deps")

    async def _install_apt_deps(self):
        """Install dependencies using apt"""
        deps = [
            "portaudio19-dev",
            "python3-pyaudio",
            "ffmpeg",
            "wget",
            "curl",
            "alsa-utils",
            "pulseaudio",
        ]

        try:
            subprocess.run(["sudo", "apt", "update"], check=True)
            subprocess.run(["sudo", "apt", "install", "-y"] + deps, check=True)
            logger.info("✓ Installed apt dependencies")
        except subprocess.CalledProcessError as e:
            logger.warning(f"⚠️ Failed to install apt deps: {e}")

    async def _install_yum_deps(self):
        """Install dependencies using yum"""
        deps = [
            "portaudio-devel",
            "python3-pyaudio",
            "ffmpeg",
            "wget",
            "curl",
            "alsa-utils",
            "pulseaudio",
        ]

        try:
            subprocess.run(["sudo", "yum", "install", "-y"] + deps, check=True)
            logger.info("✓ Installed yum dependencies")
        except subprocess.CalledProcessError as e:
            logger.warning(f"⚠️ Failed to install yum deps: {e}")

    async def _install_pacman_deps(self):
        """Install dependencies using pacman"""
        deps = [
            "portaudio",
            "python-pyaudio",
            "ffmpeg",
            "wget",
            "curl",
            "alsa-utils",
            "pulseaudio",
        ]

        try:
            subprocess.run(["sudo", "pacman", "-S", "--noconfirm"] + deps, check=True)
            logger.info("✓ Installed pacman dependencies")
        except subprocess.CalledProcessError as e:
            logger.warning(f"⚠️ Failed to install pacman deps: {e}")

    async def download_models(self):
        """Download AI models"""
        logger.info("🤖 Downloading AI models...")

        downloader = ModelDownloader(str(self.models_dir))

        # Download Whisper model
        logger.info("Downloading Whisper speech recognition model...")
        await downloader.download_whisper_model("base")

        # Download TTS voices
        logger.info("Downloading text-to-speech voices...")
        voices = ["en_US-lessac-medium", "en_US-amy-medium", "en_US-ryan-medium"]

        for voice in voices:
            await downloader.download_piper_voice(voice)

        # Install Piper TTS
        await self._install_piper()

        logger.info("✓ All models downloaded")

    async def _install_piper(self):
        """Install Piper TTS binary"""
        logger.info("Installing Piper TTS...")

        piper_dir = self.models_dir / "piper_bin"
        piper_dir.mkdir(parents=True, exist_ok=True)

        # Download appropriate binary based on system
        import platform

        system = platform.system().lower()
        arch = platform.machine().lower()

        if system == "linux":
            if "x86_64" in arch or "amd64" in arch:
                url = "https://github.com/rhasspy/piper/releases/latest/download/piper_linux_x86_64.tar.gz"
            elif "aarch64" in arch or "arm64" in arch:
                url = "https://github.com/rhasspy/piper/releases/latest/download/piper_linux_aarch64.tar.gz"
            else:
                logger.warning("⚠️ Unsupported architecture for Piper")
                return
        elif system == "darwin":  # macOS
            url = "https://github.com/rhasspy/piper/releases/latest/download/piper_macos_x64.tar.gz"
        else:
            logger.warning("⚠️ Unsupported system for Piper")
            return

        try:
            # Download
            subprocess.run(
                ["wget", "-O", str(piper_dir / "piper.tar.gz"), url], check=True
            )

            # Extract
            subprocess.run(
                ["tar", "-xzf", str(piper_dir / "piper.tar.gz"), "-C", str(piper_dir)],
                check=True,
            )

            # Make executable
            piper_binary = piper_dir / "piper" / "piper"
            if piper_binary.exists():
                subprocess.run(["chmod", "+x", str(piper_binary)], check=True)

                # Create symlink in project root for easy access
                symlink_path = self.project_root / "piper"
                if symlink_path.exists():
                    symlink_path.unlink()
                symlink_path.symlink_to(piper_binary)

            logger.info("✓ Piper TTS installed")

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install Piper: {e}")

    def create_directories(self):
        """Create necessary project directories"""
        logger.info("📁 Creating project directories...")

        directories = [
            "data/games",
            "data/characters",
            "data/scripts",
            "logs",
            "backups",
            "audio_cache",
        ]

        for dir_path in directories:
            (self.project_root / dir_path).mkdir(parents=True, exist_ok=True)

        logger.info("✓ Directories created")

    async def test_installation(self):
        """Test that everything is working"""
        logger.info("🧪 Testing installation...")

        try:
            # Test imports
            import pyaudio
            import requests
            import whisper

            logger.info("✓ Python imports working")

            # Test Whisper model loading
            logger.info("Testing Whisper model...")
            model = whisper.load_model(
                "base", download_root=str(self.models_dir / "whisper_base")
            )
            logger.info("✓ Whisper model loads")

            # Test PyAudio
            logger.info("Testing audio system...")
            audio = pyaudio.PyAudio()
            device_count = audio.get_device_count()
            audio.terminate()
            logger.info(f"✓ Audio system working ({device_count} devices)")

            # Test Piper
            piper_path = self.project_root / "piper"
            if piper_path.exists():
                result = subprocess.run(
                    [str(piper_path), "--version"], capture_output=True, text=True
                )
                if result.returncode == 0:
                    logger.info("✓ Piper TTS working")
                else:
                    logger.warning("⚠️ Piper TTS not responding correctly")
            else:
                logger.warning("⚠️ Piper TTS not found")

        except Exception as e:
            logger.error(f"❌ Installation test failed: {e}")
            raise

    def create_run_script(self):
        """Create convenient run script"""
        run_script = self.project_root / "run_clocktower.sh"

        script_content = f"""#!/bin/bash
# Blood on the Clocktower AI Agent Runner

cd "{self.project_root}"

# Add Piper to PATH
export PATH="$PWD:$PATH"

# Run the main application
python -m src.main "$@"
"""

        with open(run_script, "w") as f:
            f.write(script_content)

        subprocess.run(["chmod", "+x", str(run_script)])
        logger.info("✓ Created run script: ./run_clocktower.sh")


async def main():
    """Main setup function"""
    setup = ProjectSetup()
    await setup.setup_everything()
    setup.create_run_script()

    print("\n" + "=" * 60)
    print("🎭 Blood on the Clocktower AI Agent Setup Complete!")
    print("=" * 60)
    print()
    print("To run the game:")
    print("  ./run_clocktower.sh")
    print()
    print("Or directly:")
    print("  python -m src.main")
    print()
    print("Enjoy your games! 🌙🔪")


if __name__ == "__main__":
    asyncio.run(main())
