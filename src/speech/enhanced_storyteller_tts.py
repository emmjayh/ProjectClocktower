"""
Enhanced Storyteller Text-to-Speech System
Provides dramatic narration, character voices, and atmospheric audio for Blood on the Clocktower
"""

import asyncio
import logging
import os
import random
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum

from .speech_handler import SpeechHandler, SpeechConfig


class NarrativeStyle(Enum):
    DRAMATIC = "dramatic"
    MYSTERIOUS = "mysterious"
    OMINOUS = "ominous"
    TRIUMPHANT = "triumphant"
    SOLEMN = "solemn"
    INFORMATIVE = "informative"


@dataclass
class VoiceProfile:
    """Configuration for different voice characteristics"""

    name: str
    speed: float = 1.0  # Speaking speed multiplier
    pitch: float = 1.0  # Pitch adjustment
    volume: float = 1.0  # Volume adjustment
    pause_multiplier: float = 1.0  # Pause length multiplier


class EnhancedStoryteller:
    """Enhanced storyteller with dramatic voice synthesis and narration"""

    def __init__(self, speech_handler: SpeechHandler):
        self.speech_handler = speech_handler
        self.logger = logging.getLogger(__name__)

        # Voice profiles for different situations
        self.voice_profiles = {
            NarrativeStyle.DRAMATIC: VoiceProfile(
                name="dramatic", speed=0.9, pitch=0.95, volume=1.1, pause_multiplier=1.5
            ),
            NarrativeStyle.MYSTERIOUS: VoiceProfile(
                name="mysterious",
                speed=0.8,
                pitch=0.9,
                volume=0.9,
                pause_multiplier=2.0,
            ),
            NarrativeStyle.OMINOUS: VoiceProfile(
                name="ominous", speed=0.7, pitch=0.85, volume=1.2, pause_multiplier=2.5
            ),
            NarrativeStyle.TRIUMPHANT: VoiceProfile(
                name="triumphant",
                speed=1.1,
                pitch=1.05,
                volume=1.2,
                pause_multiplier=1.0,
            ),
            NarrativeStyle.SOLEMN: VoiceProfile(
                name="solemn", speed=0.8, pitch=0.9, volume=0.9, pause_multiplier=2.0
            ),
            NarrativeStyle.INFORMATIVE: VoiceProfile(
                name="informative",
                speed=1.0,
                pitch=1.0,
                volume=1.0,
                pause_multiplier=1.0,
            ),
        }

        # Narrative templates for different situations
        self.narrative_templates = {
            "game_start": [
                "Welcome, brave souls, to the cursed town of Ravenshollow...",
                "As shadows gather, evil stirs in the heart of our peaceful village...",
                "The ancient clock tower chimes midnight, and dark forces awaken...",
            ],
            "first_night": [
                "As the town sleeps, sinister forces move in the darkness...",
                "The first night falls like a shroud upon the innocent...",
                "Evil creatures emerge from their hiding places...",
            ],
            "dawn_no_deaths": [
                "The sun rises on a miraculous morning - all have survived the night.",
                "By some fortune, the darkness claimed no victims this night.",
                "Dawn breaks with unexpected mercy - the town awakens whole.",
            ],
            "dawn_with_deaths": [
                "As morning light pierces the gloom, tragedy is revealed...",
                "The dawn exposes the night's terrible price...",
                "Daybreak brings sorrow, as the town discovers its losses...",
            ],
            "execution": [
                "The town has spoken. Justice, however misguided, will be served.",
                "With heavy hearts, the people carry out their grim sentence.",
                "The community's judgment falls like an executioner's blade.",
            ],
            "good_victory": [
                "Light triumphs over darkness! The evil has been vanquished!",
                "Hope is restored as the forces of good claim victory!",
                "The town celebrates as evil's grip is finally broken!",
            ],
            "evil_victory": [
                "Darkness consumes all... Evil has achieved its terrible goal.",
                "The shadows have won... The town falls to corruption.",
                "All hope fades as evil reigns supreme over the fallen town.",
            ],
        }

        # Sound effect mappings (for future implementation)
        self.sound_effects = {
            "night_begins": "wind_howling.wav",
            "death_revealed": "bell_toll.wav",
            "execution": "drums.wav",
            "victory": "trumpets.wav",
            "defeat": "ominous_chord.wav",
        }

    async def narrate_game_opening(self, player_count: int, script_name: str) -> None:
        """Deliver dramatic game opening narration"""

        template = random.choice(self.narrative_templates["game_start"])

        opening_text = (
            f"{template} "
            f"Tonight, {player_count} souls gather in the town square, "
            f"unaware that evil walks among them. "
            f"Some are innocent... some are not. "
            f"The ancient game of deception begins now."
        )

        await self._speak_with_style(opening_text, NarrativeStyle.DRAMATIC)

    async def narrate_first_night(self) -> None:
        """Narrate the beginning of first night"""

        template = random.choice(self.narrative_templates["first_night"])

        await self._speak_with_style(template, NarrativeStyle.MYSTERIOUS)
        await asyncio.sleep(2)
        await self._speak_with_style(
            "All close your eyes... and let the darkness take hold.",
            NarrativeStyle.OMINOUS,
        )

    async def narrate_dawn(self, deaths: List[str]) -> None:
        """Narrate dawn with appropriate drama based on deaths"""

        if not deaths:
            template = random.choice(self.narrative_templates["dawn_no_deaths"])
            await self._speak_with_style(template, NarrativeStyle.SOLEMN)
        else:
            template = random.choice(self.narrative_templates["dawn_with_deaths"])
            await self._speak_with_style(template, NarrativeStyle.OMINOUS)

            await asyncio.sleep(2)

            if len(deaths) == 1:
                death_text = f"The lifeless form of {deaths[0]} is discovered, claimed by the night's evil."
            else:
                death_list = ", ".join(deaths[:-1]) + f", and {deaths[-1]}"
                death_text = (
                    f"The bodies of {death_list} are found, victims of the darkness."
                )

            await self._speak_with_style(death_text, NarrativeStyle.SOLEMN)

    async def narrate_execution(self, player_name: str, character: str) -> None:
        """Narrate a player execution dramatically"""

        template = random.choice(self.narrative_templates["execution"])

        await self._speak_with_style(template, NarrativeStyle.SOLEMN)
        await asyncio.sleep(2)

        execution_text = (
            f"{player_name} steps forward, accepting their fate. "
            f"In their final moments, they reveal themselves as... {character}."
        )

        await self._speak_with_style(execution_text, NarrativeStyle.DRAMATIC)

    async def narrate_victory(self, winning_team: str, reason: str) -> None:
        """Narrate game victory with appropriate drama"""

        if winning_team == "good":
            template = random.choice(self.narrative_templates["good_victory"])
            style = NarrativeStyle.TRIUMPHANT
        else:
            template = random.choice(self.narrative_templates["evil_victory"])
            style = NarrativeStyle.OMINOUS

        await self._speak_with_style(template, style)
        await asyncio.sleep(2)
        await self._speak_with_style(reason, NarrativeStyle.DRAMATIC)

    async def announce_character_wake(self, character: str, player_name: str) -> None:
        """Announce character awakening with appropriate drama"""

        character_intros = {
            "Fortune Teller": f"{character}, mystic seer of truth, wake up.",
            "Empath": f"{character}, sensitive to evil's presence, wake up.",
            "Washerwoman": f"{character}, seeker of the innocent, wake up.",
            "Chef": f"{character}, observer of evil conspiracies, wake up.",
            "Poisoner": f"{character}, spreader of corruption, wake up.",
            "Imp": f"{character}, creature of darkness, wake up.",
        }

        intro = character_intros.get(character, f"{character}, wake up.")
        await self._speak_with_style(intro, NarrativeStyle.MYSTERIOUS)

    async def deliver_private_information(
        self, player_name: str, info: str, character: str
    ) -> None:
        """Deliver private information to a player with character-appropriate style"""

        # Character-specific delivery styles
        character_styles = {
            "Fortune Teller": "The cosmic forces whisper to you: ",
            "Empath": "Your empathic senses reveal: ",
            "Washerwoman": "Your keen observation discovers: ",
            "Chef": "Your watchful eye notices: ",
            "Poisoner": "Your dark knowledge tells you: ",
            "Imp": "Your demonic power shows you: ",
        }

        prefix = character_styles.get(character, "You learn: ")
        full_message = prefix + info

        await self.speech_handler.speak_to_player(player_name, full_message)

    async def announce_voting(self, nominee: str) -> None:
        """Announce voting phase dramatically"""

        voting_text = (
            f"The town's gaze turns to {nominee}. "
            f"Accusations fly like arrows in the air. "
            f"The moment of judgment has arrived."
        )

        await self._speak_with_style(voting_text, NarrativeStyle.DRAMATIC)

    async def announce_vote_results(
        self, yes_votes: int, no_votes: int, threshold: int, execute: bool, nominee: str
    ) -> None:
        """Announce vote results with drama"""

        result_text = (
            f"The votes are tallied: {yes_votes} for execution, {no_votes} against."
        )
        await self._speak_with_style(result_text, NarrativeStyle.INFORMATIVE)

        await asyncio.sleep(1)

        if execute:
            execution_text = (
                f"The town has spoken! {nominee} will face the executioner's justice!"
            )
            await self._speak_with_style(execution_text, NarrativeStyle.DRAMATIC)
        else:
            survival_text = (
                f"Mercy prevails. {nominee} is spared by the town's divided will."
            )
            await self._speak_with_style(survival_text, NarrativeStyle.SOLEMN)

    async def provide_game_context(self, phase: str, day_number: int) -> None:
        """Provide atmospheric context for game phases"""

        if phase == "day":
            day_texts = [
                f"Day {day_number} dawns with uncertainty hanging over the town.",
                f"The {self._ordinal(day_number)} day brings new suspicions and fears.",
                f"As day {day_number} begins, trust grows ever more precious.",
            ]
            text = random.choice(day_texts)
            await self._speak_with_style(text, NarrativeStyle.INFORMATIVE)

        elif phase == "night":
            night_texts = [
                f"Night {day_number} descends like a predator stalking its prey.",
                f"The {self._ordinal(day_number)} night promises new terrors.",
                f"Darkness claims the town for the {self._ordinal(day_number)} time.",
            ]
            text = random.choice(night_texts)
            await self._speak_with_style(text, NarrativeStyle.MYSTERIOUS)

    async def _speak_with_style(self, text: str, style: NarrativeStyle) -> None:
        """Speak text with specific narrative style"""

        profile = self.voice_profiles[style]

        # Add dramatic pauses for certain styles
        if style in [
            NarrativeStyle.DRAMATIC,
            NarrativeStyle.MYSTERIOUS,
            NarrativeStyle.OMINOUS,
        ]:
            text = self._add_dramatic_pauses(text)

        # Modify text for emotional emphasis
        if style == NarrativeStyle.OMINOUS:
            text = self._add_ominous_emphasis(text)
        elif style == NarrativeStyle.TRIUMPHANT:
            text = self._add_triumphant_emphasis(text)

        await self.speech_handler.speak(text)

        # Add post-speech pause based on style
        pause_duration = 1.0 * profile.pause_multiplier
        await asyncio.sleep(pause_duration)

    def _add_dramatic_pauses(self, text: str) -> str:
        """Add dramatic pauses to text"""

        # Add pauses after punctuation for drama
        text = text.replace(".", "... ")
        text = text.replace("!", "! ")
        text = text.replace("?", "? ")
        text = text.replace(",", ", ")

        return text

    def _add_ominous_emphasis(self, text: str) -> str:
        """Add ominous emphasis to text"""

        # Emphasize certain words for ominous effect
        ominous_words = ["evil", "darkness", "death", "terror", "shadow", "doom"]

        for word in ominous_words:
            if word in text.lower():
                text = text.replace(word, f"*{word}*")
                text = text.replace(word.title(), f"*{word.title()}*")

        return text

    def _add_triumphant_emphasis(self, text: str) -> str:
        """Add triumphant emphasis to text"""

        triumphant_words = ["victory", "triumph", "light", "hope", "justice", "good"]

        for word in triumphant_words:
            if word in text.lower():
                text = text.replace(word, f"**{word}**")
                text = text.replace(word.title(), f"**{word.title()}**")

        return text

    def _ordinal(self, n: int) -> str:
        """Convert number to ordinal string"""

        if 10 <= n % 100 <= 20:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        return f"{n}{suffix}"


