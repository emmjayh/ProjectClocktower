"""
Configuration for Autonomous AI Storyteller
All settings for customizing the hands-off AI behavior
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from ..core.timing_config import PacingStyle, TimingConfig


@dataclass
class InformationStrategy:
    """Strategy for giving information to players"""

    # Truth vs deception rates
    truth_rate_healthy: float = 0.85  # How often to tell truth when healthy
    truth_rate_drunk: float = 0.3  # How often to tell truth when drunk
    truth_rate_poisoned: float = 0.25  # How often to tell truth when poisoned

    # Game balance factors
    balance_factor: float = 0.2  # How much to adjust based on game balance
    drama_factor: float = 0.15  # Bias toward dramatic reveals

    # Information timing
    delay_sensitive_info: bool = True  # Hold back game-ending info early
    early_game_protection: int = 2  # Days to protect from devastating info


@dataclass
class SpeechRecognitionConfig:
    """Configuration for speech recognition behavior"""

    # Recognition settings
    listening_sensitivity: float = 0.6  # How sensitive to wake words
    confidence_threshold: float = 0.7  # Minimum confidence for actions

    # Timing
    action_timeout: float = 30.0  # Seconds to wait for actions
    clarification_retries: int = 2  # Times to ask for clarification

    # Wake words and phrases
    wake_words: List[str] = None

    def __post_init__(self):
        if self.wake_words is None:
            self.wake_words = [
                "storyteller",
                "choose",
                "nominate",
                "vote",
                "fortune teller",
                "empath",
                "question",
            ]


@dataclass
class NarrationStyle:
    """Style settings for AI narration"""

    # Tone and atmosphere
    drama_level: str = "high"  # "low", "medium", "high", "epic"
    gothic_atmosphere: bool = True  # Use gothic/dark language
    humor_level: str = "light"  # "none", "light", "moderate"

    # Verbosity
    announcement_length: str = "medium"  # "brief", "medium", "verbose"
    use_player_names: bool = True  # Include player names in narration

    # Special effects
    use_sound_effects: bool = False  # Play sound effects (if available)
    dramatic_pauses: bool = True  # Add pauses for effect


@dataclass
class AutonomousConfig:
    """Complete configuration for autonomous storyteller"""

    # Core behavior
    autonomy_level: str = "high"  # "low", "medium", "high", "full"
    human_override: bool = True  # Allow human storyteller to interrupt

    # Component configs
    information_strategy: InformationStrategy = None
    speech_config: SpeechRecognitionConfig = None
    narration_style: NarrationStyle = None
    timing_config: TimingConfig = None

    # Phase management
    auto_advance_phases: bool = True  # Automatically move between phases
    night_phase_timeout: int = 600  # Max seconds for night phase
    day_phase_timeout: int = 1800  # Max seconds for day phase

    # Decision making
    use_ai_for_edge_cases: bool = True  # Let AI handle rule edge cases
    ai_decision_delay: float = 2.0  # Seconds to "think" before decisions

    # Logging and memory
    log_all_decisions: bool = True  # Log every AI decision
    remember_previous_games: bool = False  # Learn from past games

    def __post_init__(self):
        if self.information_strategy is None:
            self.information_strategy = InformationStrategy()
        if self.speech_config is None:
            self.speech_config = SpeechRecognitionConfig()
        if self.narration_style is None:
            self.narration_style = NarrationStyle()
        if self.timing_config is None:
            self.timing_config = TimingConfig.standard_game()

    @classmethod
    def quick_game(cls) -> "AutonomousConfig":
        """Configuration for quick games"""
        return cls(
            autonomy_level="high",
            timing_config=TimingConfig.quick_game(),
            information_strategy=InformationStrategy(
                truth_rate_healthy=0.9,  # More direct information
                drama_factor=0.1,  # Less dramatic delays
            ),
            narration_style=NarrationStyle(
                drama_level="medium", announcement_length="brief"
            ),
            night_phase_timeout=300,  # 5 minutes max
            day_phase_timeout=900,  # 15 minutes max
        )

    @classmethod
    def dramatic_game(cls) -> "AutonomousConfig":
        """Configuration for dramatic, story-focused games"""
        return cls(
            autonomy_level="high",
            timing_config=TimingConfig.relaxed_game(),
            information_strategy=InformationStrategy(
                truth_rate_healthy=0.75,  # More deception for drama
                drama_factor=0.3,  # High drama factor
                delay_sensitive_info=True,
            ),
            narration_style=NarrationStyle(
                drama_level="epic",
                gothic_atmosphere=True,
                announcement_length="verbose",
                dramatic_pauses=True,
            ),
        )

    @classmethod
    def tournament_mode(cls) -> "AutonomousConfig":
        """Configuration for competitive tournament games"""
        return cls(
            autonomy_level="full",
            human_override=False,  # No human intervention
            timing_config=TimingConfig(
                pacing_style=PacingStyle.STANDARD,
                allow_extensions=False,  # Strict timing
            ),
            information_strategy=InformationStrategy(
                truth_rate_healthy=0.85,
                balance_factor=0.1,  # Less balance adjustment
                drama_factor=0.05,  # Minimal drama bias
            ),
            narration_style=NarrationStyle(
                drama_level="low", announcement_length="brief", dramatic_pauses=False
            ),
            auto_advance_phases=True,
            log_all_decisions=True,
        )

    @classmethod
    def casual_social(cls) -> "AutonomousConfig":
        """Configuration for casual social games"""
        return cls(
            autonomy_level="medium",
            human_override=True,
            timing_config=TimingConfig.relaxed_game(),
            information_strategy=InformationStrategy(
                truth_rate_healthy=0.8, drama_factor=0.2
            ),
            narration_style=NarrationStyle(
                drama_level="medium",
                humor_level="moderate",
                announcement_length="medium",
            ),
            auto_advance_phases=False,  # Let players control pacing
        )

    def to_dict(self) -> Dict:
        """Convert to dictionary for saving"""
        from dataclasses import asdict

        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "AutonomousConfig":
        """Load from dictionary"""
        # This would need more sophisticated deserialization
        # For now, just return default
        return cls()


# Preset configurations for easy selection
PRESET_CONFIGS = {
    "quick": AutonomousConfig.quick_game(),
    "dramatic": AutonomousConfig.dramatic_game(),
    "tournament": AutonomousConfig.tournament_mode(),
    "casual": AutonomousConfig.casual_social(),
    "standard": AutonomousConfig(),
}


def get_config_description(config_name: str) -> str:
    """Get description of a preset configuration"""

    descriptions = {
        "quick": "Fast-paced games with direct information and minimal delays. Good for experienced players.",
        "dramatic": "Story-focused games with atmospheric narration and dramatic reveals. Great for immersion.",
        "tournament": "Competitive games with strict timing and minimal storyteller bias. Fair and balanced.",
        "casual": "Relaxed social games with flexible timing and moderate drama. Perfect for friends.",
        "standard": "Balanced settings suitable for most games. Good default choice.",
    }

    return descriptions.get(config_name, "Custom configuration")


# Example of how to use configurations
def demo_configurations():
    """Demonstrate different configuration options"""

    print("🎭 Autonomous Storyteller Configuration Options")
    print("=" * 50)

    for name, config in PRESET_CONFIGS.items():
        print(f"\n{name.upper()} Configuration:")
        print(f"Description: {get_config_description(name)}")
        print(f"Autonomy Level: {config.autonomy_level}")
        print(f"Drama Level: {config.narration_style.drama_level}")
        print(f"Truth Rate: {config.information_strategy.truth_rate_healthy}")
        print(f"Timing: {config.timing_config.pacing_style.value}")
        print(f"Human Override: {config.human_override}")


if __name__ == "__main__":
    demo_configurations()
