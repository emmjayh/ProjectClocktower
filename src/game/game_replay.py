"""
Game Replay System for Blood on the Clocktower
Record and replay complete game sessions with full event tracking
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional


class EventType(Enum):
    """Types of game events that can be recorded"""

    GAME_START = auto()
    PHASE_CHANGE = auto()
    PLAYER_ACTION = auto()
    NIGHT_ACTION = auto()
    NOMINATION = auto()
    VOTE = auto()
    EXECUTION = auto()
    DEATH = auto()
    ABILITY_EXECUTION = auto()
    ANNOUNCEMENT = auto()
    GAME_END = auto()
    ERROR = auto()


@dataclass
class GameEvent:
    """Single event in game history"""

    event_id: str
    event_type: EventType
    timestamp: float
    phase: str
    day_number: int
    night_number: int

    # Event details
    player: Optional[str] = None
    target: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    description: str = ""
    automated: bool = True  # Was this action automated or manual

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.name,
            "timestamp": self.timestamp,
            "phase": self.phase,
            "day_number": self.day_number,
            "night_number": self.night_number,
            "player": self.player,
            "target": self.target,
            "data": self.data,
            "description": self.description,
            "automated": self.automated,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GameEvent":
        """Create from dictionary"""
        return cls(
            event_id=data["event_id"],
            event_type=EventType[data["event_type"]],
            timestamp=data["timestamp"],
            phase=data["phase"],
            day_number=data["day_number"],
            night_number=data["night_number"],
            player=data.get("player"),
            target=data.get("target"),
            data=data.get("data", {}),
            description=data.get("description", ""),
            automated=data.get("automated", True),
        )


@dataclass
class ReplayMetadata:
    """Metadata for a complete game replay"""

    replay_id: str
    game_start_time: datetime
    game_end_time: Optional[datetime] = None
    total_events: int = 0

    # Game info
    script_name: str = "trouble_brewing"
    players: List[str] = field(default_factory=list)
    winner: Optional[str] = None
    total_days: int = 0
    total_nights: int = 0

    # Statistics
    nominations_count: int = 0
    executions_count: int = 0
    deaths_count: int = 0
    ability_uses_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "replay_id": self.replay_id,
            "game_start_time": self.game_start_time.isoformat(),
            "game_end_time": (
                self.game_end_time.isoformat() if self.game_end_time else None
            ),
            "total_events": self.total_events,
            "script_name": self.script_name,
            "players": self.players,
            "winner": self.winner,
            "total_days": self.total_days,
            "total_nights": self.total_nights,
            "nominations_count": self.nominations_count,
            "executions_count": self.executions_count,
            "deaths_count": self.deaths_count,
            "ability_uses_count": self.ability_uses_count,
        }


class GameRecorder:
    """Records game events for replay"""

    def __init__(self, replay_id: str = None):
        self.replay_id = replay_id or self._generate_replay_id()
        self.events: List[GameEvent] = []
        self.metadata = ReplayMetadata(
            replay_id=self.replay_id, game_start_time=datetime.now()
        )
        self.logger = logging.getLogger(__name__)

        # State tracking
        self.current_phase = "setup"
        self.current_day = 1
        self.current_night = 0
        self.event_counter = 0

    def record_event(
        self,
        event_type: EventType,
        player: str = None,
        target: str = None,
        data: Dict[str, Any] = None,
        description: str = "",
        automated: bool = True,
    ) -> GameEvent:
        """Record a new game event"""
        self.event_counter += 1

        event = GameEvent(
            event_id=f"{self.replay_id}_{self.event_counter:04d}",
            event_type=event_type,
            timestamp=asyncio.get_event_loop().time(),
            phase=self.current_phase,
            day_number=self.current_day,
            night_number=self.current_night,
            player=player,
            target=target,
            data=data or {},
            description=description,
            automated=automated,
        )

        self.events.append(event)
        self._update_metadata(event)

        self.logger.debug(f"Recorded event: {event_type.name} - {description}")
        return event

    def record_game_start(self, players: List[str], script: str = "trouble_brewing"):
        """Record game start"""
        self.metadata.players = players.copy()
        self.metadata.script_name = script

        return self.record_event(
            EventType.GAME_START,
            data={
                "players": players,
                "script": script,
                "start_time": datetime.now().isoformat(),
            },
            description=f"Game started with {len(players)} players",
        )

    def record_phase_change(self, from_phase: str, to_phase: str):
        """Record phase transition"""
        self.current_phase = to_phase

        # Update day/night counters
        if to_phase.lower() in ["dawn", "day_discussion"]:
            if from_phase.lower() in ["night", "night_actions"]:
                self.current_day += 1
        elif to_phase.lower() in ["night", "first_night"]:
            if from_phase.lower() in ["dusk", "execution"]:
                self.current_night += 1

        return self.record_event(
            EventType.PHASE_CHANGE,
            data={
                "from_phase": from_phase,
                "to_phase": to_phase,
                "day_number": self.current_day,
                "night_number": self.current_night,
            },
            description=f"Phase changed: {from_phase} → {to_phase}",
        )

    def record_nomination(
        self, nominator: str, nominee: str, successful: bool = True, reason: str = ""
    ):
        """Record nomination event"""
        return self.record_event(
            EventType.NOMINATION,
            player=nominator,
            target=nominee,
            data={"successful": successful, "reason": reason},
            description=f"{nominator} nominates {nominee}"
            + (f" ({reason})" if reason else ""),
        )

    def record_vote(self, voter: str, vote: str, nomination_target: str = None):
        """Record vote event"""
        return self.record_event(
            EventType.VOTE,
            player=voter,
            target=nomination_target,
            data={"vote": vote},
            description=f"{voter} votes {vote}"
            + (f" on {nomination_target}" if nomination_target else ""),
        )

    def record_execution(
        self,
        executed_player: str,
        vote_count: int,
        threshold: int,
        cause: str = "voting",
    ):
        """Record execution event"""
        return self.record_event(
            EventType.EXECUTION,
            target=executed_player,
            data={"vote_count": vote_count, "threshold": threshold, "cause": cause},
            description=f"{executed_player} executed ({vote_count}/{threshold} votes)",
        )

    def record_death(self, player: str, cause: str, killer: str = None):
        """Record death event"""
        return self.record_event(
            EventType.DEATH,
            target=player,
            player=killer,
            data={"cause": cause},
            description=f"{player} dies"
            + (f" (killed by {killer})" if killer else f" ({cause})"),
        )

    def record_ability_execution(
        self,
        player: str,
        character: str,
        targets: List[str] = None,
        result: str = "success",
        effects: Dict[str, Any] = None,
    ):
        """Record character ability use"""
        return self.record_event(
            EventType.ABILITY_EXECUTION,
            player=player,
            target=targets[0] if targets else None,
            data={
                "character": character,
                "targets": targets or [],
                "result": result,
                "effects": effects or {},
            },
            description=f"{player} ({character}) uses ability"
            + (f" on {targets}" if targets else ""),
        )

    def record_announcement(self, message: str, speaker: str = "Storyteller"):
        """Record announcement/speech"""
        return self.record_event(
            EventType.ANNOUNCEMENT,
            player=speaker,
            data={"message": message},
            description=(
                f"{speaker}: {message[:50]}..."
                if len(message) > 50
                else f"{speaker}: {message}"
            ),
        )

    def record_game_end(self, winner: str, reason: str = ""):
        """Record game end"""
        self.metadata.game_end_time = datetime.now()
        self.metadata.winner = winner
        self.metadata.total_days = self.current_day
        self.metadata.total_nights = self.current_night

        return self.record_event(
            EventType.GAME_END,
            data={
                "winner": winner,
                "reason": reason,
                "duration": (
                    self.metadata.game_end_time - self.metadata.game_start_time
                ).total_seconds(),
            },
            description=f"Game ended - {winner} wins"
            + (f" ({reason})" if reason else ""),
        )

    def get_events(
        self, event_type: EventType = None, player: str = None, limit: int = None
    ) -> List[GameEvent]:
        """Get filtered events"""
        filtered_events = self.events

        if event_type:
            filtered_events = [e for e in filtered_events if e.event_type == event_type]

        if player:
            filtered_events = [
                e for e in filtered_events if e.player == player or e.target == player
            ]

        if limit:
            filtered_events = filtered_events[-limit:]

        return filtered_events

    def _update_metadata(self, event: GameEvent):
        """Update metadata based on event"""
        self.metadata.total_events = len(self.events)

        if event.event_type == EventType.NOMINATION:
            self.metadata.nominations_count += 1
        elif event.event_type == EventType.EXECUTION:
            self.metadata.executions_count += 1
        elif event.event_type == EventType.DEATH:
            self.metadata.deaths_count += 1
        elif event.event_type == EventType.ABILITY_EXECUTION:
            self.metadata.ability_uses_count += 1

    def _generate_replay_id(self) -> str:
        """Generate unique replay ID"""
        return f"replay_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


class GamePlayer:
    """Plays back recorded game events"""

    def __init__(self, events: List[GameEvent], metadata: ReplayMetadata):
        self.events = events
        self.metadata = metadata
        self.logger = logging.getLogger(__name__)

        # Playback state
        self.current_position = 0
        self.playback_speed = 1.0
        self.is_playing = False
        self.auto_advance = True

        # Callbacks
        self.event_callbacks = {}

    def register_callback(self, event_type: EventType, callback):
        """Register callback for event type"""
        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []
        self.event_callbacks[event_type].append(callback)

    async def play_from_start(self, speed: float = 1.0):
        """Play entire game from beginning"""
        self.current_position = 0
        self.playback_speed = speed
        await self.play_to_end()

    async def play_to_end(self):
        """Play from current position to end"""
        self.is_playing = True

        try:
            while self.current_position < len(self.events) and self.is_playing:
                event = self.events[self.current_position]
                await self._play_event(event)

                self.current_position += 1

                if self.auto_advance and self.current_position < len(self.events):
                    # Calculate delay based on timestamp difference
                    next_event = self.events[self.current_position]
                    delay = (
                        next_event.timestamp - event.timestamp
                    ) / self.playback_speed

                    # Cap delay at reasonable maximum
                    delay = min(delay, 5.0)

                    if delay > 0:
                        await asyncio.sleep(delay)

        finally:
            self.is_playing = False

    async def play_single_event(self) -> Optional[GameEvent]:
        """Play one event and advance"""
        if self.current_position >= len(self.events):
            return None

        event = self.events[self.current_position]
        await self._play_event(event)
        self.current_position += 1

        return event

    async def seek_to_event(self, event_id: str) -> bool:
        """Seek to specific event"""
        for i, event in enumerate(self.events):
            if event.event_id == event_id:
                self.current_position = i
                return True
        return False

    def seek_to_phase(self, phase: str) -> bool:
        """Seek to first event of specific phase"""
        for i, event in enumerate(self.events):
            if event.phase == phase:
                self.current_position = i
                return True
        return False

    def seek_to_day(self, day_number: int) -> bool:
        """Seek to specific day"""
        for i, event in enumerate(self.events):
            if event.day_number == day_number:
                self.current_position = i
                return True
        return False

    def pause(self):
        """Pause playback"""
        self.is_playing = False

    def stop(self):
        """Stop playback and return to start"""
        self.is_playing = False
        self.current_position = 0

    def set_speed(self, speed: float):
        """Set playback speed multiplier"""
        self.playback_speed = max(0.1, min(10.0, speed))

    def get_progress(self) -> Dict[str, Any]:
        """Get current playback progress"""
        return {
            "current_position": self.current_position,
            "total_events": len(self.events),
            "progress_percent": (
                (self.current_position / len(self.events)) * 100 if self.events else 0
            ),
            "is_playing": self.is_playing,
            "speed": self.playback_speed,
            "current_event": (
                self.events[self.current_position].to_dict()
                if self.current_position < len(self.events)
                else None
            ),
        }

    def get_summary(self) -> Dict[str, Any]:
        """Get game summary statistics"""
        return {
            "metadata": self.metadata.to_dict(),
            "event_counts": {
                event_type.name: len(
                    [e for e in self.events if e.event_type == event_type]
                )
                for event_type in EventType
            },
            "player_stats": self._calculate_player_stats(),
            "timeline": self._generate_timeline(),
        }

    async def _play_event(self, event: GameEvent):
        """Play a single event"""
        self.logger.debug(f"Playing event: {event.description}")

        # Call registered callbacks
        if event.event_type in self.event_callbacks:
            for callback in self.event_callbacks[event.event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except Exception as e:
                    self.logger.error(f"Error in event callback: {e}")

    def _calculate_player_stats(self) -> Dict[str, Dict[str, int]]:
        """Calculate per-player statistics"""
        stats = {}

        for player in self.metadata.players:
            stats[player] = {
                "nominations_made": len(
                    [
                        e
                        for e in self.events
                        if e.event_type == EventType.NOMINATION and e.player == player
                    ]
                ),
                "votes_cast": len(
                    [
                        e
                        for e in self.events
                        if e.event_type == EventType.VOTE and e.player == player
                    ]
                ),
                "times_nominated": len(
                    [
                        e
                        for e in self.events
                        if e.event_type == EventType.NOMINATION and e.target == player
                    ]
                ),
                "ability_uses": len(
                    [
                        e
                        for e in self.events
                        if e.event_type == EventType.ABILITY_EXECUTION
                        and e.player == player
                    ]
                ),
                "died": len(
                    [
                        e
                        for e in self.events
                        if e.event_type == EventType.DEATH and e.target == player
                    ]
                )
                > 0,
                "executed": len(
                    [
                        e
                        for e in self.events
                        if e.event_type == EventType.EXECUTION and e.target == player
                    ]
                )
                > 0,
            }

        return stats

    def _generate_timeline(self) -> List[Dict[str, Any]]:
        """Generate condensed timeline of major events"""
        major_events = [
            EventType.GAME_START,
            EventType.PHASE_CHANGE,
            EventType.NOMINATION,
            EventType.EXECUTION,
            EventType.DEATH,
            EventType.GAME_END,
        ]

        timeline = []
        for event in self.events:
            if event.event_type in major_events:
                timeline.append(
                    {
                        "timestamp": event.timestamp,
                        "day": event.day_number,
                        "phase": event.phase,
                        "type": event.event_type.name,
                        "description": event.description,
                    }
                )

        return timeline


class ReplayManager:
    """Manages game replay storage and retrieval"""

    def __init__(self, replays_directory: str = "replays"):
        self.replays_dir = Path(replays_directory)
        self.replays_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)

    async def save_replay(self, recorder: GameRecorder, filename: str = None) -> str:
        """Save recorded game to file"""
        try:
            if not filename:
                filename = f"{recorder.replay_id}.replay"

            replay_path = self.replays_dir / filename

            replay_data = {
                "metadata": recorder.metadata.to_dict(),
                "events": [event.to_dict() for event in recorder.events],
            }

            with open(replay_path, "w") as f:
                json.dump(replay_data, f, indent=2)

            self.logger.info(f"Replay saved to {replay_path}")
            return str(replay_path)

        except Exception as e:
            self.logger.error(f"Failed to save replay: {e}")
            raise

    async def load_replay(self, filename: str) -> GamePlayer:
        """Load replay from file"""
        try:
            replay_path = Path(filename)
            if not replay_path.is_absolute():
                replay_path = self.replays_dir / replay_path

            with open(replay_path, "r") as f:
                replay_data = json.load(f)

            metadata = ReplayMetadata(**replay_data["metadata"])
            events = [
                GameEvent.from_dict(event_data) for event_data in replay_data["events"]
            ]

            player = GamePlayer(events, metadata)

            self.logger.info(f"Replay loaded from {replay_path}")
            return player

        except Exception as e:
            self.logger.error(f"Failed to load replay: {e}")
            raise

    def list_replays(self) -> List[Dict[str, Any]]:
        """List all available replays"""
        replays = []

        for replay_file in self.replays_dir.glob("*.replay"):
            try:
                with open(replay_file, "r") as f:
                    replay_data = json.load(f)

                metadata = replay_data.get("metadata", {})

                replay_info = {
                    "filename": replay_file.name,
                    "path": str(replay_file),
                    "size": replay_file.stat().st_size,
                    "replay_id": metadata.get("replay_id"),
                    "game_start": metadata.get("game_start_time"),
                    "game_end": metadata.get("game_end_time"),
                    "total_events": metadata.get("total_events", 0),
                    "players": metadata.get("players", []),
                    "winner": metadata.get("winner"),
                    "script": metadata.get("script_name", "unknown"),
                }

                replays.append(replay_info)

            except Exception as e:
                self.logger.warning(f"Error reading replay file {replay_file}: {e}")

        replays.sort(key=lambda x: x.get("game_start", ""), reverse=True)
        return replays

    async def delete_replay(self, filename: str) -> bool:
        """Delete a replay file"""
        try:
            replay_path = Path(filename)
            if not replay_path.is_absolute():
                replay_path = self.replays_dir / replay_path

            if replay_path.exists():
                replay_path.unlink()
                self.logger.info(f"Deleted replay: {replay_path}")
                return True
            else:
                return False

        except Exception as e:
            self.logger.error(f"Failed to delete replay: {e}")
            return False
