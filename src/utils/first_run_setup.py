"""
First Run Setup Module
Handles automatic model downloads and initial configuration
"""

import asyncio
import logging
import os
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Callable, Optional

from ..speech.speech_handler import ModelDownloader


class FirstRunSetupGUI:
    """GUI for first-run model downloads"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Blood on the Clocktower AI - First Time Setup")
        self.root.geometry("600x400")

        # Center window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        # Prevent closing during download
        self.downloading = False
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.setup_ui()
        self.downloader = ModelDownloader()

    def setup_ui(self):
        """Create the setup UI"""
        # Title
        title_label = tk.Label(
            self.root,
            text="🎭 Blood on the Clocktower AI Storyteller",
            font=("Arial", 16, "bold"),
        )
        title_label.pack(pady=20)

        # Info text
        info_text = """Welcome! This is your first time running the AI Storyteller.
        
We need to download the AI models for:
• Speech Recognition (All Whisper models) - ~4GB total
  - Tiny (39MB), Base (142MB), Small (461MB), Medium (1.5GB), Large (2.9GB)
• Text-to-Speech (Piper) - ~50MB
• AI Storytelling (DeepSeek-R1) - ~3.5GB (optional but recommended)

This is a one-time download that will take 10-20 minutes depending on your internet speed.
Having all models lets you choose the best balance of speed vs. accuracy for your setup."""

        info_label = tk.Label(self.root, text=info_text, justify=tk.LEFT)
        info_label.pack(pady=10, padx=40)

        # Progress frame
        self.progress_frame = tk.Frame(self.root)
        self.progress_frame.pack(pady=20, padx=40, fill=tk.X)

        # Status label
        self.status_label = tk.Label(
            self.progress_frame, text="Ready to download models", font=("Arial", 10)
        )
        self.status_label.pack()

        # Progress bar
        self.progress = ttk.Progressbar(
            self.progress_frame, mode="determinate", length=500, maximum=100
        )
        self.progress.pack(pady=10)

        # Progress percentage label
        self.progress_percent_label = tk.Label(
            self.progress_frame, text="0%", font=("Arial", 12, "bold"), bg="white"
        )
        self.progress_percent_label.pack(pady=5)

        # Log text
        self.log_frame = tk.Frame(self.root)
        self.log_frame.pack(pady=10, padx=40, fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(
            self.log_frame, height=8, wrap=tk.WORD, font=("Courier", 9)
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(self.log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

        # Buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=20)

        self.download_btn = tk.Button(
            button_frame,
            text="Start Download",
            command=self.start_download,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12),
            padx=20,
            pady=10,
        )
        self.download_btn.pack(side=tk.LEFT, padx=10)

        # Auto-start download after a short delay
        self.root.after(2000, self.auto_start_download)

        self.skip_btn = tk.Button(
            button_frame,
            text="Skip (Manual Setup)",
            command=self.skip_setup,
            font=("Arial", 10),
            padx=10,
            pady=5,
        )
        self.skip_btn.pack(side=tk.LEFT)

    def log(self, message: str):
        """Add message to log"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update()

    def on_closing(self):
        """Handle window close"""
        if self.downloading:
            messagebox.showwarning(
                "Download in Progress", "Please wait for the download to complete."
            )
        else:
            self.root.destroy()

    def auto_start_download(self):
        """Auto-start download after delay"""
        if not self.downloading:
            self.status_label.config(text="Starting automatic download...")
            self.download_btn.config(text="Downloading...")
            self.root.after(1000, self.start_download)  # 1 second delay

    def start_download(self):
        """Start the download process"""
        if self.downloading:
            return

        self.downloading = True
        self.download_btn.config(state=tk.DISABLED, text="Downloading...")
        self.skip_btn.config(state=tk.DISABLED)
        self.progress["value"] = 0
        self.progress_percent_label.config(text="0%")

        # Run download in background thread
        thread = threading.Thread(target=self.download_models)
        thread.daemon = True
        thread.start()

    def download_models(self):
        """Download all required models"""
        try:
            # Update status
            self.root.after(
                0, self.status_label.config, {"text": "Starting download..."}
            )
            self.root.after(0, self.log, "📥 Starting model downloads...")

            # Create progress callback that updates the GUI
            def progress_callback(message, percent=None):
                self.root.after(0, self.log, message)
                self.root.after(0, self.status_label.config, {"text": message})

                if percent is not None:
                    self.root.after(0, self.progress.config, {"value": percent})
                    self.root.after(
                        0,
                        self.progress_percent_label.config,
                        {"text": f"{percent:.1f}%"},
                    )

            # Download all Whisper models
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Show immediate progress
            progress_callback("🔄 Initializing Whisper downloads...", 5)

            whisper_models = ["tiny", "base", "small", "medium", "large"]
            model_sizes = {
                "tiny": "39MB",
                "base": "142MB",
                "small": "461MB",
                "medium": "1.5GB",
                "large": "2.9GB",
            }

            self.root.after(
                0, self.log, "📥 Downloading all Whisper speech recognition models..."
            )

            for i, model in enumerate(whisper_models):
                base_progress = 10 + (i * 15)  # 10, 25, 40, 55, 70

                progress_callback(
                    f"📥 Downloading Whisper {model} model ({model_sizes[model]})...",
                    base_progress,
                )
                self.root.after(
                    0,
                    self.log,
                    f"📥 Downloading Whisper {model} model ({model_sizes[model]})...",
                )

                try:
                    # Use real progress tracking without hardcoded limits
                    success = loop.run_until_complete(
                        self.downloader.download_whisper_model(
                            model,
                            lambda msg, p=None: progress_callback(msg, p),
                        )
                    )

                    if not success:
                        self.root.after(
                            0, self.log, f"❌ Failed to download {model} model"
                        )
                        # Continue with other models
                        continue
                except Exception as e:
                    self.root.after(
                        0, self.log, f"❌ Error downloading {model} model: {str(e)}"
                    )
                    # Continue with other models
                    continue

                # Don't override the final progress from the actual download
                self.root.after(0, self.log, f"✅ Whisper {model} model downloaded!")

            # Let the actual download progress show, don't jump to 80%
            progress_callback("✅ All Whisper models downloaded successfully!", None)
            self.root.after(
                0, self.log, "✅ All Whisper models downloaded successfully!"
            )

            # Download Piper
            self.root.after(0, self.log, "📥 Downloading Piper text-to-speech voice...")

            success = loop.run_until_complete(
                self.downloader.download_piper_voice(
                    "en_US-lessac-medium",
                    lambda msg, p=None: progress_callback(msg, p),
                )
            )

            if not success:
                raise Exception("Failed to download Piper voice")

            self.root.after(0, self.log, "✅ Piper voice downloaded successfully!")

            # Download DeepSeek model (optional)
            self.root.after(
                0, self.log, "🤖 Downloading DeepSeek AI model (optional)..."
            )

            try:
                success = loop.run_until_complete(
                    self.downloader.download_deepseek_model(
                        lambda msg, p=None: progress_callback(msg, p if p else 90),
                    )
                )

                if success:
                    self.root.after(
                        0, self.log, "✅ DeepSeek AI model downloaded successfully!"
                    )
                else:
                    self.root.after(
                        0,
                        self.log,
                        "⚠️ DeepSeek download failed - AI storytelling disabled",
                    )

            except Exception as e:
                self.root.after(0, self.log, f"⚠️ DeepSeek download skipped: {str(e)}")

            # Mark as complete
            self.mark_setup_complete()
            progress_callback("🎉 Setup complete!", 100)

            # Success
            self.root.after(0, self.download_complete)

        except Exception as e:
            self.root.after(0, self.download_failed, str(e))

    def download_complete(self):
        """Handle successful download"""
        self.downloading = False
        self.progress["value"] = 100
        self.progress_percent_label.config(text="100%")
        self.status_label.config(text="✅ Download complete!")
        self.log("🎉 All models downloaded successfully!")
        self.log("You can now close this window and the AI Storyteller will start.")

        self.download_btn.config(
            text="Close & Start AI",
            state=tk.NORMAL,
            command=self.root.destroy,
            bg="#27ae60",
        )

    def download_failed(self, error: str):
        """Handle download failure"""
        self.downloading = False
        self.progress.stop()
        self.status_label.config(text="❌ Download failed")
        self.log(f"Error: {error}")

        messagebox.showerror(
            "Download Failed",
            f"Failed to download models:\n{error}\n\n"
            "Please check your internet connection and try again.",
        )

        self.download_btn.config(state=tk.NORMAL)
        self.skip_btn.config(state=tk.NORMAL)

    def skip_setup(self):
        """Skip automatic setup"""
        result = messagebox.askyesno(
            "Skip Setup?",
            "Without the AI models, speech recognition and text-to-speech won't work.\n\n"
            "You'll need to download them manually later.\n\n"
            "Are you sure you want to skip?",
        )

        if result:
            self.mark_setup_complete()
            self.root.destroy()

    def mark_setup_complete(self):
        """Mark first-run setup as complete"""
        config_dir = Path.home() / ".bloodclocktower"
        config_dir.mkdir(exist_ok=True)

        setup_file = config_dir / "first_run_complete"
        setup_file.write_text("1")

    def run(self):
        """Run the setup GUI"""
        self.root.mainloop()


def check_first_run() -> bool:
    """Check if this is the first run"""
    config_dir = Path.home() / ".bloodclocktower"
    setup_file = config_dir / "first_run_complete"

    # Also check if models exist
    models_dir = Path("models")
    whisper_exists = (models_dir / "whisper_large").exists()
    piper_exists = (
        models_dir / "piper" / "en_US-lessac-medium" / "en_US-lessac-medium.onnx"
    ).exists()

    return not setup_file.exists() or not (whisper_exists and piper_exists)


def run_first_time_setup():
    """Run the first-time setup if needed"""
    if check_first_run():
        # Set up logging
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )

        # Run setup GUI
        setup = FirstRunSetupGUI()
        setup.run()

        return True

    return False


if __name__ == "__main__":
    # Test the setup GUI
    run_first_time_setup()