class GameStateAnnouncer:
    """Handles audio announcements for game state changes"""

    def __init__(self, enhanced_storyteller: EnhancedStoryteller):
        self.storyteller = enhanced_storyteller
        self.logger = logging.getLogger(__name__)

    async def announce_phase_change(
        self, old_phase: str, new_phase: str, day_number: int
    ):
        """Announce phase transitions"""

        if old_phase == "night" and new_phase == "day":
            await self.storyteller.provide_game_context("day", day_number)
        elif old_phase == "day" and new_phase == "night":
            await self.storyteller.provide_game_context("night", day_number)

    async def announce_player_death(self, player_name: str, cause: str = "unknown"):
        """Announce a player's death"""

        death_announcements = [
            f"The town mourns the loss of {player_name}.",
            f"{player_name} has fallen victim to the night's evil.",
            f"We bid farewell to {player_name}, taken too soon.",
        ]

        announcement = random.choice(death_announcements)
        await self.storyteller._speak_with_style(announcement, NarrativeStyle.SOLEMN)

    async def announce_ability_activation(self, character: str, player_name: str):
        """Announce when special abilities activate"""

        ability_announcements = {
            "Mayor": f"The Mayor's vote carries extra weight in these dire times.",
            "Slayer": f"The Slayer prepares to strike at evil.",
            "Virgin": f"The Virgin's innocence becomes apparent to all.",
        }

        if character in ability_announcements:
            announcement = ability_announcements[character]
            await self.storyteller._speak_with_style(
                announcement, NarrativeStyle.DRAMATIC
            )


