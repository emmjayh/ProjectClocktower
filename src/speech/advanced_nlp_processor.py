"""
Advanced Natural Language Processing for Blood on the Clocktower Commands
Handles complex speech patterns, game-specific terminology, and intent recognition
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict


class Intent(Enum):
    NOMINATE = "nominate"
    VOTE = "vote"
    QUESTION = "question"
    ABILITY_TARGET = "ability_target"
    CLAIM = "claim"
    ACCUSATION = "accusation"
    DEFENSE = "defense"
    INFORMATION = "information"
    CONFIRM = "confirm"
    DENY = "deny"
    UNKNOWN = "unknown"


@dataclass
class ParsedCommand:
    """Result of NLP parsing"""
    intent: Intent
    confidence: float
    entities: Dict[str, Any]
    raw_text: str
    normalized_text: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class GameTerminologyProcessor:
    """Processes Blood on the Clocktower specific terminology"""
    
    def __init__(self, player_names: List[str]):
        self.player_names = player_names
        self.logger = logging.getLogger(__name__)
        
        # Character names and aliases
        self.character_aliases = {
            "fortune teller": ["ft", "seer", "oracle"],
            "empath": ["emp", "feeler"],
            "washerwoman": ["ww", "washer"],
            "chef": [],
            "investigator": ["invest", "inv"],
            "librarian": ["lib"],
            "undertaker": ["under"],
            "monk": [],
            "ravenkeeper": ["raven", "rk"],
            "virgin": [],
            "slayer": [],
            "soldier": [],
            "mayor": [],
            "butler": [],
            "drunk": [],
            "recluse": [],
            "saint": [],
            "poisoner": ["poison"],
            "spy": [],
            "scarlet woman": ["scarlet", "sw"],
            "baron": [],
            "imp": ["demon"]
        }
        
        # Game-specific terms and phrases
        self.game_terms = {
            "execution": ["execute", "kill", "eliminate", "lynch"],
            "nomination": ["nominate", "nom", "vote for"],
            "ability": ["power", "action", "use"],
            "information": ["info", "learn", "know", "see"],
            "evil": ["bad", "scum", "mafia"],
            "good": ["town", "innocent"],
            "poison": ["poisoned", "drunk"],
            "dead": ["died", "killed", "eliminated"],
            "alive": ["living", "breathing"]
        }
        
        # Common voting patterns
        self.vote_patterns = {
            "yes": ["yes", "aye", "yay", "yeah", "vote yes", "execute", "kill"],
            "no": ["no", "nay", "nope", "vote no", "spare", "save"]
        }
        
        # Ability target patterns
        self.target_patterns = [
            r"(?:choose|select|target|pick) (\w+)",
            r"(\w+) (?:and|&) (\w+)",  # dual targets
            r"i (?:choose|pick|select) (\w+)",
            r"(?:point to|indicate) (\w+)"
        ]
        
    def normalize_text(self, text: str) -> str:
        """Normalize text for better processing"""
        
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove filler words
        filler_words = ["um", "uh", "like", "you know", "basically", "actually", "so"]
        words = text.split()
        words = [w for w in words if w not in filler_words]
        text = " ".join(words)
        
        # Normalize character names
        for character, aliases in self.character_aliases.items():
            for alias in aliases:
                text = text.replace(alias, character)
                
        # Normalize game terms
        for term, alternatives in self.game_terms.items():
            for alt in alternatives:
                text = text.replace(alt, term)
                
        return text
        
    def extract_player_names(self, text: str) -> List[str]:
        """Extract player names from text"""
        
        found_players = []
        text_lower = text.lower()
        
        for name in self.player_names:
            # Exact match
            if name.lower() in text_lower:
                found_players.append(name)
            # Partial match (first 3+ characters)
            elif len(name) >= 3:
                for word in text_lower.split():
                    if word.startswith(name[:3].lower()) and len(word) >= 3:
                        found_players.append(name)
                        break
                        
        return list(set(found_players))  # Remove duplicates
        
    def extract_character_names(self, text: str) -> List[str]:
        """Extract character names from text"""
        
        found_characters = []
        text_lower = text.lower()
        
        for character in self.character_aliases.keys():
            if character in text_lower:
                found_characters.append(character)
                
        return found_characters


class IntentClassifier:
    """Classifies the intent of spoken commands"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Intent patterns with confidence scores
        self.intent_patterns = {
            Intent.NOMINATE: [
                (r"i nominate (\w+)", 0.95),
                (r"nominate (\w+)", 0.90),
                (r"i (?:vote for|choose) (\w+) (?:for execution|to (?:die|be executed))", 0.85),
                (r"(\w+) should (?:die|be executed)", 0.80),
                (r"let's (?:execute|kill) (\w+)", 0.75)
            ],
            Intent.VOTE: [
                (r"(?:i vote|my vote is) (?:yes|aye|no)", 0.95),
                (r"^(?:yes|no|aye)$", 0.90),
                (r"i'm voting (?:yes|no)", 0.85),
                (r"(?:execute|spare) (?:them|him|her)", 0.80)
            ],
            Intent.ABILITY_TARGET: [
                (r"i (?:choose|select|target|pick) (\w+)", 0.95),
                (r"(\w+) and (\w+)", 0.90),
                (r"my targets? (?:are|is) (\w+)", 0.85),
                (r"point to (\w+)", 0.80)
            ],
            Intent.CLAIM: [
                (r"i am (?:the )?(\w+)", 0.95),
                (r"i'm (?:the )?(\w+)", 0.90),
                (r"my (?:character|role) is (\w+)", 0.85),
                (r"(\w+) claim", 0.80)
            ],
            Intent.ACCUSATION: [
                (r"(\w+) is (?:the )?(?:demon|imp|evil|poisoner|spy)", 0.90),
                (r"i think (\w+) is (?:evil|bad|scum)", 0.85),
                (r"(\w+) (?:must be|has to be) (?:evil|the demon)", 0.80),
                (r"i suspect (\w+)", 0.75)
            ],
            Intent.QUESTION: [
                (r"(?:what|who|how|when|why|where)", 0.85),
                (r"can (?:you tell me|someone explain)", 0.80),
                (r"i (?:don't understand|need help)", 0.75),
                (r"(?:rules|how does)", 0.70)
            ],
            Intent.INFORMATION: [
                (r"i (?:know|learned|saw) that", 0.85),
                (r"(?:my information|i got) (?:is|was)", 0.80),
                (r"the (?:fortune teller|empath|chef) (?:told me|said)", 0.75)
            ],
            Intent.CONFIRM: [
                (r"(?:yes|correct|right|true|that's right)", 0.90),
                (r"i (?:agree|confirm)", 0.85),
                (r"(?:exactly|precisely)", 0.80)
            ],
            Intent.DENY: [
                (r"(?:no|wrong|false|incorrect)", 0.90),
                (r"that's not (?:right|true|correct)", 0.85),
                (r"i (?:disagree|deny)", 0.80)
            ]
        }
        
    def classify_intent(self, text: str) -> Tuple[Intent, float]:
        """Classify the intent of the text with confidence score"""
        
        text_lower = text.lower().strip()
        best_intent = Intent.UNKNOWN
        best_confidence = 0.0
        
        for intent, patterns in self.intent_patterns.items():
            for pattern, base_confidence in patterns:
                if re.search(pattern, text_lower):
                    # Adjust confidence based on text length and clarity
                    adjusted_confidence = self._adjust_confidence(
                        base_confidence, text_lower, pattern
                    )
                    
                    if adjusted_confidence > best_confidence:
                        best_confidence = adjusted_confidence
                        best_intent = intent
                        
        return best_intent, best_confidence
        
    def _adjust_confidence(self, base_confidence: float, text: str, pattern: str) -> float:
        """Adjust confidence based on text characteristics"""
        
        confidence = base_confidence
        
        # Reduce confidence for very short or very long texts
        word_count = len(text.split())
        if word_count < 2:
            confidence *= 0.8
        elif word_count > 20:
            confidence *= 0.9
            
        # Increase confidence for exact matches
        if re.fullmatch(pattern, text):
            confidence *= 1.1
            
        # Reduce confidence for uncertain language
        uncertain_words = ["maybe", "perhaps", "might", "could", "possibly"]
        if any(word in text for word in uncertain_words):
            confidence *= 0.8
            
        return min(confidence, 0.99)  # Cap at 99%


