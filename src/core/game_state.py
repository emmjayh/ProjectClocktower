"""
Game State Management System for Blood on the Clocktower
Handles all game state persistence, validation, and serialization
"""

import json
import sqlite3
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
from datetime import datetime
import logging

class GamePhase(Enum):
    SETUP = "setup"
    FIRST_NIGHT = "first_night"
    DAY = "day"
    NIGHT = "night"
    VOTING = "voting"
    EXECUTION = "execution"
    GAME_OVER = "game_over"

class PlayerStatus(Enum):
    ALIVE = "alive"
    DEAD = "dead"
    TRAVELER = "traveler"

class Team(Enum):
    GOOD = "good"
    EVIL = "evil"
    NEUTRAL = "neutral"

@dataclass
class ReminderToken:
    token_type: str
    description: str
    is_active: bool = True
    source_character: Optional[str] = None

@dataclass
class Player:
    id: str
    name: str
    seat_position: int
    character: Optional[str] = None
    status: PlayerStatus = PlayerStatus.ALIVE
    team: Optional[Team] = None
    is_drunk: bool = False
    is_poisoned: bool = False
    ghost_vote_used: bool = False
    reminder_tokens: List[ReminderToken] = field(default_factory=list)
    private_info: Dict[str, Any] = field(default_factory=dict)
    vote_count: int = 1  # Can be modified by abilities
    
    def add_reminder(self, token_type: str, description: str, source: Optional[str] = None):
        """Add a reminder token to this player"""
        self.reminder_tokens.append(ReminderToken(token_type, description, True, source))
        
    def remove_reminder(self, token_type: str, source: Optional[str] = None):
        """Remove a reminder token"""
        self.reminder_tokens = [
            t for t in self.reminder_tokens 
            if not (t.token_type == token_type and t.source_character == source)
        ]
        
    def is_alive(self) -> bool:
        return self.status == PlayerStatus.ALIVE
        
    def get_neighbors(self, all_players: List['Player']) -> tuple['Player', 'Player']:
        """Get left and right neighbors in seating order"""
        sorted_players = sorted(all_players, key=lambda p: p.seat_position)
        player_count = len(sorted_players)
        
        current_index = next(i for i, p in enumerate(sorted_players) if p.id == self.id)
        left_neighbor = sorted_players[(current_index - 1) % player_count]
        right_neighbor = sorted_players[(current_index + 1) % player_count]
        
        return left_neighbor, right_neighbor

@dataclass
class Nomination:
    nominator: str
    nominee: str
    timestamp: datetime
    vote_count: int = 0
    voters: List[str] = field(default_factory=list)
    is_executed: bool = False

