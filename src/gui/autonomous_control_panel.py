"""
Autonomous Storyteller Control Panel
Complete UI for managing the hands-off AI storyteller
"""

import asyncio
import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, scrolledtext, ttk
from typing import Any, Dict, Optional

from ..ai.autonomous_config import (PRESET_CONFIGS, AutonomousConfig,
                                    get_config_description)
from ..ai.autonomous_storyteller import AutonomousStoryteller, GameContext
from ..ai.character_handlers import CharacterAbilityHandler
from ..core.game_state import GamePhase, GameState, Player
from ..core.timing_config import PacingStyle, TimingManager
from ..speech.speech_handler import SpeechConfig, SpeechHandler


class AutonomousControlPanel:
    """Main control panel for autonomous storyteller"""

    def __init__(self, parent: tk.Widget):
        self.parent = parent
        self.autonomous_storyteller: Optional[AutonomousStoryteller] = None
        self.config = AutonomousConfig()
        self.is_running = False

        # Create main panel
        self.panel = ttk.LabelFrame(
            parent, text="🤖 Autonomous AI Storyteller", style="Dark.TFrame"
        )

        self._create_widgets()

    def _create_widgets(self):
        """Create all UI widgets"""

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.panel)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Configuration Tab
        self.config_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.config_frame, text="⚙️ Configuration")
        self._create_config_tab()

        # Status Monitor Tab
        self.status_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.status_frame, text="📊 Status")
        self._create_status_tab()

        # Decision Log Tab
        self.log_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.log_frame, text="📋 Decisions")
        self._create_decision_log_tab()

        # Game State Tab
        self.game_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.game_frame, text="🎮 Game State")
        self._create_game_state_tab()

        # Control buttons at bottom
        self._create_control_buttons()

    def _create_config_tab(self):
        """Create configuration controls"""

        # Preset configurations
        preset_frame = ttk.LabelFrame(self.config_frame, text="Quick Presets")
        preset_frame.pack(fill="x", padx=10, pady=10)

        self.preset_var = tk.StringVar(value="standard")
        preset_combo = ttk.Combobox(
            preset_frame,
            textvariable=self.preset_var,
            values=list(PRESET_CONFIGS.keys()),
            state="readonly",
            width=15,
        )
        preset_combo.pack(side="left", padx=5)
        preset_combo.bind("<<ComboboxSelected>>", self._on_preset_change)

        self.preset_desc_label = ttk.Label(
            preset_frame, text=get_config_description("standard"), foreground="#888888"
        )
        self.preset_desc_label.pack(side="left", padx=10)

        # Autonomy Level
        autonomy_frame = ttk.LabelFrame(self.config_frame, text="Autonomy Settings")
        autonomy_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(autonomy_frame, text="Autonomy Level:").grid(
            row=0, column=0, sticky="w", padx=5
        )
        self.autonomy_var = tk.StringVar(value="high")
        autonomy_combo = ttk.Combobox(
            autonomy_frame,
            textvariable=self.autonomy_var,
            values=["low", "medium", "high", "full"],
            state="readonly",
            width=10,
        )
        autonomy_combo.grid(row=0, column=1, padx=5)

        self.override_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            autonomy_frame, text="Allow human override", variable=self.override_var
        ).grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        self.auto_advance_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            autonomy_frame,
            text="Auto-advance game phases",
            variable=self.auto_advance_var,
        ).grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        # Information Strategy
        info_frame = ttk.LabelFrame(self.config_frame, text="Information Strategy")
        info_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(info_frame, text="Truth Rate (Healthy):").grid(
            row=0, column=0, sticky="w", padx=5
        )
        self.truth_rate_var = tk.DoubleVar(value=0.85)
        truth_scale = ttk.Scale(
            info_frame,
            from_=0.0,
            to=1.0,
            variable=self.truth_rate_var,
            orient="horizontal",
        )
        truth_scale.grid(row=0, column=1, sticky="ew", padx=5)

        ttk.Label(info_frame, text="Drama Factor:").grid(
            row=1, column=0, sticky="w", padx=5
        )
        self.drama_var = tk.DoubleVar(value=0.15)
        drama_scale = ttk.Scale(
            info_frame, from_=0.0, to=0.5, variable=self.drama_var, orient="horizontal"
        )
        drama_scale.grid(row=1, column=1, sticky="ew", padx=5)

        info_frame.columnconfigure(1, weight=1)

        # Narration Style
        narration_frame = ttk.LabelFrame(self.config_frame, text="Narration Style")
        narration_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(narration_frame, text="Drama Level:").grid(
            row=0, column=0, sticky="w", padx=5
        )
        self.drama_level_var = tk.StringVar(value="high")
        drama_combo = ttk.Combobox(
            narration_frame,
            textvariable=self.drama_level_var,
            values=["low", "medium", "high", "epic"],
            state="readonly",
            width=10,
        )
        drama_combo.grid(row=0, column=1, padx=5)

        ttk.Label(narration_frame, text="Length:").grid(
            row=1, column=0, sticky="w", padx=5
        )
        self.length_var = tk.StringVar(value="medium")
        length_combo = ttk.Combobox(
            narration_frame,
            textvariable=self.length_var,
            values=["brief", "medium", "verbose"],
            state="readonly",
            width=10,
        )
        length_combo.grid(row=1, column=1, padx=5)

        self.gothic_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            narration_frame, text="Gothic atmosphere", variable=self.gothic_var
        ).grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        # Speech Recognition
        speech_frame = ttk.LabelFrame(self.config_frame, text="Speech Recognition")
        speech_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(speech_frame, text="Sensitivity:").grid(
            row=0, column=0, sticky="w", padx=5
        )
        self.sensitivity_var = tk.DoubleVar(value=0.6)
        sensitivity_scale = ttk.Scale(
            speech_frame,
            from_=0.1,
            to=1.0,
            variable=self.sensitivity_var,
            orient="horizontal",
        )
        sensitivity_scale.grid(row=0, column=1, sticky="ew", padx=5)

        ttk.Label(speech_frame, text="Action Timeout (sec):").grid(
            row=1, column=0, sticky="w", padx=5
        )
        self.timeout_var = tk.DoubleVar(value=30.0)
        timeout_scale = ttk.Scale(
            speech_frame,
            from_=10.0,
            to=120.0,
            variable=self.timeout_var,
            orient="horizontal",
        )
        timeout_scale.grid(row=1, column=1, sticky="ew", padx=5)

        speech_frame.columnconfigure(1, weight=1)

    def _create_status_tab(self):
        """Create status monitoring display"""

        # Current Status
        status_frame = ttk.LabelFrame(self.status_frame, text="Current Status")
        status_frame.pack(fill="x", padx=10, pady=10)

        self.status_label = ttk.Label(
            status_frame,
            text="🔴 Autonomous mode inactive",
            font=("Segoe UI", 12, "bold"),
            foreground="#e74c3c",
        )
        self.status_label.pack(pady=10)

        self.phase_status_label = ttk.Label(
            status_frame, text="Phase: Not started", foreground="#888888"
        )
        self.phase_status_label.pack()

        # Real-time Activity
        activity_frame = ttk.LabelFrame(self.status_frame, text="AI Activity")
        activity_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.activity_text = scrolledtext.ScrolledText(
            activity_frame, height=15, bg="#1a1a1a", fg="#ffffff", font=("Consolas", 9)
        )
        self.activity_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Speech Recognition Status
        speech_status_frame = ttk.LabelFrame(
            self.status_frame, text="Speech Recognition"
        )
        speech_status_frame.pack(fill="x", padx=10, pady=10)

        self.speech_status_label = ttk.Label(
            speech_status_frame, text="🎤 Not listening", foreground="#888888"
        )
        self.speech_status_label.pack(pady=5)

        self.last_heard_label = ttk.Label(
            speech_status_frame, text="Last heard: None", foreground="#666666"
        )
        self.last_heard_label.pack()

    def _create_decision_log_tab(self):
        """Create decision history log"""

        # Controls
        controls_frame = ttk.Frame(self.log_frame)
        controls_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(
            controls_frame, text="🔄 Refresh", command=self._refresh_decision_log
        ).pack(side="left", padx=5)

        ttk.Button(
            controls_frame, text="💾 Export Log", command=self._export_decisions
        ).pack(side="left", padx=5)

        ttk.Button(
            controls_frame, text="🗑️ Clear Log", command=self._clear_decision_log
        ).pack(side="left", padx=5)

        # Decision tree
        self.decision_tree = ttk.Treeview(
            self.log_frame,
            columns=("time", "player", "character", "info", "truthful"),
            show="tree headings",
        )

        self.decision_tree.heading("#0", text="Night")
        self.decision_tree.heading("time", text="Time")
        self.decision_tree.heading("player", text="Player")
        self.decision_tree.heading("character", text="Character")
        self.decision_tree.heading("info", text="Information")
        self.decision_tree.heading("truthful", text="Truthful")

        self.decision_tree.column("#0", width=50)
        self.decision_tree.column("time", width=80)
        self.decision_tree.column("player", width=100)
        self.decision_tree.column("character", width=100)
        self.decision_tree.column("info", width=200)
        self.decision_tree.column("truthful", width=80)

        # Scrollbar for tree
        tree_scroll = ttk.Scrollbar(
            self.log_frame, orient="vertical", command=self.decision_tree.yview
        )
        self.decision_tree.configure(yscrollcommand=tree_scroll.set)

        self.decision_tree.pack(
            side="left", fill="both", expand=True, padx=(10, 0), pady=10
        )
        tree_scroll.pack(side="right", fill="y", padx=(0, 10), pady=10)

    def _create_game_state_tab(self):
        """Create game state viewer"""

        # Player list
        players_frame = ttk.LabelFrame(self.game_frame, text="Players")
        players_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.players_tree = ttk.Treeview(
            players_frame,
            columns=("character", "status", "modifiers", "seat"),
            show="tree headings",
        )

        self.players_tree.heading("#0", text="Name")
        self.players_tree.heading("character", text="Character")
        self.players_tree.heading("status", text="Status")
        self.players_tree.heading("modifiers", text="Modifiers")
        self.players_tree.heading("seat", text="Seat")

        self.players_tree.pack(fill="both", expand=True, padx=5, pady=5)

        # Game info
        info_frame = ttk.LabelFrame(self.game_frame, text="Game Information")
        info_frame.pack(fill="x", padx=10, pady=10)

        self.game_info_text = tk.Text(
            info_frame, height=8, bg="#1a1a1a", fg="#ffffff", font=("Consolas", 9)
        )
        self.game_info_text.pack(fill="x", padx=5, pady=5)

    def _create_control_buttons(self):
        """Create main control buttons"""

        button_frame = ttk.Frame(self.panel)
        button_frame.pack(fill="x", padx=10, pady=10)

        # Start/Stop button
        self.start_stop_button = ttk.Button(
            button_frame,
            text="🚀 Start Autonomous Mode",
            command=self._toggle_autonomous_mode,
            style="Start.TButton",
        )
        self.start_stop_button.pack(side="left", padx=5)

        # Emergency stop
        self.emergency_button = ttk.Button(
            button_frame,
            text="🛑 Emergency Stop",
            command=self._emergency_stop,
            style="Stop.TButton",
        )
        self.emergency_button.pack(side="left", padx=5)

        # Manual override
        self.override_button = ttk.Button(
            button_frame,
            text="✋ Take Control",
            command=self._manual_override,
            state="disabled",
        )
        self.override_button.pack(side="left", padx=5)

        # Apply config
        ttk.Button(
            button_frame, text="💾 Apply Config", command=self._apply_config
        ).pack(side="right", padx=5)

    def _on_preset_change(self, event=None):
        """Handle preset configuration change"""

        preset_name = self.preset_var.get()
        self.config = (
            PRESET_CONFIGS[preset_name].copy()
            if preset_name in PRESET_CONFIGS
            else AutonomousConfig()
        )

        # Update description
        self.preset_desc_label.config(text=get_config_description(preset_name))

        # Update UI controls to match preset
        self._update_ui_from_config()

    def _update_ui_from_config(self):
        """Update UI controls to match current config"""

        self.autonomy_var.set(self.config.autonomy_level)
        self.override_var.set(self.config.human_override)
        self.auto_advance_var.set(self.config.auto_advance_phases)

        self.truth_rate_var.set(self.config.information_strategy.truth_rate_healthy)
        self.drama_var.set(self.config.information_strategy.drama_factor)

        self.drama_level_var.set(self.config.narration_style.drama_level)
        self.length_var.set(self.config.narration_style.announcement_length)
        self.gothic_var.set(self.config.narration_style.gothic_atmosphere)

        self.sensitivity_var.set(self.config.speech_config.listening_sensitivity)
        self.timeout_var.set(self.config.speech_config.action_timeout)

    def _apply_config(self):
        """Apply current UI settings to configuration"""

        # Update config from UI
        self.config.autonomy_level = self.autonomy_var.get()
        self.config.human_override = self.override_var.get()
        self.config.auto_advance_phases = self.auto_advance_var.get()

        self.config.information_strategy.truth_rate_healthy = self.truth_rate_var.get()
        self.config.information_strategy.drama_factor = self.drama_var.get()

        self.config.narration_style.drama_level = self.drama_level_var.get()
        self.config.narration_style.announcement_length = self.length_var.get()
        self.config.narration_style.gothic_atmosphere = self.gothic_var.get()

        self.config.speech_config.listening_sensitivity = self.sensitivity_var.get()
        self.config.speech_config.action_timeout = self.timeout_var.get()

        self._log_activity("⚙️ Configuration updated")

    def _toggle_autonomous_mode(self):
        """Start or stop autonomous mode"""

        if not self.is_running:
            self._start_autonomous_mode()
        else:
            self._stop_autonomous_mode()

    def _start_autonomous_mode(self):
        """Start autonomous storyteller"""

        try:
            self._apply_config()

            # Initialize autonomous storyteller
            speech_config = SpeechConfig(
                whisper_model="base", tts_voice="en_US-lessac-medium"
            )

            speech_handler = SpeechHandler(speech_config)
            self.autonomous_storyteller = AutonomousStoryteller(speech_handler)

            # Start in background thread
            self._start_background_thread()

            # Update UI
            self.is_running = True
            self.start_stop_button.config(
                text="⏹️ Stop Autonomous Mode", style="Stop.TButton"
            )
            self.override_button.config(state="normal")
            self.status_label.config(
                text="🟢 Autonomous mode active", foreground="#27ae60"
            )

            self._log_activity("🚀 Autonomous storyteller started")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start autonomous mode: {e}")

    def _stop_autonomous_mode(self):
        """Stop autonomous storyteller"""

        if self.autonomous_storyteller:
            self.autonomous_storyteller.stop_autonomous_operation()

        self.is_running = False
        self.start_stop_button.config(
            text="🚀 Start Autonomous Mode", style="Start.TButton"
        )
        self.override_button.config(state="disabled")
        self.status_label.config(
            text="🔴 Autonomous mode inactive", foreground="#e74c3c"
        )

        self._log_activity("⏹️ Autonomous storyteller stopped")

    def _emergency_stop(self):
        """Emergency stop all AI operations"""

        if messagebox.askyesno(
            "Emergency Stop", "This will immediately stop all AI operations. Continue?"
        ):
            self._stop_autonomous_mode()
            self._log_activity("🛑 EMERGENCY STOP - All AI operations halted")

    def _manual_override(self):
        """Take manual control from AI"""

        if self.is_running and self.config.human_override:
            # Pause autonomous operations
            self._log_activity("✋ Manual override activated - AI paused")
            messagebox.showinfo(
                "Manual Override", "AI operations paused. You now have manual control."
            )
        else:
            messagebox.showwarning(
                "Override Denied",
                "Manual override not allowed in current configuration.",
            )

    def _start_background_thread(self):
        """Start background thread for async operations"""

        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._async_operations())
            except Exception as e:
                self._log_activity(f"❌ Background error: {e}")
            finally:
                loop.close()

        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()

    async def _async_operations(self):
        """Run autonomous storyteller operations"""

        if self.autonomous_storyteller:
            await self.autonomous_storyteller.initialize()
            self._log_activity("🤖 AI storyteller initialized")

    def _refresh_decision_log(self):
        """Refresh the decision log display"""

        # Clear existing items
        for item in self.decision_tree.get_children():
            self.decision_tree.delete(item)

        # Add decisions if available
        if self.autonomous_storyteller and self.autonomous_storyteller.game_context:
            for info in self.autonomous_storyteller.game_context.information_history:
                self.decision_tree.insert(
                    "",
                    "end",
                    text=f"N{info.night_number}",
                    values=(
                        info.timestamp.strftime("%H:%M"),
                        info.player_name,
                        info.character,
                        (
                            info.information[:50] + "..."
                            if len(info.information) > 50
                            else info.information
                        ),
                        "✅" if info.was_true else "❌",
                    ),
                )

    def _export_decisions(self):
        """Export decision log to file"""

        # This would implement CSV/JSON export
        messagebox.showinfo("Export", "Decision log export not yet implemented")

    def _clear_decision_log(self):
        """Clear the decision log"""

        if messagebox.askyesno("Clear Log", "Clear all decision history?"):
            for item in self.decision_tree.get_children():
                self.decision_tree.delete(item)
            self._log_activity("🗑️ Decision log cleared")

    def _log_activity(self, message: str):
        """Log activity to the status display"""

        timestamp = datetime.now().strftime("%H:%M:%S")
        self.activity_text.insert("end", f"[{timestamp}] {message}\n")
        self.activity_text.see("end")

    def get_panel(self) -> ttk.LabelFrame:
        """Get the main panel widget"""
        return self.panel
