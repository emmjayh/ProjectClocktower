"""
Windows Build Script for Blood on the Clocktower AI Agent
Creates standalone Windows executable with PyInstaller
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Fix Windows encoding issues
if sys.platform.startswith("win"):
    try:
        import subprocess

        subprocess.run(["chcp", "65001"], capture_output=True, check=False)
        os.environ["PYTHONIOENCODING"] = "utf-8"
    except Exception:
        pass


def safe_print(text):
    """Safely print text on Windows"""
    fallback = (
        text.replace("🏗️", "[BUILD]")
        .replace("✅", "[OK]")
        .replace("❌", "[ERROR]")
        .replace("📦", "[PACKAGE]")
        .replace("🔨", "[COMPILE]")
        .replace("✓", "[OK]")
        .replace("⚠️", "[WARNING]")
        .replace("⚠", "[WARNING]")
        .replace("💡", "[INFO]")
        .replace("🎭", "[GAME]")
        .replace("🎮", "[GAME]")
        .replace("🎯", "[TARGET]")
        .replace("🏗", "[BUILD]")
        .replace("📝", "[NOTE]")
        .replace("🔧", "[CONFIG]")
        .replace("️", "")
    )  # Remove variation selector
    try:
        print(text)
    except UnicodeEncodeError:
        print(fallback)


class WindowsBuilder:
    """Builds Windows executable package"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"

    def build_executable(self):
        """Build standalone Windows executable"""
        safe_print("🏗️ Building Windows executable...")

        try:
            # Install build dependencies
            self._install_build_deps()

            # Create spec file
            self._create_pyinstaller_spec()

            # Run PyInstaller
            self._run_pyinstaller()

            # Package resources
            self._package_resources()

            # Create installer
            self._create_installer()

            safe_print("✅ Windows build complete!")
            safe_print(f"📦 Executable: {self.dist_dir / 'BloodClockTowerAI.exe'}")

        except Exception as e:
            safe_print(f"❌ Build failed: {e}")
            sys.exit(1)

    def _install_build_deps(self):
        """Install build dependencies"""
        safe_print("📦 Installing build dependencies...")

        deps = [
            "pyinstaller>=6.0.0",
            "auto-py-to-exe>=2.42.0",  # Optional GUI for PyInstaller
            "pillow>=10.0.0",  # For icon handling
            "tk",  # Ensure Tkinter is available
        ]

        for dep in deps:
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", dep],
                    check=True,
                    capture_output=True,
                )
                safe_print(f"✓ Installed {dep}")
            except subprocess.CalledProcessError:
                safe_print(f"⚠️ Failed to install {dep}")

    def _create_pyinstaller_spec(self):
        """Create PyInstaller spec file for advanced configuration"""
        spec_content = """
# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

# Define paths
project_root = Path(SPECPATH)
src_path = project_root / "src"

a = Analysis(
    ["botc_launcher.py"],
    pathex=[str(project_root), str(src_path)],
    binaries=[],
    datas=[
        # Include all source files
        (str(src_path), "src"),
        # Include character data if it exists
        (str(project_root / "data"), "data") if (project_root / "data").exists() else (".", "."),
        # Include documentation files if they exist
        ("README.md", ".") if (project_root / "README.md").exists() else (".", "."),
        ("CLAUDE.md", ".") if (project_root / "CLAUDE.md").exists() else (".", "."),
    ],
    hiddenimports=[
        # GUI framework
        "tkinter",
        "tkinter.ttk",
        "tkinter.filedialog", 
        "tkinter.messagebox",
        "tkinter.scrolledtext",
        # Core Python modules
        "asyncio",
        "threading",
        "json",
        "logging",
        "hashlib",
        "datetime",
        "sqlite3",
        "tempfile",
        "wave",
        "pathlib",
        "dataclasses",
        "collections",
        "queue",
        "pickle",
        "time",
        "os",
        "sys",
        # Optional web dependencies  
        "requests",
        "aiohttp",
        "websockets",
        # Core application modules (use absolute imports)
        "src",
        "src.core",
        "src.core.ai_storyteller",
        "src.core.game_state", 
        "src.game",
        "src.game.rule_engine",
        "src.game.clocktower_api",
        "src.game.live_game_monitor",
        "src.gui",
        "src.gui.main_window",
        "src.speech",
        "src.speech.speech_handler",
        "src.speech.audio_dependencies",
        "src.speech.continuous_listener",
        "src.speech.enhanced_tts", 
        "src.speech.speaker_identification",
        "src.utils",
        "src.utils.first_run_setup",
        # Optional audio dependencies
        "whisper",
        "numpy", 
        "pyaudio",
        "pygame",
        "librosa",
        "sklearn",
        "sklearn.cluster",
        "sklearn.preprocessing",
        "torch",
        "tqdm",
        "pillow",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="BloodClockTowerAI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI app, no console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / "assets" / "icon.ico") if (project_root / "assets" / "icon.ico").exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="BloodClockTowerAI",
)
"""

        spec_file = self.project_root / "bloodclocktower.spec"
        with open(spec_file, "w", encoding="utf-8") as f:
            f.write(spec_content)

        safe_print("✓ Created PyInstaller spec file")

    def _run_pyinstaller(self):
        """Run PyInstaller to build executable"""
        safe_print("🔨 Running PyInstaller...")

        try:
            subprocess.run(
                ["pyinstaller", "--clean", "--noconfirm", "bloodclocktower.spec"],
                check=True,
                cwd=self.project_root,
            )

            safe_print("✓ PyInstaller build completed")

        except subprocess.CalledProcessError as e:
            raise Exception(f"PyInstaller failed: {e}")

    def _package_resources(self):
        """Package additional resources with the executable"""
        safe_print("📦 Packaging resources...")

        exe_dir = self.dist_dir / "BloodClockTowerAI"

        # Create models directory
        models_dir = exe_dir / "models"
        models_dir.mkdir(exist_ok=True)

        # Create simple launcher script
        launcher_script = exe_dir / "BloodClockTowerAI.bat"
        with open(launcher_script, "w", encoding="utf-8") as f:
            f.write(
                """@echo off
cd /d "%~dp0"
start "" "BloodClockTowerAI.exe"
"""
            )

        # Create README for Windows
        readme_file = exe_dir / "README.txt"
        with open(readme_file, "w", encoding="utf-8") as f:
            f.write(
                """Blood on the Clocktower AI Agent - Windows Version

[GAME] QUICK START:
1. Double-click "BloodClockTowerAI.exe" to start
2. On first run, the AI will automatically download required models
3. After setup completes, the main application will start

[GAME] HOW TO USE:
- Enter player names in the Setup tab (one per line)
- Choose your script (Trouble Brewing recommended for beginners)
- Select storyteller voice
- Click "Start New Game"
- Use the Game Control tab to manage phases
- The AI will guide you through the game!

[CONFIG] TROUBLESHOOTING:
- If audio doesn't work, check Windows sound settings
- Make sure microphone permissions are enabled
- For best results, use a quiet room
- If speech recognition fails, use manual text input

[NOTE] FIRST RUN:
- The first time you run the app, it will download AI models
- This requires an internet connection (about 200MB download)
- The download only happens once
- Models are saved in your user folder

[TARGET] REQUIREMENTS:
- Windows 10/11
- Microphone for voice commands (optional)
- Speakers/headphones for AI narration
- Internet connection for first-time setup

For support, visit: https://github.com/emmjayh/ProjectClocktower/issues
"""
            )

        safe_print("✓ Resources packaged")

    def _create_installer(self):
        """Create Windows installer using NSIS (if available)"""
        safe_print("📦 Creating installer...")

        try:
            # Check if NSIS is available
            subprocess.run(["makensis", "/VERSION"], check=True, capture_output=True)

            # Create NSIS script
            self._create_nsis_script()

            # Build installer
            subprocess.run(
                ["makensis", str(self.project_root / "installer.nsi")], check=True
            )

            safe_print("✓ Installer created")

        except (subprocess.CalledProcessError, FileNotFoundError):
            safe_print("⚠️ NSIS not found, skipping installer creation")
            safe_print(
                "💡 You can distribute the 'dist/BloodClockTowerAI' folder directly"
            )

    def _create_nsis_script(self):
        """Create NSIS installer script"""
        nsis_script = """
!define APP_NAME "Blood on the Clocktower AI Agent"
!define APP_VERSION "1.0"
!define APP_PUBLISHER "BOTC AI Team"
!define APP_URL "https://github.com/your-repo"
!define APP_EXECUTABLE "BloodClockTowerAI.exe"

Name "${APP_NAME}"
OutFile "BloodClockTowerAI_Setup.exe"
InstallDir "$PROGRAMFILES\\${APP_NAME}"
RequestExecutionLevel admin

Page directory
Page instfiles

Section "Main Application"
    SetOutPath "$INSTDIR"
    
    ; Copy all files
    File /r "dist\\BloodClockTowerAI\\*"
    
    ; Create shortcuts
    CreateDirectory "$SMPROGRAMS\\${APP_NAME}"
    CreateShortcut "$SMPROGRAMS\\${APP_NAME}\\${APP_NAME}.lnk" "$INSTDIR\\${APP_EXECUTABLE}"
    CreateShortcut "$SMPROGRAMS\\${APP_NAME}\\Download Models.lnk" "$INSTDIR\\download_models.bat"
    CreateShortcut "$SMPROGRAMS\\${APP_NAME}\\Uninstall.lnk" "$INSTDIR\\uninstall.exe"
    CreateShortcut "$DESKTOP\\${APP_NAME}.lnk" "$INSTDIR\\${APP_EXECUTABLE}"
    
    ; Write uninstaller
    WriteUninstaller "$INSTDIR\\uninstall.exe"
    
    ; Registry entries
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "UninstallString" "$INSTDIR\\uninstall.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "DisplayVersion" "${APP_VERSION}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "Publisher" "${APP_PUBLISHER}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "URLInfoAbout" "${APP_URL}"
    
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\\*.*"
    RMDir /r "$INSTDIR"
    
    Delete "$SMPROGRAMS\\${APP_NAME}\\*.*"
    RMDir "$SMPROGRAMS\\${APP_NAME}"
    Delete "$DESKTOP\\${APP_NAME}.lnk"
    
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}"
SectionEnd
"""

        nsis_file = self.project_root / "installer.nsi"
        with open(nsis_file, "w", encoding="utf-8") as f:
            f.write(nsis_script)

    def create_dev_script(self):
        """Create development script for easy testing"""
        dev_script = self.project_root / "run_dev.bat"
        with open(dev_script, "w", encoding="utf-8") as f:
            f.write(
                """@echo off
echo Starting Blood on the Clocktower AI Agent (Development Mode)
cd /d "%~dp0"
python -m src.gui.main_window
pause
"""
            )

        safe_print("✓ Created development script: run_dev.bat")


def main():
    """Main build function"""
    builder = WindowsBuilder()

    if len(sys.argv) > 1 and sys.argv[1] == "--dev":
        builder.create_dev_script()
    else:
        builder.build_executable()


if __name__ == "__main__":
    main()
