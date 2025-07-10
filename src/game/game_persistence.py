"""
Game Persistence System for Blood on the Clocktower
Save and load complete game states, including automation and ability history
"""

import asyncio
import json
import logging
import os
import pickle
import gzip
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.game_state import GameState, Player


class GameSaveData:
    """Complete saveable game state"""
    
    def __init__(self):
        # Basic game info
        self.save_version = "1.0"
        self.timestamp = datetime.now().isoformat()
        self.game_id = None
        self.script_name = "trouble_brewing"
        
        # Game state
        self.game_state = None
        self.current_phase = None
        self.phase_start_time = None
        self.day_number = 1
        self.night_number = 0
        
        # Automation state  
        self.automation_state = None
        self.night_order = []
        self.current_night_position = 0
        self.pending_nominations = []
        self.nomination_queue = []
        self.execution_queue = []
        
        # Live monitoring
        self.live_monitoring_active = False
        
        # Character abilities
        self.ability_executions = []
        self.night_action_history = []
        
        # Game history
        self.day_history = []
        self.vote_history = []
        self.death_history = []
        self.nomination_history = []
        
        # Settings
        self.speech_config = None
        self.automation_config = None


class GamePersistence:
    """Handles saving and loading game states"""
    
    def __init__(self, saves_directory: str = "saves"):
        self.saves_dir = Path(saves_directory)
        self.saves_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # Auto-save settings
        self.auto_save_enabled = True
        self.auto_save_interval = 300  # 5 minutes
        self.max_auto_saves = 10
        
        # Compression settings
        self.use_compression = True
        
    async def save_game(self, game_automation, filename: str = None, 
                       auto_save: bool = False) -> str:
        """Save complete game state"""
        try:
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                prefix = "autosave" if auto_save else "save"
                filename = f"{prefix}_{timestamp}.botc"
                
            save_path = self.saves_dir / filename
            
            # Create save data
            save_data = GameSaveData()
            await self._populate_save_data(save_data, game_automation)
            
            # Convert to dict for JSON serialization
            save_dict = self._save_data_to_dict(save_data)
            
            # Save to file
            if self.use_compression:
                await self._save_compressed(save_dict, save_path)
            else:
                await self._save_json(save_dict, save_path)
                
            self.logger.info(f"Game saved to {save_path}")
            
            # Clean up old auto-saves if this is an auto-save
            if auto_save:
                await self._cleanup_auto_saves()
                
            return str(save_path)
            
        except Exception as e:
            self.logger.error(f"Failed to save game: {e}")
            raise
            
    async def load_game(self, filename: str) -> GameSaveData:
        """Load complete game state"""
        try:
            save_path = Path(filename)
            if not save_path.is_absolute():
                save_path = self.saves_dir / save_path
                
            if not save_path.exists():
                raise FileNotFoundError(f"Save file not found: {save_path}")
                
            # Load from file
            if save_path.suffix == '.gz' or self.use_compression:
                save_dict = await self._load_compressed(save_path)
            else:
                save_dict = await self._load_json(save_path)
                
            # Convert back to save data object
            save_data = self._dict_to_save_data(save_dict)
            
            self.logger.info(f"Game loaded from {save_path}")
            return save_data
            
        except Exception as e:
            self.logger.error(f"Failed to load game: {e}")
            raise
            
    async def restore_game_state(self, save_data: GameSaveData, game_automation) -> bool:
        """Restore game automation from save data"""
        try:
            # Restore basic game state
            game_automation.game_state = save_data.game_state
            game_automation.current_phase = save_data.current_phase
            game_automation.phase_start_time = save_data.phase_start_time
            
            # Restore automation state
            game_automation.night_order = save_data.night_order
            game_automation.current_night_position = save_data.current_night_position
            game_automation.pending_nominations = save_data.pending_nominations
            game_automation.nomination_queue = save_data.nomination_queue
            game_automation.execution_queue = save_data.execution_queue
            
            # Restore ability history
            if hasattr(game_automation, 'ability_system'):
                game_automation.ability_system.execution_history = save_data.ability_executions
                
            self.logger.info("Game state restored successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore game state: {e}")
            return False
            
    async def quick_save(self, game_automation) -> str:
        """Create a quick save with timestamp"""
        return await self.save_game(game_automation, auto_save=False)
        
    async def auto_save(self, game_automation) -> str:
        """Create an auto-save"""
        return await self.save_game(game_automation, auto_save=True)
        
    def list_saves(self) -> List[Dict[str, Any]]:
        """List all available save files with metadata"""
        saves = []
        
        for save_file in self.saves_dir.glob("*.botc*"):
            try:
                stat = save_file.stat()
                save_info = {
                    "filename": save_file.name,
                    "path": str(save_file),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "is_auto_save": save_file.name.startswith("autosave_")
                }
                
                # Try to read basic metadata
                try:
                    if save_file.suffix == '.gz' or self.use_compression:
                        with gzip.open(save_file, 'rt') as f:
                            metadata = json.load(f)
                    else:
                        with open(save_file, 'r') as f:
                            metadata = json.load(f)
                            
                    save_info.update({
                        "save_version": metadata.get("save_version", "unknown"),
                        "timestamp": metadata.get("timestamp"),
                        "game_id": metadata.get("game_id"),
                        "script_name": metadata.get("script_name"),
                        "current_phase": metadata.get("current_phase"),
                        "player_count": len(metadata.get("game_state", {}).get("players", []))
                    })
                    
                except Exception:
                    # Couldn't read metadata, just use file info
                    pass
                    
                saves.append(save_info)
                
            except Exception as e:
                self.logger.warning(f"Error reading save file {save_file}: {e}")
                
        # Sort by modification time, newest first
        saves.sort(key=lambda x: x["modified"], reverse=True)
        return saves
        
    async def delete_save(self, filename: str) -> bool:
        """Delete a save file"""
        try:
            save_path = Path(filename)
            if not save_path.is_absolute():
                save_path = self.saves_dir / save_path
                
            if save_path.exists():
                save_path.unlink()
                self.logger.info(f"Deleted save file: {save_path}")
                return True
            else:
                self.logger.warning(f"Save file not found: {save_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to delete save file: {e}")
            return False
            
    async def export_game_log(self, save_data: GameSaveData, filename: str = None) -> str:
        """Export game as human-readable log"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"game_log_{timestamp}.txt"
                
            log_path = self.saves_dir / filename
            
            with open(log_path, 'w') as f:
                f.write("BLOOD ON THE CLOCKTOWER - GAME LOG\\n")
                f.write("=" * 50 + "\\n\\n")
                
                # Game metadata
                f.write(f"Script: {save_data.script_name}\\n")
                f.write(f"Save Date: {save_data.timestamp}\\n")
                f.write(f"Current Phase: {save_data.current_phase}\\n\\n")
                
                # Players
                if save_data.game_state and hasattr(save_data.game_state, 'players'):
                    f.write("PLAYERS:\\n")
                    f.write("-" * 20 + "\\n")
                    for player in save_data.game_state.players:
                        status = "ALIVE" if player.is_alive() else "DEAD"
                        f.write(f"  {player.name}: {player.character} ({player.team}) - {status}\\n")
                    f.write("\\n")
                
                # Game history
                if save_data.day_history:
                    f.write("DAY HISTORY:\\n")
                    f.write("-" * 20 + "\\n")
                    for day_info in save_data.day_history:
                        f.write(f"  Day {day_info.get('day_number', '?')}: {day_info.get('summary', 'No summary')}\\n")
                    f.write("\\n")
                
                # Nominations
                if save_data.nomination_history:
                    f.write("NOMINATION HISTORY:\\n")
                    f.write("-" * 20 + "\\n")
                    for nom in save_data.nomination_history:
                        f.write(f"  {nom.get('nominator', '?')} nominated {nom.get('nominee', '?')}\\n")
                    f.write("\\n")
                
                # Deaths
                if save_data.death_history:
                    f.write("DEATH HISTORY:\\n")
                    f.write("-" * 20 + "\\n")
                    for death in save_data.death_history:
                        f.write(f"  {death.get('player', '?')} died: {death.get('cause', 'unknown')}\\n")
                    f.write("\\n")
                
                # Ability executions
                if save_data.ability_executions:
                    f.write("ABILITY EXECUTIONS:\\n")
                    f.write("-" * 20 + "\\n")
                    for exec_info in save_data.ability_executions[-20:]:  # Last 20
                        f.write(f"  {exec_info.get('character', '?')} ({exec_info.get('player_name', '?')}): {exec_info.get('result', '?')}\\n")
                    f.write("\\n")
                
            self.logger.info(f"Game log exported to {log_path}")
            return str(log_path)
            
        except Exception as e:
            self.logger.error(f"Failed to export game log: {e}")
            raise
            
    # Private methods
    
    async def _populate_save_data(self, save_data: GameSaveData, game_automation):
        """Populate save data from game automation"""
        import uuid
        
        # Basic info
        save_data.game_id = str(uuid.uuid4())
        save_data.current_phase = game_automation.current_phase.name if game_automation.current_phase else None
        save_data.phase_start_time = game_automation.phase_start_time.isoformat() if game_automation.phase_start_time else None
        
        # Game state
        save_data.game_state = self._serialize_game_state(game_automation.game_state)
        
        # Automation state
        save_data.automation_state = {
            "auto_mode": game_automation.auto_mode,
            "is_waiting": game_automation.is_waiting,
            "pause_requested": game_automation.pause_requested
        }
        
        save_data.night_order = game_automation.night_order.copy()
        save_data.current_night_position = game_automation.current_night_position
        save_data.pending_nominations = game_automation.pending_nominations.copy()
        save_data.nomination_queue = game_automation.nomination_queue.copy()
        save_data.execution_queue = game_automation.execution_queue.copy()
        
        # Live monitoring
        if hasattr(game_automation, 'live_monitor') and game_automation.live_monitor:
            save_data.live_monitoring_active = game_automation.live_monitor.listening_active
            
        # Ability executions
        if hasattr(game_automation, 'ability_system') and game_automation.ability_system:
            save_data.ability_executions = [
                self._serialize_ability_execution(exec_obj) 
                for exec_obj in game_automation.ability_system.execution_history
            ]
            
        # Create game history from current state
        save_data.day_history = self._generate_day_history(game_automation)
        save_data.death_history = self._generate_death_history(game_automation)
        save_data.nomination_history = self._generate_nomination_history(game_automation)
        
    def _serialize_game_state(self, game_state: GameState) -> Dict[str, Any]:
        """Serialize game state to dict"""
        if not game_state:
            return {}
            
        return {
            "players": [
                {
                    "name": p.name,
                    "character": p.character,
                    "team": p.team,
                    "seat_position": p.seat_position,
                    "status": p.status.name if hasattr(p, 'status') else "unknown",
                    "alive": p.is_alive(),
                    "votes_today": getattr(p, 'votes_today', 0),
                    "nominated_today": getattr(p, 'nominated_today', False),
                    # Custom attributes
                    "poisoned": getattr(p, 'poisoned', False),
                    "protected": getattr(p, 'protected', False),
                    "drunk": getattr(p, 'drunk', False),
                    "butler_master": getattr(p, 'butler_master', None),
                    "virgin_used": getattr(p, 'virgin_used', False),
                    "died_today": getattr(p, 'died_today', False)
                } for p in game_state.players
            ],
            "setup": getattr(game_state, 'setup', {}),
            "script_info": getattr(game_state, 'script_info', {})
        }
        
    def _serialize_ability_execution(self, execution) -> Dict[str, Any]:
        """Serialize ability execution to dict"""
        return {
            "character": execution.character,
            "player_name": execution.player_name,
            "trigger": execution.trigger.name,
            "result": execution.result.name,
            "targets": execution.targets,
            "effects": execution.effects,
            "timestamp": execution.timestamp,
            "night_number": execution.night_number
        }
        
    def _generate_day_history(self, game_automation) -> List[Dict[str, Any]]:
        """Generate day history from current state"""
        # This would be populated from actual game events
        # For now, return basic info
        return [
            {
                "day_number": 1,
                "summary": f"Game in progress - Phase: {game_automation.current_phase.name if game_automation.current_phase else 'Unknown'}"
            }
        ]
        
    def _generate_death_history(self, game_automation) -> List[Dict[str, Any]]:
        """Generate death history from current state"""
        deaths = []
        if game_automation.game_state:
            for player in game_automation.game_state.players:
                if not player.is_alive():
                    deaths.append({
                        "player": player.name,
                        "character": player.character,
                        "cause": "unknown",  # Would track this in real implementation
                        "day": 1  # Would track actual day
                    })
        return deaths
        
    def _generate_nomination_history(self, game_automation) -> List[Dict[str, Any]]:
        """Generate nomination history from current state"""
        # Would be populated from actual nomination events
        return []
        
    def _save_data_to_dict(self, save_data: GameSaveData) -> Dict[str, Any]:
        """Convert save data object to dict"""
        return {
            "save_version": save_data.save_version,
            "timestamp": save_data.timestamp,
            "game_id": save_data.game_id,
            "script_name": save_data.script_name,
            "current_phase": save_data.current_phase,
            "phase_start_time": save_data.phase_start_time,
            "day_number": save_data.day_number,
            "night_number": save_data.night_number,
            "game_state": save_data.game_state,
            "automation_state": save_data.automation_state,
            "night_order": save_data.night_order,
            "current_night_position": save_data.current_night_position,
            "pending_nominations": save_data.pending_nominations,
            "nomination_queue": save_data.nomination_queue,
            "execution_queue": save_data.execution_queue,
            "live_monitoring_active": save_data.live_monitoring_active,
            "ability_executions": save_data.ability_executions,
            "day_history": save_data.day_history,
            "vote_history": save_data.vote_history,
            "death_history": save_data.death_history,
            "nomination_history": save_data.nomination_history,
            "speech_config": save_data.speech_config,
            "automation_config": save_data.automation_config
        }
        
    def _dict_to_save_data(self, save_dict: Dict[str, Any]) -> GameSaveData:
        """Convert dict to save data object"""
        save_data = GameSaveData()
        
        # Basic restoration
        for key, value in save_dict.items():
            if hasattr(save_data, key):
                setattr(save_data, key, value)
                
        # Special handling for game state
        if save_dict.get("game_state"):
            save_data.game_state = self._deserialize_game_state(save_dict["game_state"])
            
        return save_data
        
    def _deserialize_game_state(self, game_state_dict: Dict[str, Any]) -> GameState:
        """Deserialize game state from dict"""
        # Create new game state
        game_state = GameState()
        
        # Restore players
        if "players" in game_state_dict:
            for player_data in game_state_dict["players"]:
                player = Player(
                    name=player_data["name"],
                    character=player_data.get("character"),
                    team=player_data.get("team"),
                    seat_position=player_data.get("seat_position", 0)
                )
                
                # Restore status
                if not player_data.get("alive", True):
                    player.kill("restored_from_save")
                    
                # Restore custom attributes
                for attr in ["poisoned", "protected", "drunk", "butler_master", 
                           "virgin_used", "died_today", "votes_today", "nominated_today"]:
                    if attr in player_data:
                        setattr(player, attr, player_data[attr])
                        
                game_state.add_player(player)
                
        return game_state
        
    async def _save_compressed(self, data: Dict[str, Any], path: Path):
        """Save data with gzip compression"""
        with gzip.open(path.with_suffix('.botc.gz'), 'wt') as f:
            json.dump(data, f, indent=2)
            
    async def _save_json(self, data: Dict[str, Any], path: Path):
        """Save data as JSON"""
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
            
    async def _load_compressed(self, path: Path) -> Dict[str, Any]:
        """Load compressed data"""
        with gzip.open(path, 'rt') as f:
            return json.load(f)
            
    async def _load_json(self, path: Path) -> Dict[str, Any]:
        """Load JSON data"""
        with open(path, 'r') as f:
            return json.load(f)
            
    async def _cleanup_auto_saves(self):
        """Clean up old auto-save files"""
        auto_saves = [f for f in self.saves_dir.glob("autosave_*.botc*")]
        auto_saves.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Keep only the most recent auto-saves
        for old_save in auto_saves[self.max_auto_saves:]:
            try:
                old_save.unlink()
                self.logger.info(f"Cleaned up old auto-save: {old_save}")
            except Exception as e:
                self.logger.warning(f"Failed to delete old auto-save {old_save}: {e}")


# Auto-save manager for running games
class AutoSaveManager:
    """Manages automatic saving during game play"""
    
    def __init__(self, persistence: GamePersistence):
        self.persistence = persistence
        self.auto_save_task = None
        self.logger = logging.getLogger(__name__)
        
    async def start_auto_save(self, game_automation):
        """Start automatic saving"""
        if self.auto_save_task:
            return
            
        self.auto_save_task = asyncio.create_task(
            self._auto_save_loop(game_automation)
        )
        self.logger.info("Auto-save started")
        
    async def stop_auto_save(self):
        """Stop automatic saving"""
        if self.auto_save_task:
            self.auto_save_task.cancel()
            try:
                await self.auto_save_task
            except asyncio.CancelledError:
                pass
            self.auto_save_task = None
            self.logger.info("Auto-save stopped")
            
    async def _auto_save_loop(self, game_automation):
        """Auto-save loop"""
        try:
            while True:
                await asyncio.sleep(self.persistence.auto_save_interval)
                
                # Only auto-save if game is running
                if hasattr(game_automation, 'is_running') and game_automation.is_running:
                    try:
                        await self.persistence.auto_save(game_automation)
                        self.logger.debug("Auto-save completed")
                    except Exception as e:
                        self.logger.error(f"Auto-save failed: {e}")
                        
        except asyncio.CancelledError:
            self.logger.info("Auto-save loop cancelled")