@dataclass
class GameEvent:
    timestamp: datetime
    event_type: str
    description: str
    players_involved: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class NightAction:
    character: str
    player_id: str
    action_type: str
    target: Optional[str] = None
    result: Optional[Any] = None
    information_given: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class GameState:
    game_id: str
    players: List[Player]
    phase: GamePhase = GamePhase.SETUP
    day_number: int = 0
    night_number: int = 0
    current_night_order: List[str] = field(default_factory=list)
    completed_night_actions: List[str] = field(default_factory=list)
    nominations: List[Nomination] = field(default_factory=list)
    executions_today: int = 0
    demon_bluffs: List[str] = field(default_factory=list)
    script_name: str = "trouble_brewing"
    fabled_characters: List[str] = field(default_factory=list)
    game_events: List[GameEvent] = field(default_factory=list)
    night_actions: List[NightAction] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def get_player_by_name(self, name: str) -> Optional[Player]:
        """Get player by name"""
        return next((p for p in self.players if p.name.lower() == name.lower()), None)
        
    def get_player_by_id(self, player_id: str) -> Optional[Player]:
        """Get player by ID"""
        return next((p for p in self.players if p.id == player_id), None)
        
    def get_alive_players(self) -> List[Player]:
        """Get all alive players"""
        return [p for p in self.players if p.status == PlayerStatus.ALIVE]
        
    def get_dead_players(self) -> List[Player]:
        """Get all dead players"""
        return [p for p in self.players if p.status == PlayerStatus.DEAD]
        
    def get_players_by_character(self, character: str) -> List[Player]:
        """Get all players with specific character"""
        return [p for p in self.players if p.character == character]
        
    def get_players_by_team(self, team: Team) -> List[Player]:
        """Get all players on specific team"""
        return [p for p in self.players if p.team == team]
        
    def add_event(self, event_type: str, description: str, players: List[str] = None, metadata: Dict = None):
        """Add a game event"""
        self.game_events.append(GameEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            description=description,
            players_involved=players or [],
            metadata=metadata or {}
        ))
        self.updated_at = datetime.now()
        
    def add_night_action(self, character: str, player_id: str, action_type: str, 
                        target: str = None, result: Any = None, info: str = None):
        """Add a night action"""
        self.night_actions.append(NightAction(
            character=character,
            player_id=player_id,
            action_type=action_type,
            target=target,
            result=result,
            information_given=info
        ))
        self.updated_at = datetime.now()
        
    def can_nominate(self, nominator_name: str, nominee_name: str) -> tuple[bool, str]:
        """Check if nomination is valid"""
        nominator = self.get_player_by_name(nominator_name)
        nominee = self.get_player_by_name(nominee_name)
        
        if not nominator:
            return False, f"Player {nominator_name} not found"
        if not nominee:
            return False, f"Player {nominee_name} not found"
        if not nominator.is_alive():
            return False, f"{nominator_name} is dead and cannot nominate"
        if not nominee.is_alive():
            return False, f"{nominee_name} is dead and cannot be nominated"
            
        # Check if already nominated today
        today_nominees = [n.nominee for n in self.nominations if n.timestamp.date() == datetime.now().date()]
        if nominee_name in today_nominees:
            return False, f"{nominee_name} has already been nominated today"
            
        return True, "Valid nomination"
        
    def calculate_vote_threshold(self) -> int:
        """Calculate minimum votes needed for execution"""
        alive_count = len(self.get_alive_players())
        return (alive_count // 2) + 1


class GameStateManager:
    """Manages game state persistence and validation"""
    
    def __init__(self, db_path: str = "clocktower_games.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS games (
                    game_id TEXT PRIMARY KEY,
                    game_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS game_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (game_id) REFERENCES games (game_id)
                )
            """)
            
    def save_game_state(self, game_state: GameState) -> bool:
        """Save game state to database"""
        try:
            game_data = self._serialize_game_state(game_state)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO games (game_id, game_data, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (game_state.game_id, game_data))
                
            self.logger.info(f"Saved game state for game {game_state.game_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save game state: {e}")
            return False
            
    def load_game_state(self, game_id: str) -> Optional[GameState]:
        """Load game state from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT game_data FROM games WHERE game_id = ?", 
                    (game_id,)
                )
                result = cursor.fetchone()
                
            if result:
                return self._deserialize_game_state(result[0])
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to load game state: {e}")
            return None
            
    def _serialize_game_state(self, game_state: GameState) -> str:
        """Serialize game state to JSON"""
        # Convert dataclasses to dictionaries
        data = asdict(game_state)
        
        # Handle datetime objects
        data['created_at'] = game_state.created_at.isoformat()
        data['updated_at'] = game_state.updated_at.isoformat()
        
        # Handle nested datetime objects in events and actions
        for event in data['game_events']:
            event['timestamp'] = event['timestamp'].isoformat() if isinstance(event['timestamp'], datetime) else event['timestamp']
            
        for action in data['night_actions']:
            action['timestamp'] = action['timestamp'].isoformat() if isinstance(action['timestamp'], datetime) else action['timestamp']
            
        for nomination in data['nominations']:
            nomination['timestamp'] = nomination['timestamp'].isoformat() if isinstance(nomination['timestamp'], datetime) else nomination['timestamp']
            
        return json.dumps(data, indent=2)
        
    def _deserialize_game_state(self, json_data: str) -> GameState:
        """Deserialize game state from JSON"""
        data = json.loads(json_data)
        
        # Convert datetime strings back to datetime objects
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        # Handle nested datetime objects
        for event in data['game_events']:
            event['timestamp'] = datetime.fromisoformat(event['timestamp'])
            
        for action in data['night_actions']:
            action['timestamp'] = datetime.fromisoformat(action['timestamp'])
            
        for nomination in data['nominations']:
            nomination['timestamp'] = datetime.fromisoformat(nomination['timestamp'])
            
        # Convert enum strings back to enums
        data['phase'] = GamePhase(data['phase'])
        
        for player_data in data['players']:
            player_data['status'] = PlayerStatus(player_data['status'])
            if player_data['team']:
                player_data['team'] = Team(player_data['team'])
                
            # Convert reminder tokens
            reminder_tokens = []
            for token_data in player_data['reminder_tokens']:
                reminder_tokens.append(ReminderToken(**token_data))
            player_data['reminder_tokens'] = reminder_tokens
            
        # Reconstruct dataclass objects
        players = [Player(**player_data) for player_data in data['players']]
        nominations = [Nomination(**nom_data) for nom_data in data['nominations']]
        events = [GameEvent(**event_data) for event_data in data['game_events']]
        actions = [NightAction(**action_data) for action_data in data['night_actions']]
        
        data['players'] = players
        data['nominations'] = nominations
        data['game_events'] = events
        data['night_actions'] = actions
        
        return GameState(**data)
        
    def create_backup(self, game_id: str) -> bool:
        """Create a backup of the current game state"""
        try:
            game_state = self.load_game_state(game_id)
            if game_state:
                backup_id = f"{game_id}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                game_state.game_id = backup_id
                return self.save_game_state(game_state)
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return False
            
    def list_games(self) -> List[Dict[str, Any]]:
        """List all games in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT game_id, created_at, updated_at 
                    FROM games 
                    ORDER BY updated_at DESC
                """)
                
                return [
                    {
                        'game_id': row[0],
                        'created_at': row[1],
                        'updated_at': row[2]
                    }
                    for row in cursor.fetchall()
                ]
                
        except Exception as e:
            self.logger.error(f"Failed to list games: {e}")
            return []


