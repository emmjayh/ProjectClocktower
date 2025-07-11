"""
Integration of Autonomous Control Panel into Main Storyteller Dashboard
Shows how to add the autonomous AI controls to the existing interface
"""

try:
    import tkinter as tk
    from tkinter import ttk
    from .autonomous_control_panel import AutonomousControlPanel
    GUI_AVAILABLE = True
except ImportError:
    # Mock objects for systems without GUI
    class MockTk:
        def __init__(self, *args, **kwargs): pass
        def pack(self, *args, **kwargs): pass
        def add(self, *args, **kwargs): pass
    tk = MockTk()
    ttk = MockTk()
    AutonomousControlPanel = MockTk
    GUI_AVAILABLE = False

# This would be added to storyteller_dashboard.py or main_window.py


def integrate_autonomous_controls(self):
    """Add autonomous storyteller controls to the main dashboard"""

    from .autonomous_control_panel import AutonomousControlPanel

    # Add autonomous control panel to the right panel or create new tab
    if hasattr(self, "right_panel"):
        # Add to existing right panel
        self.autonomous_panel = AutonomousControlPanel(self.right_panel)
        self.autonomous_panel.get_panel().pack(fill="both", expand=True, padx=5, pady=5)
    elif hasattr(self, "notebook"):
        # Add as new tab to existing notebook
        autonomous_frame = ttk.Frame(self.notebook)
        self.notebook.add(autonomous_frame, text="🤖 Autonomous AI")

        self.autonomous_panel = AutonomousControlPanel(autonomous_frame)
        self.autonomous_panel.get_panel().pack(
            fill="both", expand=True, padx=10, pady=10
        )
    else:
        # Create new window
        self._create_autonomous_window()

    # Connect to existing speech handler if available
    if hasattr(self, "speech_handler"):
        self._connect_autonomous_to_speech()

    # Connect to game state updates
    if hasattr(self, "game_state"):
        self._connect_autonomous_to_game_state()


def _create_autonomous_window(self):
    """Create separate window for autonomous controls"""

    self.autonomous_window = tk.Toplevel(self.root)
    self.autonomous_window.title("🤖 Autonomous AI Storyteller")
    self.autonomous_window.geometry("800x600")

    self.autonomous_panel = AutonomousControlPanel(self.autonomous_window)
    self.autonomous_panel.get_panel().pack(fill="both", expand=True, padx=10, pady=10)


def _connect_autonomous_to_speech(self):
    """Connect autonomous system to existing speech handler"""

    # Share speech handler between manual and autonomous modes
    if hasattr(self.autonomous_panel, "autonomous_storyteller"):
        autonomous_st = self.autonomous_panel.autonomous_storyteller
        if autonomous_st:
            autonomous_st.speech_handler = self.speech_handler


def _connect_autonomous_to_game_state(self):
    """Connect autonomous system to game state updates"""

    # Update autonomous system when game state changes
    def on_game_state_change():
        if hasattr(self.autonomous_panel, "autonomous_storyteller"):
            autonomous_st = self.autonomous_panel.autonomous_storyteller
            if autonomous_st:
                autonomous_st.game_state = self.game_state

    # This would be called whenever game state updates
    self.on_game_state_change = on_game_state_change


