"""
Blood on the Clocktower AI Storyteller - Main Entry Point
Launch the AI Storyteller Dashboard for managing games
"""

from gui.storyteller_dashboard import StorytellerDashboard
from utils import fix_windows_encoding
import logging
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Fix Windows Unicode encoding issues early

fix_windows_encoding()


def setup_logging():
    """Setup logging configuration"""
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "storyteller.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )

    logger = logging.getLogger(__name__)
    logger.info("🎭 Starting Blood on the Clocktower AI Storyteller")


def check_dependencies():
    """Check if required dependencies are available"""
    missing = []

    try:
        pass
    except ImportError:
        missing.append("openai-whisper")

    try:
        pass
    except ImportError:
        missing.append("pyaudio")

    try:
        pass
    except ImportError:
        missing.append("requests")

    if missing:
        error_msg = (
            f"Missing dependencies: {', '.join(missing)}\n\n"
            f"Please run: pip install {' '.join(missing)}"
        )
        messagebox.showerror("Missing Dependencies", error_msg)
        return False

    return True


def main():
    """Main function"""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        # Check dependencies
        if not check_dependencies():
            sys.exit(1)

        # Create main window
        root = tk.Tk()

        # Set window icon (if available)
        try:
            icon_path = Path(__file__).parent.parent / "assets" / "icon.ico"
            if icon_path.exists():
                root.iconbitmap(str(icon_path))
        except Exception:
            pass  # Icon not critical

        # Create application
        app = StorytellerDashboard(root)

        # Handle window closing
        def on_closing():
            if messagebox.askokcancel("Quit", "Do you want to quit?"):
                logger.info("🎭 AI Storyteller shutting down")
                if hasattr(app, "api_client") and app.api_client:
                    app.api_client.disconnect()
                if hasattr(app, "speech_handler") and app.speech_handler:
                    app.speech_handler.cleanup()
                root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)

        # Center window on screen
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f"{width}x{height}+{x}+{y}")

        logger.info("🎭 AI Storyteller Dashboard launched")

        # Start the GUI event loop
        root.mainloop()

    except KeyboardInterrupt:
        logger.info("🎭 AI Storyteller interrupted by user")
    except Exception as e:
        logger.error(f"🎭 Fatal error: {e}", exc_info=True)
        messagebox.showerror("Fatal Error", f"An unexpected error occurred:\n{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
