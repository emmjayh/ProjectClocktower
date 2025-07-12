"""
Live Game Monitor
Integrates continuous listening with game state management
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from ..core.game_state import GameState
from ..game.rule_engine import RuleEngine
from ..speech.continuous_listener import ContinuousListener, ListenerConfig


@dataclass
class NominationEvent:
    """Represents a nomination event"""

    nominator: str
    nominee: str
    timestamp: datetime
    phase: str
    valid: bool
    reason: Optional[str] = None


class LiveGameMonitor:
    """Monitors live game audio and processes events in real-time"""

    def __init__(self, game_state: GameState, rule_engine: RuleEngine):
        self.game_state = game_state
        self.rule_engine = rule_engine
        self.logger = logging.getLogger(__name__)

        # Audio monitoring
        self.listener = None
        self.listening_active = False

        # Event tracking
        self.pending_nominations = []
        self.active_votes = []
        self.recent_events = []

        # Game phase monitoring
        self.current_phase = "day"
        self.nominations_open = False
        self.voting_in_progress = False

        # Callbacks for UI updates
        self.event_callbacks = {}

    async def initialize(self) -> bool:
        """Initialize the live game monitor"""
        try:
            # Configure listener for Blood on the Clocktower
            config = ListenerConfig(
                window_duration=2.5,
                overlap_duration=0.8,
                wake_words=[
                    "nominate",
                    "i nominate",
                    "vote",
                    "execution",
                    "storyteller",
                    "demon",
                    "minion",
                    "outsider",
                    "townsfolk",
                    "clocktower",
                    "close nominations",
                ],
                confidence_threshold=0.6,
                vad_threshold=0.025,  # Slightly lower for group settings
            )

            self.listener = ContinuousListener(config)

            # Register command handlers
            self.listener.register_command_callback(
                "nomination", self._handle_nomination
            )
            self.listener.register_command_callback("vote", self._handle_vote)
            self.listener.register_command_callback(
                "general", self._handle_general_command
            )
            self.listener.register_command_callback(
                "character_mention", self._handle_character_mention
            )

            # Initialize listener
            success = await self.listener.initialize()
            if success:
                self.logger.info("Live game monitor initialized")

            return success

        except Exception as e:
            self.logger.error(f"Failed to initialize live game monitor: {e}")
            return False

    def register_event_callback(self, event_type: str, callback):
        """Register callback for specific event types"""
        self.event_callbacks[event_type] = callback

    def start_monitoring(self, phase: str = "day"):
        """Start live audio monitoring"""
        if not self.listener:
            self.logger.error("Monitor not initialized")
            return

        self.current_phase = phase
        self.listening_active = True

        if phase == "day":
            self.nominations_open = True
            self.logger.info("🎤 Started monitoring for nominations and votes")
        else:
            self.nominations_open = False
            self.logger.info(f"🎤 Started monitoring for {phase} phase")

        self.listener.start_listening()

    def stop_monitoring(self):
        """Stop live audio monitoring"""
        if self.listener:
            self.listener.stop_listening()

        self.listening_active = False
        self.nominations_open = False
        self.voting_in_progress = False

        self.logger.info("🔇 Stopped live monitoring")

    def set_phase(self, phase: str):
        """Update current game phase"""
        self.current_phase = phase

        if phase == "day":
            self.nominations_open = True
        else:
            self.nominations_open = False
            self.voting_in_progress = False

    async def _handle_nomination(self, command: Dict[str, Any]):
        """Handle detected nomination"""
        try:
            if not self.nominations_open:
                self.logger.info(
                    f"Nomination ignored - nominations not open (phase: {self.current_phase})"
                )
                return

            nominee = command.get("nominee")
            nominator = command.get("nominator", "Unknown")

            if not nominee:
                self.logger.warning("Unclear nomination detected")
                await self._trigger_clarification("nomination_unclear", command)
                return

            # Validate nomination
            validation = self.rule_engine.validate_nomination(
                nominator, nominee, self.game_state
            )

            nomination = NominationEvent(
                nominator=nominator,
                nominee=nominee,
                timestamp=datetime.now(),
                phase=self.current_phase,
                valid=validation["valid"],
                reason=validation.get("reason"),
            )

            if validation["valid"]:
                # Add to pending nominations
                self.pending_nominations.append(nomination)

                self.logger.info(
                    f"✅ Valid nomination: {nominator} nominates {nominee}"
                )

                # Trigger callbacks
                await self._trigger_event(
                    "nomination_received",
                    {
                        "nominator": nominator,
                        "nominee": nominee,
                        "validation": validation,
                    },
                )

                # Auto-announce if configured
                await self._announce_nomination(nomination)

            else:
                self.logger.info(f"❌ Invalid nomination: {nomination.reason}")

                await self._trigger_event(
                    "nomination_invalid",
                    {
                        "nominator": nominator,
                        "nominee": nominee,
                        "reason": validation["reason"],
                    },
                )

        except Exception as e:
            self.logger.error(f"Error handling nomination: {e}")

    async def _handle_vote(self, command: Dict[str, Any]):
        """Handle detected vote"""
        try:
            if not self.voting_in_progress:
                self.logger.debug("Vote ignored - no active voting")
                return

            vote = command.get("vote")
            text = command.get("text", "")

            self.logger.info(f"🗳️ Vote detected: {vote} ('{text}')")

            # Add to active votes
            vote_event = {
                "vote": vote,
                "text": text,
                "timestamp": datetime.now(),
                "voter": "Unknown",  # Would need speaker identification
            }

            self.active_votes.append(vote_event)

            await self._trigger_event("vote_received", vote_event)

        except Exception as e:
            self.logger.error(f"Error handling vote: {e}")

    async def _handle_general_command(self, command: Dict[str, Any]):
        """Handle general game-related speech"""
        text = command.get("text", "").lower()
        wake_words = command.get("wake_words", [])

        # Check for phase change requests
        if any(
            phrase in text
            for phrase in ["close nominations", "end nominations", "voting time"]
        ):
            if self.nominations_open:
                self.logger.info("📢 Request to close nominations detected")
                await self._trigger_event("close_nominations_request", command)

        elif any(
            phrase in text for phrase in ["start voting", "time to vote", "begin vote"]
        ):
            if self.pending_nominations:
                self.logger.info("📢 Request to start voting detected")
                await self._trigger_event("start_voting_request", command)

        # Log for analysis
        self.recent_events.append(
            {
                "type": "general_speech",
                "text": text,
                "wake_words": wake_words,
                "timestamp": datetime.now(),
            }
        )

        # Keep only recent events
        if len(self.recent_events) > 50:
            self.recent_events = self.recent_events[-25:]

    async def _handle_character_mention(self, command: Dict[str, Any]):
        """Handle character or role mentions"""
        text = command.get("text", "")
        wake_words = command.get("wake_words", [])

        self.logger.info(f"🎭 Character mention: {wake_words} in '{text}'")

        # Could be used for role claims, accusations, etc.
        await self._trigger_event(
            "character_mention",
            {"text": text, "characters": wake_words, "timestamp": datetime.now()},
        )

    async def _announce_nomination(self, nomination: NominationEvent):
        """Announce a valid nomination"""
        message = f"{nomination.nominator} nominates {nomination.nominee}."

        # Trigger TTS announcement
        await self._trigger_event(
            "tts_announce", {"message": message, "priority": "high"}
        )

    async def _trigger_clarification(self, event_type: str, command: Dict[str, Any]):
        """Request clarification for unclear commands"""
        await self._trigger_event(
            "request_clarification",
            {
                "type": event_type,
                "command": command,
                "message": "I heard something that sounded like a nomination, but I'm not sure. Could you repeat that?",
            },
        )

    async def _trigger_event(self, event_type: str, data: Dict[str, Any]):
        """Trigger event callback"""
        if event_type in self.event_callbacks:
            try:
                callback = self.event_callbacks[event_type]
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as e:
                self.logger.error(f"Event callback error for {event_type}: {e}")

    def start_voting_on_nomination(self, nomination_index: int = -1):
        """Start voting on a specific nomination"""
        if not self.pending_nominations:
            return False

        nomination = self.pending_nominations[nomination_index]
        self.voting_in_progress = True
        self.active_votes = []

        self.logger.info(
            f"🗳️ Started voting on: {nomination.nominator} nominates {nomination.nominee}"
        )
        return True

    def end_voting(self) -> Dict[str, Any]:
        """End current voting and return results"""
        if not self.voting_in_progress:
            return {"error": "No active voting"}

        results = {
            "total_votes": len(self.active_votes),
            "yes_votes": len([v for v in self.active_votes if v["vote"] == "yes"]),
            "no_votes": len([v for v in self.active_votes if v["vote"] == "no"]),
            "votes": self.active_votes.copy(),
        }

        self.voting_in_progress = False
        self.active_votes = []

        self.logger.info(
            f"🗳️ Voting ended: {results['yes_votes']} yes, {results['no_votes']} no"
        )

        return results

    def get_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        return {
            "listening": self.listening_active,
            "phase": self.current_phase,
            "nominations_open": self.nominations_open,
            "voting_in_progress": self.voting_in_progress,
            "pending_nominations": len(self.pending_nominations),
            "active_votes": len(self.active_votes),
            "recent_events": len(self.recent_events),
        }


# Integration example
async def example_integration():
    """Example of how to integrate with the main game"""

    # Mock game state and rule engine
    game_state = None  # Would be actual GameState instance
    rule_engine = None  # Would be actual RuleEngine instance

    monitor = LiveGameMonitor(game_state, rule_engine)

    # Set up event handlers
    async def on_nomination(data):
        print(f"🎯 New nomination: {data}")
        # Update UI, announce, etc.

    async def on_vote(data):
        print(f"🗳️ New vote: {data}")
        # Update vote counter

    async def on_tts_announce(data):
        print(f"📢 Announce: {data['message']}")
        # Trigger text-to-speech

    monitor.register_event_callback("nomination_received", on_nomination)
    monitor.register_event_callback("vote_received", on_vote)
    monitor.register_event_callback("tts_announce", on_tts_announce)

    # Initialize and start
    if await monitor.initialize():
        monitor.start_monitoring("day")

        # Simulate game flow
        try:
            print("🎮 Game monitoring active - speak nominations!")
            await asyncio.sleep(60)  # Listen for 1 minute
        finally:
            monitor.stop_monitoring()


if __name__ == "__main__":
    asyncio.run(example_integration())
