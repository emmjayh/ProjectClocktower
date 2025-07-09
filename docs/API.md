# API Documentation

## Platform Integration API

The AI Storyteller integrates with online Blood on the Clocktower platforms through a standardized API.

### ClockTowerAPI Class

```python
from src.game.clocktower_api import ClockTowerAPI

# Initialize client
api = ClockTowerAPI("https://clocktower.online", "ROOM123")

# Connect to game
await api.connect()

# Send storyteller actions
await api.announce_phase_change("night", 1)
await api.give_private_info("Alice", "You are the Fortune Teller")
await api.announce_death("Bob", "demon")
```

### Supported Platforms

#### clocktower.online
- **WebSocket URL**: `wss://clocktower.online/ws/{room_code}`
- **REST API**: `https://clocktower.online/api/`
- **Features**: Full integration, real-time sync, private messaging

#### botc.app
- **Status**: Basic integration
- **Features**: Game state updates, phase announcements

### Event Types

The API listens for these event types from platforms:

```python
{
  "type": "game_state_update",
  "data": {
    "players": [...],
    "phase": "night",
    "day": 1
  }
}

{
  "type": "player_action", 
  "data": {
    "player": "Alice",
    "action": "nominate",
    "target": "Bob"
  }
}

{
  "type": "phase_change",
  "data": {
    "from": "day",
    "to": "night",
    "day": 1
  }
}
```

### Storyteller Actions

The AI can send these actions to platforms:

```python
# Phase management
await api.announce_phase_change("night", day_number)
await api.announce_phase_change("day", day_number)

# Player management  
await api.set_player_status("Alice", "dead")
await api.add_reminder_token("Bob", "poisoned", "Poisoned by Poisoner")

# Information distribution
await api.give_private_info("Alice", "You learn Bob is the Chef")
await api.wake_player("Alice", "Fortune Teller ability")

# Game events
await api.announce_death("Bob", "demon")
await api.announce_execution("Charlie", 5)
await api.start_voting("Diana", "Alice")
```

## AI Decision API

### StorytellerAI Class

```python
from src.ai.storyteller_ai import StorytellerAI

# Initialize AI
ai = StorytellerAI(api_client, speech_handler)

# Character ability decisions
result = ai.decide_fortune_teller_result(player, "Alice", "Bob", game_state)
count = ai.decide_empath_result(player, left_neighbor, right_neighbor, game_state)
target = ai.decide_demon_kill(demon_player, game_state)

# Story generation
story = await ai.generate_opening_story("trouble_brewing", 8)
announcement = ai.generate_death_announcement(dead_player, "demon")
```

### Decision Making

All AI decisions follow this pattern:

1. **Analyze Game State**: Consider current players, roles, game balance
2. **Apply Character Rules**: Follow official ability rules and timing
3. **Consider Effects**: Handle drunk/poisoned/other status effects  
4. **Balance Game**: Adjust for dramatic tension and fair gameplay
5. **Log Decision**: Record reasoning and confidence level

### Custom Character Implementation

To add a new character:

```python
# 1. Add to character data
character_data = {
    "NewCharacter": {
        "team": "good",
        "type": "townsfolk", 
        "ability": "night_info",
        "targets": 1
    }
}

# 2. Implement decision logic
def decide_new_character_result(self, player, target, game_state):
    # Get actual result
    actual = self._calculate_true_result(target, game_state)
    
    # Apply drunk/poisoned
    if player.is_drunk or player.is_poisoned:
        result = self._modify_for_malfunction(actual)
    else:
        result = actual
        
    # Log decision
    self._log_decision("new_character", 0.8, "reasoning", {
        "player": player.name,
        "target": target,
        "result": result
    })
    
    return result

# 3. Add to night order
night_order = {
    "first_night": [..., "NewCharacter"],
    "other_nights": [..., "NewCharacter"]
}
```

## Speech API

### SpeechHandler Class