class ContextAwareProcessor:
    """Processes commands with game context awareness"""
    
    def __init__(self, player_names: List[str]):
        self.player_names = player_names
        self.terminology = GameTerminologyProcessor(player_names)
        self.classifier = IntentClassifier()
        self.logger = logging.getLogger(__name__)
        
        # Game context state
        self.current_phase = "setup"
        self.current_character = None
        self.alive_players = set(player_names)
        self.nominations_today = set()
        
    def parse_command(self, text: str) -> ParsedCommand:
        """Parse a spoken command with full context awareness"""
        
        # Normalize text
        normalized_text = self.terminology.normalize_text(text)
        
        # Classify intent
        intent, confidence = self.classifier.classify_intent(normalized_text)
        
        # Extract entities
        entities = self._extract_entities(normalized_text, intent)
        
        # Context validation
        entities, confidence = self._validate_with_context(entities, intent, confidence)
        
        return ParsedCommand(
            intent=intent,
            confidence=confidence,
            entities=entities,
            raw_text=text,
            normalized_text=normalized_text,
            metadata={
                "phase": self.current_phase,
                "character": self.current_character
            }
        )
        
    def _extract_entities(self, text: str, intent: Intent) -> Dict[str, Any]:
        """Extract relevant entities based on intent"""
        
        entities = {}
        
        # Always extract player names
        players = self.terminology.extract_player_names(text)
        if players:
            entities["players"] = players
            
        # Extract characters
        characters = self.terminology.extract_character_names(text)
        if characters:
            entities["characters"] = characters
            
        # Intent-specific extractions
        if intent == Intent.NOMINATE:
            if players:
                entities["nominee"] = players[0]
                
        elif intent == Intent.VOTE:
            vote_value = self._extract_vote_value(text)
            if vote_value is not None:
                entities["vote"] = vote_value
                
        elif intent == Intent.ABILITY_TARGET:
            if players:
                entities["targets"] = players
                
        elif intent == Intent.CLAIM:
            if characters:
                entities["claimed_character"] = characters[0]
                
        elif intent == Intent.ACCUSATION:
            if players:
                entities["accused"] = players[0]
            if characters:
                entities["accused_character"] = characters[0]
                
        return entities
        
    def _extract_vote_value(self, text: str) -> Optional[bool]:
        """Extract vote value from text"""
        
        text_lower = text.lower()
        
        yes_words = ["yes", "aye", "yay", "yeah", "execute", "kill"]
        no_words = ["no", "nay", "nope", "spare", "save"]
        
        if any(word in text_lower for word in yes_words):
            return True
        elif any(word in text_lower for word in no_words):
            return False
            
        return None
        
    def _validate_with_context(self, entities: Dict[str, Any], intent: Intent, 
                             confidence: float) -> Tuple[Dict[str, Any], float]:
        """Validate entities against current game context"""
        
        # Validate player existence and alive status
        if "players" in entities:
            valid_players = []
            for player in entities["players"]:
                if player in self.player_names:
                    valid_players.append(player)
                else:
                    confidence *= 0.8  # Reduce confidence for invalid players
                    
            entities["players"] = valid_players
            
        # Context-specific validations
        if intent == Intent.NOMINATE:
            if "nominee" in entities:
                nominee = entities["nominee"]
                if nominee not in self.alive_players:
                    confidence *= 0.5  # Dead players can't be nominated
                elif nominee in self.nominations_today:
                    confidence *= 0.3  # Already nominated today
                    
        elif intent == Intent.ABILITY_TARGET:
            if self.current_phase != "night":
                confidence *= 0.6  # Abilities usually happen at night
                
        return entities, confidence
        
    def update_game_context(self, phase: str = None, character: str = None, 
                          alive_players: List[str] = None, 
                          nominations: List[str] = None):
        """Update game context for better parsing"""
        
        if phase:
            self.current_phase = phase
        if character:
            self.current_character = character
        if alive_players:
            self.alive_players = set(alive_players)
        if nominations:
            self.nominations_today = set(nominations)