class GameStateValidator:
    """Validates game state integrity and consistency"""
    
    @staticmethod
    def validate_game_state(game_state: GameState) -> tuple[bool, List[str]]:
        """Validate game state for consistency"""
        errors = []
        
        # Basic validation
        if not game_state.players:
            errors.append("Game must have at least one player")
            
        if len(game_state.players) < 5:
            errors.append("Game must have at least 5 players")
            
        # Check for duplicate seat positions
        seat_positions = [p.seat_position for p in game_state.players]
        if len(seat_positions) != len(set(seat_positions)):
            errors.append("Duplicate seat positions found")
            
        # Check character assignments
        characters = [p.character for p in game_state.players if p.character]
        if len(characters) != len(set(characters)):
            errors.append("Duplicate character assignments found")
            
        # Phase-specific validation
        if game_state.phase == GamePhase.GAME_OVER:
            alive_players = game_state.get_alive_players()
            if len(alive_players) > 2:
                errors.append("Game marked as over but more than 2 players alive")
                
        return len(errors) == 0, errors
        
    @staticmethod
    def validate_nomination(nomination: Nomination, game_state: GameState) -> tuple[bool, str]:
        """Validate a nomination"""
        nominator = game_state.get_player_by_name(nomination.nominator)
        nominee = game_state.get_player_by_name(nomination.nominee)
        
        if not nominator:
            return False, "Nominator not found"
        if not nominee:
            return False, "Nominee not found"
        if not nominator.is_alive():
            return False, "Dead players cannot nominate"
        if not nominee.is_alive():
            return False, "Dead players cannot be nominated"
            
        return True, "Valid nomination"