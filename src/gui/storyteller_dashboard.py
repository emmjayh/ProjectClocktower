"""
Blood on the Clocktower AI Storyteller Dashboard
Main interface for AI Storyteller to manage games on online platforms
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import asyncio
import threading
import json
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from dataclasses import dataclass

from ..core.game_state import GameState, Player, PlayerStatus, GamePhase
from ..speech.speech_handler import SpeechHandler, SpeechConfig
from ..game.clocktower_api import ClockTowerAPI
from ..ai.storyteller_ai import StorytellerAI


class StorytellerDashboard:
    """Main dashboard for AI Storyteller"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("🎭 Blood on the Clocktower - AI Storyteller Dashboard")
        self.root.geometry("1600x900")
        self.root.configure(bg='#0a0a0a')
        
        # Core components
        self.api_client = None
        self.speech_handler = None
        self.storyteller_ai = None
        self.game_state = None
        
        # State tracking
        self.is_connected = False
        self.is_listening = False
        self.current_speaker = None
        self.wake_list = []
        
        # Setup GUI
        self._setup_styles()
        self._create_widgets()
        self._setup_layout()
        
        # Threading
        self.event_loop = None
        self.background_thread = None
        self._start_background_thread()
        
        self.logger = logging.getLogger(__name__)
        
    def _setup_styles(self):
        """Setup dark theme styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Colors
        bg_color = '#0a0a0a'
        panel_color = '#1a1a1a'
        accent_color = '#8b0000'
        text_color = '#ffffff'
        
        style.configure('Dashboard.TLabel', 
                       background=bg_color, 
                       foreground=text_color, 
                       font=('Segoe UI', 11))
        
        style.configure('Title.TLabel', 
                       background=bg_color, 
                       foreground=accent_color, 
                       font=('Segoe UI', 20, 'bold'))
        
        style.configure('Phase.TLabel', 
                       background=panel_color, 
                       foreground='#ffcc00', 
                       font=('Segoe UI', 14, 'bold'))
        
        style.configure('Dark.TFrame', background=panel_color, relief='flat')
        style.configure('Action.TButton', font=('Segoe UI', 10, 'bold'))
        
    def _create_widgets(self):
        """Create all GUI widgets"""
        # Main container
        self.main_frame = ttk.Frame(self.root, style='Dark.TFrame')
        
        # Title bar
        self.title_frame = ttk.Frame(self.main_frame, style='Dark.TFrame')
        self.title_label = ttk.Label(
            self.title_frame, 
            text="🎭 AI STORYTELLER DASHBOARD", 
            style='Title.TLabel'
        )
        
        # Create main layout with 3 columns
        self.content_frame = ttk.Frame(self.main_frame, style='Dark.TFrame')
        
        # Left panel - Game State & Controls
        self.left_panel = ttk.Frame(self.content_frame, style='Dark.TFrame', width=400)
        self.left_panel.pack_propagate(False)
        
        # Middle panel - Grimoire (Player Grid)
        self.middle_panel = ttk.Frame(self.content_frame, style='Dark.TFrame')
        
        # Right panel - Communication & AI
        self.right_panel = ttk.Frame(self.content_frame, style='Dark.TFrame', width=400)
        self.right_panel.pack_propagate(False)
        
        self._create_connection_panel()
        self._create_game_control_panel()
        self._create_grimoire_panel()
        self._create_communication_panel()
        self._create_ai_panel()
        
    def _create_connection_panel(self):
        """Create connection panel"""
        conn_frame = ttk.LabelFrame(self.left_panel, text="🔗 Platform Connection", style='Dark.TFrame')
        conn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Platform selection
        platform_frame = ttk.Frame(conn_frame, style='Dark.TFrame')
        platform_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(platform_frame, text="Platform:", style='Dashboard.TLabel').pack(side=tk.LEFT)
        
        self.platform_var = tk.StringVar(value="clocktower.online")
        platform_combo = ttk.Combobox(
            platform_frame,
            textvariable=self.platform_var,
            values=["clocktower.online", "botc.app", "custom"],
            state="readonly",
            width=20
        )
        platform_combo.pack(side=tk.LEFT, padx=5)
        
        # Room code
        room_frame = ttk.Frame(conn_frame, style='Dark.TFrame')
        room_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(room_frame, text="Room Code:", style='Dashboard.TLabel').pack(side=tk.LEFT)
        
        self.room_var = tk.StringVar()
        room_entry = tk.Entry(
            room_frame,
            textvariable=self.room_var,
            bg='#2a2a2a',
            fg='#ffffff',
            font=('Segoe UI', 10),
            width=15
        )
        room_entry.pack(side=tk.LEFT, padx=5)
        
        # Connect button
        self.connect_button = ttk.Button(
            conn_frame,
            text="Connect to Game",
            command=self._connect_to_platform,
            style='Action.TButton'
        )
        self.connect_button.pack(pady=5)
        
        # Status
        self.connection_status = ttk.Label(
            conn_frame,
            text="❌ Not Connected",
            style='Dashboard.TLabel',
            foreground='#ff6b6b'
        )
        self.connection_status.pack(pady=5)
        
    def _create_game_control_panel(self):
        """Create game control panel"""
        control_frame = ttk.LabelFrame(self.left_panel, text="🎮 Game Control", style='Dark.TFrame')
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Phase display
        self.phase_label = ttk.Label(
            control_frame,
            text="Phase: SETUP",
            style='Phase.TLabel'
        )
        self.phase_label.pack(pady=5)
        
        # Day counter
        self.day_label = ttk.Label(
            control_frame,
            text="Day 0",
            style='Dashboard.TLabel',
            font=('Segoe UI', 12)
        )
        self.day_label.pack()
        
        # Phase control buttons
        phase_buttons = ttk.Frame(control_frame, style='Dark.TFrame')
        phase_buttons.pack(pady=10)
        
        ttk.Button(
            phase_buttons,
            text="🌙 Start Night",
            command=self._start_night_phase,
            style='Action.TButton'
        ).grid(row=0, column=0, padx=2, pady=2)
        
        ttk.Button(
            phase_buttons,
            text="☀️ Start Day",
            command=self._start_day_phase,
            style='Action.TButton'
        ).grid(row=0, column=1, padx=2, pady=2)
        
        ttk.Button(
            phase_buttons,
            text="🗳️ Nominations",
            command=self._open_nominations,
            style='Action.TButton'
        ).grid(row=1, column=0, padx=2, pady=2)
        
        ttk.Button(
            phase_buttons,
            text="⚖️ Execute",
            command=self._execute_player,
            style='Action.TButton'
        ).grid(row=1, column=1, padx=2, pady=2)
        
        # Quick actions
        action_frame = ttk.LabelFrame(control_frame, text="Quick Actions", style='Dark.TFrame')
        action_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            action_frame,
            text="💀 Kill Player",
            command=self._kill_player_dialog,
            style='Action.TButton'
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            action_frame,
            text="🍺 Drunk/Poison",
            command=self._status_effect_dialog,
            style='Action.TButton'
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            action_frame,
            text="📝 Add Reminder",
            command=self._reminder_dialog,
            style='Action.TButton'
        ).pack(side=tk.LEFT, padx=2)
        
    def _create_grimoire_panel(self):
        """Create grimoire panel (player grid)"""
        grimoire_frame = ttk.LabelFrame(self.middle_panel, text="📖 Grimoire", style='Dark.TFrame')
        grimoire_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollable canvas for player tokens
        self.grimoire_canvas = tk.Canvas(
            grimoire_frame,
            bg='#0a0a0a',
            highlightthickness=0
        )
        
        grimoire_scroll = ttk.Scrollbar(grimoire_frame, orient=tk.VERTICAL, command=self.grimoire_canvas.yview)
        self.grimoire_scrollable = ttk.Frame(self.grimoire_canvas, style='Dark.TFrame')
        
        self.grimoire_scrollable.bind(
            "<Configure>",
            lambda e: self.grimoire_canvas.configure(scrollregion=self.grimoire_canvas.bbox("all"))
        )
        
        self.grimoire_canvas.create_window((0, 0), window=self.grimoire_scrollable, anchor="nw")
        self.grimoire_canvas.configure(yscrollcommand=grimoire_scroll.set)
        
        self.grimoire_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        grimoire_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Player token widgets will be created dynamically
        self.player_tokens = {}
        
    def _create_communication_panel(self):
        """Create communication panel"""
        comm_frame = ttk.LabelFrame(self.right_panel, text="🎤 Communication", style='Dark.TFrame')
        comm_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Voice controls
        voice_controls = ttk.Frame(comm_frame, style='Dark.TFrame')
        voice_controls.pack(fill=tk.X, pady=5)
        
        self.listen_button = ttk.Button(
            voice_controls,
            text="👂 Start Listening",
            command=self._toggle_listening,
            style='Action.TButton'
        )
        self.listen_button.pack(side=tk.LEFT, padx=5)
        
        self.speak_button = ttk.Button(
            voice_controls,
            text="🔊 Speak",
            command=self._speak_to_all,
            style='Action.TButton'
        )
        self.speak_button.pack(side=tk.LEFT, padx=5)
        
        # Current speaker indicator
        self.speaker_label = ttk.Label(
            comm_frame,
            text="🔇 No one speaking",
            style='Dashboard.TLabel'
        )
        self.speaker_label.pack(pady=5)
        
        # Speech input/output
        ttk.Label(comm_frame, text="Message to speak:", style='Dashboard.TLabel').pack(anchor=tk.W, padx=5)
        
        self.speech_input = tk.Text(
            comm_frame,
            height=3,
            bg='#2a2a2a',
            fg='#ffffff',
            font=('Segoe UI', 10),
            wrap=tk.WORD
        )
        self.speech_input.pack(fill=tk.X, padx=5, pady=5)
        
        # Communication log
        ttk.Label(comm_frame, text="Communication Log:", style='Dashboard.TLabel').pack(anchor=tk.W, padx=5)
        
        self.comm_log = scrolledtext.ScrolledText(
            comm_frame,
            height=10,
            bg='#1a1a1a',
            fg='#4CAF50',
            font=('Consolas', 9),
            wrap=tk.WORD
        )
        self.comm_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def _create_ai_panel(self):
        """Create AI decision panel"""
        ai_frame = ttk.LabelFrame(self.right_panel, text="🧠 AI Decisions", style='Dark.TFrame')
        ai_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # AI mode selection
        mode_frame = ttk.Frame(ai_frame, style='Dark.TFrame')
        mode_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(mode_frame, text="AI Mode:", style='Dashboard.TLabel').pack(side=tk.LEFT)
        
        self.ai_mode_var = tk.StringVar(value="balanced")
        ai_modes = ["balanced", "favor_good", "favor_evil", "chaotic", "story_focused"]
        
        mode_combo = ttk.Combobox(
            mode_frame,
            textvariable=self.ai_mode_var,
            values=ai_modes,
            state="readonly",
            width=15
        )
        mode_combo.pack(side=tk.LEFT, padx=5)
        
        # AI decision log
        self.ai_log = scrolledtext.ScrolledText(
            ai_frame,
            height=8,
            bg='#1a1a1a',
            fg='#ff9800',
            font=('Consolas', 9),
            wrap=tk.WORD
        )
        self.ai_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def _setup_layout(self):
        """Setup main layout"""
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.title_frame.pack(fill=tk.X, pady=10)
        self.title_label.pack()
        
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10)
        
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        self.middle_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.right_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
    def _start_background_thread(self):
        """Start background thread for async operations"""
        self.background_thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.background_thread.start()
        
    def _run_event_loop(self):
        """Run async event loop in background thread"""
        self.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.event_loop)
        self.event_loop.run_forever()
        
    def _connect_to_platform(self):
        """Connect to online platform"""
        platform = self.platform_var.get()
        room_code = self.room_var.get()
        
        if not room_code:
            messagebox.showerror("Error", "Please enter a room code")
            return
            
        asyncio.run_coroutine_threadsafe(
            self._async_connect(platform, room_code),
            self.event_loop
        )
        
    async def _async_connect(self, platform: str, room_code: str):
        """Async connection to platform"""
        try:
            # Update UI
            self.root.after(0, lambda: self.connection_status.config(
                text="🔄 Connecting...", foreground='#ffeb3b'
            ))
            
            # Initialize API client
            base_url = {
                "clocktower.online": "https://clocktower.online",
                "botc.app": "https://botc.app",
                "custom": "http://localhost:8000"
            }.get(platform, "https://clocktower.online")
            
            self.api_client = ClockTowerAPI(base_url, room_code)
            
            # Connect
            success = await self.api_client.connect()
            
            if success:
                self.is_connected = True
                
                # Initialize speech handler
                config = SpeechConfig(tts_voice="en_US-lessac-medium")
                self.speech_handler = SpeechHandler(config)
                await self.speech_handler.initialize()
                
                # Initialize AI
                self.storyteller_ai = StorytellerAI(self.api_client, self.speech_handler)
                
                # Get initial game state
                game_state = await self.api_client.get_current_game_state()
                if game_state:
                    self.game_state = self._parse_game_state(game_state)
                    self.root.after(0, self._update_grimoire)
                    
                # Start listening for events
                asyncio.create_task(self._listen_for_events())
                
                # Update UI
                self.root.after(0, lambda: self.connection_status.config(
                    text="✅ Connected", foreground='#4CAF50'
                ))
                
                self._log_communication("🔗 Connected to game platform")
                self._log_ai_decision("AI Storyteller initialized and ready")
                
                # Initial greeting
                await self._speak("Good evening, players. I am your AI Storyteller. Let's begin our tale of good versus evil.")
                
            else:
                raise Exception("Connection failed")
                
        except Exception as error:
            error_msg = str(error)
            self.root.after(0, lambda: self._on_connection_error(error_msg))
            
    def _on_connection_error(self, error: str):
        """Handle connection error"""
        self.connection_status.config(text="❌ Connection Failed", foreground='#ff6b6b')
        messagebox.showerror("Connection Error", f"Failed to connect: {error}")
        
    async def _listen_for_events(self):
        """Listen for platform events"""
        try:
            async for event in self.api_client.listen_for_events():
                await self._process_platform_event(event)
                
        except Exception as e:
            self.logger.error(f"Event listening error: {e}")
            
    async def _process_platform_event(self, event):
        """Process event from platform"""
        event_type = event.event_type
        data = event.data
        
        self._log_communication(f"📥 Event: {event_type}")
        
        # Update local game state based on event
        if event_type == "player_joined":
            await self._handle_player_joined(data)
        elif event_type == "game_started":
            await self._handle_game_started(data)
        elif event_type == "player_action":
            await self._handle_player_action(data)
            
    def _start_night_phase(self):
        """Start night phase"""
        if not self.is_connected:
            messagebox.showerror("Error", "Not connected to game")
            return
            
        asyncio.run_coroutine_threadsafe(
            self._async_start_night(),
            self.event_loop
        )
        
    async def _async_start_night(self):
        """Async night phase start"""
        try:
            # Update phase
            self.game_state.phase = GamePhase.NIGHT
            self.game_state.night_number += 1
            
            # Announce to platform
            await self.api_client.announce_phase_change("night", self.game_state.night_number)
            
            # Update UI
            self.root.after(0, lambda: self.phase_label.config(text="Phase: NIGHT"))
            
            # Start night sequence
            await self._speak("Night falls upon the town. Everyone, close your eyes.")
            
            # Process night order
            await self._process_night_order()
            
        except Exception as e:
            self.logger.error(f"Night phase error: {e}")
            
    async def _process_night_order(self):
        """Process night order for character abilities"""
        self._log_ai_decision("Processing night order...")
        
        # Get night order based on script
        if self.game_state.night_number == 0:
            # First night order
            night_order = self._get_first_night_order()
        else:
            # Other nights order
            night_order = self._get_other_night_order()
            
        # Process each character
        for character in night_order:
            players_with_character = [
                p for p in self.game_state.players 
                if p.character == character and p.is_alive()
            ]
            
            for player in players_with_character:
                await self._process_night_ability(player, character)
                
    async def _process_night_ability(self, player: Player, character: str):
        """Process a character's night ability"""
        self._log_communication(f"🌙 Processing {character} ({player.name})")
        
        # Wake player
        await self.api_client.wake_player(player.name, f"{character} ability")
        await self._speak(f"{player.name}, wake up.")
        
        # Wait for player to wake
        await asyncio.sleep(2)
        
        # Handle specific character abilities
        if character == "Fortune Teller":
            await self._handle_fortune_teller(player)
        elif character == "Empath":
            await self._handle_empath(player)
        elif character == "Undertaker":
            await self._handle_undertaker(player)
        # ... handle other characters
        
        # Sleep player
        await self._speak(f"{player.name}, go to sleep.")
        await self.api_client.sleep_player(player.name)
        
        await asyncio.sleep(2)
        
    async def _handle_fortune_teller(self, player: Player):
        """Handle Fortune Teller ability"""
        # Start listening for player choice
        await self._speak("Fortune Teller, choose two players to learn if one is the Demon.")
        
        # Listen for player choices
        self.is_listening = True
        choices = await self._listen_for_player_choices(2)
        self.is_listening = False
        
        if len(choices) == 2:
            # AI decides the result
            result = self.storyteller_ai.decide_fortune_teller_result(
                player, choices[0], choices[1], self.game_state
            )
            
            # Give information
            response = "Yes" if result else "No"
            await self._speak_to_player(player.name, response)
            await self.api_client.give_private_info(player.name, f"Fortune Teller result: {response}")
            
            self._log_ai_decision(f"Fortune Teller ({player.name}) checked {choices[0]} & {choices[1]}: {response}")
            
    async def _handle_empath(self, player: Player):
        """Handle Empath ability"""
        # Get neighbors
        left, right = player.get_neighbors(self.game_state.players)
        
        # AI decides how many evil neighbors
        evil_count = self.storyteller_ai.decide_empath_result(player, left, right, self.game_state)
        
        # Show fingers
        await self._speak_to_player(player.name, f"You sense {evil_count} evil neighbors.")
        await self.api_client.give_private_info(player.name, f"Empath senses: {evil_count}")
        
        self._log_ai_decision(f"Empath ({player.name}) senses {evil_count} evil neighbors")
        
    def _toggle_listening(self):
        """Toggle voice listening"""
        if not self.speech_handler:
            messagebox.showerror("Error", "Speech not initialized")
            return
            
        if self.is_listening:
            self.is_listening = False
            self.listen_button.config(text="👂 Start Listening")
            self.speaker_label.config(text="🔇 Not listening")
        else:
            self.is_listening = True
            self.listen_button.config(text="⏹️ Stop Listening")
            self.speaker_label.config(text="👂 Listening...")
            
            # Start listening in background
            asyncio.run_coroutine_threadsafe(
                self._continuous_listen(),
                self.event_loop
            )
            
    async def _continuous_listen(self):
        """Continuously listen for speech"""
        while self.is_listening:
            try:
                # Listen for speech
                text = await self.speech_handler.listen_for_command(timeout=5.0)
                
                if text:
                    self._log_communication(f"🎤 Heard: {text}")
                    
                    # Process speech command
                    await self._process_speech_command(text)
                    
            except Exception as e:
                self.logger.error(f"Listening error: {e}")
                
    async def _process_speech_command(self, text: str):
        """Process speech command from players"""
        text_lower = text.lower()
        
        # Check for storyteller queries
        if "storyteller" in text_lower:
            if "question" in text_lower or "help" in text_lower:
                await self._handle_player_question(text)
            elif "ready" in text_lower:
                await self._handle_player_ready(text)
                
        # Check for game commands
        elif "nominate" in text_lower:
            await self._handle_nomination_speech(text)
        elif "vote" in text_lower or "yes" in text_lower:
            await self._handle_vote_speech(text)
            
    async def _speak(self, text: str):
        """Speak to all players"""
        self._log_communication(f"🔊 Speaking: {text}")
        
        if self.speech_handler:
            await self.speech_handler.speak(text)
            
    async def _speak_to_player(self, player_name: str, text: str):
        """Speak privately to specific player"""
        self._log_communication(f"🔊 To {player_name}: {text}")
        
        if self.speech_handler:
            await self.speech_handler.speak_to_player(player_name, text)
            
    def _speak_to_all(self):
        """Speak text from input box"""
        text = self.speech_input.get(1.0, tk.END).strip()
        if text:
            asyncio.run_coroutine_threadsafe(
                self._speak(text),
                self.event_loop
            )
            self.speech_input.delete(1.0, tk.END)
            
    def _update_grimoire(self):
        """Update grimoire display with player tokens"""
        # Clear existing tokens
        for widget in self.grimoire_scrollable.winfo_children():
            widget.destroy()
            
        if not self.game_state:
            return
            
        # Create grid of player tokens
        columns = 4
        for i, player in enumerate(self.game_state.players):
            row = i // columns
            col = i % columns
            
            # Create player token frame
            token_frame = tk.Frame(
                self.grimoire_scrollable,
                bg='#2a2a2a',
                relief='raised',
                bd=2
            )
            token_frame.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
            
            # Player name
            name_label = tk.Label(
                token_frame,
                text=f"#{player.seat_position + 1}: {player.name}",
                bg='#2a2a2a',
                fg='#ffffff',
                font=('Segoe UI', 10, 'bold')
            )
            name_label.pack(pady=2)
            
            # Character
            char_label = tk.Label(
                token_frame,
                text=player.character or "Unknown",
                bg='#2a2a2a',
                fg='#4CAF50' if player.team == "good" else '#ff6b6b',
                font=('Segoe UI', 9)
            )
            char_label.pack()
            
            # Status
            status_color = '#4CAF50' if player.is_alive() else '#666666'
            status_text = "ALIVE" if player.is_alive() else "DEAD"
            
            status_label = tk.Label(
                token_frame,
                text=status_text,
                bg='#2a2a2a',
                fg=status_color,
                font=('Segoe UI', 8)
            )
            status_label.pack()
            
            # Effects
            effects = []
            if player.is_drunk:
                effects.append("🍺")
            if player.is_poisoned:
                effects.append("☠️")
            if player.ghost_vote_used:
                effects.append("👻")
                
            if effects:
                effect_label = tk.Label(
                    token_frame,
                    text=" ".join(effects),
                    bg='#2a2a2a',
                    fg='#ffcc00',
                    font=('Segoe UI', 10)
                )
                effect_label.pack()
                
            # Reminder tokens
            if player.reminder_tokens:
                reminders = ", ".join([t.token_type for t in player.reminder_tokens])
                reminder_label = tk.Label(
                    token_frame,
                    text=f"📌 {reminders}",
                    bg='#2a2a2a',
                    fg='#9c27b0',
                    font=('Segoe UI', 8)
                )
                reminder_label.pack()
                
            # Click handler for player actions
            token_frame.bind("<Button-1>", lambda e, p=player: self._on_player_click(p))
            
            self.player_tokens[player.name] = token_frame
            
    def _on_player_click(self, player: Player):
        """Handle click on player token"""
        # Show player action menu
        menu = tk.Menu(self.root, tearoff=0)
        
        menu.add_command(label=f"Wake {player.name}", 
                        command=lambda: self._wake_player(player))
        menu.add_command(label=f"Give Info to {player.name}", 
                        command=lambda: self._give_info_dialog(player))
        menu.add_separator()
        
        if player.is_alive():
            menu.add_command(label="Kill", 
                            command=lambda: self._kill_player(player))
        else:
            menu.add_command(label="Resurrect", 
                            command=lambda: self._resurrect_player(player))
            
        menu.add_separator()
        menu.add_command(label="Make Drunk", 
                        command=lambda: self._make_drunk(player))
        menu.add_command(label="Poison", 
                        command=lambda: self._poison_player(player))
        menu.add_command(label="Add Reminder", 
                        command=lambda: self._add_reminder(player))
        
        # Show menu at cursor
        menu.post(self.root.winfo_pointerx(), self.root.winfo_pointery())
        
    def _log_communication(self, message: str):
        """Log communication event"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.comm_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.comm_log.see(tk.END)
        
    def _log_ai_decision(self, message: str):
        """Log AI decision"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.ai_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.ai_log.see(tk.END)
        
    def _get_first_night_order(self) -> List[str]:
        """Get first night character order"""
        # This would be script-specific
        return [
            "Washerwoman", "Librarian", "Investigator", "Chef",
            "Empath", "Fortune Teller", "Butler", "Poisoner", "Spy"
        ]
        
    def _get_other_night_order(self) -> List[str]:
        """Get other nights character order"""
        return [
            "Poisoner", "Monk", "Scarlet Woman", "Imp", "Ravenkeeper",
            "Empath", "Fortune Teller", "Undertaker", "Butler"
        ]


def main():
    """Main function"""
    root = tk.Tk()
    app = StorytellerDashboard(root)
    
    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", root.destroy)
    
    # Start the GUI
    root.mainloop()


if __name__ == "__main__":
    main()