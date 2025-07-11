# 🤖 Autonomous AI Storyteller System

## Complete Hands-Off Blood on the Clocktower AI

This system provides a fully autonomous AI Storyteller that can run Blood on the Clocktower games with minimal human intervention. The AI listens to players, makes storyteller decisions, and manages the entire game flow.

---

## 🏗️ **System Architecture**

### **Core Components:**

1. **🧠 Local DeepSeek-R1 AI** (`local_deepseek_storyteller.py`)
   - Runs DeepSeek-R1-Distill-Qwen-1.5B locally
   - Provides atmospheric narration and rule decisions
   - No API calls - completely offline

2. **🎤 Speech Recognition Pipeline** (`speech_handler.py`)
   - Continuous listening with Whisper
   - Parses player speech into game actions
   - "Fortune Teller chooses Alice and Bob" → structured action

3. **🎭 Autonomous Controller** (`autonomous_storyteller.py`)
   - Orchestrates the entire game flow
   - Makes all storyteller decisions
   - Manages night/day phases automatically

4. **📊 Game Context Tracker** (`autonomous_storyteller.py` - `GameContext`)
   - Records all information given to players
   - Tracks voting patterns and suspicions
   - Builds comprehensive game state for AI decisions

5. **🎲 Character Ability Handlers** (`character_handlers.py`)
   - Implements all character abilities
   - Makes information decisions (Fortune Teller, Empath, etc.)
   - Considers drunk/poisoned effects

6. **⏰ Timing Management** (`timing_config.py`)
   - Flexible timing suggestions (not hard limits)
   - Player-controlled extensions
   - Automatic phase progression

7. **🖥️ Comprehensive UI Controls** (`autonomous_control_panel.py`)
   - Complete configuration interface
   - Real-time monitoring
   - Manual override capabilities

---

## 🎮 **How It Works**

### **Setup Phase:**
1. User configures AI behavior via UI (drama level, truth rates, timing)
2. AI downloads and initializes models (DeepSeek, Whisper, Piper)
3. Game state created with player assignments

### **Game Flow:**
1. **Speech Recognition:** AI continuously listens for player actions
2. **Action Parsing:** Converts speech to structured game commands
3. **Decision Making:** AI uses game context to make storyteller choices
4. **Information Delivery:** Private/public announcements via TTS
5. **State Tracking:** Every decision recorded for future context

### **Example Sequence:**
```
Player speaks: "Fortune Teller chooses Alice and Bob"
↓
Speech Parser: fortune_teller_action(targets=["Alice", "Bob"])
↓
AI Decision: Analyzes game context, character states, balance
↓
Information: "You learn: NO - neither is the demon"
↓
Context Update: Logs decision for future reference
```

---

## ⚙️ **Configuration Options**

### **Autonomy Levels:**
- **Low:** AI assists but human makes decisions
- **Medium:** AI handles routine decisions, human handles complex ones
- **High:** AI makes most decisions, human can override
- **Full:** Complete AI control (tournament mode)

### **Information Strategy:**
- **Truth Rate:** How often to give accurate information (0.85 default)
- **Drama Factor:** Bias toward dramatic/story moments (0.15 default)
- **Balance Factor:** Adjust based on team advantages (0.2 default)

### **Narration Style:**
- **Drama Level:** Low/Medium/High/Epic
- **Length:** Brief/Medium/Verbose announcements
- **Atmosphere:** Gothic/Light/Humorous tone

### **Timing:**
- **Pacing:** Quick/Standard/Relaxed/Custom
- **Extensions:** Allow player time requests
- **Auto-advance:** Automatic phase progression

---

## 🎯 **Key Features**

### **✅ What the AI Does (Storyteller Role):**
- **Decides information** for Fortune Teller, Empath, Washerwoman, etc.
- **Manages drunk/poisoned effects** (gives false information)
- **Provides atmospheric narration** for all game events
- **Handles rule edge cases** with context awareness
- **Tracks game balance** and adjusts decisions accordingly
- **Manages timing and pacing** with flexible suggestions

### **❌ What the AI Doesn't Do (Player Decisions):**
- Choose demon kills (that's the demon player's choice)
- Choose monk protection targets (monk player decides)
- Make nominations or votes (players decide)
- Control player discussions (they control their own speech)

### **🤝 Hybrid Control:**
- **Manual Override:** Take control at any time
- **Hybrid Mode:** Mix AI and manual control
- **Emergency Stop:** Immediate halt of all AI operations
- **Decision Review:** See all AI choices with reasoning

---

## 📁 **File Structure**

