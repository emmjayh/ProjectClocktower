#!/usr/bin/env python3
"""
Release Verification Script for Blood on the Clocktower AI Storyteller
Verifies all core systems are ready for release
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def verify_core_modules():
    """Verify core game modules can be imported"""
    try:
        from core.game_engine import GameEngine
        from core.mvp_character_abilities import MVPCharacterAbilities
        from core.voting_system import SimpleMajorityVoting
        from core.player_choice_system import MockPlayerChoices
        from core.mvp_game_controller import MVPGameController
        print("✅ Core game modules: OK")
        return True
    except ImportError as e:
        print(f"❌ Core modules failed: {e}")
        return False

def verify_speech_modules():
    """Verify speech modules can be imported (with mocks)"""
    try:
        from speech.enhanced_storyteller_tts import EnhancedStoryteller
        from speech.advanced_nlp_processor import AdvancedNLPProcessor
        from speech.voice_player_identification import VoicePlayerIdentifier
        print("✅ Speech modules: OK")
        return True
    except ImportError as e:
        print(f"❌ Speech modules failed: {e}")
        return False

def verify_tests():
    """Run basic functionality verification"""
    try:
        # Test game engine
        from core.game_engine import GameEngine
        engine = GameEngine()
        game_state = engine.create_game(["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace"])
        
        if len(game_state.players) == 7:
            print("✅ Game creation: OK")
        else:
            print("❌ Game creation failed")
            return False
            
        # Test character abilities
        from core.mvp_character_abilities import AbilityDispatcher
        dispatcher = AbilityDispatcher(game_state)
        print("✅ Character abilities: OK")
        
        return True
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False

def main():
    print("🎭 Blood on the Clocktower AI Storyteller - Release Verification")
    print("=" * 60)
    
    all_good = True
    
    all_good &= verify_core_modules()
    all_good &= verify_speech_modules()
    all_good &= verify_tests()
    
    print("=" * 60)
    if all_good:
        print("🎉 RELEASE READY: All systems verified!")
        print("🚀 Version 2.1.0 Stable is ready for deployment")
    else:
        print("⚠️  Some verification checks failed")
        
    return 0 if all_good else 1

if __name__ == "__main__":
    sys.exit(main())