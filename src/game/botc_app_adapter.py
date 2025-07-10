"""
BotC.app Adapter
Specialized adapter for improving compatibility with botc.app platform
"""

import asyncio
import json
import logging
import websockets
from datetime import datetime
from typing import Any, Dict, List, Optional

from .clocktower_api import ClockTowerAPI, GameEvent


class BotCAppAdapter:
    """Specialized adapter for botc.app with enhanced compatibility"""

    def __init__(self, api_client: ClockTowerAPI):
        self.api = api_client
        self.logger = logging.getLogger(__name__)
        self.player_cache = {}
        self.state_cache = {}
        self.last_sync = None

    async def enhanced_connect(self, room_code: str) -> bool:
        """Enhanced connection with botc.app specific optimizations"""
        try:
            self.logger.info(f"Connecting to botc.app room: {room_code}")

            # First, try standard connection
            success = await self.api.connect()

            if success:
                # Perform botc.app specific initialization
                await self._initialize_botc_session()
                await self._sync_initial_state()
                return True
            else:
                # If connection fails, try alternative methods
                return await self._fallback_connection(room_code)

        except Exception as e:
            self.logger.error(f"Enhanced connection failed: {e}")
            return False

    async def _initialize_botc_session(self):
        """Initialize botc.app specific session features"""
        try:
            # Send enhanced identification
            if self.api.websocket:
                init_message = {
                    "type": "storyteller_init",
                    "features": [
                        "auto_night_order",
                        "character_abilities",
                        "reminder_tokens",
                        "private_chat",
                        "state_sync",
                    ],
                    "version": "1.0.1",
                    "client": "BotC-AI-Storyteller",
                }

                await self.api.websocket.send(json.dumps(init_message))
                self.logger.info("Sent botc.app storyteller initialization")

        except Exception as e:
            self.logger.warning(f"Session initialization failed: {e}")

    async def _sync_initial_state(self):
        """Sync initial game state with enhanced data"""
        try:
            # Get comprehensive game state
            state = await self.get_enhanced_game_state()
            if state:
                self.state_cache = state
                self.last_sync = datetime.now()
                self.logger.info("Initial state synchronized")

        except Exception as e:
            self.logger.warning(f"Initial state sync failed: {e}")

    async def _fallback_connection(self, room_code: str) -> bool:
        """Fallback connection methods for botc.app"""
        try:
            self.logger.info("Attempting fallback connection methods")

            # Method 1: Direct room access
            if await self._try_direct_room_access(room_code):
                return True

            # Method 2: Observer mode connection
            if await self._try_observer_mode(room_code):
                return True

            # Method 3: Polling-only mode
            if await self._setup_polling_mode(room_code):
                return True

            return False

        except Exception as e:
            self.logger.error(f"All fallback methods failed: {e}")
            return False

    async def _try_direct_room_access(self, room_code: str) -> bool:
        """Try direct room access without websocket"""
        try:
            room_url = f"{self.api.base_url}/room/{room_code}"
            async with self.api.session.get(room_url) as response:
                if response.status == 200:
                    self.logger.info("Direct room access successful")
                    return True
            return False

        except Exception as e:
            self.logger.debug(f"Direct room access failed: {e}")
            return False

    async def _try_observer_mode(self, room_code: str) -> bool:
        """Try connecting as observer first, then upgrade to storyteller"""
        try:
            # Connect as observer
            observer_url = (
                f"{self.api.base_url.replace('http', 'ws')}/observe/{room_code}"
            )
            self.api.websocket = await asyncio.wait_for(
                websockets.connect(observer_url), timeout=10
            )

            # Request storyteller privileges
            upgrade_message = {
                "type": "request_storyteller",
                "auth": "AI_STORYTELLER_TOKEN",
            }

            await self.api.websocket.send(json.dumps(upgrade_message))
            self.logger.info("Observer mode connection established")
            return True

        except Exception as e:
            self.logger.debug(f"Observer mode failed: {e}")
            return False

    async def _setup_polling_mode(self, room_code: str) -> bool:
        """Setup enhanced polling mode for botc.app"""
        try:
            self.api.connection_mode = "enhanced_polling"
            self.api.polling_active = True
            self.api.room_code = room_code

            self.logger.info("Enhanced polling mode activated")
            return True

        except Exception as e:
            self.logger.error(f"Enhanced polling setup failed: {e}")
            return False

    async def get_enhanced_game_state(self) -> Optional[Dict[str, Any]]:
        """Get enhanced game state with botc.app specific data"""
        try:
            # Try multiple endpoints for comprehensive state
            state_endpoints = [
                f"/api/room/{self.api.room_code}/full_state",
                f"/room/{self.api.room_code}/grimoire",
                f"/api/game/{self.api.room_code}/detailed",
                f"/game/{self.api.room_code}/state",
            ]

            for endpoint in state_endpoints:
                try:
                    url = f"{self.api.base_url}{endpoint}"
                    async with self.api.session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()

                            # Enhance the data with processed information
                            enhanced_data = await self._enhance_state_data(data)
                            return enhanced_data

                except Exception:
                    continue

            return None

        except Exception as e:
            self.logger.error(f"Enhanced state retrieval failed: {e}")
            return None

    async def _enhance_state_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance raw state data with additional processing"""
        try:
            enhanced = raw_data.copy()

            # Add player analysis
            if "players" in enhanced:
                enhanced["player_analysis"] = await self._analyze_players(
                    enhanced["players"]
                )

            # Add night order information
            enhanced["night_order"] = await self._get_night_order()

            # Add script information
            enhanced["script_info"] = await self._get_script_info()

            # Add timing information
            enhanced["last_updated"] = datetime.now().isoformat()

            return enhanced

        except Exception as e:
            self.logger.warning(f"State enhancement failed: {e}")
            return raw_data

    async def _analyze_players(self, players: List[Dict]) -> Dict[str, Any]:
        """Analyze player data for enhanced insights"""
        analysis = {
            "total_count": len(players),
            "alive_count": 0,
            "dead_count": 0,
            "teams": {"good": 0, "evil": 0, "unknown": 0},
            "special_statuses": [],
        }

        for player in players:
            if player.get("alive", True):
                analysis["alive_count"] += 1
            else:
                analysis["dead_count"] += 1

            team = player.get("team", "unknown")
            analysis["teams"][team] = analysis["teams"].get(team, 0) + 1

            # Check for special statuses
            if player.get("drunk"):
                analysis["special_statuses"].append(f"{player['name']}: drunk")
            if player.get("poisoned"):
                analysis["special_statuses"].append(f"{player['name']}: poisoned")

        return analysis

    async def _get_night_order(self) -> List[str]:
        """Get current night order for the script"""
        # This would ideally come from the botc.app API
        # For now, return a standard Trouble Brewing night order
        return [
            "Poisoner",
            "Monk",
            "Scarlet Woman",
            "Imp",
            "Ravenkeeper",
            "Empath",
            "Fortune Teller",
            "Undertaker",
            "Butler",
        ]

    async def _get_script_info(self) -> Dict[str, Any]:
        """Get information about the current script"""
        return {
            "name": "Unknown Script",
            "characters": [],
            "night_order": await self._get_night_order(),
            "special_rules": [],
        }

    async def send_enhanced_action(self, action_type: str, **kwargs) -> bool:
        """Send enhanced action with botc.app optimizations"""
        try:
            # Pre-process action for botc.app compatibility
            processed_data = await self._preprocess_action(action_type, kwargs)

            # Send via multiple channels for reliability
            success = await self.api.send_storyteller_action(
                action_type, processed_data
            )

            # If websocket fails, try HTTP fallback
            if not success and hasattr(self.api, "connection_mode"):
                success = await self.api._send_botc_http_action(
                    action_type, processed_data
                )

            # Cache successful actions for state tracking
            if success:
                await self._cache_action(action_type, processed_data)

            return success

        except Exception as e:
            self.logger.error(f"Enhanced action failed: {e}")
            return False

    async def _preprocess_action(
        self, action_type: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Preprocess action data for botc.app compatibility"""
        processed = data.copy()

        # Add timestamp if not present
        if "timestamp" not in processed:
            processed["timestamp"] = datetime.now().isoformat()

        # Add room context
        if self.api.room_code:
            processed["room"] = self.api.room_code

        # Add storyteller signature
        processed["storyteller"] = "AI_STORYTELLER"

        return processed

    async def _cache_action(self, action_type: str, data: Dict[str, Any]):
        """Cache action for state tracking"""
        try:
            if not hasattr(self, "action_cache"):
                self.action_cache = []

            self.action_cache.append(
                {
                    "type": action_type,
                    "data": data,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Keep only recent actions
            if len(self.action_cache) > 100:
                self.action_cache = self.action_cache[-50:]

        except Exception as e:
            self.logger.warning(f"Action caching failed: {e}")

    async def sync_state(self) -> bool:
        """Manually sync state with botc.app"""
        try:
            current_state = await self.get_enhanced_game_state()
            if current_state:
                self.state_cache = current_state
                self.last_sync = datetime.now()
                self.logger.info("State sync completed")
                return True
            return False

        except Exception as e:
            self.logger.error(f"State sync failed: {e}")
            return False

    def get_cached_state(self) -> Optional[Dict[str, Any]]:
        """Get last cached state"""
        return self.state_cache.copy() if self.state_cache else None

    def get_connection_info(self) -> Dict[str, Any]:
        """Get detailed connection information"""
        return {
            "platform": "botc_app",
            "connection_mode": getattr(self.api, "connection_mode", "unknown"),
            "websocket_active": self.api.websocket is not None,
            "polling_active": getattr(self.api, "polling_active", False),
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "room_code": self.api.room_code,
            "cached_players": len(self.player_cache),
            "supported_features": self.api.get_supported_features(),
        }


class BotCAppEventProcessor:
    """Process and normalize events from botc.app"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def process_event(self, raw_event: GameEvent) -> GameEvent:
        """Process and normalize botc.app events"""
        try:
            # Normalize event type
            normalized_type = self._normalize_event_type(raw_event.event_type)

            # Enhance event data
            enhanced_data = self._enhance_event_data(raw_event.data)

            return GameEvent(
                event_type=normalized_type,
                timestamp=raw_event.timestamp,
                data=enhanced_data,
                source="botc_app_processed",
            )

        except Exception as e:
            self.logger.warning(f"Event processing failed: {e}")
            return raw_event

    def _normalize_event_type(self, event_type: str) -> str:
        """Normalize botc.app event types to standard format"""
        mapping = {
            "phase": "phase_change",
            "kill": "death",
            "execute": "execution",
            "nomination": "start_voting",
            "vote_result": "end_voting",
            "whisper": "private_info",
            "wake": "wake_player",
            "sleep": "sleep_player",
            "update_player": "set_status",
            "reminder": "add_reminder",
        }

        return mapping.get(event_type, event_type)

    def _enhance_event_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance event data with additional context"""
        enhanced = data.copy()

        # Add processing timestamp
        enhanced["processed_at"] = datetime.now().isoformat()

        # Add event source
        enhanced["source_platform"] = "botc_app"

        return enhanced
