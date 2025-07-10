"""
Game Automation System for Blood on the Clocktower
Handles complete game flow with intelligent waiting
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple

from ..core.game_state import GameState, Player, PlayerStatus
from ..speech.speech_handler import SpeechHandler
from .character_abilities import AbilitySystem, TriggerType
from .game_persistence import AutoSaveManager, GamePersistence
from .game_replay import EventType, GamePlayer, GameRecorder, ReplayManager
from .live_game_monitor import LiveGameMonitor
from .rule_engine import RuleEngine


class GamePhase(Enum):
    """All possible game phases"""

    SETUP = auto()
    FIRST_NIGHT = auto()
    FIRST_NIGHT_INFO = auto()
    DAWN = auto()
    DAY_DISCUSSION = auto()
    NOMINATIONS = auto()
    VOTING = auto()
    EXECUTION = auto()
    DUSK = auto()
    NIGHT = auto()
    NIGHT_ACTIONS = auto()
    GAME_OVER = auto()


class WaitReason(Enum):
    """Reasons the AI might need to wait"""

    PLAYER_THINKING = auto()
    DISCUSSION_TIME = auto()
    NOMINATION_PERIOD = auto()
    VOTING_PERIOD = auto()
    NIGHT_ACTION = auto()
    DRAMATIC_PAUSE = auto()
    CONFIRMATION_NEEDED = auto()


@dataclass
class WaitCondition:
    """Defines when and why to wait"""

    reason: WaitReason
    min_duration: float = 0.0  # Minimum wait time in seconds
    max_duration: float = 300.0  # Maximum wait time in seconds
    interruptible: bool = True  # Can be interrupted by player action
    prompt_after: Optional[float] = None  # Prompt player after X seconds


@dataclass
class PhaseTransition:
    """Defines how to transition between phases"""

    from_phase: GamePhase
    to_phase: GamePhase
    condition: Optional[callable] = None  # Function to check if transition is allowed
    wait_before: Optional[WaitCondition] = None
    announcement: Optional[str] = None


class GameAutomation:
    """Fully automated game controller with intelligent waiting"""

    def __init__(
        self,
        game_state: GameState,
        rule_engine: RuleEngine,
        speech_handler: SpeechHandler,
        live_monitor: LiveGameMonitor = None,
    ):
        self.game_state = game_state
        self.rule_engine = rule_engine
        self.speech_handler = speech_handler
        self.live_monitor = live_monitor
        self.logger = logging.getLogger(__name__)

        # Current state
        self.current_phase = GamePhase.SETUP
        self.is_waiting = False
        self.wait_interrupted = False
        self.phase_start_time = datetime.now()

        # Game flow control
        self.auto_mode = True
        self.pause_requested = False

        # Phase-specific data
        self.night_order = []
        self.current_night_position = 0
        self.pending_nominations = []
        self.current_vote = None
        self.execution_queue = []

        # Live monitoring integration
        self.nomination_queue = []
        self.vote_results = {}

        # Character ability system
        self.ability_system = AbilitySystem()

        # Game persistence
        self.persistence = GamePersistence()
        self.auto_save_manager = AutoSaveManager(self.persistence)
        self.is_running = False

        # Game replay system
        self.recorder = GameRecorder()
        self.replay_manager = ReplayManager()
        self.recording_enabled = True

        # Define phase transitions
        self._define_transitions()

        # Set up live monitor callbacks if available
        if self.live_monitor:
            self._setup_live_monitor_callbacks()

    def _define_transitions(self):
        """Define all valid phase transitions"""
        self.transitions = [
            # Setup to First Night
            PhaseTransition(
                GamePhase.SETUP,
                GamePhase.FIRST_NIGHT,
                condition=lambda: len(self.game_state.players) >= 5,
                announcement="Welcome to Blood on the Clocktower! Let us begin... "
                "It is the first night. Everyone, close your eyes.",
            ),
            # First Night to Dawn
            PhaseTransition(
                GamePhase.FIRST_NIGHT_INFO,
                GamePhase.DAWN,
                wait_before=WaitCondition(WaitReason.DRAMATIC_PAUSE, min_duration=2.0),
                announcement="The night is over. Everyone, open your eyes. "
                "It is now dawn of the first day.",
            ),
            # Dawn to Day Discussion
            PhaseTransition(
                GamePhase.DAWN,
                GamePhase.DAY_DISCUSSION,
                wait_before=WaitCondition(
                    WaitReason.DISCUSSION_TIME,
                    min_duration=30.0,
                    max_duration=600.0,  # 10 minutes max
                    prompt_after=300.0,  # Prompt after 5 minutes
                ),
                announcement="Good morning everyone. You may now discuss.",
            ),
            # Day to Nominations
            PhaseTransition(
                GamePhase.DAY_DISCUSSION,
                GamePhase.NOMINATIONS,
                announcement="The discussion phase is over. "
                "Nominations are now open. You may nominate.",
            ),
            # Nominations to Voting
            PhaseTransition(
                GamePhase.NOMINATIONS,
                GamePhase.VOTING,
                condition=lambda: len(self.pending_nominations) > 0,
                announcement="Nominations are closed. We will now vote.",
            ),
            # Voting to Execution (if threshold met)
            PhaseTransition(
                GamePhase.VOTING,
                GamePhase.EXECUTION,
                condition=lambda: self._check_execution_threshold(),
                announcement="The vote has passed. We have an execution.",
            ),
            # Voting/Execution to Dusk
            PhaseTransition(
                GamePhase.VOTING,
                GamePhase.DUSK,
                condition=lambda: not self._check_execution_threshold(),
                announcement="The vote has failed. No execution today.",
            ),
            PhaseTransition(
                GamePhase.EXECUTION,
                GamePhase.DUSK,
                wait_before=WaitCondition(WaitReason.DRAMATIC_PAUSE, min_duration=3.0),
                announcement="The sun sets on another day.",
            ),
            # Dusk to Night
            PhaseTransition(
                GamePhase.DUSK,
                GamePhase.NIGHT,
                wait_before=WaitCondition(WaitReason.DRAMATIC_PAUSE, min_duration=2.0),
                announcement="Night falls. Everyone, close your eyes.",
            ),
            # Night to Dawn
            PhaseTransition(
                GamePhase.NIGHT_ACTIONS,
                GamePhase.DAWN,
                wait_before=WaitCondition(WaitReason.DRAMATIC_PAUSE, min_duration=2.0),
                announcement="The night is over. Everyone, open your eyes.",
            ),
        ]

    async def run_game(self):
        """Main game loop - runs entire game with intelligent waiting"""
        self.logger.info("Starting automated game...")
        self.is_running = True

        # Record game start
        if self.recording_enabled and self.game_state:
            player_names = [p.name for p in self.game_state.players]
            self.recorder.record_game_start(player_names)

        # Start auto-save
        await self.start_auto_save()

        try:
            while self.current_phase != GamePhase.GAME_OVER:
                try:
                    # Check if game should end
                    if self._check_game_over():
                        await self._handle_game_over()
                        break

                    # Handle current phase
                    await self._handle_phase()

                    # Check for phase transition
                    next_phase = self._get_next_phase()
                    if next_phase and next_phase != self.current_phase:
                        await self._transition_to_phase(next_phase)

                    # Small delay to prevent tight loop
                    await asyncio.sleep(0.1)

                except Exception as e:
                    self.logger.error(f"Error in game loop: {e}")
                    await self._announce(
                        "I encountered an error. Please check the logs."
                    )
                    break

        finally:
            # Clean up
            self.is_running = False
            await self.stop_auto_save()
            self.logger.info("Game automation stopped")

    async def _handle_phase(self):
        """Handle actions for current phase"""
        if self.current_phase == GamePhase.SETUP:
            await self._handle_setup()

        elif self.current_phase == GamePhase.FIRST_NIGHT:
            await self._handle_first_night()

        elif self.current_phase == GamePhase.FIRST_NIGHT_INFO:
            await self._handle_first_night_info()

        elif self.current_phase == GamePhase.DAY_DISCUSSION:
            await self._handle_day_discussion()

        elif self.current_phase == GamePhase.NOMINATIONS:
            await self._handle_nominations()

        elif self.current_phase == GamePhase.VOTING:
            await self._handle_voting()

        elif self.current_phase == GamePhase.EXECUTION:
            await self._handle_execution()

        elif self.current_phase == GamePhase.NIGHT:
            await self._handle_night()

        elif self.current_phase == GamePhase.NIGHT_ACTIONS:
            await self._handle_night_actions()

    async def _handle_setup(self):
        """Handle game setup phase"""
        # This is handled by the GUI/initialization
        # Just wait for players to be added
        if len(self.game_state.players) >= 5:
            self.logger.info("Enough players joined, starting game...")

    async def _handle_first_night(self):
        """Handle first night - wake roles in order"""
        if not self.night_order:
            self.night_order = self._get_first_night_order()
            self.current_night_position = 0

        if self.current_night_position < len(self.night_order):
            role = self.night_order[self.current_night_position]
            await self._wake_role_first_night(role)
            self.current_night_position += 1
        else:
            # First night complete, move to info phase
            self.current_phase = GamePhase.FIRST_NIGHT_INFO

    async def _handle_first_night_info(self):
        """Give first night information to applicable roles"""
        # This is where Fortune Teller, Empath, etc. get their info
        info_roles = self._get_info_roles()

        for player in self.game_state.get_alive_players():
            if player.character in info_roles:
                info = self._generate_role_info(player)
                await self._give_private_info(player, info)

        # Info phase complete
        await asyncio.sleep(2.0)  # Brief pause

    async def _handle_day_discussion(self):
        """Handle day discussion with smart waiting"""
        # Wait for discussion with ability to interrupt
        wait_condition = WaitCondition(
            WaitReason.DISCUSSION_TIME,
            min_duration=60.0,  # At least 1 minute
            max_duration=600.0,  # Max 10 minutes
            prompt_after=300.0,  # Prompt after 5 minutes
            interruptible=True,
        )

        if not self.is_waiting:
            await self._start_wait(wait_condition)

    async def _handle_nominations(self):
        """Handle nomination phase"""
        # Start live monitoring for nominations
        if self.live_monitor:
            self.live_monitor.set_phase("day")
            if not self.live_monitor.listening_active:
                self.live_monitor.start_monitoring("day")

        wait_condition = WaitCondition(
            WaitReason.NOMINATION_PERIOD,
            min_duration=30.0,  # At least 30 seconds
            max_duration=300.0,  # Max 5 minutes
            prompt_after=120.0,  # Prompt after 2 minutes
            interruptible=True,
        )

        if not self.is_waiting:
            await self._announce(
                "Nominations are open. Say 'I nominate [player name]' to nominate someone."
            )
            await self._start_wait(wait_condition)

    async def _handle_voting(self):
        """Handle voting on nominations"""
        # Move nominations from live queue to pending
        if self.nomination_queue:
            self.pending_nominations.extend(self.nomination_queue)
            self.nomination_queue = []

        if not self.pending_nominations:
            # No nominations, skip to dusk
            self.current_phase = GamePhase.DUSK
            return

        if not self.current_vote:
            # Start first vote
            self.current_vote = self.pending_nominations.pop(0)
            await self._start_vote(self.current_vote)
        else:
            # Check if voting complete
            if await self._is_vote_complete():
                result = self._tally_votes()
                await self._announce_vote_result(result)

                if result["passed"]:
                    self.execution_queue.append(self.current_vote["nominee"])

                # Move to next vote or execution
                if self.pending_nominations:
                    self.current_vote = self.pending_nominations.pop(0)
                    await self._start_vote(self.current_vote)
                else:
                    self.current_vote = None

    async def _handle_execution(self):
        """Handle execution of players"""
        if self.execution_queue:
            player = self.execution_queue.pop(0)
            await self._execute_player(player)

            # Check for additional executions (Virgin, etc.)
            if not self.execution_queue:
                # All executions complete
                pass

    async def _handle_night(self):
        """Handle night phase - wake roles in order"""
        if not self.night_order:
            self.night_order = self._get_night_order()
            self.current_night_position = 0

        if self.current_night_position < len(self.night_order):
            role = self.night_order[self.current_night_position]
            await self._wake_role_night(role)
            self.current_night_position += 1
        else:
            # Night complete, move to actions
            self.current_phase = GamePhase.NIGHT_ACTIONS

    async def _handle_night_actions(self):
        """Process all night actions"""
        # Apply poisoner/drunk effects
        self._apply_status_effects()

        # Process demon kill
        demon_kill = self._get_demon_kill()
        if demon_kill:
            self._kill_player(demon_kill, "demon")

        # Process other night deaths
        self._process_night_deaths()

        # Clear for next day
        self.night_order = []

    def _setup_live_monitor_callbacks(self):
        """Set up callbacks for live monitor integration"""
        if not self.live_monitor:
            return

        # Register callbacks for live events
        self.live_monitor.register_event_callback(
            "nomination_received", self._on_live_nomination
        )
        self.live_monitor.register_event_callback("vote_received", self._on_live_vote)
        self.live_monitor.register_event_callback(
            "close_nominations_request", self._on_close_nominations
        )
        self.live_monitor.register_event_callback(
            "start_voting_request", self._on_start_voting
        )

        self.logger.info("Live monitor callbacks configured")

    async def _on_live_nomination(self, data: Dict[str, Any]):
        """Handle live nomination from continuous listener"""
        nominator = data.get("nominator", "Unknown")
        nominee = data.get("nominee")

        if self.current_phase == GamePhase.NOMINATIONS and nominee:
            # Check for triggered abilities (e.g., Virgin)
            await self._check_nomination_abilities(nominator, nominee)

            # Add to nomination queue
            nomination = {
                "nominator": nominator,
                "nominee": nominee,
                "timestamp": datetime.now(),
                "votes": {"yes": [], "no": []},
            }

            self.nomination_queue.append(nomination)
            self.logger.info(f"🎯 Live nomination queued: {nominator} → {nominee}")

            # Record nomination
            if self.recording_enabled:
                self.recorder.record_nomination(nominator, nominee, successful=True)

            # Announce the nomination
            await self._announce(
                f"Nomination received: {nominator} nominates {nominee}"
            )

            # Interrupt current wait if we're waiting for nominations
            if self.is_waiting:
                self.interrupt_wait()

    async def _on_live_vote(self, data: Dict[str, Any]):
        """Handle live vote from continuous listener"""
        vote = data.get("vote")
        voter = data.get("voter", "Unknown")

        if self.current_phase == GamePhase.VOTING and self.current_vote:
            # Add vote to current nomination
            if vote in ["yes", "aye"]:
                if voter not in self.current_vote.get("votes", {}).get("yes", []):
                    self.current_vote["votes"]["yes"].append(voter)
                    self.logger.info(f"🗳️ Live vote: {voter} votes YES")

                    # Record vote
                    if self.recording_enabled:
                        self.recorder.record_vote(
                            voter, "yes", self.current_vote.get("nominee")
                        )

                    await self._announce(f"{voter} votes yes")
            elif vote in ["no", "nay"]:
                if voter not in self.current_vote.get("votes", {}).get("no", []):
                    self.current_vote["votes"]["no"].append(voter)
                    self.logger.info(f"🗳️ Live vote: {voter} votes NO")

                    # Record vote
                    if self.recording_enabled:
                        self.recorder.record_vote(
                            voter, "no", self.current_vote.get("nominee")
                        )

                    await self._announce(f"{voter} votes no")

    async def _on_close_nominations(self, data: Dict[str, Any]):
        """Handle request to close nominations"""
        if self.current_phase == GamePhase.NOMINATIONS:
            self.logger.info("📢 Request to close nominations received")
            # Move pending nominations to voting queue
            self.pending_nominations.extend(self.nomination_queue)
            self.nomination_queue = []
            self.interrupt_wait()

    async def _on_start_voting(self, data: Dict[str, Any]):
        """Handle request to start voting"""
        if self.current_phase == GamePhase.NOMINATIONS and self.pending_nominations:
            self.logger.info("📢 Request to start voting received")
            self.interrupt_wait()

    async def _start_wait(self, condition: WaitCondition):
        """Start an intelligent wait period"""
        self.is_waiting = True
        self.wait_interrupted = False
        start_time = datetime.now()

        while self.is_waiting:
            elapsed = (datetime.now() - start_time).total_seconds()

            # Check minimum duration
            if elapsed < condition.min_duration:
                await asyncio.sleep(0.5)
                continue

            # Check maximum duration
            if elapsed >= condition.max_duration:
                self.logger.info(f"Maximum wait time reached for {condition.reason}")
                break

            # Check for prompt
            if condition.prompt_after and elapsed >= condition.prompt_after:
                await self._prompt_continue()
                condition.prompt_after = None  # Only prompt once

            # Check for interruption
            if condition.interruptible and self.wait_interrupted:
                self.logger.info(f"Wait interrupted for {condition.reason}")
                break

            await asyncio.sleep(0.5)

        self.is_waiting = False

    def interrupt_wait(self):
        """Interrupt current wait period"""
        self.wait_interrupted = True

    async def _announce(self, message: str):
        """Make a public announcement"""
        self.logger.info(f"Announcing: {message}")

        # Record announcement
        if self.recording_enabled:
            self.recorder.record_announcement(message)

        if self.speech_handler:
            await self.speech_handler.speak(message)

    async def _prompt_continue(self):
        """Prompt to continue"""
        await self._announce(
            "Shall we continue? Say 'continue' when you're ready to proceed."
        )

    def _get_next_phase(self) -> Optional[GamePhase]:
        """Determine next phase based on current state"""
        for transition in self.transitions:
            if transition.from_phase == self.current_phase:
                if not transition.condition or transition.condition():
                    return transition.to_phase
        return None

    async def _transition_to_phase(self, next_phase: GamePhase):
        """Transition to next phase"""
        self.logger.info(f"Transitioning from {self.current_phase} to {next_phase}")

        # Find transition
        transition = None
        for t in self.transitions:
            if t.from_phase == self.current_phase and t.to_phase == next_phase:
                transition = t
                break

        if transition:
            # Wait if needed
            if transition.wait_before:
                await self._start_wait(transition.wait_before)

            # Make announcement
            if transition.announcement:
                await self._announce(transition.announcement)

        # Record phase change
        if self.recording_enabled:
            old_phase = self.current_phase.name if self.current_phase else "none"
            self.recorder.record_phase_change(old_phase, next_phase.name)

        # Update phase
        self.current_phase = next_phase
        self.phase_start_time = datetime.now()

    def _check_game_over(self) -> bool:
        """Check if game has ended"""
        alive_good = sum(
            1 for p in self.game_state.get_alive_players() if p.team == "good"
        )
        alive_evil = sum(
            1 for p in self.game_state.get_alive_players() if p.team == "evil"
        )

        # Evil wins if equal numbers
        if alive_evil >= alive_good:
            self.winner = "evil"
            return True

        # Good wins if no demons
        demons_alive = sum(
            1
            for p in self.game_state.get_alive_players()
            if "demon" in p.character.lower()
        )
        if demons_alive == 0:
            self.winner = "good"
            return True

        return False

    async def _handle_game_over(self):
        """Handle game over"""
        self.current_phase = GamePhase.GAME_OVER

        winner_team = "evil" if self.winner == "evil" else "good"

        # Record game end
        if self.recording_enabled:
            reason = "Demon eliminated" if winner_team == "good" else "Evil equals good"
            self.recorder.record_game_end(winner_team, reason)

        if self.winner == "evil":
            await self._announce(
                "The game is over! Evil has won. "
                "The forces of darkness have prevailed."
            )
        else:
            await self._announce(
                "The game is over! Good has won. "
                "The town has successfully eliminated all demons."
            )

        # Reveal all roles
        await self._reveal_all_roles()

        # Save replay
        if self.recording_enabled:
            try:
                replay_path = await self.replay_manager.save_replay(self.recorder)
                self.logger.info(f"Game replay saved to {replay_path}")
            except Exception as e:
                self.logger.error(f"Failed to save replay: {e}")

    def _get_first_night_order(self) -> List[str]:
        """Get first night wake order based on players in game"""
        # Get all characters in play and sort by official first night order
        first_night_order = [
            "Poisoner",
            "Washerwoman",
            "Librarian",
            "Investigator",
            "Chef",
            "Empath",
            "Fortune Teller",
            "Butler",
            "Spy",
        ]

        # Only return roles that are actually in the game
        active_roles = [p.character for p in self.game_state.get_alive_players()]
        return [role for role in first_night_order if role in active_roles]

    def _get_night_order(self) -> List[str]:
        """Get regular night wake order based on players in game"""
        # Official night order for Trouble Brewing
        night_order = [
            "Poisoner",
            "Monk",
            "Scarlet Woman",
            "Imp",
            "Ravenkeeper",
            "Fortune Teller",
            "Butler",
            "Empath",
            "Spy",
        ]

        # Only return roles that are actually in the game and alive
        active_roles = [p.character for p in self.game_state.get_alive_players()]
        return [role for role in night_order if role in active_roles]

    async def _wake_role_first_night(self, role: str):
        """Wake a role on first night"""
        players_with_role = [
            p for p in self.game_state.get_alive_players() if p.character == role
        ]

        if not players_with_role:
            return

        player = players_with_role[0]  # Assume one of each character
        await self._announce(f"{role}, wake up.")

        # Execute character ability using the ability system
        await self._execute_character_ability(player, TriggerType.FIRST_NIGHT, role)

        await self._announce(f"{role}, go to sleep.")

    async def _wake_role_night(self, role: str):
        """Wake a role on regular night"""
        players_with_role = [
            p for p in self.game_state.get_alive_players() if p.character == role
        ]

        if not players_with_role:
            return

        player = players_with_role[0]
        await self._announce(f"{role}, wake up.")

        # Execute character ability using the ability system
        await self._execute_character_ability(player, TriggerType.EACH_NIGHT, role)

        await self._announce(f"{role}, go to sleep.")

    async def _wait_for_night_action(self, role: str, count: int = 1):
        """Wait for a night action to be performed"""
        wait_condition = WaitCondition(
            WaitReason.NIGHT_ACTION,
            min_duration=5.0,  # At least 5 seconds to choose
            max_duration=60.0,  # Max 1 minute
            prompt_after=30.0,  # Prompt after 30 seconds
            interruptible=True,
        )

        await self._start_wait(wait_condition)

        # For now, return mock data - in real implementation this would
        # capture the player's choice through pointing, touch, or voice
        if count == 1:
            return "MockPlayer"  # Single target
        else:
            return ["MockPlayer1", "MockPlayer2"]  # Multiple targets

    def _check_execution_threshold(self) -> bool:
        """Check if current vote meets execution threshold"""
        if not self.current_vote:
            return False

        # Count votes
        yes_votes = len(self.current_vote.get("yes_votes", []))
        alive_players = len(self.game_state.get_alive_players())

        # Need more than half
        threshold = (alive_players // 2) + 1
        return yes_votes >= threshold

    async def _start_vote(self, nomination: Dict[str, Any]):
        """Start voting on a nomination"""
        nominator = nomination.get("nominator", "Unknown")
        nominee = nomination.get("nominee", "Unknown")

        await self._announce(
            f"We are now voting on the nomination of {nominee} by {nominator}. "
            f"Those who wish to execute {nominee}, please raise your hand and say 'yes'."
        )

        # Start live monitoring for votes
        if self.live_monitor:
            self.live_monitor.voting_in_progress = True
            self.live_monitor.active_votes = []

        # Initialize vote structure if not exists
        if "votes" not in nomination:
            nomination["votes"] = {"yes": [], "no": []}

        self.logger.info(f"🗳️ Started voting on: {nominator} → {nominee}")

    async def _is_vote_complete(self) -> bool:
        """Check if current vote is complete"""
        if not self.current_vote:
            return False

        # For now, wait for a timeout or manual intervention
        # In a real implementation, this would check if all players have voted
        # or a sufficient amount of time has passed

        total_votes = len(self.current_vote.get("votes", {}).get("yes", [])) + len(
            self.current_vote.get("votes", {}).get("no", [])
        )
        alive_players = len(self.game_state.get_alive_players())

        # Vote is complete if everyone voted or timeout reached
        return total_votes >= alive_players

    def _tally_votes(self) -> Dict[str, Any]:
        """Tally the current vote"""
        if not self.current_vote:
            return {"error": "No active vote"}

        votes = self.current_vote.get("votes", {"yes": [], "no": []})
        yes_votes = len(votes.get("yes", []))
        no_votes = len(votes.get("no", []))
        alive_players = len(self.game_state.get_alive_players())

        threshold = (alive_players // 2) + 1
        passed = yes_votes >= threshold

        return {
            "yes_votes": yes_votes,
            "no_votes": no_votes,
            "total_votes": yes_votes + no_votes,
            "threshold": threshold,
            "passed": passed,
            "nominee": self.current_vote.get("nominee"),
            "nominator": self.current_vote.get("nominator"),
        }

    async def _announce_vote_result(self, result: Dict[str, Any]):
        """Announce the result of a vote"""
        nominee = result.get("nominee", "Unknown")
        yes_votes = result.get("yes_votes", 0)
        threshold = result.get("threshold", 0)

        if result.get("passed"):
            await self._announce(
                f"The vote passes with {yes_votes} votes. " f"{nominee} is executed."
            )
        else:
            await self._announce(
                f"The vote fails with {yes_votes} votes. "
                f"At least {threshold} votes were needed. {nominee} lives."
            )

        # Stop live voting
        if self.live_monitor:
            self.live_monitor.voting_in_progress = False

    async def _execute_player(self, player_name: str):
        """Execute a player"""
        player = self.game_state.get_player_by_name(player_name)
        if player and player.is_alive():
            player.kill("execution")

            # Record execution
            if self.recording_enabled:
                # Get vote counts from current vote
                yes_votes = (
                    len(self.current_vote.get("votes", {}).get("yes", []))
                    if self.current_vote
                    else 0
                )
                alive_players = len(self.game_state.get_alive_players())
                threshold = (alive_players // 2) + 1

                self.recorder.record_execution(player_name, yes_votes, threshold)
                self.recorder.record_death(player_name, "execution")

            await self._announce(f"{player_name} has been executed.")

            # Check for execution abilities (Virgin, etc.)
            await self._process_execution_abilities(player)

        self.logger.info(f"⚰️ Player executed: {player_name}")

    async def _process_execution_abilities(self, executed_player):
        """Process abilities that trigger on execution"""
        # Virgin ability: if Virgin executed, nominator might die
        if executed_player.character == "Virgin":
            # Implementation depends on the specific rules
            self.logger.info("Virgin executed - checking for additional deaths")

        # Other execution-triggered abilities would go here

    def _get_info_roles(self) -> List[str]:
        """Get roles that receive first night information"""
        return [
            "Fortune Teller",
            "Empath",
            "Chef",
            "Washerwoman",
            "Librarian",
            "Investigator",
            "Spy",
        ]

    def _generate_role_info(self, player) -> str:
        """Generate information for a player's role"""
        if player.character == "Fortune Teller":
            return "You learn whether the Demon is one of two players."
        elif player.character == "Empath":
            return "You learn how many of your living neighbors are evil."
        elif player.character == "Chef":
            return "You learn how many pairs of evil players there are."
        # Add more role-specific information
        return "You have no information tonight."

    async def _give_private_info(self, player, info: str):
        """Give private information to a player"""
        if self.speech_handler:
            await self.speech_handler.speak_to_player(player.name, info)
        self.logger.info(f"ℹ️ Info to {player.name}: {info}")

    def _apply_status_effects(self):
        """Apply status effects like poison and drunkenness"""
        # Apply poisoner effects
        for player in self.game_state.get_alive_players():
            if hasattr(player, "poisoned") and player.poisoned:
                self.logger.info(f"🧪 {player.name} is poisoned")

    def _get_demon_kill(self) -> Optional[str]:
        """Get the demon's kill choice for the night"""
        # This would be determined by demon player choice
        # For now, return None (no kill)
        return None

    def _kill_player(self, player_name: str, cause: str):
        """Kill a player for the given cause"""
        player = self.game_state.get_player_by_name(player_name)
        if player and player.is_alive():
            player.kill(cause)
            self.logger.info(f"💀 {player_name} killed by {cause}")

    def _process_night_deaths(self):
        """Process all night deaths and apply them at dawn"""
        # Process all scheduled night deaths and announce them
        deaths = self._process_night_deaths_at_dawn()

        if deaths:
            death_announcement = (
                "During the night, the following players died: " + ", ".join(deaths)
            )
            asyncio.create_task(self._announce(death_announcement))
        else:
            asyncio.create_task(self._announce("Nobody died during the night."))

    async def _reveal_all_roles(self):
        """Reveal all player roles at game end"""
        await self._announce("Game over! Here are the roles:")

        for player in self.game_state.players:
            status = "ALIVE" if player.is_alive() else "DEAD"
            await self._announce(
                f"{player.name}: {player.character} ({player.team}) - {status}"
            )

    # Character-specific ability implementations

    async def _apply_poison(self, target_name: str):
        """Apply poison effect to target"""
        target = self.game_state.get_player_by_name(target_name)
        if target:
            setattr(target, "poisoned", True)
            self.logger.info(f"🧪 {target_name} has been poisoned")

    async def _apply_protection(self, target_name: str):
        """Apply monk protection to target"""
        target = self.game_state.get_player_by_name(target_name)
        if target:
            setattr(target, "protected", True)
            self.logger.info(f"🛡️ {target_name} has been protected by the Monk")

    async def _schedule_demon_kill(self, target_name: str):
        """Schedule demon kill for dawn"""
        target = self.game_state.get_player_by_name(target_name)
        if target:
            # Check protection
            if hasattr(target, "protected") and target.protected:
                self.logger.info(f"🛡️ {target_name} was protected from demon kill")
                # Remove protection
                setattr(target, "protected", False)
            else:
                setattr(target, "demon_kill_pending", True)
                self.logger.info(f"💀 {target_name} marked for demon kill")

    async def _set_butler_master(self, butler_player, master_name: str):
        """Set the Butler's master"""
        setattr(butler_player, "master", master_name)
        self.logger.info(f"🤵 Butler's master is now {master_name}")

    async def _check_butler_voting(self, butler_player):
        """Check Butler voting restrictions"""
        if hasattr(butler_player, "master"):
            master_name = butler_player.master
            # Implementation would check if master voted and restrict Butler accordingly
            self.logger.info(f"🤵 Checking Butler voting based on {master_name}'s vote")

    def _get_player_character(self, player_name: str) -> str:
        """Get character of specified player"""
        player = self.game_state.get_player_by_name(player_name)
        return player.character if player else "Unknown"

    async def _generate_washerwoman_info(self) -> str:
        """Generate Washerwoman information"""
        # In real implementation, this would show two players, one with a Townsfolk character
        return "Between PlayerA and PlayerB, one is the Librarian."

    async def _generate_librarian_info(self) -> str:
        """Generate Librarian information"""
        # Shows two players, one with an Outsider character
        return "Between PlayerC and PlayerD, one is the Butler."

    async def _generate_investigator_info(self) -> str:
        """Generate Investigator information"""
        # Shows two players, one with a Minion character
        return "Between PlayerE and PlayerF, one is the Poisoner."

    async def _generate_chef_info(self) -> str:
        """Generate Chef information"""
        # Count pairs of evil players sitting next to each other
        evil_pairs = 0  # Would calculate based on actual seating
        return f"There are {evil_pairs} pairs of evil players."

    async def _generate_empath_info(self, empath_player) -> str:
        """Generate Empath information"""
        # Count evil neighbors
        evil_neighbors = 0  # Would calculate based on actual neighbors
        return f"You have {evil_neighbors} evil neighbors."

    async def _generate_fortune_teller_info(self, targets: List[str]) -> str:
        """Generate Fortune Teller information"""
        # Check if demon is among the two targets
        has_demon = False  # Would check if either target is demon
        if has_demon:
            return f"One of {targets[0]} or {targets[1]} is the Demon."
        else:
            return f"Neither {targets[0]} nor {targets[1]} is the Demon."

    async def _generate_spy_info(self) -> str:
        """Generate Spy information (sees everything)"""
        # Spy would see the entire Grimoire state
        info_parts = []
        info_parts.append("GRIMOIRE STATE:")

        for player in self.game_state.players:
            status = "ALIVE" if player.is_alive() else "DEAD"
            team = "GOOD" if player.team == "good" else "EVIL"
            info_parts.append(
                f"  {player.name}: {player.character} ({team}) - {status}"
            )

        return "\n".join(info_parts)

    # Night death processing

    def _process_night_deaths_at_dawn(self):
        """Process all scheduled night deaths at dawn"""
        deaths = []

        for player in self.game_state.get_alive_players():
            if hasattr(player, "demon_kill_pending") and player.demon_kill_pending:
                player.kill("demon")
                deaths.append(f"{player.name} (killed by demon)")
                setattr(player, "demon_kill_pending", False)

        # Clear daily status effects
        for player in self.game_state.players:
            if hasattr(player, "protected"):
                setattr(player, "protected", False)
            if hasattr(player, "died_today"):
                setattr(player, "died_today", False)

        # Mark today's deaths
        for player in self.game_state.players:
            if not player.is_alive() and not hasattr(player, "died_today"):
                setattr(player, "died_today", True)

        return deaths

    # Game state utilities

    def get_automation_status(self) -> Dict[str, Any]:
        """Get current automation status"""
        return {
            "phase": self.current_phase.name,
            "is_waiting": self.is_waiting,
            "auto_mode": self.auto_mode,
            "pause_requested": self.pause_requested,
            "night_position": f"{self.current_night_position}/{len(self.night_order)}",
            "pending_nominations": len(self.pending_nominations),
            "nomination_queue": len(self.nomination_queue),
            "execution_queue": len(self.execution_queue),
            "live_monitoring": (
                self.live_monitor.listening_active if self.live_monitor else False
            ),
        }

    def pause_automation(self):
        """Pause the automation system"""
        self.pause_requested = True
        self.auto_mode = False
        if self.is_waiting:
            self.interrupt_wait()
        self.logger.info("⏸️ Game automation paused")

    def resume_automation(self):
        """Resume the automation system"""
        self.pause_requested = False
        self.auto_mode = True
        self.logger.info("▶️ Game automation resumed")

    def force_phase_transition(self, target_phase: GamePhase):
        """Force transition to specific phase (manual override)"""
        self.logger.info(f"🔧 Forcing phase transition to {target_phase.name}")
        self.current_phase = target_phase
        self.phase_start_time = datetime.now()
        if self.is_waiting:
            self.interrupt_wait()

    async def _execute_character_ability(
        self, player: Player, trigger: TriggerType, role: str
    ):
        """Execute a character's ability through the ability system"""
        try:
            # Get targets if needed
            targets = None

            if trigger in [TriggerType.FIRST_NIGHT, TriggerType.EACH_NIGHT]:
                targets = await self._get_ability_targets(role, trigger)

            # Execute the ability
            execution = await self.ability_system.execute_ability(
                role, player, self.game_state, trigger, targets
            )

            if execution:
                # Record ability execution
                if self.recording_enabled:
                    self.recorder.record_ability_execution(
                        player.name,
                        role,
                        targets,
                        execution.result.name,
                        execution.effects,
                    )

                # Process the results
                await self._process_ability_execution(execution)

        except Exception as e:
            self.logger.error(f"Error executing {role} ability: {e}")

    async def _get_ability_targets(
        self, role: str, trigger: TriggerType
    ) -> Optional[List[str]]:
        """Get targets for character abilities"""
        # Provide appropriate prompts based on character
        if role == "Imp":
            await self._announce("Choose a player to kill.")
            return [await self._wait_for_night_action(role)]

        elif role == "Poisoner":
            await self._announce("Choose a player to poison.")
            return [await self._wait_for_night_action(role)]

        elif role == "Monk":
            await self._announce("Choose a player to protect from the demon.")
            return [await self._wait_for_night_action(role)]

        elif role == "Fortune Teller":
            await self._announce("Choose two players.")
            return await self._wait_for_night_action(role, count=2)

        elif role == "Butler" and trigger == TriggerType.FIRST_NIGHT:
            await self._announce("Choose a player to be your master.")
            return [await self._wait_for_night_action(role)]

        # Information roles don't need targets
        return None

    async def _process_ability_execution(self, execution):
        """Process the results of an ability execution"""
        if execution.effects.get("information"):
            # Give information to the player
            player = self.game_state.get_player_by_name(execution.player_name)
            if player:
                await self._give_private_info(player, execution.effects["information"])

        if execution.effects.get("kill_scheduled"):
            # Kill was scheduled - will be processed at dawn
            self.logger.info(f"💀 Kill scheduled by {execution.character}")

        if execution.effects.get("protected"):
            # Protection applied
            target = execution.targets[0] if execution.targets else "Unknown"
            self.logger.info(f"🛡️ {target} protected by {execution.character}")

        if execution.effects.get("poisoned"):
            # Poison applied
            target = execution.targets[0] if execution.targets else "Unknown"
            self.logger.info(f"🧪 {target} poisoned by {execution.character}")

        if execution.effects.get("becomes_imp"):
            # Scarlet Woman became Imp
            await self._announce(f"{execution.player_name} is now the Imp!")

        if execution.effects.get("nominator_dies"):
            # Virgin power triggered
            nominator = execution.targets[0] if execution.targets else "Unknown"
            await self._announce(f"{nominator} dies for nominating the Virgin!")

        # Log the execution
        self.logger.info(f"🎭 {execution.character} ability: {execution.result.name}")

    async def _check_nomination_abilities(self, nominator: str, nominee: str):
        """Check for abilities that trigger on nomination"""
        nominee_player = self.game_state.get_player_by_name(nominee)

        if nominee_player and nominee_player.character == "Virgin":
            # Execute Virgin ability
            execution = await self.ability_system.execute_ability(
                "Virgin",
                nominee_player,
                self.game_state,
                TriggerType.ON_NOMINATION,
                nominator=nominator,
            )

            if execution:
                await self._process_ability_execution(execution)

    # Game persistence methods

    async def save_game(self, filename: str = None) -> str:
        """Save the current game state"""
        try:
            save_path = await self.persistence.save_game(self, filename)
            await self._announce("Game saved successfully.")
            self.logger.info(f"Game saved to {save_path}")
            return save_path
        except Exception as e:
            error_msg = f"Failed to save game: {e}"
            await self._announce(error_msg)
            self.logger.error(error_msg)
            raise

    async def load_game(self, filename: str) -> bool:
        """Load a game state"""
        try:
            # Stop current auto-save
            await self.auto_save_manager.stop_auto_save()

            # Load the save data
            save_data = await self.persistence.load_game(filename)

            # Restore the game state
            success = await self.persistence.restore_game_state(save_data, self)

            if success:
                await self._announce("Game loaded successfully.")
                self.logger.info(f"Game loaded from {filename}")

                # Restart auto-save if game was running
                if self.is_running:
                    await self.auto_save_manager.start_auto_save(self)

                return True
            else:
                await self._announce("Failed to restore game state.")
                return False

        except Exception as e:
            error_msg = f"Failed to load game: {e}"
            await self._announce(error_msg)
            self.logger.error(error_msg)
            return False

    async def quick_save(self) -> str:
        """Create a quick save"""
        return await self.persistence.quick_save(self)

    def list_saves(self) -> List[Dict[str, Any]]:
        """List all available save files"""
        return self.persistence.list_saves()

    async def delete_save(self, filename: str) -> bool:
        """Delete a save file"""
        return await self.persistence.delete_save(filename)

    async def export_game_log(self, filename: str = None) -> str:
        """Export game as human-readable log"""
        # Create save data for export
        from .game_persistence import GameSaveData

        save_data = GameSaveData()
        await self.persistence._populate_save_data(save_data, self)

        return await self.persistence.export_game_log(save_data, filename)

    async def start_auto_save(self):
        """Start automatic saving"""
        await self.auto_save_manager.start_auto_save(self)

    async def stop_auto_save(self):
        """Stop automatic saving"""
        await self.auto_save_manager.stop_auto_save()

    # Game replay methods

    def enable_recording(self, enabled: bool = True):
        """Enable or disable game recording"""
        self.recording_enabled = enabled
        if enabled:
            self.logger.info("Game recording enabled")
        else:
            self.logger.info("Game recording disabled")

    async def save_replay(self, filename: str = None) -> str:
        """Save current game replay"""
        try:
            replay_path = await self.replay_manager.save_replay(self.recorder, filename)
            self.logger.info(f"Replay saved to {replay_path}")
            return replay_path
        except Exception as e:
            self.logger.error(f"Failed to save replay: {e}")
            raise

    async def load_replay(self, filename: str) -> GamePlayer:
        """Load a game replay"""
        try:
            player = await self.replay_manager.load_replay(filename)
            self.logger.info(f"Replay loaded from {filename}")
            return player
        except Exception as e:
            self.logger.error(f"Failed to load replay: {e}")
            raise

    def list_replays(self) -> List[Dict[str, Any]]:
        """List all available replays"""
        return self.replay_manager.list_replays()

    async def delete_replay(self, filename: str) -> bool:
        """Delete a replay file"""
        return await self.replay_manager.delete_replay(filename)

    def get_current_replay_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent events from current recording"""
        events = self.recorder.get_events(limit=limit)
        return [event.to_dict() for event in events]

    def get_replay_summary(self) -> Dict[str, Any]:
        """Get summary of current recording"""
        return {
            "replay_id": self.recorder.replay_id,
            "total_events": len(self.recorder.events),
            "current_phase": self.current_phase.name if self.current_phase else "none",
            "current_day": self.recorder.current_day,
            "current_night": self.recorder.current_night,
            "metadata": self.recorder.metadata.to_dict(),
            "recording_enabled": self.recording_enabled,
        }
