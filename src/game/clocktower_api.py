"""
ClockTower Online API Integration
Connects to popular online Blood on the Clocktower platforms
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional

import aiohttp
import requests
import websockets


@dataclass
class GameEvent:
    """Represents a game event from online platform"""

    event_type: str
    timestamp: datetime
    data: Dict[str, Any]
    source: str = "online_tool"


class ClockTowerAPI:
    """API client for connecting to online ClockTower tools"""

    def __init__(self, base_url: str, room_code: str = None):
        self.base_url = base_url.rstrip("/")
        self.room_code = room_code
        self.websocket = None
        self.session = None
        self.logger = logging.getLogger(__name__)

        # Detect platform type
        self.platform = self._detect_platform(base_url)

    def _detect_platform(self, url: str) -> str:
        """Detect which online platform we're connecting to"""
        if "clocktower.online" in url:
            return "clocktower_online"
        elif "botc.app" in url:
            return "botc_app"
        elif "clocktower.com" in url:
            return "official_app"
        else:
            return "unknown"

    async def connect(self) -> bool:
        """Connect to the online game"""
        try:
            self.logger.info(f"Connecting to {self.platform} at {self.base_url}")

            # Create HTTP session
            self.session = aiohttp.ClientSession()

            # Platform-specific connection logic
            if self.platform == "clocktower_online":
                return await self._connect_clocktower_online()
            elif self.platform == "botc_app":
                return await self._connect_botc_app()
            else:
                return await self._connect_generic()

        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False

    async def _connect_clocktower_online(self) -> bool:
        """Connect to clocktower.online"""
        try:
            # Get game info
            if self.room_code:
                game_url = f"{self.base_url}/api/game/{self.room_code}"
                async with self.session.get(game_url) as response:
                    if response.status != 200:
                        raise Exception(f"Game not found: {self.room_code}")

                    game_data = await response.json()
                    self.logger.info(f"Found game: {game_data.get('name', 'Unnamed')}")

            # Connect to WebSocket
            ws_url = f"{self.base_url.replace('http', 'ws')}/ws"
            if self.room_code:
                ws_url += f"/{self.room_code}"

            self.websocket = await websockets.connect(ws_url)

            # Send identification as storyteller/observer
            await self.websocket.send(
                json.dumps(
                    {
                        "type": "identify",
                        "role": "storyteller",
                        "name": "AI Storyteller",
                    }
                )
            )

            return True

        except Exception as e:
            self.logger.error(f"ClockTower.online connection failed: {e}")
            return False

    async def _connect_botc_app(self) -> bool:
        """Connect to botc.app"""
        # Implementation for botc.app would go here
        self.logger.warning("botc.app integration not yet implemented")
        return False

    async def _connect_generic(self) -> bool:
        """Generic connection for unknown platforms"""
        self.logger.warning("Using generic connection - limited functionality")
        return True

    async def listen_for_events(self) -> AsyncGenerator[GameEvent, None]:
        """Listen for game events from the platform"""
        if not self.websocket:
            raise Exception("Not connected to game")

        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    event = GameEvent(
                        event_type=data.get("type", "unknown"),
                        timestamp=datetime.now(),
                        data=data,
                        source=self.platform,
                    )

                    yield event

                except json.JSONDecodeError:
                    self.logger.warning(f"Invalid JSON received: {message}")

        except websockets.exceptions.ConnectionClosed:
            self.logger.info("WebSocket connection closed")
        except Exception as e:
            self.logger.error(f"Error listening for events: {e}")

    async def send_storyteller_action(
        self, action_type: str, data: Dict[str, Any]
    ) -> bool:
        """Send storyteller action to the game"""
        if not self.websocket:
            return False

        try:
            message = {
                "type": "storyteller_action",
                "action": action_type,
                "data": data,
                "timestamp": datetime.now().isoformat(),
            }

            await self.websocket.send(json.dumps(message))
            return True

        except Exception as e:
            self.logger.error(f"Failed to send action: {e}")
            return False

    async def update_game_state(self, game_state: Dict[str, Any]) -> bool:
        """Update the online game state"""
        try:
            if self.platform == "clocktower_online":
                return await self._update_clocktower_online_state(game_state)
            else:
                return await self._update_generic_state(game_state)

        except Exception as e:
            self.logger.error(f"Failed to update game state: {e}")
            return False

    async def _update_clocktower_online_state(self, game_state: Dict[str, Any]) -> bool:
        """Update state on clocktower.online"""
        if not self.room_code:
            return False

        url = f"{self.base_url}/api/game/{self.room_code}/state"

        async with self.session.put(url, json=game_state) as response:
            return response.status == 200

    async def _update_generic_state(self, game_state: Dict[str, Any]) -> bool:
        """Generic state update"""
        return await self.send_storyteller_action("update_state", game_state)

    async def announce_phase_change(self, phase: str, day: int = None) -> bool:
        """Announce phase change to players"""
        data = {"phase": phase}
        if day is not None:
            data["day"] = day

        return await self.send_storyteller_action("phase_change", data)

    async def announce_death(self, player_name: str, cause: str = "unknown") -> bool:
        """Announce player death"""
        data = {
            "player": player_name,
            "cause": cause,
            "timestamp": datetime.now().isoformat(),
        }

        return await self.send_storyteller_action("death", data)

    async def announce_execution(self, player_name: str, vote_count: int) -> bool:
        """Announce execution result"""
        data = {"executed": player_name, "votes": vote_count}

        return await self.send_storyteller_action("execution", data)

    async def start_voting(self, nominee: str, nominator: str) -> bool:
        """Start voting phase for nomination"""
        data = {"nominee": nominee, "nominator": nominator}

        return await self.send_storyteller_action("start_voting", data)

    async def end_voting(self, nominee: str, votes: List[str], result: str) -> bool:
        """End voting and announce result"""
        data = {
            "nominee": nominee,
            "voters": votes,
            "result": result,
            "vote_count": len(votes),
        }

        return await self.send_storyteller_action("end_voting", data)

    async def give_private_info(self, player_name: str, information: str) -> bool:
        """Give private information to a player"""
        data = {"target": player_name, "info": information, "private": True}

        return await self.send_storyteller_action("private_info", data)

    async def wake_player(self, player_name: str, reason: str = "night_action") -> bool:
        """Wake a player during night phase"""
        data = {"player": player_name, "reason": reason}

        return await self.send_storyteller_action("wake_player", data)

    async def sleep_player(self, player_name: str) -> bool:
        """Put player back to sleep"""
        data = {"player": player_name}

        return await self.send_storyteller_action("sleep_player", data)

    async def set_player_status(
        self, player_name: str, status: str, drunk: bool = False, poisoned: bool = False
    ) -> bool:
        """Set player status (alive/dead/drunk/poisoned)"""
        data = {
            "player": player_name,
            "status": status,
            "drunk": drunk,
            "poisoned": poisoned,
        }

        return await self.send_storyteller_action("set_status", data)

    async def add_reminder_token(
        self, player_name: str, token_type: str, description: str
    ) -> bool:
        """Add reminder token to player"""
        data = {"player": player_name, "token": token_type, "description": description}

        return await self.send_storyteller_action("add_reminder", data)

    async def remove_reminder_token(self, player_name: str, token_type: str) -> bool:
        """Remove reminder token from player"""
        data = {"player": player_name, "token": token_type}

        return await self.send_storyteller_action("remove_reminder", data)

    async def get_current_game_state(self) -> Optional[Dict[str, Any]]:
        """Get current game state from platform"""
        if not self.session or not self.room_code:
            return None

        try:
            url = f"{self.base_url}/api/game/{self.room_code}/state"
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()

        except Exception as e:
            self.logger.error(f"Failed to get game state: {e}")

        return None

    async def get_player_list(self) -> List[Dict[str, Any]]:
        """Get list of players in the game"""
        if not self.session or not self.room_code:
            return []

        try:
            url = f"{self.base_url}/api/game/{self.room_code}/players"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("players", [])

        except Exception as e:
            self.logger.error(f"Failed to get players: {e}")

        return []

    async def create_game_room(self, script: str, player_count: int) -> Optional[str]:
        """Create a new game room (if supported)"""
        try:
            data = {
                "script": script,
                "player_count": player_count,
                "storyteller": "AI Storyteller",
            }

            url = f"{self.base_url}/api/game/create"
            async with self.session.post(url, json=data) as response:
                if response.status == 201:
                    result = await response.json()
                    room_code = result.get("room_code")
                    self.room_code = room_code
                    return room_code

        except Exception as e:
            self.logger.error(f"Failed to create room: {e}")

        return None

    def disconnect(self):
        """Disconnect from the platform"""
        if self.websocket:
            asyncio.create_task(self.websocket.close())

        if self.session:
            asyncio.create_task(self.session.close())

        self.logger.info("Disconnected from platform")

    def get_supported_features(self) -> List[str]:
        """Get list of supported features for this platform"""
        base_features = [
            "connect",
            "listen_events",
            "announce_phase",
            "announce_death",
            "announce_execution",
        ]

        if self.platform == "clocktower_online":
            return base_features + [
                "create_room",
                "private_info",
                "wake_player",
                "set_status",
                "reminder_tokens",
            ]
        elif self.platform == "botc_app":
            return base_features + ["private_info"]
        else:
            return base_features

    async def test_connection(self) -> bool:
        """Test if connection is working"""
        try:
            if self.session:
                url = f"{self.base_url}/api/health"
                async with self.session.get(url) as response:
                    return response.status == 200

            return self.websocket is not None and not self.websocket.closed

        except Exception:
            return False


class MockClockTowerAPI(ClockTowerAPI):
    """Mock API for testing without real online connection"""

    def __init__(self, room_code: str = "TEST123"):
        super().__init__("http://localhost:8000", room_code)
        self.platform = "mock"
        self.connected = False
        self.mock_events = []

    async def connect(self) -> bool:
        """Mock connection"""
        self.connected = True
        self.logger.info("Connected to mock platform")
        return True

    async def listen_for_events(self) -> AsyncGenerator[GameEvent, None]:
        """Generate mock events for testing"""
        while self.connected:
            await asyncio.sleep(5)  # Event every 5 seconds

            mock_event = GameEvent(
                event_type="test_event",
                timestamp=datetime.now(),
                data={"message": "Mock event for testing"},
            )

            yield mock_event

    async def send_storyteller_action(
        self, action_type: str, data: Dict[str, Any]
    ) -> bool:
        """Mock action sending"""
        self.logger.info(f"Mock action sent: {action_type} - {data}")
        return True

    def disconnect(self):
        """Mock disconnect"""
        self.connected = False
        self.logger.info("Disconnected from mock platform")
