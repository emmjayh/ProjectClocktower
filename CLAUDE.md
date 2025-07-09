# Blood on the Clocktower AI Storyteller

## Project Overview
An AI Storyteller that manages Blood on the Clocktower games through voice interaction and online platform integration. The AI acts as the Storyteller, guiding players through the game while providing dramatic narration and intelligent decision-making.

## Technical Stack
- **Speech Recognition**: OpenAI Whisper (local) for voice commands
- **Speech Synthesis**: Piper TTS (local) for AI narration
- **Platform Integration**: Connects to clocktower.online, botc.app, and other platforms
- **AI Engine**: Custom decision-making system for storytelling
- **GUI**: Tkinter dashboard for Storyteller management
- **Game State**: Real-time synchronization with online platforms

## Core Components
1. **Storyteller Dashboard**: Main GUI for managing games
2. **Speech Interface**: Voice interaction with players
3. **AI Decision Engine**: Intelligent storytelling and rule decisions
4. **Platform API**: Integration with online BOTC tools
5. **Game State Manager**: Tracks game state and player actions
6. **Rule Engine**: Validates actions and enforces game rules

## Key Features
- **Voice-Controlled Storytelling**: Listen to players and respond naturally
- **Platform Integration**: Works with existing online BOTC tools
- **AI-Driven Decisions**: Intelligent information distribution and game balance
- **Dramatic Narration**: Dynamic story generation based on game events
- **Rule Enforcement**: Automatic validation of game actions
- **Real-time Grimoire**: Visual player tracking and token management

## Setup and Installation

### Quick Start
```bash
# Clone the repository
git clone <repository-url>
cd projectclocktower

# Install dependencies
pip install -r requirements.txt

# Download AI models (first time only)
python setup.py

# Run the AI Storyteller
python -m src.main
```

### Windows Executable
```bash
# Build Windows standalone executable
python build_windows.py

# Creates dist/BloodClockTowerAI.exe
```

## Usage Instructions

### 1. Connect to Online Game
- Enter the platform URL (e.g., clocktower.online)
- Input the room code for your game
- Click "Connect to Game" to join as Storyteller

### 2. Voice Controls
- Click "Start Listening" to enable voice recognition
- Players can ask questions: "Storyteller, I have a question"
- Use "Speak" button or text input for announcements

### 3. Game Management
- Use phase control buttons to manage night/day cycles
- Click player tokens in the Grimoire for quick actions
- Monitor AI decisions in the decision log

### 4. Night Phase
- AI automatically processes character abilities
- Provides appropriate information to players
- Manages wake order and ability resolution

### 5. Day Phase
- Facilitates nominations and voting
- Announces execution results
- Tracks game state and win conditions

## Project Structure
```
/
├── src/
│   ├── main.py              # Main entry point
│   ├── gui/                 # User interface
│   │   ├── storyteller_dashboard.py  # Main dashboard
│   │   └── observer_window.py        # Observer mode
│   ├── core/                # Core game systems
│   │   ├── ai_storyteller.py         # Main AI controller
│   │   └── game_state.py             # Game state management
│   ├── speech/              # Voice interaction
│   │   └── speech_handler.py         # Speech recognition/TTS
│   ├── game/                # Game logic
│   │   ├── rule_engine.py            # Rule enforcement
│   │   └── clocktower_api.py         # Platform integration
│   └── ai/                  # AI systems
│       └── storyteller_ai.py         # Decision engine
├── data/                    # Game data
├── models/                  # AI models (downloaded)
├── logs/                    # Application logs
├── requirements.txt         # Python dependencies
├── setup.py                # Automated setup script
├── build_windows.py        # Windows build script
└── rules.md                # Complete game rules reference
```

## AI Decision Making

The AI makes intelligent decisions about:
- **Information Distribution**: What to tell Fortune Tellers, Empaths, etc.
- **Game Balance**: Adjusting decisions to maintain exciting gameplay
- **Drunk/Poisoned Effects**: When to give false information
- **Demon Kills**: Strategic target selection for dramatic effect
- **Story Generation**: Creating atmospheric announcements

## Platform Integration

Supports multiple online platforms:
- **clocktower.online**: Full integration with WebSocket events
- **botc.app**: Basic integration for popular platform
- **Custom platforms**: Extensible API system

## Voice Commands

Players can interact with the AI using natural speech:
- "Storyteller, I have a question about [rule]"
- "Storyteller, I'm ready" (during night phases)
- "I nominate [player name]"
- "I vote yes/no"

## Development Status
✅ **Completed**:
- Core AI architecture and decision engine
- Speech recognition and TTS integration
- Platform API integration
- Storyteller dashboard GUI
- Rule enforcement engine
- Game state management
- Windows executable building

🔄 **In Progress**:
- Advanced character ability implementations
- Enhanced narrative generation
- Platform-specific optimizations

## Requirements
- **Python 3.11+**
- **Windows 10/11** (for executable)
- **Microphone** for voice commands
- **Internet connection** for platform integration
- **4GB RAM** minimum for AI models

## Troubleshooting

### Common Issues
1. **Speech recognition not working**: Check microphone permissions
2. **Platform connection failed**: Verify room code and internet connection
3. **Models not downloading**: Run `python setup.py` manually
4. **Audio issues**: Ensure Windows audio drivers are updated

### Logs
Check `logs/storyteller.log` for detailed error information.

## Contributing
This is an AI-assisted development project. The codebase is designed to be:
- Modular and extensible
- Well-documented with inline comments
- Type-hinted for better maintainability
- Tested with comprehensive validation

## License
This project is for educational and entertainment purposes. Blood on the Clocktower is a trademark of The Pandemonium Institute.