```python
from src.speech.speech_handler import SpeechHandler, SpeechConfig

# Configure speech
config = SpeechConfig(
    whisper_model="base",
    tts_voice="en_US-lessac-medium",
    vad_threshold=0.01
)

# Initialize handler
speech = SpeechHandler(config)
await speech.initialize()

# Voice interaction
text = await speech.listen_for_command(["nominate", "question"], timeout=30.0)
await speech.speak("Good evening, players.")
await speech.speak_to_player("Alice", "You are the Fortune Teller.")
```

### Voice Commands

Players can use these natural language commands:

- **Questions**: "Storyteller, I have a question about the Butler"
- **Ready Signals**: "Storyteller, I'm ready" (during night phases)
- **Nominations**: "I nominate Bob" 
- **Voting**: "I vote yes" / "I vote no"

### Speech Configuration

```python
SpeechConfig(
    whisper_model="base",          # tiny, base, small, medium, large
    tts_voice="en_US-lessac-medium",  # Voice personality
    sample_rate=16000,             # Audio sample rate
    vad_threshold=0.01,            # Voice activation threshold
    silence_duration=2.0           # Silence before stopping
)
```

## Game State API

### GameState Class

```python
from src.core.game_state import GameState, Player, PlayerStatus

# Create game state
game_state = GameState(
    game_id="game123",
    players=[...],
    script_name="trouble_brewing"
)

# Player management
player = game_state.get_player_by_name("Alice")
alive_players = game_state.get_alive_players()
evil_players = game_state.get_players_by_team(Team.EVIL)

# Validation
can_nominate, reason = game_state.can_nominate("Alice", "Bob")
threshold = game_state.calculate_vote_threshold()
```

### Player State

```python
Player(
    id="1",
    name="Alice", 
    seat_position=0,
    character="Fortune Teller",
    status=PlayerStatus.ALIVE,
    team=Team.GOOD,
    is_drunk=False,
    is_poisoned=False,
    ghost_vote_used=False,
    reminder_tokens=[...]
)
```

## Error Handling

### Exception Types

```python
from src.game.rule_engine import RuleViolation

try:
    result = validate_nomination("Alice", "Bob", game_state)
except RuleViolation as e:
    print(f"Rule violation: {e}")
```

### Logging

```python
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log levels used:
logger.debug("Detailed debug information")
logger.info("General information") 
logger.warning("Warning about potential issues")
logger.error("Error that needs attention")
logger.critical("Critical error requiring immediate action")
```

## Testing

### Unit Tests

```python
import pytest
from src.ai.storyteller_ai import StorytellerAI

def test_fortune_teller_decision():
    # Arrange
    ai = StorytellerAI(mock_api, mock_speech)
    player = create_test_player("Fortune Teller")
    
    # Act  
    result = ai.decide_fortune_teller_result(player, "Alice", "Bob", game_state)
    
    # Assert
    assert isinstance(result, bool)
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_full_night_sequence():
    # Test complete night phase processing
    storyteller = AIStoryteller(api_client, speech_handler, character_data)
    await storyteller.start_new_game(["Alice", "Bob", "Charlie"])
    
    # Verify game state
    assert storyteller.game_state.phase == GamePhase.FIRST_NIGHT
```

## Configuration

### Environment Variables

```bash
# Speech settings
WHISPER_MODEL=base
TTS_VOICE=en_US-lessac-medium
VOICE_THRESHOLD=0.01

# Platform settings  
DEFAULT_PLATFORM=clocktower.online
API_TIMEOUT=30

# AI settings
AI_MODE=balanced
STORYTELLING_STYLE=dramatic
```

### Settings File

```json
{
  "speech": {
    "whisper_model": "base",
    "tts_voice": "en_US-lessac-medium", 
    "threshold": 0.01
  },
  "ai": {
    "mode": "balanced",
    "style": "dramatic",
    "balance_preference": "dynamic"
  },
  "platforms": {
    "default": "clocktower.online",
    "timeout": 30
  }
}
```