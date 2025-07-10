## Blood on the Clocktower AI Storyteller v1.0.5

### 🎉 Major Improvement: Automatic Model Downloads!

The AI Storyteller now automatically downloads required AI models on first run. No more separate download step!

### 🆕 What's New:
- **Automatic Setup**: First-run wizard downloads all AI models (~200MB)
- **Progress Tracking**: Visual progress bar and status updates during download
- **Simplified Installation**: Just run BloodClockTowerAI.exe - that's it!
- **Smart Detection**: Only downloads models if they're not already present
- **User-Friendly**: Clear instructions and error handling

### 🎭 Features:
- Full AI Storyteller for Blood on the Clocktower
- Voice interaction with speech recognition and TTS
- Enhanced botc.app platform integration
- Complete Trouble Brewing script support
- Intelligent decision making for character abilities
- Real-time game state management

### 🔧 Installation:
**Windows Users:**
1. Download `BloodClockTowerAI-Windows.zip`
2. Extract to a folder
3. Double-click `BloodClockTowerAI.exe`
4. The app will download AI models on first run (requires internet)
5. Start playing!

**Developers:**
```bash
git clone https://github.com/emmjayh/ProjectClocktower.git
cd ProjectClocktower
pip install -r requirements.txt
python -m src.gui.main_window
```

### 🎯 System Requirements:
- Windows 10/11
- ~200MB free disk space for AI models
- Internet connection for first-time setup
- Microphone for voice commands (optional)
- Speakers/headphones for AI narration (optional)

### 🐛 Fixed Issues:
- Removed manual download_models.bat step
- Integrated model downloads into main application
- Better error handling for network issues

For support, visit: https://github.com/emmjayh/ProjectClocktower/issues