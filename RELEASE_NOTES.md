## Blood on the Clocktower AI Storyteller v1.0.2

### 🎭 Features:
- Full AI Storyteller for Blood on the Clocktower
- Voice interaction with speech recognition and TTS
- Enhanced botc.app platform integration
- Complete Trouble Brewing script support
- Intelligent decision making for character abilities
- Real-time game state management

### 🆕 What's New in v1.0.2:
- **Enhanced botc.app Compatibility**: Added specialized BotCAppAdapter for seamless integration
- **Improved Connection Handling**: WebSocket with HTTP polling fallback
- **Better Error Recovery**: Robust handling of connection failures
- **Windows Build Fixes**: Resolved Unicode encoding and PyInstaller dependency issues
- **Code Quality**: Fixed all Black, isort, and flake8 formatting issues

### 🔧 Installation:
**For Developers:**
```bash
git clone https://github.com/emmjayh/ProjectClocktower.git
cd ProjectClocktower
pip install -r requirements.txt
python -m src.gui.main_window
```

**Windows Users:**
- Windows executable will be available in future releases once CI/CD pipeline is fully operational
- For now, please use the developer installation method

### 🎯 System Requirements:
- Python 3.11 or 3.12
- Microphone for voice commands (optional)
- Speakers/headphones for AI narration (optional)
- Internet connection for platform integration

### 🐛 Known Issues:
- Automated release creation is currently being fixed
- Windows executable build requires manual intervention

For support, visit: https://github.com/emmjayh/ProjectClocktower/issues