# Integration class for easy use
class DramaticStoryteller:
    """Main interface for dramatic storytelling functionality"""

    def __init__(self, speech_handler: SpeechHandler):
        self.enhanced_storyteller = EnhancedStoryteller(speech_handler)
        self.announcer = GameStateAnnouncer(self.enhanced_storyteller)

    async def narrate_game_event(self, event_type: str, **kwargs):
        """Narrate any game event with appropriate drama"""

        if event_type == "game_start":
            await self.enhanced_storyteller.narrate_game_opening(
                kwargs["player_count"], kwargs["script_name"]
            )
        elif event_type == "first_night":
            await self.enhanced_storyteller.narrate_first_night()
        elif event_type == "dawn":
            await self.enhanced_storyteller.narrate_dawn(kwargs.get("deaths", []))
        elif event_type == "execution":
            await self.enhanced_storyteller.narrate_execution(
                kwargs["player_name"], kwargs["character"]
            )
        elif event_type == "victory":
            await self.enhanced_storyteller.narrate_victory(
                kwargs["winning_team"], kwargs["reason"]
            )
        elif event_type == "character_wake":
            await self.enhanced_storyteller.announce_character_wake(
                kwargs["character"], kwargs["player_name"]
            )
        elif event_type == "voting":
            await self.enhanced_storyteller.announce_voting(kwargs["nominee"])
        elif event_type == "vote_results":
            await self.enhanced_storyteller.announce_vote_results(
                kwargs["yes_votes"],
                kwargs["no_votes"],
                kwargs["threshold"],
                kwargs["execute"],
                kwargs["nominee"],
            )
        elif event_type == "phase_change":
            await self.announcer.announce_phase_change(
                kwargs["old_phase"], kwargs["new_phase"], kwargs["day_number"]
            )
        elif event_type == "player_death":
            await self.announcer.announce_player_death(
                kwargs["player_name"], kwargs.get("cause", "unknown")
            )
        elif event_type == "ability_activation":
            await self.announcer.announce_ability_activation(
                kwargs["character"], kwargs["player_name"]
            )

    async def deliver_private_info(self, player_name: str, info: str, character: str):
        """Deliver private information to a player"""
        await self.enhanced_storyteller.deliver_private_information(
            player_name, info, character
        )
