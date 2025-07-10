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
        try:
            self.logger.info("Connecting to botc.app...")
            
            # botc.app uses a different connection pattern
            # Try to detect the room structure first
            if self.room_code:
                # Check if room exists and is accessible
                room_url = f"{self.base_url}/room/{self.room_code}"
                async with self.session.get(room_url) as response:
                    if response.status != 200:
                        raise Exception(f"Room not found or not accessible: {self.room_code}")
                    
                    # Parse room data to understand structure
                    room_html = await response.text()
                    self.logger.info(f"Connected to botc.app room: {self.room_code}")
            
            # Attempt websocket connection with botc.app patterns
            # Try common websocket endpoints
            ws_endpoints = [
                f"{self.base_url.replace('http', 'ws')}/socket.io/",
                f"{self.base_url.replace('http', 'ws')}/ws",
                f"{self.base_url.replace('http', 'ws')}/live/{self.room_code}",
                f"{self.base_url.replace('http', 'ws')}/game/{self.room_code}"
            ]
            
            for ws_url in ws_endpoints:
                try:
                    self.logger.debug(f"Trying websocket: {ws_url}")
                    self.websocket = await websockets.connect(
                        ws_url,
                        timeout=5,
                        extra_headers={
                            'User-Agent': 'BotC-AI-Storyteller/1.0',
                            'Origin': self.base_url
                        }
                    )
                    
                    # Send initial handshake if connected
                    await self._send_botc_handshake()
                    self.logger.info(f"Successfully connected to botc.app via {ws_url}")
                    return True
                    
                except Exception as e:
                    self.logger.debug(f"Failed to connect to {ws_url}: {e}")
                    continue
            
            # If websocket fails, fall back to polling mode
            self.logger.warning("WebSocket connection failed, using polling mode")
            return await self._setup_botc_polling()
            
        except Exception as e:
            self.logger.error(f"botc.app connection failed: {e}")
            return False

    async def _send_botc_handshake(self):
        """Send initial handshake to botc.app"""
        try:
            handshake_data = {
                "type": "join",
                "role": "storyteller",
                "name": "AI Storyteller",
                "room": self.room_code,
                "version": "1.0.1"
            }
            
            await self.websocket.send(json.dumps(handshake_data))
            
            # Wait for handshake response
            response = await asyncio.wait_for(self.websocket.recv(), timeout=10)
            response_data = json.loads(response)
            
            if response_data.get("type") == "welcome":
                self.logger.info("botc.app handshake successful")
                return True
            else:
                self.logger.warning(f"Unexpected handshake response: {response_data}")
                return False
                
        except Exception as e:
            self.logger.error(f"Handshake failed: {e}")
            return False

    async def _setup_botc_polling(self) -> bool:
        """Setup polling mode for botc.app when websocket fails"""
        try:
            # Create a polling task that checks for game state changes
            self.polling_active = True
            self.last_state_hash = None
            
            # Store that we're using polling mode
            self.connection_mode = "polling"
            
            self.logger.info("botc.app polling mode initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup polling: {e}")
            return False

    async def _poll_botc_state(self) -> Optional[Dict[str, Any]]:
        """Poll botc.app for game state changes"""
        if not self.session or not self.room_code:
            return None
            
        try:
            # Try different API endpoints that botc.app might use
            endpoints = [
                f"/api/room/{self.room_code}/state",
                f"/room/{self.room_code}/api/state",
                f"/api/game/{self.room_code}",
                f"/game/{self.room_code}/state"
            ]
            
            for endpoint in endpoints:
                try:
                    url = f"{self.base_url}{endpoint}"
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            return data
                except:
                    continue
                    
            return None
            
        except Exception as e:
            self.logger.debug(f"Polling failed: {e}")
            return None

    async def _connect_generic(self) -> bool:
        """Generic connection for unknown platforms"""
        self.logger.warning("Using generic connection - limited functionality")
        return True

    async def listen_for_events(self) -> AsyncGenerator[GameEvent, None]:
        """Listen for game events from the platform"""
        if self.platform == "botc_app" and hasattr(self, 'connection_mode') and self.connection_mode == "polling":
            # Use polling mode for botc.app
            async for event in self._poll_for_events():
                yield event
            return
            
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

    async def _poll_for_events(self) -> AsyncGenerator[GameEvent, None]:
        """Poll botc.app for events when websocket is not available"""
        import hashlib
        
        while hasattr(self, 'polling_active') and self.polling_active:
            try:
                # Poll for state changes
                current_state = await self._poll_botc_state()
                
                if current_state:
                    # Create hash of current state to detect changes
                    state_str = json.dumps(current_state, sort_keys=True)
                    current_hash = hashlib.md5(state_str.encode()).hexdigest()
                    
                    if current_hash != self.last_state_hash:
                        self.last_state_hash = current_hash
                        
                        # Generate state change event
                        event = GameEvent(
                            event_type="state_change",
                            timestamp=datetime.now(),
                            data=current_state,
                            source="botc_app_polling"
                        )
                        
                        yield event
                
                # Wait before next poll
                await asyncio.sleep(2)  # Poll every 2 seconds
                
            except Exception as e:
                self.logger.error(f"Polling error: {e}")
                await asyncio.sleep(5)  # Wait longer on error

    async def send_storyteller_action(
        self, action_type: str, data: Dict[str, Any]
    ) -> bool:
        """Send storyteller action to the game"""
        if self.platform == "botc_app":
            return await self._send_botc_action(action_type, data)
            
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

    async def _send_botc_action(self, action_type: str, data: Dict[str, Any]) -> bool:
        """Send action to botc.app using their specific format"""
        try:
            if hasattr(self, 'connection_mode') and self.connection_mode == "polling":
                # Use HTTP API for actions in polling mode
                return await self._send_botc_http_action(action_type, data)
            elif self.websocket:
                # Use websocket with botc.app specific format
                botc_message = self._format_botc_message(action_type, data)
                await self.websocket.send(json.dumps(botc_message))
                return True
            else:
                self.logger.error("No connection available for botc.app action")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send botc.app action: {e}")
            return False

    def _format_botc_message(self, action_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format message for botc.app websocket protocol"""
        # Map our generic actions to botc.app specific format
        action_mapping = {
            "phase_change": "phase",
            "death": "kill",
            "execution": "execute", 
            "start_voting": "nomination",
            "end_voting": "vote_result",
            "private_info": "whisper",
            "wake_player": "wake",
            "sleep_player": "sleep",
            "set_status": "update_player",
            "add_reminder": "reminder",
            "remove_reminder": "remove_reminder"
        }
        
        botc_action = action_mapping.get(action_type, action_type)
        
        return {
            "type": botc_action,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "source": "storyteller"
        }

    async def _send_botc_http_action(self, action_type: str, data: Dict[str, Any]) -> bool:
        """Send action via HTTP when websocket is not available"""
        if not self.session or not self.room_code:
            return False
            
        try:
            # Try different API endpoints for actions
            endpoints = [
                f"/api/room/{self.room_code}/action",
                f"/room/{self.room_code}/api/action",
                f"/api/game/{self.room_code}/storyteller",
                f"/game/{self.room_code}/action"
            ]
            
            action_data = {
                "action": action_type,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            
            for endpoint in endpoints:
                try:
                    url = f"{self.base_url}{endpoint}"
                    async with self.session.post(url, json=action_data) as response:
                        if response.status in [200, 201, 202]:
                            self.logger.debug(f"Action sent via {endpoint}")
                            return True
                except:
                    continue
                    
            self.logger.warning("No valid HTTP endpoint found for botc.app action")
            return False
            
        except Exception as e:
            self.logger.error(f"HTTP action failed: {e}")
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
        # Stop polling if active
        if hasattr(self, 'polling_active'):
            self.polling_active = False
            
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
            return base_features + [
                "private_info",
                "wake_player", 
                "set_status",
                "reminder_tokens",
                "polling_mode",
                "state_sync"
            ]
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
