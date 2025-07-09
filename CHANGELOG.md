# Changelog

All notable changes to the Blood on the Clocktower AI Storyteller project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project setup and architecture
- Complete AI Storyteller implementation

## [1.0.0] - 2024-01-XX

### Added
- 🎭 **Core AI Storyteller System**
  - Intelligent decision-making engine for all character abilities
  - Dynamic game balancing based on team performance
  - Dramatic story generation and atmospheric narration
  - Complete rule enforcement for Blood on the Clocktower

- 🎤 **Voice Interaction System**
  - Local speech recognition using OpenAI Whisper
  - Text-to-speech narration using Piper TTS
  - Natural language processing for player commands
  - "Storyteller, I have a question" handling

- 🖥️ **Storyteller Dashboard**
  - Professional dark-themed GUI with three-panel layout
  - Interactive grimoire with real-time player token display
  - Game phase management (setup/night/day/voting/execution)
  - Quick action buttons for common storyteller tasks
  - AI decision logging and transparency

- 🔗 **Platform Integration**
  - clocktower.online WebSocket integration
  - botc.app basic integration
  - Extensible API system for custom platforms
  - Real-time game state synchronization

- ⚖️ **Complete Rule Engine**
  - Full Trouble Brewing script implementation
  - Nomination and voting validation
  - Win condition checking and announcement
  - Character ability resolution with edge cases
  - Drunk/poisoned information modification

- 🧠 **Character Ability Support**
  - **Townsfolk**: Washerwoman, Librarian, Investigator, Chef, Empath, Fortune Teller, Undertaker, Monk, Ravenkeeper, Virgin, Slayer, Soldier, Mayor
  - **Outsiders**: Butler, Drunk, Recluse, Saint
  - **Minions**: Poisoner, Spy, Scarlet Woman, Baron
  - **Demons**: Imp

- 🛠️ **Development Tools**
  - Automated model download system
  - Windows executable builder with PyInstaller
  - Professional installer creation with NSIS
  - Comprehensive logging and error handling

- 📦 **Distribution**
  - Standalone Windows executable
  - Automated dependency installation
  - One-click model download script
  - Cross-platform Python support

### Technical Features
- **Local AI Processing**: No cloud dependencies for core functionality
- **Real-time Performance**: Sub-2-second response times for voice commands
- **Secure Architecture**: Voice data never leaves local machine
- **Extensible Design**: Plugin system for new characters and platforms
- **Professional Logging**: Comprehensive debug and audit trails

### Documentation
- Complete README with usage instructions
- Detailed CONTRIBUTING guidelines
- Comprehensive rules reference (rules.md)
- API documentation for platform integration
- Character implementation guides

### Quality Assurance
- Type hints throughout codebase
- Comprehensive error handling
- Input validation and sanitization
- Memory leak prevention
- Resource cleanup on shutdown

---

## Version Numbering

This project uses [Semantic Versioning](https://semver.org/):
- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible functionality additions  
- **PATCH** version for backwards-compatible bug fixes

## Release Process

Releases are created when:
1. All planned features for version are complete
2. All tests pass and code quality checks succeed
3. Documentation is updated
4. Windows executable builds successfully
5. Beta testing is completed

## Future Releases

### [1.1.0] - Planned
- Bad Moon Rising character support
- Enhanced narrative generation
- Multiple voice personality options
- Discord integration

### [1.2.0] - Planned  
- Sects & Violets character support
- Tournament mode features
- Advanced analytics dashboard
- Mobile companion app

### [2.0.0] - Future
- VR integration support
- AI player bots
- Community script sharing
- Live streaming integration

---

For detailed information about each release, see the [Releases](https://github.com/yourusername/ProjectClocktower/releases) page.