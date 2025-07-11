"""
Example integration of timing controls into the Storyteller Dashboard
Shows how to add timing features to existing dashboard
"""

# This would be added to storyteller_dashboard.py

def _add_timing_controls(self):
    """Add timing controls to the dashboard"""
    
    # Import the timing controls
    from .timing_controls import TimingControlsFrame
    
    # Create timing controls in the left panel
    self.timing_controls = TimingControlsFrame(
        self.left_panel,
        on_config_change=self._on_timing_config_change
    )
    
    # Pack the timing frame
    self.timing_controls.get_frame().pack(
        fill="x", 
        padx=10, 
        pady=(10, 0)
    )
    
    # Store reference to timing manager
    self.timing_manager = self.timing_controls.get_timing_manager()
    
def _on_timing_config_change(self, new_config):
    """Handle timing configuration changes"""
    self.log_message(
        f"⏰ Timing updated: {new_config.pacing_style.value} pacing",
        "system"
    )
    
    # Update any AI storyteller with new timing
    if hasattr(self, 'timed_narrator'):
        summary = self.timing_manager.format_timing_summary()
        self.log_message(summary, "system")

# Modified phase transition methods to include timing

async def _start_night_phase(self):
    """Start night phase with timing"""
    if not self.game_state:
        return
        
    self.game_state.phase = GamePhase.NIGHT
    self.game_state.day_number += 1
    
    # Start phase timer
    if hasattr(self, 'timing_controls'):
        self.timing_controls.start_phase_timer("night", {
            "night_number": self.game_state.day_number,
            "alive_count": len([p for p in self.game_state.players if p.is_alive()])
        })
    
    # Narrate with timing suggestion
    narration = await self.narrator.narrate_night_phase(
        self.game_state.day_number,
        len([p for p in self.game_state.players if p.is_alive()])
    )
    
    timing_suggestion = self.timing_manager.start_phase("night")
    full_narration = f"{narration}\n\n{timing_suggestion}"
    
    await self.announce(full_narration)
    
async def _start_day_phase(self):
    """Start day phase with timing"""
    if not self.game_state:
        return
        
    self.game_state.phase = GamePhase.DAY
    
    # Get deaths from last night
    deaths = []  # This would be determined by game logic
    
    # Start phase timer
    if hasattr(self, 'timing_controls'):
        self.timing_controls.start_phase_timer("day_discussion", {
            "deaths": deaths
        })
    
    # Announce with timing
    death_announcement = await self.narrator.announce_deaths(deaths)
    timing_suggestion = self.timing_manager.start_phase("day_discussion")
    
    full_announcement = f"{death_announcement}\n\n{timing_suggestion}"
    await self.announce(full_announcement)
    
async def handle_nomination(self, nominator: str, nominee: str):
    """Handle nomination with timing"""
    
    # Start nomination timer
    if hasattr(self, 'timing_controls'):
        self.timing_controls.start_phase_timer("nomination", {
            "nominator": nominator,
            "nominee": nominee
        })
    
    # Narrate
    narration = await self.narrator.narrate_nomination(nominator, nominee)
    timing_suggestion = self.timing_manager.start_phase("nomination")
    
    await self.announce(f"{narration}\n\n{timing_suggestion}")
    
async def start_voting(self):
    """Start voting with countdown"""
    
    # Start voting timer
    if hasattr(self, 'timing_controls'):
        self.timing_controls.start_phase_timer("voting", {})
    
    timing_suggestion = self.timing_manager.start_phase("voting")
    await self.announce(f"🗳️ Time to vote!\n\n{timing_suggestion}")
    
    # Could add countdown display
    countdown = self.timing_manager.config.voting_countdown
    for i in range(countdown, 0, -1):
        if i <= 5:
            await self.announce(f"⏰ {i}...")
        await asyncio.sleep(1)
        
    await self.announce("🔔 Voting closed!")

# Example of checking for timing reminders periodically
async def check_timing_reminders(self):
    """Background task to check for timing reminders"""
    while self.is_connected:
        if hasattr(self, 'timing_manager') and self.game_state:
            # Map game phase to timing phase
            phase_map = {
                GamePhase.NIGHT: "night",
                GamePhase.DAY: "day_discussion"
            }
            
            current_phase = phase_map.get(self.game_state.phase)
            if current_phase:
                reminder = self.timing_manager.check_timing(current_phase)
                if reminder:
                    await self.announce(reminder, priority="low")
                    
        await asyncio.sleep(30)  # Check every 30 seconds

# Player command to request more time
async def handle_time_extension_request(self, player_name: str):
    """Handle player request for more time"""
    if hasattr(self, 'timing_manager'):
        response = self.timing_manager.request_extension("current_phase")
        await self.announce(f"{player_name} requested more time. {response}")
        
        # Update UI
        if hasattr(self, 'timing_controls'):
            self.timing_controls.status_label.config(text=response)