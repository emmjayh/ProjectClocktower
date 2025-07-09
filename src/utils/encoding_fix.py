"""
Windows encoding fix for Unicode characters
"""

import sys
import os


def fix_windows_encoding():
    """Fix Windows console encoding for Unicode support"""
    if sys.platform.startswith('win'):
        try:
            # Set console to UTF-8 on Windows
            os.system('chcp 65001 > nul')
            # Set environment variables for UTF-8
            os.environ['PYTHONIOENCODING'] = 'utf-8'
        except Exception:
            # If we can't fix encoding, just continue
            pass


def safe_print(text, fallback=None):
    """Safely print text with Unicode fallback for Windows"""
    if fallback is None:
        # Remove common emojis if encoding fails
        fallback = (text.replace('🎭', '[GAME]')
                       .replace('✅', '[OK]')
                       .replace('❌', '[ERROR]')
                       .replace('🔧', '[CONFIG]')
                       .replace('🤖', '[AI]')
                       .replace('🎤', '[MIC]')
                       .replace('🔊', '[SPEAKER]')
                       .replace('🌙', '[NIGHT]')
                       .replace('☀️', '[DAY]')
                       .replace('🗳️', '[VOTE]')
                       .replace('⚖️', '[EXECUTE]')
                       .replace('💀', '[DEATH]')
                       .replace('🍺', '[DRUNK]')
                       .replace('📝', '[NOTE]')
                       .replace('🔗', '[CONNECT]')
                       .replace('🧠', '[AI]')
                       .replace('💭', '[COMMENT]'))
    
    try:
        print(text)
    except UnicodeEncodeError:
        try:
            print(fallback)
        except Exception:
            print(text.encode('ascii', 'replace').decode('ascii'))


# Initialize encoding fix when module is imported
fix_windows_encoding()