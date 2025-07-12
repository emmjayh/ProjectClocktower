"""
Blood on the Clocktower Speech-Integrated AI Storyteller - Main Entry Point
Complete voice-controlled Blood on the Clocktower with autonomous AI storytelling
"""

import asyncio
import logging
import sys
from pathlib import Path

from src.core.master_speech_controller import MasterSpeechController
from src.speech.speech_handler import SpeechConfig

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


async def main():
    """Main entry point for the Speech-Integrated AI Storyteller"""

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger = logging.getLogger(__name__)
    logger.info("🎭 Starting Speech-Integrated Blood on the Clocktower AI Storyteller")

    try:
        # Configure speech systems
        speech_config = SpeechConfig(
            whisper_model="base",  # Balanced speed/accuracy
            tts_voice="en_US-lessac-medium",
            sample_rate=16000,
            vad_threshold=0.01,
            silence_duration=2.0,
        )

        # Create master speech controller
        controller = MasterSpeechController(speech_config)

        # Get player names (could be voice-configured in the future)
        player_names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace"]

        logger.info(f"Setting up game for players: {', '.join(player_names)}")

        # Setup and run the game
        success = await controller.setup_game(player_names)

        if success:
            logger.info("🚀 Starting speech-controlled Blood on the Clocktower game!")
            result = await controller.run_game()

            if result:
                winning_team, reason = result
                logger.info(
                    f"🏆 Game completed! {winning_team.upper()} team wins: {reason}"
                )
            else:
                logger.info("Game ended without a clear winner")
        else:
            logger.error("❌ Failed to setup speech-integrated game")

    except KeyboardInterrupt:
        logger.info("🛑 Game interrupted by user")
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        # Cleanup speech resources
        if "controller" in locals():
            controller.cleanup()
            logger.info("🧹 Speech systems cleaned up")


def print_welcome():
    """Print welcome message"""
    print("🎭 BLOOD ON THE CLOCKTOWER AI STORYTELLER")
    print("=" * 50)
    print("🤖 Autonomous AI Storyteller with Speech Integration")
    print("🎤 Voice-controlled nominations, voting, and abilities")
    print("🎭 Dramatic narration and atmospheric storytelling")
    print("🧠 Advanced natural language processing")
    print("🔒 Secure voice identification system")
    print("=" * 50)
    print()


if __name__ == "__main__":
    print_welcome()
    asyncio.run(main())
