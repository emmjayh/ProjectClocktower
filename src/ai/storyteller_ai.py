"""
AI Storyteller Engine - Core decision making and narrative generation
Handles all AI decisions for running Blood on the Clocktower games
"""

import logging
import random
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from ..core.game_state import GameState, Player
from ..game.clocktower_api import ClockTowerAPI
from ..speech.speech_handler import SpeechHandler


@dataclass
class StorytellerDecision:
    """Represents an AI storyteller decision"""

    decision_type: str
    confidence: float  # 0-1
    reasoning: str
    data: Dict[str, Any]
    timestamp: datetime


class StorytellerAI:
    """Main AI engine for storytelling decisions"""

    def __init__(self, api_client: ClockTowerAPI, speech_handler: SpeechHandler):
        self.api_client = api_client
        self.speech_handler = speech_handler
        self.logger = logging.getLogger(__name__)

        # Decision tracking
        self.decisions_made = []
        self.player_analysis = {}
        self.game_balance_score = 0.5  # 0 = evil favored, 1 = good favored

        # Storyteller personality
        self.storytelling_style = "dramatic"  # dramatic, mysterious, comedic, dark
        self.balance_preference = "dynamic"  # dynamic, favor_good, favor_evil, chaos

        # Game knowledge
        self.character_data = self._load_character_data()
        self.script_data = self._load_script_data()

    def _load_character_data(self) -> Dict[str, Dict]:
        """Load character ability data"""
        return {
            # TOWNSFOLK
            "Washerwoman": {
                "team": "good",
                "type": "townsfolk",
                "ability": "first_night_info",
                "learns": "townsfolk_or_type",
                "targets": 2,
            },
            "Librarian": {
                "team": "good",
                "type": "townsfolk",
                "ability": "first_night_info",
                "learns": "outsider_or_type",
                "targets": 2,
            },
            "Investigator": {
                "team": "good",
                "type": "townsfolk",
                "ability": "first_night_info",
                "learns": "minion_or_type",
                "targets": 2,
            },
            "Chef": {
                "team": "good",
                "type": "townsfolk",
                "ability": "first_night_info",
                "learns": "evil_pairs",
                "targets": 0,
            },
            "Empath": {
                "team": "good",
                "type": "townsfolk",
                "ability": "ongoing_info",
                "learns": "evil_neighbors",
                "targets": 0,
            },
            "Fortune Teller": {
                "team": "good",
                "type": "townsfolk",
                "ability": "ongoing_info",
                "learns": "demon_detection",
                "targets": 2,
            },
            "Undertaker": {
                "team": "good",
                "type": "townsfolk",
                "ability": "ongoing_info",
                "learns": "executed_character",
                "targets": 0,
            },
            "Monk": {
                "team": "good",
                "type": "townsfolk",
                "ability": "protection",
                "protects": "demon_kill",
                "targets": 1,
            },
            "Ravenkeeper": {
                "team": "good",
                "type": "townsfolk",
                "ability": "death_trigger",
                "learns": "killer_character",
                "targets": 1,
            },
            "Virgin": {
                "team": "good",
                "type": "townsfolk",
                "ability": "nomination_trigger",
                "effect": "nominator_executed",
                "targets": 0,
            },
            "Slayer": {
                "team": "good",
                "type": "townsfolk",
                "ability": "one_shot_kill",
                "targets": 1,
                "condition": "demon_only",
            },
            "Soldier": {
                "team": "good",
                "type": "townsfolk",
                "ability": "passive_immunity",
                "immune_to": "demon_kill",
                "targets": 0,
            },
            "Mayor": {
                "team": "good",
                "type": "townsfolk",
                "ability": "win_condition",
                "condition": "no_execution_3_alive",
                "targets": 0,
            },
            # OUTSIDERS
            "Butler": {
                "team": "good",
                "type": "outsider",
                "ability": "voting_restriction",
                "restriction": "master_dependent",
                "targets": 1,
            },
            "Drunk": {
                "team": "good",
                "type": "outsider",
                "ability": "malfunction",
                "effect": "thinks_townsfolk",
                "targets": 0,
            },
            "Recluse": {
                "team": "good",
                "type": "outsider",
                "ability": "misregister",
                "registers_as": "evil",
                "targets": 0,
            },
            "Saint": {
                "team": "good",
                "type": "outsider",
                "ability": "execution_loss",
                "effect": "good_loses_if_executed",
                "targets": 0,
            },
            # MINIONS
            "Poisoner": {
                "team": "evil",
                "type": "minion",
                "ability": "poison",
                "effect": "malfunction_target",
                "targets": 1,
                "ongoing": True,
            },
            "Spy": {
                "team": "evil",
                "type": "minion",
                "ability": "misregister_and_grimoire",
                "registers_as": "good",
                "sees": "grimoire",
                "targets": 0,
            },
            "Scarlet Woman": {
                "team": "evil",
                "type": "minion",
                "ability": "demon_replacement",
                "condition": "demon_dies_5plus_alive",
                "targets": 0,
            },
            "Baron": {
                "team": "evil",
                "type": "minion",
                "ability": "setup_modification",
                "effect": "add_outsiders",
                "targets": 0,
            },
            # DEMONS
            "Imp": {
                "team": "evil",
                "type": "demon",
                "ability": "kill_and_transfer",
                "kills": 1,
                "targets": 1,
                "can_starpass": True,
            },
        }

    def _load_script_data(self) -> Dict[str, Dict]:
        """Load script configurations"""
        return {
            "trouble_brewing": {
                "characters": [
                    "Washerwoman",
                    "Librarian",
                    "Investigator",
                    "Chef",
                    "Empath",
                    "Fortune Teller",
                    "Undertaker",
                    "Monk",
                    "Ravenkeeper",
                    "Virgin",
                    "Slayer",
                    "Soldier",
                    "Mayor",
                    "Butler",
                    "Drunk",
                    "Recluse",
                    "Saint",
                    "Poisoner",
                    "Spy",
                    "Scarlet Woman",
                    "Baron",
                    "Imp",
                ],
                "first_night_order": [
                    "Poisoner",
                    "Washerwoman",
                    "Librarian",
                    "Investigator",
                    "Chef",
                    "Empath",
                    "Fortune Teller",
                    "Butler",
                    "Spy",
                ],
                "other_night_order": [
                    "Poisoner",
                    "Monk",
                    "Scarlet Woman",
                    "Imp",
                    "Ravenkeeper",
                    "Empath",
                    "Fortune Teller",
                    "Undertaker",
                    "Butler",
                    "Spy",
                ],
            }
        }

    async def generate_opening_story(self, script: str, player_count: int) -> str:
        """Generate opening story for the game"""
        stories = {
            "trouble_brewing": [
                f"Welcome to Ravenshollow, a peaceful town of {player_count} souls. "
                "But tonight, evil stirs in the shadows. An Imp has infiltrated your midst, "
                "and only by working together can the forces of good prevail.",
                f"The sun sets over the quiet village of {player_count} residents. "
                "Little do they know that darkness has crept into their community. "
                "Trust will be tested, lies will be told, and only the light of truth can banish the evil.",
                f"In a small town where everyone knows everyone, {player_count} neighbors gather. "
                "But one among you serves the forces of darkness. "
                "Will good triumph over evil, or will the shadows consume all?",
            ]
        }

        script_stories = stories.get(script, stories["trouble_brewing"])
        story = random.choice(script_stories)

        self._log_decision(
            "opening_story", 1.0, f"Generated opening for {script}", {"story": story}
        )

        return story

    def decide_fortune_teller_result(
        self, fortune_teller: Player, target1: str, target2: str, game_state: GameState
    ) -> bool:
        """Decide Fortune Teller result"""

        # Get target players
        player1 = game_state.get_player_by_name(target1)
        player2 = game_state.get_player_by_name(target2)

        if not player1 or not player2:
            return False

        # Check if either is actually the demon
        actual_result = self._is_demon(player1.character) or self._is_demon(
            player2.character
        )

        # Apply drunk/poisoned effects
        if fortune_teller.is_drunk or fortune_teller.is_poisoned:
            # Give false information sometimes
            if self.balance_preference == "favor_evil" or random.random() < 0.3:
                result = not actual_result
                reasoning = "False info given (drunk/poisoned)"
            else:
                result = actual_result
                reasoning = (
                    "True info given despite drunk/poisoned (storyteller choice)"
                )
        else:
            result = actual_result
            reasoning = "True information given"

        # Consider game balance
        if self.game_balance_score < 0.3:  # Evil is winning
            # Maybe give helpful info to good
            if not actual_result and random.random() < 0.2:
                result = True  # False positive to help good team
                reasoning += " (balanced to help good team)"
        elif self.game_balance_score > 0.7:  # Good is winning
            # Maybe give misleading info
            if actual_result and random.random() < 0.2:
                result = False  # False negative to help evil team
                reasoning += " (balanced to help evil team)"

        self._log_decision(
            "fortune_teller",
            0.8,
            reasoning,
            {
                "fortune_teller": fortune_teller.name,
                "targets": [target1, target2],
                "result": result,
                "actual": actual_result,
            },
        )

        return result

    def decide_empath_result(
        self,
        empath: Player,
        left_neighbor: Player,
        right_neighbor: Player,
        game_state: GameState,
    ) -> int:
        """Decide Empath result"""

        # Count actual evil neighbors
        actual_count = 0
        if self._is_evil(left_neighbor.character):
            actual_count += 1
        if self._is_evil(right_neighbor.character):
            actual_count += 1

        # Apply drunk/poisoned effects
        if empath.is_drunk or empath.is_poisoned:
            # Give false information
            possible_counts = [0, 1, 2]
            possible_counts.remove(actual_count)  # Remove correct answer
            result = random.choice(possible_counts)
            reasoning = "False info given (drunk/poisoned)"
        else:
            result = actual_count
            reasoning = "True information given"

        self._log_decision(
            "empath",
            0.9,
            reasoning,
            {
                "empath": empath.name,
                "neighbors": [left_neighbor.name, right_neighbor.name],
                "result": result,
                "actual": actual_count,
            },
        )

        return result

    def decide_chef_result(self, chef: Player, game_state: GameState) -> int:
        """Decide Chef result (number of evil pairs sitting next to each other)"""

        # Count actual evil pairs
        actual_count = 0
        players = sorted(game_state.players, key=lambda p: p.seat_position)

        for i in range(len(players)):
            current = players[i]
            next_player = players[(i + 1) % len(players)]

            if self._is_evil(current.character) and self._is_evil(
                next_player.character
            ):
                actual_count += 1

        # Apply drunk/poisoned effects
        if chef.is_drunk or chef.is_poisoned:
            # Give false information
            max_possible = len(players) // 2
            possible_counts = list(range(max_possible + 1))
            if actual_count in possible_counts:
                possible_counts.remove(actual_count)
            result = random.choice(possible_counts) if possible_counts else actual_count
            reasoning = "False info given (drunk/poisoned)"
        else:
            result = actual_count
            reasoning = "True information given"

        self._log_decision(
            "chef",
            0.9,
            reasoning,
            {"chef": chef.name, "result": result, "actual": actual_count},
        )

        return result

    def decide_investigator_result(
        self, investigator: Player, game_state: GameState
    ) -> Tuple[str, str, str]:
        """Decide Investigator result (show 2 players, one is minion or both are wrong type)"""

        # Get all minions
        minions = [p for p in game_state.players if self._is_minion(p.character)]

        if investigator.is_drunk or investigator.is_poisoned:
            # Give false information - show 2 players where neither is a minion
            non_minions = [
                p for p in game_state.players if not self._is_minion(p.character)
            ]
            if len(non_minions) >= 2:
                targets = random.sample(non_minions, 2)
                character = random.choice(["Poisoner", "Spy", "Baron", "Scarlet Woman"])
                reasoning = "False info given (drunk/poisoned)"
            else:
                # Fallback
                targets = random.sample(game_state.players, 2)
                character = random.choice(["Poisoner", "Spy", "Baron", "Scarlet Woman"])
                reasoning = "False info given (drunk/poisoned) - fallback"
        else:
            if minions:
                # Show one minion and one non-minion
                minion = random.choice(minions)
                non_minions = [
                    p
                    for p in game_state.players
                    if p.name != minion.name and not self._is_minion(p.character)
                ]
                if non_minions:
                    non_minion = random.choice(non_minions)
                    targets = [minion, non_minion]
                    random.shuffle(targets)  # Random order
                    character = minion.character
                    reasoning = "True information given"
                else:
                    # All other players are minions?! Fallback
                    targets = random.sample(game_state.players, 2)
                    character = (
                        targets[0].character
                        if self._is_minion(targets[0].character)
                        else targets[1].character
                    )
                    reasoning = "True info given (unusual game state)"
            else:
                # No minions in game - show any 2 players and any minion type
                targets = random.sample(game_state.players, 2)
                character = random.choice(["Poisoner", "Spy", "Baron", "Scarlet Woman"])
                reasoning = "No minions in game - showing type not in play"

        self._log_decision(
            "investigator",
            0.8,
            reasoning,
            {
                "investigator": investigator.name,
                "targets": [t.name for t in targets],
                "character": character,
            },
        )

        return targets[0].name, targets[1].name, character

    def decide_demon_kill(self, demon: Player, game_state: GameState) -> Optional[str]:
        """Decide who the demon kills"""

        # Get possible targets (alive players except demon and minions)
        possible_targets = [
            p
            for p in game_state.players
            if p.is_alive()
            and p.name != demon.name
            and not self._is_minion(p.character)
        ]

        if not possible_targets:
            return None

        # AI decision based on game balance and strategy
        target_scores = {}

        for target in possible_targets:
            score = 0

            # Prefer targeting information roles
            if (
                self.character_data.get(target.character, {}).get("ability")
                == "ongoing_info"
            ):
                score += 3
            elif (
                self.character_data.get(target.character, {}).get("ability")
                == "first_night_info"
            ):
                score += 1

            # Prefer targeting protection roles
            if (
                self.character_data.get(target.character, {}).get("ability")
                == "protection"
            ):
                score += 2

            # Consider game balance
            if self.game_balance_score > 0.6:  # Good is winning
                # Target more aggressively
                score += random.randint(1, 3)
            elif self.game_balance_score < 0.4:  # Evil is winning
                # Maybe target less optimal targets
                score += random.randint(-1, 1)

            # Random factor
            score += random.random()

            target_scores[target.name] = score

        # Choose target with highest score
        target_name = max(target_scores.keys(), key=lambda k: target_scores[k])

        self._log_decision(
            "demon_kill",
            0.7,
            "Selected based on role value and game balance",
            {
                "demon": demon.name,
                "target": target_name,
                "scores": target_scores,
                "balance": self.game_balance_score,
            },
        )

        return target_name

    def decide_monk_protection(
        self, monk: Player, game_state: GameState
    ) -> Optional[str]:
        """Decide who the Monk protects"""

        # Get possible targets (alive players except monk)
        possible_targets = [
            p for p in game_state.players if p.is_alive() and p.name != monk.name
        ]

        if not possible_targets:
            return None

        # AI decision - protect valuable players
        protection_scores = {}

        for target in possible_targets:
            score = 0

            # Protect information roles
            if self.character_data.get(target.character, {}).get("ability") in [
                "ongoing_info",
                "first_night_info",
            ]:
                score += 2

            # Protect powerful roles
            if target.character in ["Slayer", "Virgin", "Mayor"]:
                score += 2

            # Consider who might be demon target
            # (This is meta-gaming but acceptable for AI storyteller)
            if target.character in ["Fortune Teller", "Empath", "Undertaker"]:
                score += 3

            # Random factor
            score += random.random()

            protection_scores[target.name] = score

        # Choose target with highest score
        target_name = max(protection_scores.keys(), key=lambda k: protection_scores[k])

        self._log_decision(
            "monk_protection",
            0.6,
            "Protected most valuable target",
            {"monk": monk.name, "target": target_name, "scores": protection_scores},
        )

        return target_name

    def analyze_nomination(
        self, nominator: str, nominee: str, game_state: GameState
    ) -> Dict[str, Any]:
        """Analyze a nomination for AI insights"""

        nominator_player = game_state.get_player_by_name(nominator)
        nominee_player = game_state.get_player_by_name(nominee)

        analysis = {
            "suspicion_level": "medium",
            "strategic_value": "medium",
            "likely_outcome": "unknown",
            "ai_recommendation": "observe",
        }

        if not nominator_player or not nominee_player:
            return analysis

        # Analyze suspicion level
        if self._is_evil(nominee_player.character):
            if self._is_good(nominator_player.character):
                analysis["suspicion_level"] = "high"
                analysis["ai_recommendation"] = "good_nomination"
            else:
                analysis["suspicion_level"] = "low"
                analysis["ai_recommendation"] = "distancing_play"
        else:
            if self._is_evil(nominator_player.character):
                analysis["suspicion_level"] = "high"
                analysis["ai_recommendation"] = "evil_misdirection"
            else:
                analysis["suspicion_level"] = "medium"
                analysis["ai_recommendation"] = "good_misread"

        # Calculate likely execution probability
        alive_players = len(game_state.get_alive_players())

        # Estimate based on character and game state
        execution_probability = 0.5

        if self._is_evil(nominee_player.character):
            execution_probability += 0.2  # Evil more likely to be executed
        if nominee_player.character in ["Saint"]:
            execution_probability -= 0.3  # Dangerous to execute
        if len(game_state.nominations) > 3:
            execution_probability -= 0.1  # Later nominations less likely

        analysis["execution_probability"] = max(0.1, min(0.9, execution_probability))

        return analysis

    def generate_death_announcement(self, dead_player: Player, cause: str) -> str:
        """Generate dramatic death announcement"""

        announcements = {
            "demon": [
                f"As dawn breaks, the town discovers {dead_player.name} has met a terrible fate in the night.",
                f"The shadows claimed {dead_player.name} in the darkness. Their lifeless form is found at first light.",
                f"Evil has struck! {dead_player.name} was taken by the forces of darkness.",
                f"The demon's hunger was satisfied by {dead_player.name}'s life force.",
            ],
            "execution": [
                f"The town has spoken. {dead_player.name} takes their final breath.",
                f"Justice or tragedy? {dead_player.name} pays the ultimate price for the town's decision.",
                f"With heavy hearts, the townspeople watch as {dead_player.name} meets their end.",
                f"The rope tightens, and {dead_player.name}'s fate is sealed.",
            ],
        }

        cause_announcements = announcements.get(cause, announcements["demon"])
        announcement = random.choice(cause_announcements)

        # Add character-specific flavor
        if dead_player.character == "Virgin" and cause == "execution":
            announcement = (
                f"The Virgin {dead_player.name} dies by the town's hand. "
                "Was this justice, or has evil triumphed?"
            )
        elif dead_player.character == "Saint" and cause == "execution":
            announcement = (
                f"The Saint {dead_player.name} is executed! "
                "The town realizes too late their terrible mistake..."
            )

        return announcement

    def generate_victory_announcement(self, winning_team: str, reason: str) -> str:
        """Generate victory announcement"""

        if winning_team == "good":
            announcements = [
                f"The light of truth has banished the darkness! Good triumphs over evil. {reason}",
                f"Justice prevails! The forces of good have saved the town. {reason}",
                f"Through courage and wisdom, good has emerged victorious! {reason}",
                f"The nightmare is over. Good has won! {reason}",
            ]
        else:
            announcements = [
                f"Darkness consumes the town. Evil has triumphed! {reason}",
                f"The shadows have won. Evil reigns supreme! {reason}",
                f"Chaos and corruption prevail. Evil is victorious! {reason}",
                f"The town falls to darkness. Evil has succeeded! {reason}",
            ]

        return random.choice(announcements)

    def update_game_balance(self, game_state: GameState):
        """Update game balance assessment"""

        alive_good = len(
            [p for p in game_state.get_alive_players() if self._is_good(p.character)]
        )
        alive_evil = len(
            [p for p in game_state.get_alive_players() if self._is_evil(p.character)]
        )

        total_alive = alive_good + alive_evil

        if total_alive > 0:
            good_ratio = alive_good / total_alive

            # Adjust based on game state
            if game_state.day_number == 1:
                # Early game, favor based on information
                info_roles_alive = len(
                    [
                        p
                        for p in game_state.get_alive_players()
                        if self.character_data.get(p.character, {}).get("ability")
                        in ["ongoing_info", "first_night_info"]
                    ]
                )
                if info_roles_alive > 2:
                    good_ratio += 0.1  # Good has information advantage

            # Update balance score
            self.game_balance_score = good_ratio

    def _is_demon(self, character: str) -> bool:
        """Check if character is a demon"""
        return self.character_data.get(character, {}).get("type") == "demon"

    def _is_minion(self, character: str) -> bool:
        """Check if character is a minion"""
        return self.character_data.get(character, {}).get("type") == "minion"

    def _is_evil(self, character: str) -> bool:
        """Check if character is evil"""
        return self.character_data.get(character, {}).get("team") == "evil"

    def _is_good(self, character: str) -> bool:
        """Check if character is good"""
        return self.character_data.get(character, {}).get("team") == "good"

    def _log_decision(
        self,
        decision_type: str,
        confidence: float,
        reasoning: str,
        data: Dict[str, Any],
    ):
        """Log an AI decision"""
        decision = StorytellerDecision(
            decision_type=decision_type,
            confidence=confidence,
            reasoning=reasoning,
            data=data,
            timestamp=datetime.now(),
        )

        self.decisions_made.append(decision)
        self.logger.info(
            f"AI Decision [{decision_type}]: {reasoning} (confidence: {confidence:.2f})"
        )

    def get_decision_summary(self) -> Dict[str, Any]:
        """Get summary of AI decisions made"""
        decision_types = {}
        for decision in self.decisions_made:
            if decision.decision_type not in decision_types:
                decision_types[decision.decision_type] = []
            decision_types[decision.decision_type].append(decision)

        return {
            "total_decisions": len(self.decisions_made),
            "by_type": {k: len(v) for k, v in decision_types.items()},
            "average_confidence": (
                sum(d.confidence for d in self.decisions_made)
                / len(self.decisions_made)
                if self.decisions_made
                else 0
            ),
            "game_balance": self.game_balance_score,
        }
