# 🎭 Blood on the Clocktower AI Storyteller

> *An intelligent AI that serves as the Storyteller for Blood on the Clocktower games, featuring voice interaction, dramatic narration, and seamless integration with online platforms.*

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: Educational](https://img.shields.io/badge/License-Educational-green.svg)](LICENSE)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://github.com/yourusername/ProjectClocktower/releases)

## 🌟 Features

- **🎤 Voice-Controlled Storytelling**: Natural speech recognition for player interactions
- **🎭 Dramatic AI Narration**: Dynamic story generation with atmospheric announcements  
- **🔗 Platform Integration**: Seamless connection to clocktower.online, botc.app, and more
- **🧠 Intelligent Decision Making**: Smart information distribution and game balancing
- **📖 Visual Grimoire**: Real-time player tracking with professional dashboard
- **⚖️ Complete Rule Enforcement**: Full Blood on the Clocktower rules implementation
- **💾 Standalone Windows App**: One-click executable with automatic model downloads

## 🚀 Quick Start

### Option 1: Windows Executable (Recommended)
1. Download the latest release from [Releases](https://github.com/yourusername/ProjectClocktower/releases)
2. Run `download_models.bat` (first time only - downloads AI models)
3. Launch `BloodClockTowerAI.exe`
4. Connect to your online game and start storytelling!

### Option 2: Python Installation
```bash
git clone https://github.com/yourusername/ProjectClocktower.git
cd ProjectClocktower
pip install -r requirements.txt
python setup.py  # Downloads AI models
python -m src.main
```

## 🎮 How It Works

The AI Storyteller connects to existing Blood on the Clocktower online platforms and acts as your game's Storyteller:

1. **Connect**: Enter your game's URL and room code
2. **Listen**: AI hears player questions and commands through voice recognition
3. **Decide**: Intelligent algorithms determine information distribution and game balance
4. **Speak**: Dramatic narration brings the game to life
5. **Manage**: Automatic rule enforcement and phase management

## 🎭 Example Usage

**Player**: *"Storyteller, I have a question about the Fortune Teller ability"*

**AI Storyteller**: *"Fortune Teller, each night you may choose two players to learn if one of them is the Demon."*

**During Night Phase**: 
- AI automatically wakes Fortune Teller
- Listens for their choices: *"I choose Alice and Bob"*
- Makes intelligent decision based on game state
- Responds: *"Yes"* or *"No"*
- Continues with next character in night order

## 📋 Supported Platforms

- ✅ **clocktower.online** - Full integration with real-time sync
- ✅ **botc.app** - Basic integration for popular platform  
- ✅ **Custom platforms** - Extensible API for any BOTC tool
- 🔄 **More platforms** - Coming soon based on community requests

## 🛠️ Technical Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Speech I/O    │────│   AI Engine     │────│ Online Platform │
│                 │    │                 │    │                 │
│ • Whisper STT   │    │ • Decision AI   │    │ • clocktower.   │
│ • Piper TTS     │    │ • Rule Engine   │    │   online        │
│ • Voice Commands│    │ • Game Balance  │    │ • WebSocket API │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ Dashboard GUI   │
                    │                 │
                    │ • Grimoire View │
                    │ • Phase Control │
                    │ • AI Decisions  │
                    └─────────────────┘
```

## 🎯 AI Decision Making

The AI makes intelligent storytelling decisions:

### Information Distribution
- **Fortune Teller Results**: Considers game balance, drunk/poisoned status
- **Empath Information**: Calculates neighbor alignment with strategic flexibility  
- **Investigator Clues**: Balances helpful vs. misleading information
- **All Abilities**: Context-aware decisions based on game state

### Game Balancing
- **Dynamic Difficulty**: Adjusts information accuracy based on team performance
- **Dramatic Timing**: Optimizes reveals for maximum tension
- **Strategic Decisions**: Demon kills and ability outcomes for engaging gameplay

### Story Generation
- **Atmospheric Narration**: Creates immersive death announcements and phase transitions
- **Character-Specific Flavor**: Tailored responses based on roles and abilities
- **Adaptive Tone**: Adjusts storytelling style based on game progression

## 🎚️ Dashboard Features

### 🎮 Game Control Panel
- **Phase Management**: Night/Day transitions with one click
- **Quick Actions**: Kill players, add drunk/poison effects, manage reminders
- **Vote Processing**: Handle nominations and executions seamlessly

### 📖 Interactive Grimoire  
- **Player Tokens**: Visual representation with real-time status updates
- **Character Display**: Shows roles, alignment, and current effects
- **Click Actions**: Right-click players for quick storyteller actions

### 🎤 Communication Hub
- **Voice Controls**: Start/stop listening with visual feedback
- **Speech Input**: Manual text input for announcements
- **Communication Log**: Track all voice interactions and decisions

### 🧠 AI Insights
- **Decision Log**: See AI reasoning for all choices made
- **Balance Tracking**: Monitor game state and team performance
- **Confidence Metrics**: View AI confidence levels for decisions

## 🔧 Advanced Configuration

### Speech Settings
```python
# Adjust in settings panel or config file
whisper_model = "base"      # tiny, base, small, medium, large
voice_threshold = 0.01      # Voice activation sensitivity  
tts_voice = "en_US-lessac-medium"  # Voice personality
```

### AI Personality
```python
storytelling_style = "dramatic"    # dramatic, mysterious, comedic, dark
balance_preference = "dynamic"     # dynamic, favor_good, favor_evil, chaos
```

## 📁 Project Structure

```
ProjectClocktower/
├── src/
│   ├── main.py                     # Application entry point
│   ├── gui/
│   │   ├── storyteller_dashboard.py    # Main dashboard interface
│   │   └── observer_window.py          # Spectator mode (future)
│   ├── core/
│   │   ├── ai_storyteller.py           # Core AI controller  
│   │   └── game_state.py               # Game state management
│   ├── speech/
│   │   └── speech_handler.py           # Voice recognition/synthesis
│   ├── game/
│   │   ├── rule_engine.py              # BOTC rules implementation
│   │   └── clocktower_api.py           # Platform integration
│   └── ai/
│       └── storyteller_ai.py           # Decision engine
├── data/                    # Game data and character definitions
├── models/                  # AI models (auto-downloaded)
├── logs/                    # Application logs
├── requirements.txt         # Python dependencies
├── setup.py                # Automated setup and model download
├── build_windows.py        # Windows executable builder
├── rules.md                # Complete BOTC rules reference
└── README.md               # This file
```

## 🎯 Use Cases

### 🏠 **Home Games**
- Replace human storyteller for intimate friend groups
- Learn storytelling techniques by observing AI decisions
- Practice new characters and edge cases

### 🎪 **Online Communities**  
- Run games for remote players across different platforms
- Provide consistent storytelling for regular game groups
- Enable 24/7 games with AI storyteller availability

### 📚 **Learning Tool**
- New players can ask questions anytime during the game
- Veteran players can observe AI decision-making process
- Perfect rule enforcement for learning correct gameplay

### 🔬 **Game Analysis**
- Research optimal information distribution strategies
- Analyze game balance across different scripts
- Study player behavior patterns and decision trees

## ⚙️ System Requirements

### Minimum Requirements
- **OS**: Windows 10/11 (Linux/macOS support planned)
- **RAM**: 4GB minimum (8GB recommended for larger models)
- **Storage**: 2GB free space for AI models
- **Audio**: Microphone and speakers/headphones
- **Network**: Internet connection for platform integration

### Recommended Setup
- **CPU**: Intel i5 or AMD Ryzen 5 (for real-time speech processing)
- **RAM**: 8GB+ for smooth AI model performance
- **Audio**: USB headset for clear voice recognition
- **Network**: Stable broadband for seamless platform sync

## 🚧 Roadmap

### 🔄 **Current Development**
- [ ] Advanced character abilities (Sects & Violets, Bad Moon Rising)
- [ ] Enhanced narrative generation with character backstories
- [ ] Platform-specific optimizations and features
- [ ] Mobile companion app for players

### 🎯 **Planned Features**
- [ ] **Multi-Script Support**: All official and homebrew scripts
- [ ] **Tournament Mode**: Advanced features for competitive play
- [ ] **Analytics Dashboard**: Deep game analysis and statistics
- [ ] **Custom Voice Training**: Personalized AI voice options
- [ ] **Integration Hub**: Connect with Discord, Twitch, and more

### 🌟 **Future Vision**
- [ ] **VR Integration**: Immersive storytelling in virtual reality
- [ ] **AI Player Bots**: Computer players for practice games  
- [ ] **Community Scripts**: Shared custom character database
- [ ] **Live Streaming**: Built-in streaming with AI commentary

## 🤝 Contributing

We welcome contributions from the Blood on the Clocktower community!

### 🐛 **Bug Reports**
- Use the [Issues](https://github.com/yourusername/ProjectClocktower/issues) page
- Include system info, logs, and steps to reproduce
- Check existing issues before creating new ones

### 🔧 **Development**
```bash
# Setup development environment
git clone https://github.com/yourusername/ProjectClocktower.git
cd ProjectClocktower
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# Run tests
pytest tests/

# Code formatting  
black src/
flake8 src/
```

### 📋 **Pull Request Guidelines**
1. Fork the repository and create a feature branch
2. Write tests for new functionality
3. Ensure all tests pass and code is properly formatted
4. Update documentation for new features
5. Submit PR with clear description of changes

## 🔒 Privacy & Security

### 🎤 **Voice Data**
- **Local Processing**: All speech recognition happens locally using Whisper
- **No Cloud Upload**: Voice data never leaves your computer
- **Session Only**: Audio is processed in real-time and not stored

### 🌐 **Platform Integration**  
- **Minimal Data**: Only sends necessary game state updates
- **No Personal Info**: No personal data transmitted beyond game context
- **Secure Connections**: All platform communication uses secure protocols

### 💾 **Data Storage**
- **Local Only**: Game logs and settings stored locally
- **User Control**: Full control over data retention and deletion
- **Open Source**: Code is transparent and auditable

## 🎮 Supported Characters

### Trouble Brewing (✅ Complete)
**Townsfolk**: Washerwoman, Librarian, Investigator, Chef, Empath, Fortune Teller, Undertaker, Monk, Ravenkeeper, Virgin, Slayer, Soldier, Mayor

**Outsiders**: Butler, Drunk, Recluse, Saint

**Minions**: Poisoner, Spy, Scarlet Woman, Baron

**Demons**: Imp

### Bad Moon Rising (🔄 Coming Soon)
**Townsfolk**: Grandmother, Sailor, Chambermaid, Exorcist, Innkeeper, Gambler, Gossip, Courtier, Professor, Minstrel, Tea Lady, Pacifist, Fool

**Outsiders**: Goon, Lunatic, Tinker, Moonchild

**Minions**: Godfather, Devil's Advocate, Assassin, Mastermind

**Demons**: Zombuul, Pukka, Shabaloth, Po

### Sects & Violets (🔄 Coming Soon)  
**Townsfolk**: Clockmaker, Dreamer, Snake Charmer, Mathematician, Flowergirl, Town Crier, Oracle, Savant, Seamstress, Philosopher, Artist, Juggler, Sage

**Outsiders**: Klutz, Evil Twin, Mutant, Sweetheart

**Minions**: Fang Gu, Vigormortis, No Dashii, Vortox

**Demons**: Cerenovus, Pit-Hag, Fang Gu, Vigormortis

## 🛟 Troubleshooting

### Common Issues

#### 🎤 Voice Recognition Not Working
```bash
# Check microphone permissions
# Windows: Settings > Privacy > Microphone
# Verify microphone in Windows Sound settings
# Try different USB port for USB microphones
```

#### 🌐 Platform Connection Failed  
```bash
# Verify internet connection
# Check room code spelling
# Ensure platform is accessible in browser
# Try refreshing the platform webpage
```

#### 🤖 AI Models Not Downloading
```bash
# Run setup manually
python setup.py

# Check internet connection  
# Verify 2GB+ free disk space
# Check antivirus blocking downloads
```

#### 🔊 Audio Output Issues
```bash
# Update Windows audio drivers
# Check default audio device in Windows
# Verify audio device in application settings
# Try different audio output device
```

### 📋 Getting Help

1. **Check Logs**: Review `logs/storyteller.log` for error details
2. **Search Issues**: Look through [existing issues](https://github.com/yourusername/ProjectClocktower/issues)
3. **Discord Community**: Join our [Discord server](https://discord.gg/your-invite) for real-time help
4. **Create Issue**: Submit detailed bug report with system information

### 📊 System Information
When reporting issues, include:
```bash
# Get system info
python -m src.main --version
python --version
pip list | grep -E "(whisper|pyaudio|requests)"
```

## 📜 License & Legal

### 📄 **License**
This project is released under the Educational Use License. See [LICENSE](LICENSE) for details.

### ⚖️ **Blood on the Clocktower**
Blood on the Clocktower is a trademark of The Pandemonium Institute. This project is an unofficial fan-made tool and is not affiliated with or endorsed by The Pandemonium Institute.

### 🎯 **Fair Use**
This project is created for educational and entertainment purposes under fair use provisions. It does not reproduce game content but provides tools to enhance the playing experience.

### 🤝 **Community Guidelines**
- Use this tool to enhance games, not replace human creativity
- Respect platform terms of service when connecting
- Support the official game by purchasing legitimate copies
- Contribute improvements back to the community

## 🙏 Acknowledgments

### 🎭 **Blood on the Clocktower**
- Steven Medway and The Pandemonium Institute for creating this amazing game
- The BOTC community for extensive playtesting and feedback

### 🤖 **Technology Partners**
- **OpenAI** for Whisper speech recognition technology
- **Piper TTS** team for high-quality text-to-speech synthesis  
- **Python Community** for excellent libraries and tools

### 🌟 **Special Thanks**
- **Alpha Testers** who provided invaluable feedback
- **Platform Developers** who make online BOTC possible
- **AI Researchers** advancing speech and language technology
- **Open Source Contributors** who make projects like this possible

---

<div align="center">

**🎭 Ready to tell tales of good versus evil? Download and start your AI storytelling journey today! 🎭**

[Download Latest Release](https://github.com/yourusername/ProjectClocktower/releases) • [View Documentation](docs/) • [Join Community](https://discord.gg/your-invite) • [Report Issues](https://github.com/yourusername/ProjectClocktower/issues)

</div>