class CommandValidator:
    """Validates parsed commands against game rules"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def validate_command(self, parsed_command: ParsedCommand, 
                        game_state: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate if command is legal in current game state"""
        
        intent = parsed_command.intent
        entities = parsed_command.entities
        phase = game_state.get("phase", "unknown")
        
        # Phase-specific validations
        if intent == Intent.NOMINATE and phase != "day":
            return False, "Nominations only allowed during day phase"
            
        if intent == Intent.VOTE and phase != "voting":
            return False, "Voting only allowed during voting phase"
            
        if intent == Intent.ABILITY_TARGET and phase != "night":
            return False, "Abilities only used during night phase"
            
        # Entity validations
        if intent == Intent.NOMINATE:
            if "nominee" not in entities:
                return False, "No valid nominee specified"
                
            nominee = entities["nominee"]
            alive_players = game_state.get("alive_players", [])
            if nominee not in alive_players:
                return False, f"{nominee} is not alive"
                
            nominations_today = game_state.get("nominations_today", [])
            if nominee in nominations_today:
                return False, f"{nominee} already nominated today"
                
        return True, "Command is valid"


# Main NLP processor class
class AdvancedNLPProcessor:
    """Main class for advanced natural language processing"""
    
    def __init__(self, player_names: List[str]):
        self.player_names = player_names
        self.processor = ContextAwareProcessor(player_names)
        self.validator = CommandValidator()
        self.logger = logging.getLogger(__name__)
        
        # Processing history for context
        self.command_history = []
        self.confidence_threshold = 0.7
        
    def process_speech(self, text: str, game_state: Dict[str, Any] = None) -> ParsedCommand:
        """Process speech input with full NLP pipeline"""
        
        if not text or not text.strip():
            return ParsedCommand(
                intent=Intent.UNKNOWN,
                confidence=0.0,
                entities={},
                raw_text=text,
                normalized_text=""
            )
            
        # Update context if provided
        if game_state:
            self._update_context_from_game_state(game_state)
            
        # Parse command
        parsed = self.processor.parse_command(text)
        
        # Validate command
        if game_state:
            is_valid, validation_message = self.validator.validate_command(parsed, game_state)
            parsed.metadata["is_valid"] = is_valid
            parsed.metadata["validation_message"] = validation_message
            
        # Add to history
        self.command_history.append(parsed)
        if len(self.command_history) > 50:  # Keep last 50 commands
            self.command_history.pop(0)
            
        return parsed
        
    def _update_context_from_game_state(self, game_state: Dict[str, Any]):
        """Update processor context from game state"""
        
        self.processor.update_game_context(
            phase=game_state.get("phase"),
            character=game_state.get("current_character"),
            alive_players=game_state.get("alive_players", []),
            nominations=game_state.get("nominations_today", [])
        )
        
    def get_confidence_assessment(self, parsed_command: ParsedCommand) -> str:
        """Get human-readable confidence assessment"""
        
        confidence = parsed_command.confidence
        
        if confidence >= 0.9:
            return "Very confident"
        elif confidence >= 0.7:
            return "Confident"
        elif confidence >= 0.5:
            return "Somewhat confident"
        elif confidence >= 0.3:
            return "Low confidence"
        else:
            return "Very uncertain"
            
    def suggest_clarification(self, parsed_command: ParsedCommand) -> Optional[str]:
        """Suggest clarification questions for low-confidence parses"""
        
        if parsed_command.confidence >= self.confidence_threshold:
            return None
            
        intent = parsed_command.intent
        entities = parsed_command.entities
        
        if intent == Intent.NOMINATE and "nominee" not in entities:
            return "Who would you like to nominate?"
            
        elif intent == Intent.ABILITY_TARGET and "targets" not in entities:
            return "Who would you like to target with your ability?"
            
        elif intent == Intent.VOTE and "vote" not in entities:
            return "Are you voting yes or no?"
            
        elif intent == Intent.UNKNOWN:
            return "I didn't understand. Could you please rephrase that?"
            
        return "Could you please clarify what you meant?"