```
src/
├── ai/
│   ├── local_deepseek_storyteller.py    # Local AI model
│   ├── autonomous_storyteller.py        # Main controller
│   ├── character_handlers.py            # Character abilities
│   ├── autonomous_config.py             # Configuration system
│   └── narrator_integration.py          # Clean narrator interface
│
├── core/
│   ├── timing_config.py                 # Timing management
│   └── game_state.py                    # Game state tracking
│
├── gui/
│   ├── autonomous_control_panel.py      # Main UI controls
│   ├── timing_controls.py               # Timing UI
│   └── dashboard_autonomous_integration.py # Integration example
│
├── speech/
│   └── speech_handler.py                # Speech recognition/TTS
│
└── utils/
    └── first_run_setup.py               # Model downloads
```

---

## 🚀 **Getting Started**

### **1. First Time Setup:**
```bash
# Download all AI models (~7GB total)
python setup.py

# Models downloaded:
# - Whisper (5 models): ~4GB
# - Piper TTS: ~50MB  
# - DeepSeek-R1: ~3.5GB
```

### **2. Launch Enhanced Dashboard:**
```python
from src.gui.dashboard_autonomous_integration import create_enhanced_dashboard

root, dashboard = create_enhanced_dashboard()
root.mainloop()
```

### **3. Configure & Start:**
1. Choose preset configuration (Quick/Standard/Dramatic/Tournament)
2. Adjust specific settings as needed
3. Click "🚀 Start Autonomous Mode"
4. AI takes over and manages the game

### **4. Monitor & Control:**
- **Status Tab:** Real-time AI activity and speech recognition
- **Decisions Tab:** Complete log of all AI choices
- **Game State Tab:** Current player states and information
- **Manual Override:** Take control whenever needed

---

## 🎲 **Example Game Flow**

### **Night 1:**
```
AI: "The first night begins. Everyone close your eyes."
AI: "Fortune Teller, wake up. Choose two players."
Player: "I choose Alice and Bob"
AI: [Analyzes: Alice=Villager, Bob=Imp, FT=healthy]
AI: [Decision: Tell truth - this creates good story tension]
AI: "You learn: YES - one of them is the demon."
AI: "Fortune Teller, close your eyes."
```

### **Day 1:**
```
AI: "Dawn breaks. Miraculously, everyone survived the night."
AI: "The town may discuss and vote. You have about 5 minutes."
Player: "I nominate Charlie"
AI: [Recognizes nomination action]
AI: "Charlie has been nominated. The town has 2 minutes to debate."
[... debate occurs ...]
AI: "Time to vote. Voting closes in 30 seconds."
```

---

## 🔧 **Advanced Features**

### **Context-Aware Decisions:**
- AI remembers all previous information given
- Considers voting patterns and suspicions  
- Adjusts strategy based on game balance
- Learns player behavior during the game

### **Flexible Timing:**
- Soft time limits with gentle reminders
- "Can we have more time?" → "Of course!"
- Auto-extension during heated discussions
- Emergency time controls for tournaments

### **Smart Information Strategy:**
- Early game protection (holds back game-ending info)
- Drama factor (creates tension at key moments)
- Balance adjustment (helps losing team when appropriate)
- Drunk/poisoned handling (realistic false information)

### **Real-Time Monitoring:**
- Live activity log of all AI decisions
- Speech recognition status and confidence
- Decision tree with reasoning
- Game state visualization

---

## 🎯 **Use Cases**

### **🏆 Tournament Mode:**
- Strict timing enforcement
- Minimal storyteller bias
- Complete autonomy
- Fair and balanced decisions

### **🎭 Story Mode:**
- Maximum drama and atmosphere
- Epic narration style
- Flexible timing
- Story-focused decisions

### **⚡ Quick Games:**
- Fast-paced decisions
- Brief announcements
- Direct information
- Minimal delays

### **🍺 Casual Social:**
- Relaxed timing
- Moderate humor
- Flexible rules
- Social-friendly pacing

---

## 💡 **Benefits**

### **For Players:**
- ✅ Consistent, unbiased storytelling
- ✅ Always available (no human storyteller needed)
- ✅ Perfect rule knowledge
- ✅ Dramatic, atmospheric experience
- ✅ Flexible timing that adapts to the group

### **For Storytellers:**
- ✅ Learn from AI decision-making
- ✅ Focus on social aspects while AI handles mechanics
- ✅ Use as training tool for new storytellers
- ✅ Consistent experience across games

### **For the Community:**
- ✅ More games possible (no storyteller shortage)
- ✅ 24/7 availability for online play
- ✅ Standardized rule enforcement
- ✅ Accessibility for new players

---

## 🔮 **Future Enhancements**

- **Multi-language support** via different speech models
- **Custom character implementations** for homebrew roles
- **Advanced player modeling** (learning individual behaviors)
- **Integration with online platforms** (clocktower.online, botc.app)
- **Voice cloning** for personalized storyteller voices
- **Machine learning** from game outcomes

---

*The Autonomous AI Storyteller represents the future of Blood on the Clocktower - where technology enhances the social deduction experience while preserving the human elements that make the game special.*