# Example of enhanced storyteller dashboard with autonomous controls
class EnhancedStorytellerDashboard:
    """Enhanced dashboard with autonomous AI integration"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("🎭 Blood on the Clocktower - Enhanced AI Storyteller")
        self.root.geometry("1800x1000")  # Larger for autonomous controls

        # Initialize existing components
        self._setup_base_dashboard()

        # Add autonomous controls
        self._setup_autonomous_integration()

        # Setup coordination between manual and autonomous modes
        self._setup_mode_coordination()

    def _setup_base_dashboard(self):
        """Setup the base storyteller dashboard"""

        # This would include all the existing dashboard components:
        # - Connection controls
        # - Game phase management
        # - Speech controls
        # - Player grimoire
        # - etc.

        # Create main layout
        self.main_paned = ttk.PanedWindow(self.root, orient="horizontal")
        self.main_paned.pack(fill="both", expand=True, padx=10, pady=10)

        # Left panel - traditional controls
        self.left_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.left_frame, weight=1)

        # Right panel - autonomous controls
        self.right_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.right_frame, weight=1)

        self._create_traditional_controls()

    def _create_traditional_controls(self):
        """Create traditional manual storyteller controls"""

        # Connection frame
        conn_frame = ttk.LabelFrame(self.left_frame, text="Platform Connection")
        conn_frame.pack(fill="x", padx=10, pady=10)

        # Platform selection
        ttk.Label(conn_frame, text="Platform:").grid(
            row=0, column=0, sticky="w", padx=5
        )
        self.platform_var = tk.StringVar(value="clocktower.online")
        platform_combo = ttk.Combobox(
            conn_frame,
            textvariable=self.platform_var,
            values=["clocktower.online", "botc.app"],
            state="readonly",
        )
        platform_combo.grid(row=0, column=1, padx=5, pady=5)

        # Room code
        ttk.Label(conn_frame, text="Room Code:").grid(
            row=1, column=0, sticky="w", padx=5
        )
        self.room_var = tk.StringVar()
        room_entry = ttk.Entry(conn_frame, textvariable=self.room_var, width=20)
        room_entry.grid(row=1, column=1, padx=5, pady=5)

        # Connect button
        self.connect_button = ttk.Button(
            conn_frame, text="🔗 Connect", command=self._connect_to_platform
        )
        self.connect_button.grid(row=2, column=0, columnspan=2, pady=10)

        # Manual game controls
        control_frame = ttk.LabelFrame(self.left_frame, text="Manual Game Control")
        control_frame.pack(fill="x", padx=10, pady=10)

        # Phase buttons
        phase_buttons = ttk.Frame(control_frame)
        phase_buttons.pack(fill="x", pady=5)

        ttk.Button(phase_buttons, text="🌙 Night", command=self._manual_night).pack(
            side="left", padx=2
        )
        ttk.Button(phase_buttons, text="☀️ Day", command=self._manual_day).pack(
            side="left", padx=2
        )
        ttk.Button(
            phase_buttons, text="🗳️ Nominations", command=self._manual_nominations
        ).pack(side="left", padx=2)

        # Speech controls
        speech_frame = ttk.LabelFrame(self.left_frame, text="Speech Controls")
        speech_frame.pack(fill="x", padx=10, pady=10)

        self.listen_button = ttk.Button(
            speech_frame, text="🎤 Listen", command=self._toggle_listening
        )
        self.listen_button.pack(side="left", padx=5, pady=5)

        self.speak_button = ttk.Button(
            speech_frame, text="🔊 Speak", command=self._manual_speak
        )
        self.speak_button.pack(side="left", padx=5, pady=5)

        # Text input for manual announcements
        self.speech_text = tk.Text(speech_frame, height=3, width=40)
        self.speech_text.pack(fill="x", padx=5, pady=5)

    def _setup_autonomous_integration(self):
        """Setup autonomous AI integration"""

        from .autonomous_control_panel import AutonomousControlPanel

        # Add autonomous control panel to right frame
        self.autonomous_panel = AutonomousControlPanel(self.right_frame)
        self.autonomous_panel.get_panel().pack(
            fill="both", expand=True, padx=10, pady=10
        )

    def _setup_mode_coordination(self):
        """Setup coordination between manual and autonomous modes"""

        # Mode selector
        mode_frame = ttk.LabelFrame(self.root, text="Control Mode")
        mode_frame.pack(side="top", fill="x", padx=10, pady=5)

        self.mode_var = tk.StringVar(value="manual")

        ttk.Radiobutton(
            mode_frame,
            text="👤 Manual Control",
            variable=self.mode_var,
            value="manual",
            command=self._switch_to_manual,
        ).pack(side="left", padx=10)

        ttk.Radiobutton(
            mode_frame,
            text="🤖 Autonomous AI",
            variable=self.mode_var,
            value="autonomous",
            command=self._switch_to_autonomous,
        ).pack(side="left", padx=10)

        ttk.Radiobutton(
            mode_frame,
            text="🤝 Hybrid Mode",
            variable=self.mode_var,
            value="hybrid",
            command=self._switch_to_hybrid,
        ).pack(side="left", padx=10)

        # Status indicator
        self.mode_status = ttk.Label(
            mode_frame, text="Currently in manual mode", foreground="#888888"
        )
        self.mode_status.pack(side="right", padx=10)

    def _switch_to_manual(self):
        """Switch to manual control mode"""

        # Stop autonomous mode if running
        if (
            hasattr(self.autonomous_panel, "is_running")
            and self.autonomous_panel.is_running
        ):
            self.autonomous_panel._stop_autonomous_mode()

        # Enable manual controls
        self._enable_manual_controls(True)

        self.mode_status.config(text="Manual mode active - You control everything")

    def _switch_to_autonomous(self):
        """Switch to autonomous AI mode"""

        # Disable manual controls
        self._enable_manual_controls(False)

        # Start autonomous mode
        if not (
            hasattr(self.autonomous_panel, "is_running")
            and self.autonomous_panel.is_running
        ):
            self.autonomous_panel._start_autonomous_mode()

        self.mode_status.config(text="Autonomous mode active - AI controls the game")

    def _switch_to_hybrid(self):
        """Switch to hybrid mode"""

        # Enable both manual and autonomous controls
        self._enable_manual_controls(True)

        self.mode_status.config(
            text="Hybrid mode - Both manual and AI control available"
        )

    def _enable_manual_controls(self, enabled: bool):
        """Enable or disable manual controls"""

        state = "normal" if enabled else "disabled"

        # Update button states
        if hasattr(self, "connect_button"):
            self.connect_button.config(state=state)
        if hasattr(self, "listen_button"):
            self.listen_button.config(state=state)
        if hasattr(self, "speak_button"):
            self.speak_button.config(state=state)

    # Manual control methods (simplified)
    def _connect_to_platform(self):
        """Connect to game platform"""
        platform = self.platform_var.get()
        room = self.room_var.get()
        print(f"Connecting to {platform} room {room}")

    def _manual_night(self):
        """Manually start night phase"""
        print("Manual: Starting night phase")

    def _manual_day(self):
        """Manually start day phase"""
        print("Manual: Starting day phase")

    def _manual_nominations(self):
        """Manually open nominations"""
        print("Manual: Opening nominations")

    def _toggle_listening(self):
        """Toggle speech listening"""
        print("Manual: Toggling speech listening")

    def _manual_speak(self):
        """Speak manual text"""
        text = self.speech_text.get(1.0, "end").strip()
        if text:
            print(f"Manual speak: {text}")
            self.speech_text.delete(1.0, "end")


# Example usage
def create_enhanced_dashboard():
    """Create the enhanced dashboard with autonomous controls"""

    root = tk.Tk()

    # Setup styles
    style = ttk.Style()
    style.theme_use("clam")

    # Dark theme
    style.configure("Dark.TFrame", background="#1a1a1a")
    style.configure("Start.TButton", background="#27ae60", foreground="white")
    style.configure("Stop.TButton", background="#e74c3c", foreground="white")

    # Create enhanced dashboard
    dashboard = EnhancedStorytellerDashboard(root)

    return root, dashboard


if __name__ == "__main__":
    # Demo the enhanced dashboard
    root, dashboard = create_enhanced_dashboard()

    def on_closing():
        print("Shutting down enhanced storyteller dashboard")
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
