"""
Timing Configuration for Blood on the Clocktower
Manages game pacing with AI-suggested timing
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class PacingStyle(Enum):
    """Game pacing preferences"""

    QUICK = "quick"  # Fast-paced, 5-10 min rounds
    STANDARD = "standard"  # Normal pace, 10-15 min rounds
    RELAXED = "relaxed"  # Leisurely, 15-20 min rounds
    CUSTOM = "custom"  # User-defined timing


@dataclass
class TimingConfig:
    """
    Timing configuration for game phases
    All times are in seconds and are SUGGESTIONS, not hard limits
    """

    # Night phase timing
    night_phase_duration: int = 180  # 3 minutes default
    character_wake_time: int = 30  # Time per character during night

    # Day phase timing
    day_discussion_time: int = 300  # 5 minutes general discussion
    nomination_discussion: int = 120  # 2 minutes per nomination
    voting_countdown: int = 30  # 30 seconds to vote

    # Other timings
    execution_speech_time: int = 60  # Final words before execution
    between_phase_pause: int = 15  # Pause between phases

    # Pacing style
    pacing_style: PacingStyle = PacingStyle.STANDARD

    # Flexibility settings
    allow_extensions: bool = True  # Players can request more time
    auto_extend_heated: bool = True  # Auto-extend during heated discussions
    reminder_intervals: int = 60  # Gentle reminders every minute

    @classmethod
    def quick_game(cls) -> "TimingConfig":
        """Quick game settings - good for experienced players"""
        return cls(
            night_phase_duration=120,
            character_wake_time=20,
            day_discussion_time=180,
            nomination_discussion=60,
            voting_countdown=20,
            execution_speech_time=30,
            between_phase_pause=10,
            pacing_style=PacingStyle.QUICK,
        )

    @classmethod
    def standard_game(cls) -> "TimingConfig":
        """Standard timing - balanced for most games"""
        return cls()  # Uses defaults

    @classmethod
    def relaxed_game(cls) -> "TimingConfig":
        """Relaxed timing - good for new players or social games"""
        return cls(
            night_phase_duration=300,
            character_wake_time=45,
            day_discussion_time=600,
            nomination_discussion=180,
            voting_countdown=45,
            execution_speech_time=90,
            between_phase_pause=20,
            pacing_style=PacingStyle.RELAXED,
        )

    def get_phase_suggestion(self, phase: str, context: dict = None) -> str:
        """Get timing suggestion for current phase"""

        suggestions = {
            "night": f"Night phase typically takes {
                self.night_phase_duration //
                60} minutes",
            "day_discussion": f"Allow about {
                self.day_discussion_time //
                60} minutes for open discussion",
            "nomination": f"Each nomination deserves {
                self.nomination_discussion //
                60} minutes of debate",
            "voting": f"Voting should conclude within {
                self.voting_countdown} seconds",
            "execution": f"Grant the condemned {
                self.execution_speech_time} seconds for final words",
        }

        base_suggestion = suggestions.get(phase, "Take the time you need")

        # Add flexibility note
        if self.allow_extensions:
            base_suggestion += " (flexible - extend as needed)"

        return base_suggestion


class TimingManager:
    """Manages game timing and pacing suggestions"""

    def __init__(self, config: Optional[TimingConfig] = None):
        self.config = config or TimingConfig.standard_game()
        self.phase_start_times = {}
        self.extension_count = {}

    def start_phase(self, phase_name: str) -> str:
        """Start timing a phase and return suggestion"""
        import time

        self.phase_start_times[phase_name] = time.time()
        self.extension_count[phase_name] = 0

        return self.config.get_phase_suggestion(phase_name)

    def check_timing(self, phase_name: str) -> Optional[str]:
        """Check if a gentle reminder is needed"""
        import time

        if phase_name not in self.phase_start_times:
            return None

        elapsed = time.time() - self.phase_start_times[phase_name]

        # Get expected duration for this phase
        expected_durations = {
            "night": self.config.night_phase_duration,
            "day_discussion": self.config.day_discussion_time,
            "nomination": self.config.nomination_discussion,
            "voting": self.config.voting_countdown,
            "execution": self.config.execution_speech_time,
        }

        expected = expected_durations.get(phase_name, 300)  # 5 min default

        # Provide gentle reminders at intervals
        if (
            elapsed > expected
            and (elapsed - expected) % self.config.reminder_intervals < 5
        ):
            extensions = self.extension_count.get(phase_name, 0)

            if extensions == 0:
                return f"⏰ Just a gentle reminder: {phase_name} has been going for {
                    int(
                        elapsed //
                        60)} minutes. Take your time if needed!"
            elif extensions < 3:
                return f"⏰ Still discussing? That's fine! You've been at it for {
                    int(
                        elapsed //
                        60)} minutes."
            else:
                # After many extensions, just occasional check-ins
                if (elapsed - expected) % (self.config.reminder_intervals * 3) < 5:
                    return "⏰ Take all the time you need - just checking in!"

        return None

    def request_extension(self, phase_name: str) -> str:
        """Handle a request for more time"""
        self.extension_count[phase_name] = self.extension_count.get(phase_name, 0) + 1

        responses = [
            "Of course! Take the time you need for thorough discussion.",
            "Time extended! Good deliberation is worth the wait.",
            "No problem! The best games aren't rushed.",
            "Extension granted! Let the debate continue!",
        ]

        import random

        return random.choice(responses)

    def get_pacing_recommendation(
        self, player_count: int, experience_level: str = "mixed"
    ) -> TimingConfig:
        """Recommend timing based on game parameters"""

        if player_count <= 7:
            # Smaller games can be quicker
            if experience_level == "experienced":
                return TimingConfig.quick_game()
            else:
                return TimingConfig.standard_game()
        elif player_count <= 12:
            # Medium games need standard timing
            return TimingConfig.standard_game()
        else:
            # Large games need more time
            if experience_level == "new":
                return TimingConfig.relaxed_game()
            else:
                return TimingConfig.standard_game()

    def format_timing_summary(self) -> str:
        """Get a summary of current timing settings"""

        return f"""Current Timing Settings ({self.config.pacing_style.value}):
🌙 Night Phase: ~{self.config.night_phase_duration // 60} minutes
☀️ Day Discussion: ~{self.config.day_discussion_time // 60} minutes
🗣️ Nomination Debate: ~{self.config.nomination_discussion // 60} minutes each
🗳️ Voting Time: {self.config.voting_countdown} seconds
⚰️ Final Words: {self.config.execution_speech_time} seconds

Remember: These are suggestions! Take the time your group needs."""


# Integration with narrator
class TimedNarrator:
    """Wrapper that adds timing awareness to narrator"""

    def __init__(self, narrator, timing_manager: TimingManager):
        self.narrator = narrator
        self.timing = timing_manager

    async def narrate_phase_start(self, phase: str, context: dict = None) -> str:
        """Narrate phase start with timing suggestion"""

        # Get base narration
        if phase == "night":
            narration = await self.narrator.narrate_night_phase(
                context.get("night_number", 1), context.get("alive_count", 0)
            )
        elif phase == "day_discussion":
            narration = await self.narrator.announce_deaths(context.get("deaths", []))
        else:
            narration = f"Starting {phase} phase..."

        # Add timing suggestion
        timing_suggestion = self.timing.start_phase(phase)
        return f"{narration}\n\n{timing_suggestion}"

    async def check_timing_reminder(self, current_phase: str) -> Optional[str]:
        """Check if timing reminder needed"""
        reminder = self.timing.check_timing(current_phase)
        if reminder:
            # Can optionally have AI rephrase the reminder
            return reminder
        return None
