"""
Utility functions and helpers
"""

from .encoding_fix import fix_windows_encoding, safe_print

# Auto-fix encoding when utils package is imported
fix_windows_encoding()

__all__ = ['fix_windows_encoding', 'safe_print']