"""
Timing Controls Widget for Storyteller Dashboard
Provides UI for managing game pacing
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from ..core.timing_config import PacingStyle, TimingConfig, TimingManager


class TimingControlsFrame:
    """Frame containing timing controls for the storyteller"""

    def __init__(self, parent: tk.Widget, on_config_change: Optional[Callable] = None):
        self.parent = parent
        self.on_config_change = on_config_change

        # Create the timing manager
        self.timing_manager = TimingManager()

        # Create the main frame
        self.frame = ttk.LabelFrame(parent, text="⏰ Game Timing", style="Dark.TFrame")

        self._create_widgets()

    def _create_widgets(self):
        """Create timing control widgets"""

        # Pacing style selector
        style_frame = ttk.Frame(self.frame, style="Dark.TFrame")
        style_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(
            style_frame,
            text="Pacing Style:",
            foreground="#ffffff",
            background="#1a1a1a",
        ).pack(side="left", padx=(0, 10))

        self.pacing_var = tk.StringVar(value="standard")
        self.pacing_combo = ttk.Combobox(
            style_frame,
            textvariable=self.pacing_var,
            values=["quick", "standard", "relaxed", "custom"],
            state="readonly",
            width=15,
        )
        self.pacing_combo.pack(side="left")
        self.pacing_combo.bind("<<ComboboxSelected>>", self._on_pacing_change)

        # Timer display
        self.timer_frame = ttk.Frame(self.frame, style="Dark.TFrame")
        self.timer_frame.pack(fill="x", padx=10, pady=10)

        self.timer_label = ttk.Label(
            self.timer_frame,
            text="No active timer",
            font=("Segoe UI", 14, "bold"),
            foreground="#4ecdc4",
            background="#1a1a1a",
        )
        self.timer_label.pack()

        self.phase_timer_label = ttk.Label(
            self.timer_frame,
            text="",
            font=("Segoe UI", 10),
            foreground="#888888",
            background="#1a1a1a",
        )
        self.phase_timer_label.pack()

        # Control buttons
        button_frame = ttk.Frame(self.frame, style="Dark.TFrame")
        button_frame.pack(fill="x", padx=10, pady=5)

        self.extend_button = ttk.Button(
            button_frame,
            text="⏱️ Extend Time",
            command=self._request_extension,
            style="Action.TButton",
        )
        self.extend_button.pack(side="left", padx=2)

        self.skip_button = ttk.Button(
            button_frame,
            text="⏭️ Skip Timer",
            command=self._skip_timer,
            style="Action.TButton",
        )
        self.skip_button.pack(side="left", padx=2)

        # Custom timing controls (hidden by default)
        self.custom_frame = ttk.Frame(self.frame, style="Dark.TFrame")

        # Night phase duration
        self._create_time_slider(
            self.custom_frame, "Night Phase (min):", "night_duration", 1, 10, 3
        )

        # Day discussion duration
        self._create_time_slider(
            self.custom_frame, "Day Discussion (min):", "day_duration", 3, 20, 5
        )

        # Nomination discussion
        self._create_time_slider(
            self.custom_frame, "Per Nomination (min):", "nomination_duration", 1, 5, 2
        )

        # Voting countdown
        self._create_time_slider(
            self.custom_frame, "Voting Time (sec):", "voting_duration", 15, 60, 30
        )

        # Flexibility options
        flex_frame = ttk.Frame(self.frame, style="Dark.TFrame")
        flex_frame.pack(fill="x", padx=10, pady=10)

        self.allow_extensions_var = tk.BooleanVar(value=True)
        self.allow_extensions_check = ttk.Checkbutton(
            flex_frame,
            text="Allow time extensions",
            variable=self.allow_extensions_var,
            command=self._on_config_change,
        )
        self.allow_extensions_check.pack(anchor="w")

        self.auto_extend_var = tk.BooleanVar(value=True)
        self.auto_extend_check = ttk.Checkbutton(
            flex_frame,
            text="Auto-extend heated discussions",
            variable=self.auto_extend_var,
            command=self._on_config_change,
        )
        self.auto_extend_check.pack(anchor="w")

        # Status display
        self.status_frame = ttk.Frame(self.frame, style="Dark.TFrame")
        self.status_frame.pack(fill="x", padx=10, pady=5)

        self.status_label = ttk.Label(
            self.status_frame,
            text="💡 Timing is flexible - these are suggestions only",
            font=("Segoe UI", 9, "italic"),
            foreground="#666666",
            background="#1a1a1a",
        )
        self.status_label.pack()

    def _create_time_slider(
        self,
        parent: tk.Widget,
        label: str,
        var_name: str,
        min_val: int,
        max_val: int,
        default: int,
    ):
        """Create a time adjustment slider"""

        frame = ttk.Frame(parent, style="Dark.TFrame")
        frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(
            frame, text=label, foreground="#ffffff", background="#1a1a1a", width=20
        ).pack(side="left")

        var = tk.IntVar(value=default)
        setattr(self, f"{var_name}_var", var)

        slider = ttk.Scale(
            frame,
            from_=min_val,
            to=max_val,
            variable=var,
            orient="horizontal",
            command=lambda v: self._on_slider_change(var_name, v),
        )
        slider.pack(side="left", fill="x", expand=True, padx=10)

        value_label = ttk.Label(
            frame,
            text=str(default),
            foreground="#4ecdc4",
            background="#1a1a1a",
            width=5,
        )
        value_label.pack(side="left")
        setattr(self, f"{var_name}_label", value_label)

    def _on_pacing_change(self, event=None):
        """Handle pacing style change"""
        style = self.pacing_var.get()

        if style == "custom":
            self.custom_frame.pack(fill="x", padx=10, pady=10)
        else:
            self.custom_frame.pack_forget()

            # Apply preset
            if style == "quick":
                config = TimingConfig.quick_game()
            elif style == "relaxed":
                config = TimingConfig.relaxed_game()
            else:
                config = TimingConfig.standard_game()

            self.timing_manager.config = config

        self._on_config_change()

    def _on_slider_change(self, var_name: str, value: str):
        """Handle slider value change"""
        val = int(float(value))
        getattr(self, f"{var_name}_label").config(text=str(val))

        # Update custom config
        if self.pacing_var.get() == "custom":
            self._apply_custom_config()

    def _apply_custom_config(self):
        """Apply custom timing configuration"""
        config = TimingConfig(
            night_phase_duration=self.night_duration_var.get() * 60,
            day_discussion_time=self.day_duration_var.get() * 60,
            nomination_discussion=self.nomination_duration_var.get() * 60,
            voting_countdown=self.voting_duration_var.get(),
            pacing_style=PacingStyle.CUSTOM,
            allow_extensions=self.allow_extensions_var.get(),
            auto_extend_heated=self.auto_extend_var.get(),
        )

        self.timing_manager.config = config
        self._on_config_change()

    def _request_extension(self):
        """Handle time extension request"""
        # This would be called by players or storyteller
        response = self.timing_manager.request_extension("current_phase")
        self.status_label.config(text=f"⏱️ {response}")

    def _skip_timer(self):
        """Skip current timer"""
        self.status_label.config(text="⏭️ Timer skipped - moving on!")

    def _on_config_change(self):
        """Notify parent of config change"""
        if self.on_config_change:
            self.on_config_change(self.timing_manager.config)

    def start_phase_timer(self, phase_name: str, context: dict = None):
        """Start timing for a new phase"""
        suggestion = self.timing_manager.start_phase(phase_name)

        # Update display
        phase_display = phase_name.replace("_", " ").title()
        self.timer_label.config(text=f"⏰ {phase_display} Active")
        self.phase_timer_label.config(text=suggestion)

        # Start update loop
        self._update_timer_display(phase_name)

    def _update_timer_display(self, phase_name: str):
        """Update timer display"""
        import time

        if phase_name not in self.timing_manager.phase_start_times:
            return

        elapsed = time.time() - self.timing_manager.phase_start_times[phase_name]
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)

        self.timer_label.config(text=f"⏰ {minutes:02d}:{seconds:02d}")

        # Check for reminders
        reminder = self.timing_manager.check_timing(phase_name)
        if reminder:
            self.status_label.config(text=reminder)

        # Schedule next update
        self.frame.after(1000, lambda: self._update_timer_display(phase_name))

    def get_timing_manager(self) -> TimingManager:
        """Get the timing manager instance"""
        return self.timing_manager

    def get_frame(self) -> ttk.Frame:
        """Get the main frame widget"""
        return self.frame
