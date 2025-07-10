#!/usr/bin/env python3
"""
Blood on the Clocktower AI Agent - Launcher Script
Entry point that handles import path setup for both development and executable
"""

import os
import sys
from pathlib import Path

def setup_imports():
    """Setup import paths for the application"""
    # Get the directory containing this script
    launcher_dir = Path(__file__).parent.absolute()
    
    # Add the project root to Python path
    if launcher_dir not in sys.path:
        sys.path.insert(0, str(launcher_dir))
    
    # Add the src directory to Python path  
    src_dir = launcher_dir / "src"
    if src_dir.exists() and str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    
    print(f"Launcher directory: {launcher_dir}")
    print(f"Python path: {sys.path[:3]}...")  # Show first 3 entries

def main():
    """Main launcher function"""
    print("Blood on the Clocktower AI Agent - Starting...")
    
    # Setup import paths
    setup_imports()
    
    try:
        # Try to import and run the main window
        from src.gui.main_window import main as gui_main
        print("Successfully imported GUI module")
        gui_main()
    except ImportError as e:
        print(f"Import error with src.gui: {e}")
        try:
            # Fallback: try direct import
            from gui.main_window import main as gui_main
            print("Successfully imported GUI module (fallback)")
            gui_main()
        except ImportError as e2:
            print(f"Import error with gui: {e2}")
            print("\nTroubleshooting:")
            print("1. Make sure all required files are present")
            print("2. Check that the executable was built correctly")
            print("3. Try running from source with: python botc_launcher.py")
            print(f"\nCurrent working directory: {os.getcwd()}")
            print(f"Script location: {Path(__file__).parent}")
            print(f"Files in directory: {list(Path('.').glob('*'))}")
            sys.exit(1)

if __name__ == "__main__":
    main()