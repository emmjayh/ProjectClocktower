"""
Blood on the Clocktower AI Agent - Windows GUI Application
Main window and user interface for Windows desktop app
"""

import asyncio
import json
import logging
import threading
import tkinter as tk
from dataclasses import asdict
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import Dict, List, Optional

# Handle imports for both package and executable contexts
try:
    from ..core.ai_storyteller import AIStoryteller, GamePhase
    from ..core.game_state import GameState, Player, PlayerStatus
    from ..speech.speech_handler import SpeechConfig, SpeechHandler
except ImportError:
    # Fallback for when running as executable or direct script
    import os
    import sys
    # Add the src directory to the path
    src_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    from core.ai_storyteller import AIStoryteller, GamePhase
    from core.game_state import GameState, Player, PlayerStatus
    from speech.speech_handler import SpeechConfig, SpeechHandler


class MainWindow:
    """Main application window for Windows"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Blood on the Clocktower - AI Storyteller")
        self.root.geometry("1200x800")
        self.root.configure(bg="#2c3e50")

        # Initialize components
        self.storyteller = None
        self.speech_handler = None
        self.game_state = None
        self.is_running = False

        # Threading for async operations
        self.event_loop = None
        self.background_thread = None

        # Setup GUI
        self._setup_styles()
        self._create_widgets()
        self._setup_layout()

        # Setup logging
        self.logger = logging.getLogger(__name__)

    def _setup_styles(self):
        """Setup custom styles for dark theme"""
        style = ttk.Style()
        style.theme_use("clam")

        # Dark theme colors
        style.configure(
            "Title.TLabel",
            background="#2c3e50",
            foreground="#ecf0f1",
            font=("Arial", 16, "bold"),
        )

        style.configure(
            "Subtitle.TLabel",
            background="#2c3e50",
            foreground="#bdc3c7",
            font=("Arial", 12),
        )

        style.configure("Dark.TFrame", background="#34495e")
        style.configure("Player.TFrame", background="#34495e", relief="raised")

        style.configure(
            "Start.TButton",
            background="#27ae60",
            foreground="white",
            font=("Arial", 12, "bold"),
        )

        style.configure(
            "Stop.TButton",
            background="#e74c3c",
            foreground="white",
            font=("Arial", 12, "bold"),
        )

    def _create_widgets(self):
        """Create all GUI widgets"""
        # Main container
        self.main_frame = ttk.Frame(self.root, style="Dark.TFrame")

        # Title
        self.title_label = ttk.Label(
            self.main_frame,
            text="🎭 Blood on the Clocktower - AI Storyteller",
            style="Title.TLabel",
        )

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)

        # Setup Tab
        self.setup_frame = ttk.Frame(self.notebook, style="Dark.TFrame")
        self.notebook.add(self.setup_frame, text="Game Setup")

        # Game Tab
        self.game_frame = ttk.Frame(self.notebook, style="Dark.TFrame")
        self.notebook.add(self.game_frame, text="Game Control")

        # Players Tab
        self.players_frame = ttk.Frame(self.notebook, style="Dark.TFrame")
        self.notebook.add(self.players_frame, text="Players")

        # Settings Tab
        self.settings_frame = ttk.Frame(self.notebook, style="Dark.TFrame")
        self.notebook.add(self.settings_frame, text="Settings")

        self._create_setup_tab()
        self._create_game_tab()
        self._create_players_tab()
        self._create_settings_tab()

    def _create_setup_tab(self):
        """Create game setup tab"""
        # Player names input
        ttk.Label(
            self.setup_frame,
            text="Player Names (one per line):",
            style="Subtitle.TLabel",
        ).pack(pady=10)

        self.players_text = scrolledtext.ScrolledText(
            self.setup_frame,
            height=10,
            width=40,
            bg="#34495e",
            fg="#ecf0f1",
            font=("Arial", 11),
        )
        self.players_text.pack(pady=10)

        # Script selection
        script_frame = ttk.Frame(self.setup_frame, style="Dark.TFrame")
        script_frame.pack(pady=10)

        ttk.Label(script_frame, text="Script:", style="Subtitle.TLabel").pack(
            side=tk.LEFT, padx=5
        )

        self.script_var = tk.StringVar(value="trouble_brewing")
        self.script_combo = ttk.Combobox(
            script_frame,
            textvariable=self.script_var,
            values=["trouble_brewing", "bad_moon_rising", "sects_and_violets"],
            state="readonly",
            width=20,
        )
        self.script_combo.pack(side=tk.LEFT, padx=5)

        # Voice settings
        voice_frame = ttk.Frame(self.setup_frame, style="Dark.TFrame")
        voice_frame.pack(pady=10)

        ttk.Label(voice_frame, text="Storyteller Voice:", style="Subtitle.TLabel").pack(
            side=tk.LEFT, padx=5
        )

        self.voice_var = tk.StringVar(value="en_US-lessac-medium")
        self.voice_combo = ttk.Combobox(
            voice_frame,
            textvariable=self.voice_var,
            values=["en_US-lessac-medium", "en_US-amy-medium", "en_US-ryan-medium"],
            state="readonly",
            width=20,
        )
        self.voice_combo.pack(side=tk.LEFT, padx=5)

        # Start/Stop buttons
        button_frame = ttk.Frame(self.setup_frame, style="Dark.TFrame")
        button_frame.pack(pady=20)

        self.start_button = ttk.Button(
            button_frame,
            text="🎮 Start New Game",
            command=self._start_game,
            style="Start.TButton",
        )
        self.start_button.pack(side=tk.LEFT, padx=10)

        self.stop_button = ttk.Button(
            button_frame,
            text="⏹️ Stop Game",
            command=self._stop_game,
            style="Stop.TButton",
            state=tk.DISABLED,
        )
        self.stop_button.pack(side=tk.LEFT, padx=10)

        # Load/Save buttons
        file_frame = ttk.Frame(self.setup_frame, style="Dark.TFrame")
        file_frame.pack(pady=10)

        ttk.Button(file_frame, text="💾 Save Setup", command=self._save_setup).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(file_frame, text="📂 Load Setup", command=self._load_setup).pack(
            side=tk.LEFT, padx=5
        )

    def _create_game_tab(self):
        """Create game control tab"""
        # Game status
        status_frame = ttk.Frame(self.game_frame, style="Dark.TFrame")
        status_frame.pack(fill=tk.X, pady=10)

        ttk.Label(status_frame, text="Game Status:", style="Subtitle.TLabel").pack(
            anchor=tk.W
        )

        self.status_label = ttk.Label(
            status_frame, text="Not Started", style="Title.TLabel", foreground="#e74c3c"
        )
        self.status_label.pack(anchor=tk.W)

        # Phase controls
        phase_frame = ttk.Frame(self.game_frame, style="Dark.TFrame")
        phase_frame.pack(fill=tk.X, pady=10)

        ttk.Label(phase_frame, text="Phase Control:", style="Subtitle.TLabel").pack(
            anchor=tk.W
        )

        phase_buttons = ttk.Frame(phase_frame, style="Dark.TFrame")
        phase_buttons.pack(anchor=tk.W, pady=5)

        self.night_button = ttk.Button(
            phase_buttons, text="🌙 Start Night", command=self._start_night
        )
        self.night_button.pack(side=tk.LEFT, padx=5)

        self.day_button = ttk.Button(
            phase_buttons, text="☀️ Start Day", command=self._start_day
        )
        self.day_button.pack(side=tk.LEFT, padx=5)

        self.nomination_button = ttk.Button(
            phase_buttons, text="🗳️ Open Nominations", command=self._open_nominations
        )
        self.nomination_button.pack(side=tk.LEFT, padx=5)

        # Speech controls
        speech_frame = ttk.Frame(self.game_frame, style="Dark.TFrame")
        speech_frame.pack(fill=tk.X, pady=10)

        ttk.Label(speech_frame, text="Speech Control:", style="Subtitle.TLabel").pack(
            anchor=tk.W
        )

        speech_buttons = ttk.Frame(speech_frame, style="Dark.TFrame")
        speech_buttons.pack(anchor=tk.W, pady=5)

        self.listen_button = ttk.Button(
            speech_buttons, text="🎤 Listen", command=self._toggle_listening
        )
        self.listen_button.pack(side=tk.LEFT, padx=5)

        self.speak_button = ttk.Button(
            speech_buttons, text="🔊 Speak", command=self._manual_speak
        )
        self.speak_button.pack(side=tk.LEFT, padx=5)

        # Manual input for speech
        ttk.Label(
            self.game_frame, text="Manual Announcement:", style="Subtitle.TLabel"
        ).pack(anchor=tk.W, pady=(10, 0))

        self.speech_entry = tk.Text(
            self.game_frame, height=3, bg="#34495e", fg="#ecf0f1", font=("Arial", 11)
        )
        self.speech_entry.pack(fill=tk.X, pady=5)

        # Game log
        ttk.Label(self.game_frame, text="Game Log:", style="Subtitle.TLabel").pack(
            anchor=tk.W, pady=(10, 0)
        )

        self.log_text = scrolledtext.ScrolledText(
            self.game_frame,
            height=15,
            bg="#2c3e50",
            fg="#ecf0f1",
            font=("Consolas", 10),
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)

    def _create_players_tab(self):
        """Create players management tab"""
        # Player list
        self.players_list_frame = ttk.Frame(self.players_frame, style="Dark.TFrame")
        self.players_list_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Will be populated when game starts

    def _create_settings_tab(self):
        """Create settings tab"""
        # Speech settings
        speech_settings = ttk.LabelFrame(self.settings_frame, text="Speech Settings")
        speech_settings.pack(fill=tk.X, pady=10, padx=10)

        # Whisper model
        ttk.Label(speech_settings, text="Whisper Model:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )
        self.whisper_model_var = tk.StringVar(value="base")
        whisper_combo = ttk.Combobox(
            speech_settings,
            textvariable=self.whisper_model_var,
            values=["tiny", "base", "small", "medium", "large"],
            state="readonly",
        )
        whisper_combo.grid(row=0, column=1, padx=5, pady=5)

        # Voice threshold
        ttk.Label(speech_settings, text="Voice Threshold:").grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=5
        )
        self.threshold_var = tk.DoubleVar(value=0.01)
        threshold_scale = ttk.Scale(
            speech_settings,
            from_=0.001,
            to=0.1,
            variable=self.threshold_var,
            orient=tk.HORIZONTAL,
        )
        threshold_scale.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)

        # AI settings
        ai_settings = ttk.LabelFrame(self.settings_frame, text="AI Settings")
        ai_settings.pack(fill=tk.X, pady=10, padx=10)

        # Story complexity
        ttk.Label(ai_settings, text="Story Complexity:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )
        self.complexity_var = tk.StringVar(value="Medium")
        complexity_combo = ttk.Combobox(
            ai_settings,
            textvariable=self.complexity_var,
            values=["Simple", "Medium", "Complex", "Epic"],
            state="readonly",
        )
        complexity_combo.grid(row=0, column=1, padx=5, pady=5)

        # Auto-mode
        self.auto_mode_var = tk.BooleanVar(value=True)
        auto_check = ttk.Checkbutton(
            ai_settings, text="Auto-manage game phases", variable=self.auto_mode_var
        )
        auto_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)

        # Save settings button
        ttk.Button(
            self.settings_frame, text="💾 Save Settings", command=self._save_settings
        ).pack(pady=20)

    def _setup_layout(self):
        """Setup main layout"""
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.title_label.pack(pady=(0, 20))
        self.notebook.pack(fill=tk.BOTH, expand=True)

    def _start_game(self):
        """Start a new game"""
        try:
            # Get player names
            player_names = [
                name.strip()
                for name in self.players_text.get(1.0, tk.END).strip().split("\n")
                if name.strip()
            ]

            if len(player_names) < 5:
                messagebox.showerror(
                    "Error", "Need at least 5 players to start a game!"
                )
                return

            if len(player_names) > 20:
                messagebox.showerror("Error", "Maximum 20 players allowed!")
                return

            # Initialize background thread for async operations
            self._start_background_thread()

            # Schedule game start
            asyncio.run_coroutine_threadsafe(
                self._async_start_game(player_names), self.event_loop
            )

            # Update UI
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.status_label.config(text="Starting...", foreground="#f39c12")

            self._log("🎭 Starting new game...")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start game: {e}")
            self.logger.error(f"Failed to start game: {e}")

    async def _async_start_game(self, player_names: List[str]):
        """Async game initialization"""
        try:
            # Initialize speech handler
            config = SpeechConfig(
                whisper_model=self.whisper_model_var.get(),
                tts_voice=self.voice_var.get(),
                vad_threshold=self.threshold_var.get(),
            )

            self.speech_handler = SpeechHandler(config)
            await self.speech_handler.initialize()

            # Initialize storyteller
            self.storyteller = AIStoryteller(
                llm_client=None,  # Will need to implement LLM client
                speech_handler=self.speech_handler,
                character_data=None,  # Will need to implement character data
            )

            # Start the game
            await self.storyteller.start_new_game(player_names)
            self.game_state = self.storyteller.game_state

            # Update UI on main thread
            self.root.after(0, self._on_game_started)

        except Exception as error:
            error_msg = str(error)
            self.root.after(0, lambda: self._on_game_error(error_msg))

    def _on_game_started(self):
        """Called when game successfully starts"""
        self.is_running = True
        self.status_label.config(text="Game Running", foreground="#27ae60")
        self._log("Game started successfully!")
        self._update_players_display()

    def _on_game_error(self, error: str):
        """Called when game fails to start"""
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Error", foreground="#e74c3c")
        self._log(f"❌ Error: {error}")
        messagebox.showerror("Game Error", error)

    def _stop_game(self):
        """Stop the current game"""
        if self.storyteller:
            self.is_running = False

            # Cleanup
            if self.speech_handler:
                self.speech_handler.cleanup()

            # Update UI
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.status_label.config(text="Stopped", foreground="#e74c3c")

            self._log("⏹️ Game stopped")

    def _start_background_thread(self):
        """Start background thread for async operations"""
        if self.background_thread and self.background_thread.is_alive():
            return

        self.background_thread = threading.Thread(
            target=self._run_event_loop, daemon=True
        )
        self.background_thread.start()

    def _run_event_loop(self):
        """Run async event loop in background thread"""
        self.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.event_loop)
        self.event_loop.run_forever()

    def _start_night(self):
        """Start night phase"""
        if self.storyteller and self.is_running:
            asyncio.run_coroutine_threadsafe(
                self.storyteller._transition_to_night(), self.event_loop
            )
            self._log("🌙 Starting night phase...")

    def _start_day(self):
        """Start day phase"""
        if self.storyteller and self.is_running:
            asyncio.run_coroutine_threadsafe(
                self.storyteller._transition_to_day(), self.event_loop
            )
            self._log("☀️ Starting day phase...")

    def _open_nominations(self):
        """Open nominations"""
        if self.storyteller and self.is_running:
            asyncio.run_coroutine_threadsafe(
                self.storyteller._handle_nominations(), self.event_loop
            )
            self._log("🗳️ Opening nominations...")

    def _toggle_listening(self):
        """Toggle speech listening"""
        if self.speech_handler and self.is_running:
            self._log("🎤 Listening for speech...")

    def _manual_speak(self):
        """Speak manual text"""
        text = self.speech_entry.get(1.0, tk.END).strip()
        if text and self.speech_handler and self.is_running:
            asyncio.run_coroutine_threadsafe(
                self.speech_handler.speak(text), self.event_loop
            )
            self._log(f"🔊 Speaking: {text[:50]}...")
            self.speech_entry.delete(1.0, tk.END)

    def _update_players_display(self):
        """Update players tab display"""
        # Clear existing widgets
        for widget in self.players_list_frame.winfo_children():
            widget.destroy()

        if not self.game_state:
            return

        # Create player cards
        for i, player in enumerate(self.game_state.players):
            player_frame = ttk.Frame(self.players_list_frame, style="Player.TFrame")
            player_frame.pack(fill=tk.X, pady=2, padx=5)

            # Player info
            info_text = f"#{player.seat_position + 1}: {player.name}"
            if player.character:
                info_text += f" ({player.character})"

            status_color = "#27ae60" if player.is_alive() else "#e74c3c"

            player_label = ttk.Label(
                player_frame, text=info_text, font=("Arial", 11, "bold")
            )
            player_label.pack(side=tk.LEFT, padx=10, pady=5)

            # Status indicator
            status_text = "ALIVE" if player.is_alive() else "DEAD"
            status_label = tk.Label(
                player_frame,
                text=status_text,
                fg=status_color,
                bg="#34495e",
                font=("Arial", 10, "bold"),
            )
            status_label.pack(side=tk.RIGHT, padx=10, pady=5)

    def _save_setup(self):
        """Save current setup to file"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json")],
                title="Save Game Setup",
            )

            if filename:
                setup_data = {
                    "players": self.players_text.get(1.0, tk.END).strip().split("\n"),
                    "script": self.script_var.get(),
                    "voice": self.voice_var.get(),
                    "whisper_model": self.whisper_model_var.get(),
                    "threshold": self.threshold_var.get(),
                    "complexity": self.complexity_var.get(),
                    "auto_mode": self.auto_mode_var.get(),
                }

                with open(filename, "w") as f:
                    json.dump(setup_data, f, indent=2)

                self._log(f"💾 Setup saved to {filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save setup: {e}")

    def _load_setup(self):
        """Load setup from file"""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json")], title="Load Game Setup"
            )

            if filename:
                with open(filename, "r") as f:
                    setup_data = json.load(f)

                # Apply loaded settings
                self.players_text.delete(1.0, tk.END)
                self.players_text.insert(1.0, "\n".join(setup_data.get("players", [])))

                self.script_var.set(setup_data.get("script", "trouble_brewing"))
                self.voice_var.set(setup_data.get("voice", "en_US-lessac-medium"))
                self.whisper_model_var.set(setup_data.get("whisper_model", "base"))
                self.threshold_var.set(setup_data.get("threshold", 0.01))
                self.complexity_var.set(setup_data.get("complexity", "Medium"))
                self.auto_mode_var.set(setup_data.get("auto_mode", True))

                self._log(f"📂 Setup loaded from {filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load setup: {e}")

    def _save_settings(self):
        """Save current settings"""
        settings = {
            "whisper_model": self.whisper_model_var.get(),
            "threshold": self.threshold_var.get(),
            "complexity": self.complexity_var.get(),
            "auto_mode": self.auto_mode_var.get(),
        }

        try:
            with open("settings.json", "w") as f:
                json.dump(settings, f, indent=2)
            self._log("💾 Settings saved")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")

    def _log(self, message: str):
        """Add message to game log"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)

    def on_closing(self):
        """Handle window closing"""
        if self.is_running:
            if messagebox.askokcancel(
                "Quit", "Game is running. Are you sure you want to quit?"
            ):
                self._stop_game()
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    """Main function to run the Windows GUI app"""
    # Check for first run and download models if needed
    try:
        from ..utils.first_run_setup import run_first_time_setup

        run_first_time_setup()
    except ImportError:
        # If running from source without proper package structure
        import os
        import sys

        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from utils.first_run_setup import run_first_time_setup

        run_first_time_setup()

    # Start main application
    root = tk.Tk()
    app = MainWindow(root)

    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    # Start the GUI
    root.mainloop()


if __name__ == "__main__":
    main()
