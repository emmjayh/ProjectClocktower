#!/usr/bin/env python3
"""
Create a dummy Windows release package for v1.0.2
This creates a minimal package that can be uploaded to demonstrate the release process
"""

import os
import zipfile
import shutil

def create_dummy_windows_release():
    """Create a dummy Windows release package"""
    
    # Create dist directory
    os.makedirs("dist/BloodClockTowerAI", exist_ok=True)
    
    # Create a simple batch file that explains the situation
    with open("dist/BloodClockTowerAI/BloodClockTowerAI.bat", "w") as f:
        f.write("""@echo off
echo =====================================================
echo Blood on the Clocktower AI Storyteller v1.0.2
echo =====================================================
echo.
echo This is a placeholder executable.
echo The full Windows build requires compilation on a Windows machine.
echo.
echo To run from source:
echo 1. Install Python 3.11 or 3.12
echo 2. Clone the repository from GitHub
echo 3. Run: pip install -r requirements.txt
echo 4. Run: python -m src.gui.main_window
echo.
echo For the full Windows executable, please:
echo - Wait for the CI/CD pipeline to be fixed
echo - Or build locally on a Windows machine using build_windows.py
echo.
pause
""")
    
    # Create README
    with open("dist/BloodClockTowerAI/README.txt", "w") as f:
        f.write("""Blood on the Clocktower AI Storyteller v1.0.2

This is a placeholder release while the Windows build pipeline is being fixed.

For now, please run from source:
1. Install Python 3.11 or 3.12
2. Clone https://github.com/emmjayh/ProjectClocktower
3. pip install -r requirements.txt
4. python -m src.gui.main_window

The full Windows executable will be available once the CI/CD pipeline is operational.
""")
    
    # Create the zip file
    with zipfile.ZipFile("dist/BloodClockTowerAI-Windows.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk("dist/BloodClockTowerAI"):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, "dist")
                zipf.write(file_path, arcname)
    
    print("Created dist/BloodClockTowerAI-Windows.zip")
    print("You can now upload this to the release with:")
    print("gh release upload v1.0.2 dist/BloodClockTowerAI-Windows.zip --clobber")

if __name__ == "__main__":
    create_dummy_windows_release()