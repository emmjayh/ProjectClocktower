"""
Blood on the Clocktower AI Observer - Spectator and Analysis UI
Watches online games and provides AI storytelling insights
"""

import asyncio
import logging
import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, scrolledtext, ttk
from typing import Any, Dict, List


from ..core.game_state import GamePhase, GameState, Player, PlayerStatus
from ..game.clocktower_api import ClockTowerAPI
from ..speech.speech_handler import SpeechConfig, SpeechHandler


class ObserverWindow:
    """AI Observer window for watching online games"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Blood on the Clocktower - AI Observer")
        self.root.geometry("1400x900")
        self.root.configure(bg="#1a1a1a")

        # Initialize components
        self.api_client = None
        self.speech_handler = None
        self.game_state = None
        self.is_observing = False

        # AI analysis
        self.game_analysis = {}
        self.player_suspicions = {}
        self.predicted_roles = {}

        # Setup GUI
        self._setup_styles()
        self._create_widgets()
        self._setup_layout()

        # Setup logging
        self.logger = logging.getLogger(__name__)

    def _setup_styles(self):
        """Setup dark theme styles"""
        style = ttk.Style()
        style.theme_use("clam")

        # Dark theme
        style.configure(
            "Observer.TLabel",
            background="#1a1a1a",
            foreground="#ffffff",
            font=("Segoe UI", 11),
        )

        style.configure(
            "Title.TLabel",
            background="#1a1a1a",
            foreground="#4CAF50",
            font=("Segoe UI", 16, "bold"),
        )

        style.configure(
            "Subtitle.TLabel",
            background="#1a1a1a",
            foreground="#81C784",
            font=("Segoe UI", 12, "bold"),
        )

        style.configure("Dark.TFrame", background="#2d2d2d", relief="raised")
        style.configure("Player.TFrame", background="#333333", relief="ridge")

        style.configure(
            "Connect.TButton",
            background="#2196F3",
            foreground="white",
            font=("Segoe UI", 11, "bold"),
        )

    def _create_widgets(self):
        """Create all GUI widgets"""
        # Main container
        self.main_frame = ttk.Frame(self.root, style="Dark.TFrame")

        # Title
        self.title_label = ttk.Label(
            self.main_frame,
            text="🔍 AI Observer - Blood on the Clocktower Analysis",
            style="Title.TLabel",
        )

        # Create paned window for layout
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)

        # Left panel - Connection and controls
        self.left_panel = ttk.Frame(self.paned_window, style="Dark.TFrame")
        self.paned_window.add(self.left_panel, weight=1)

        # Right panel - Game analysis
        self.right_panel = ttk.Frame(self.paned_window, style="Dark.TFrame")
        self.paned_window.add(self.right_panel, weight=2)

        self._create_connection_panel()
        self._create_game_state_panel()
        self._create_analysis_panel()
        self._create_ai_insights_panel()

    def _create_connection_panel(self):
        """Create connection controls"""
        connection_frame = ttk.LabelFrame(
            self.left_panel, text="📡 Connection", style="Dark.TFrame"
        )
        connection_frame.pack(fill=tk.X, padx=10, pady=5)

        # Game URL input
        ttk.Label(connection_frame, text="Game URL:", style="Observer.TLabel").pack(
            anchor=tk.W, padx=5, pady=2
        )

        self.url_var = tk.StringVar(value="https://clocktower.online/")
        self.url_entry = tk.Entry(
            connection_frame,
            textvariable=self.url_var,
            bg="#333333",
            fg="#ffffff",
            font=("Segoe UI", 10),
            width=40,
        )
        self.url_entry.pack(fill=tk.X, padx=5, pady=2)

        # Room code input
        ttk.Label(connection_frame, text="Room Code:", style="Observer.TLabel").pack(
            anchor=tk.W, padx=5, pady=2
        )

        self.room_var = tk.StringVar()
        self.room_entry = tk.Entry(
            connection_frame,
            textvariable=self.room_var,
            bg="#333333",
            fg="#ffffff",
            font=("Segoe UI", 10),
            width=20,
        )
        self.room_entry.pack(fill=tk.X, padx=5, pady=2)

        # Connection buttons
        button_frame = ttk.Frame(connection_frame, style="Dark.TFrame")
        button_frame.pack(fill=tk.X, pady=5)

        self.connect_button = ttk.Button(
            button_frame,
            text="🔗 Connect & Observe",
            command=self._connect_to_game,
            style="Connect.TButton",
        )
        self.connect_button.pack(side=tk.LEFT, padx=5)

        self.disconnect_button = ttk.Button(
            button_frame,
            text="❌ Disconnect",
            command=self._disconnect_from_game,
            state=tk.DISABLED,
        )
        self.disconnect_button.pack(side=tk.LEFT, padx=5)

        # Status
        self.status_label = ttk.Label(
            connection_frame,
            text="Not connected",
            style="Observer.TLabel",
            foreground="#ff6b6b",
        )
        self.status_label.pack(pady=5)

    def _create_game_state_panel(self):
        """Create game state display"""
        state_frame = ttk.LabelFrame(
            self.left_panel, text="🎭 Game State", style="Dark.TFrame"
        )
        state_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Game info
        info_frame = ttk.Frame(state_frame, style="Dark.TFrame")
        info_frame.pack(fill=tk.X, pady=5)

        self.phase_label = ttk.Label(
            info_frame, text="Phase: Setup", style="Subtitle.TLabel"
        )
        self.phase_label.pack(anchor=tk.W, padx=5)

        self.day_label = ttk.Label(info_frame, text="Day: 0", style="Observer.TLabel")
        self.day_label.pack(anchor=tk.W, padx=5)

        self.script_label = ttk.Label(
            info_frame, text="Script: Unknown", style="Observer.TLabel"
        )
        self.script_label.pack(anchor=tk.W, padx=5)

        # Players list
        ttk.Label(state_frame, text="Players:", style="Subtitle.TLabel").pack(
            anchor=tk.W, padx=5, pady=(10, 0)
        )

        # Create scrollable players list
        players_container = ttk.Frame(state_frame, style="Dark.TFrame")
        players_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.players_canvas = tk.Canvas(
            players_container, bg="#2d2d2d", highlightthickness=0
        )
        self.players_scrollbar = ttk.Scrollbar(
            players_container, orient=tk.VERTICAL, command=self.players_canvas.yview
        )
        self.players_scrollable = ttk.Frame(self.players_canvas, style="Dark.TFrame")

        self.players_scrollable.bind(
            "<Configure>",
            lambda e: self.players_canvas.configure(
                scrollregion=self.players_canvas.bbox("all")
            ),
        )

        self.players_canvas.create_window(
            (0, 0), window=self.players_scrollable, anchor="nw"
        )
        self.players_canvas.configure(yscrollcommand=self.players_scrollbar.set)

        self.players_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.players_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_analysis_panel(self):
        """Create game analysis panel"""
        analysis_frame = ttk.LabelFrame(
            self.right_panel, text="🧠 AI Analysis", style="Dark.TFrame"
        )
        analysis_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create notebook for different analysis views
        self.analysis_notebook = ttk.Notebook(analysis_frame)
        self.analysis_notebook.pack(fill=tk.BOTH, expand=True, pady=5)

        # Player Analysis tab
        self.player_analysis_frame = ttk.Frame(
            self.analysis_notebook, style="Dark.TFrame"
        )
        self.analysis_notebook.add(self.player_analysis_frame, text="👥 Players")

        # Game Flow tab
        self.flow_analysis_frame = ttk.Frame(
            self.analysis_notebook, style="Dark.TFrame"
        )
        self.analysis_notebook.add(self.flow_analysis_frame, text="📊 Flow")

        # Predictions tab
        self.predictions_frame = ttk.Frame(self.analysis_notebook, style="Dark.TFrame")
        self.analysis_notebook.add(self.predictions_frame, text="🔮 Predictions")

        self._setup_analysis_tabs()

    def _setup_analysis_tabs(self):
        """Setup content for analysis tabs"""

        # Player Analysis
        self.player_analysis_text = scrolledtext.ScrolledText(
            self.player_analysis_frame,
            bg="#1e1e1e",
            fg="#ffffff",
            font=("Consolas", 10),
            wrap=tk.WORD,
        )
        self.player_analysis_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Game Flow
        self.flow_analysis_text = scrolledtext.ScrolledText(
            self.flow_analysis_frame,
            bg="#1e1e1e",
            fg="#ffffff",
            font=("Consolas", 10),
            wrap=tk.WORD,
        )
        self.flow_analysis_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Predictions
        self.predictions_text = scrolledtext.ScrolledText(
            self.predictions_frame,
            bg="#1e1e1e",
            fg="#ffffff",
            font=("Consolas", 10),
            wrap=tk.WORD,
        )
        self.predictions_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _create_ai_insights_panel(self):
        """Create AI insights and commentary panel"""
        insights_frame = ttk.LabelFrame(
            self.right_panel, text="💭 AI Commentary", style="Dark.TFrame"
        )
        insights_frame.pack(fill=tk.X, padx=10, pady=5)

        # Commentary text
        self.commentary_text = scrolledtext.ScrolledText(
            insights_frame,
            height=8,
            bg="#1e1e1e",
            fg="#4CAF50",
            font=("Segoe UI", 11),
            wrap=tk.WORD,
        )
        self.commentary_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Controls
        controls_frame = ttk.Frame(insights_frame, style="Dark.TFrame")
        controls_frame.pack(fill=tk.X, pady=5)

        self.speak_commentary_var = tk.BooleanVar(value=True)
        speak_check = ttk.Checkbutton(
            controls_frame,
            text="🔊 Speak Commentary",
            variable=self.speak_commentary_var,
        )
        speak_check.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            controls_frame, text="🎤 Manual Comment", command=self._add_manual_comment
        ).pack(side=tk.RIGHT, padx=5)

    def _setup_layout(self):
        """Setup main layout"""
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.title_label.pack(pady=(0, 10))
        self.paned_window.pack(fill=tk.BOTH, expand=True)

    def _connect_to_game(self):
        """Connect to online game"""
        try:
            url = self.url_var.get().strip()
            room_code = self.room_var.get().strip()

            if not url:
                messagebox.showerror("Error", "Please enter a game URL")
                return

            # Initialize API client
            self.api_client = ClockTowerAPI(url, room_code)

            # Start observing in background thread
            self._start_observation_thread()

            # Update UI
            self.connect_button.config(state=tk.DISABLED)
            self.disconnect_button.config(state=tk.NORMAL)
            self.status_label.config(text="Connecting...", foreground="#ffeb3b")

            self._add_commentary("🔗 Connecting to game...")

        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {e}")
            self.logger.error(f"Connection failed: {e}")

    def _disconnect_from_game(self):
        """Disconnect from game"""
        self.is_observing = False

        if self.api_client:
            self.api_client.disconnect()

        # Update UI
        self.connect_button.config(state=tk.NORMAL)
        self.disconnect_button.config(state=tk.DISABLED)
        self.status_label.config(text="Disconnected", foreground="#ff6b6b")

        self._add_commentary("❌ Disconnected from game")

    def _start_observation_thread(self):
        """Start background thread for game observation"""
        self.is_observing = True

        def observe():
            asyncio.run(self._observe_game_loop())

        thread = threading.Thread(target=observe, daemon=True)
        thread.start()

    async def _observe_game_loop(self):
        """Main observation loop"""
        try:
            # Initialize speech if enabled
            if self.speak_commentary_var.get():
                config = SpeechConfig(tts_voice="en_US-lessac-medium")
                self.speech_handler = SpeechHandler(config)
                await self.speech_handler.initialize()

            # Connect to game
            await self.api_client.connect()

            # Update UI on successful connection
            self.root.after(
                0,
                lambda: self.status_label.config(
                    text="Connected & Observing", foreground="#4CAF50"
                ),
            )
            self.root.after(
                0,
                lambda: self._add_commentary(
                    "Successfully connected! Observing game..."
                ),
            )

            # Main observation loop
            async for game_event in self.api_client.listen_for_events():
                if not self.is_observing:
                    break

                # Process game event
                await self._process_game_event(game_event)

        except Exception as error:
            error_msg = str(error)
            self.root.after(0, lambda: self._on_connection_error(error_msg))

    async def _process_game_event(self, event: Dict[str, Any]):
        """Process incoming game event"""
        try:
            event_type = event.get("type")
            data = event.get("data", {})

            if event_type == "game_state_update":
                await self._update_game_state(data)
            elif event_type == "player_action":
                await self._process_player_action(data)
            elif event_type == "phase_change":
                await self._process_phase_change(data)
            elif event_type == "nomination":
                await self._process_nomination(data)
            elif event_type == "vote":
                await self._process_vote(data)
            elif event_type == "execution":
                await self._process_execution(data)
            elif event_type == "night_action":
                await self._process_night_action(data)

        except Exception as e:
            self.logger.error(f"Error processing event {event_type}: {e}")

    async def _update_game_state(self, data: Dict[str, Any]):
        """Update game state from server data"""
        # Convert server data to our game state format
        self.game_state = self._parse_server_game_state(data)

        # Update UI
        self.root.after(0, self._update_ui_game_state)

        # Generate AI analysis
        await self._analyze_game_state()

    async def _analyze_game_state(self):
        """Perform AI analysis of current game state"""
        if not self.game_state:
            return

        # Analyze player behavior patterns
        player_analysis = await self._analyze_players()

        # Analyze game flow and balance
        flow_analysis = await self._analyze_game_flow()

        # Generate predictions
        predictions = await self._generate_predictions()

        # Update analysis panels
        self.root.after(
            0,
            lambda: self._update_analysis_display(
                player_analysis, flow_analysis, predictions
            ),
        )

    async def _analyze_players(self) -> str:
        """Analyze player behavior and generate insights"""
        analysis = ["=== PLAYER BEHAVIOR ANALYSIS ===\n"]

        for player in self.game_state.players:
            behavior_score = self._calculate_behavior_score(player)
            suspicion_level = self._calculate_suspicion_level(player)

            analysis.append(f"👤 {player.name}:")
            analysis.append(f"   Behavior Score: {behavior_score}/10")
            analysis.append(f"   Suspicion Level: {suspicion_level}")
            analysis.append(
                f"   Predicted Role: {self.predicted_roles.get(player.name, 'Unknown')}"
            )
            analysis.append("")

        return "\n".join(analysis)

    async def _analyze_game_flow(self) -> str:
        """Analyze game flow and pacing"""
        if not self.game_state:
            return "No game data available"

        analysis = ["=== GAME FLOW ANALYSIS ===\n"]

        # Analyze voting patterns
        analysis.append("📊 Voting Patterns:")
        for nomination in self.game_state.nominations:
            vote_ratio = len(nomination.voters) / len(
                self.game_state.get_alive_players()
            )
            analysis.append(
                f"   {nomination.nominee}: {len(nomination.voters)} votes ({vote_ratio:.1%})"
            )

        analysis.append("")

        # Analyze deaths and eliminations
        dead_players = self.game_state.get_dead_players()
        analysis.append(f"💀 Deaths: {len(dead_players)}")
        for player in dead_players:
            analysis.append(
                f"   {player.name} - Day {player.private_info.get('death_day', '?')}"
            )

        return "\n".join(analysis)

    async def _generate_predictions(self) -> str:
        """Generate AI predictions about the game"""
        predictions = ["=== AI PREDICTIONS ===\n"]

        if not self.game_state:
            return "No game data for predictions"

        # Predict demon
        demon_candidates = self._predict_demon_candidates()
        predictions.append("🔥 Demon Candidates (confidence):")
        for candidate, confidence in demon_candidates:
            predictions.append(f"   {candidate}: {confidence:.1%}")

        predictions.append("")

        # Predict next elimination
        elimination_prediction = self._predict_next_elimination()
        predictions.append(f"⚖️ Next Elimination Prediction: {elimination_prediction}")

        # Predict game outcome
        outcome_prediction = self._predict_game_outcome()
        predictions.append(f"🏆 Predicted Winner: {outcome_prediction}")

        return "\n".join(predictions)

    def _calculate_behavior_score(self, player: Player) -> int:
        """Calculate player behavior score (1-10)"""
        # Placeholder - would implement based on voting patterns, claims, etc.
        return 5

    def _calculate_suspicion_level(self, player: Player) -> str:
        """Calculate player suspicion level"""
        # Placeholder - would implement based on AI analysis
        levels = ["Very Low", "Low", "Medium", "High", "Very High"]
        return levels[2]  # Medium default

    def _predict_demon_candidates(self) -> List[tuple]:
        """Predict who might be the demon"""
        # Placeholder - would implement ML/heuristic analysis
        candidates = []
        for player in self.game_state.get_alive_players():
            confidence = 0.3  # Placeholder
            candidates.append((player.name, confidence))
        return sorted(candidates, key=lambda x: x[1], reverse=True)[:3]

    def _predict_next_elimination(self) -> str:
        """Predict who will be eliminated next"""
        # Placeholder
        alive_players = self.game_state.get_alive_players()
        return alive_players[0].name if alive_players else "Unknown"

    def _predict_game_outcome(self) -> str:
        """Predict which team will win"""
        # Placeholder - would implement based on game analysis
        return "Good Team (65% confidence)"

    def _update_analysis_display(
        self, player_analysis: str, flow_analysis: str, predictions: str
    ):
        """Update analysis display panels"""
        # Update player analysis
        self.player_analysis_text.delete(1.0, tk.END)
        self.player_analysis_text.insert(1.0, player_analysis)

        # Update flow analysis
        self.flow_analysis_text.delete(1.0, tk.END)
        self.flow_analysis_text.insert(1.0, flow_analysis)

        # Update predictions
        self.predictions_text.delete(1.0, tk.END)
        self.predictions_text.insert(1.0, predictions)

    def _update_ui_game_state(self):
        """Update UI with current game state"""
        if not self.game_state:
            return

        # Update phase and day
        self.phase_label.config(text=f"Phase: {self.game_state.phase.value.title()}")
        self.day_label.config(text=f"Day: {self.game_state.day_number}")
        self.script_label.config(text=f"Script: {self.game_state.script_name.title()}")

        # Update players list
        self._update_players_display()

    def _update_players_display(self):
        """Update players display"""
        # Clear existing widgets
        for widget in self.players_scrollable.winfo_children():
            widget.destroy()

        if not self.game_state:
            return

        # Create player entries
        for player in self.game_state.players:
            player_frame = ttk.Frame(self.players_scrollable, style="Player.TFrame")
            player_frame.pack(fill=tk.X, pady=1, padx=2)

            # Player name and status
            status_color = "#4CAF50" if player.is_alive() else "#f44336"
            status_text = "ALIVE" if player.is_alive() else "DEAD"

            name_label = tk.Label(
                player_frame,
                text=f"#{player.seat_position + 1}: {player.name}",
                bg="#333333",
                fg="#ffffff",
                font=("Segoe UI", 10, "bold"),
                anchor=tk.W,
            )
            name_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=2)

            status_label = tk.Label(
                player_frame,
                text=status_text,
                bg="#333333",
                fg=status_color,
                font=("Segoe UI", 9, "bold"),
            )
            status_label.pack(side=tk.RIGHT, padx=5, pady=2)

    def _add_commentary(self, text: str):
        """Add commentary to the AI insights panel"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_text = f"[{timestamp}] {text}\n"

        self.commentary_text.insert(tk.END, formatted_text)
        self.commentary_text.see(tk.END)

        # Speak if enabled
        if self.speak_commentary_var.get() and self.speech_handler:
            asyncio.create_task(self.speech_handler.speak(text))

    def _add_manual_comment(self):
        """Add manual comment dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Manual Comment")
        dialog.geometry("400x200")
        dialog.configure(bg="#2d2d2d")

        ttk.Label(dialog, text="Add commentary:", style="Observer.TLabel").pack(pady=10)

        comment_text = tk.Text(
            dialog, height=5, bg="#333333", fg="#ffffff", font=("Segoe UI", 10)
        )
        comment_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        def add_comment():
            comment = comment_text.get(1.0, tk.END).strip()
            if comment:
                self._add_commentary(f"💭 {comment}")
            dialog.destroy()

        ttk.Button(dialog, text="Add Comment", command=add_comment).pack(pady=10)

    def _parse_server_game_state(self, data: Dict[str, Any]) -> GameState:
        """Parse server game state data into our format"""
        # This would need to be implemented based on the specific online tool's API
        # For now, return a mock game state

        players = []
        for i, player_data in enumerate(data.get("players", [])):
            player = Player(
                id=str(i),
                name=player_data.get("name", f"Player {i + 1}"),
                seat_position=i,
                character=player_data.get("character"),
                status=(
                    PlayerStatus.ALIVE
                    if player_data.get("alive", True)
                    else PlayerStatus.DEAD
                ),
            )
            players.append(player)

        return GameState(
            game_id=data.get("game_id", "observed_game"),
            players=players,
            phase=GamePhase(data.get("phase", "setup")),
            day_number=data.get("day", 0),
            script_name=data.get("script", "unknown"),
        )

    def _on_connection_error(self, error: str):
        """Handle connection error"""
        self.status_label.config(text="Connection Error", foreground="#ff6b6b")
        self._add_commentary(f"❌ Connection error: {error}")
        messagebox.showerror("Connection Error", error)

    async def _process_player_action(self, data: Dict[str, Any]):
        """Process player action event"""
        player_name = data.get("player")
        action = data.get("action")

        self.root.after(0, lambda: self._add_commentary(f"🎭 {player_name} {action}"))

    async def _process_phase_change(self, data: Dict[str, Any]):
        """Process phase change event"""
        new_phase = data.get("phase")

        self.root.after(
            0, lambda: self._add_commentary(f"🌅 Phase changed to: {new_phase}")
        )

    async def _process_nomination(self, data: Dict[str, Any]):
        """Process nomination event"""
        nominator = data.get("nominator")
        nominee = data.get("nominee")

        self.root.after(
            0, lambda: self._add_commentary(f"⚖️ {nominator} nominates {nominee}")
        )

    async def _process_vote(self, data: Dict[str, Any]):
        """Process vote event"""
        voter = data.get("voter")
        nominee = data.get("nominee")

        self.root.after(
            0, lambda: self._add_commentary(f"🗳️ {voter} votes for {nominee}")
        )

    async def _process_execution(self, data: Dict[str, Any]):
        """Process execution event"""
        executed = data.get("executed")

        self.root.after(
            0, lambda: self._add_commentary(f"💀 {executed} has been executed")
        )

    async def _process_night_action(self, data: Dict[str, Any]):
        """Process night action event"""
        character = data.get("character")

        self.root.after(
            0, lambda: self._add_commentary(f"🌙 {character} acts during the night")
        )


def main():
    """Main function for observer app"""
    root = tk.Tk()
    ObserverWindow(root)

    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", root.destroy)

    # Start the GUI
    root.mainloop()


if __name__ == "__main__":
    main()
