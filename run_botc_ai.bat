@echo off
REM Blood on the Clocktower AI Storyteller Launcher
REM This batch file handles PowerShell execution policy issues

echo.
echo ============================================
echo   Blood on the Clocktower AI Storyteller
echo ============================================
echo.

REM Check if the executable exists
if exist "dist\BloodClockTowerAI\BloodClockTowerAI.exe" (
    set EXECUTABLE="dist\BloodClockTowerAI\BloodClockTowerAI.exe"
) else if exist "BloodClockTowerAI.exe" (
    set EXECUTABLE="BloodClockTowerAI.exe"
) else if exist "botc_ai_storyteller.exe" (
    set EXECUTABLE="botc_ai_storyteller.exe"
) else (
    echo ERROR: Blood on the Clocktower AI executable not found!
    echo.
    echo Searched for:
    echo - dist\BloodClockTowerAI\BloodClockTowerAI.exe
    echo - BloodClockTowerAI.exe  
    echo - botc_ai_storyteller.exe
    echo.
    echo Please make sure you downloaded the complete release package.
    echo.
    pause
    exit /b 1
)

echo Starting Blood on the Clocktower AI Storyteller...
echo Found executable: %EXECUTABLE%
echo.

REM Try to run the executable directly first
echo Attempting to start the application...
start "" %EXECUTABLE%

REM Check if it started successfully
timeout /t 3 /nobreak >nul 2>&1
tasklist | find /i "BloodClockTowerAI.exe" >nul 2>&1
if %errorlevel% neq 0 (
    tasklist | find /i "botc_ai_storyteller.exe" >nul 2>&1
)
if %errorlevel% equ 0 (
    echo.
    echo Application started successfully!
    echo Check your taskbar for the Blood on the Clocktower AI window.
    echo.
    echo TIP: If you don't see the window, check if it's minimized in your taskbar.
    echo.
) else (
    echo.
    echo The application may have failed to start or exited immediately.
    echo This could be due to missing dependencies or system requirements.
    echo.
    echo Troubleshooting steps:
    echo 1. Make sure you have Windows 10/11 with latest updates
    echo 2. Try running as Administrator (right-click this file, "Run as administrator")
    echo 3. Check Windows Defender or antivirus isn't blocking the executable
    echo 4. Ensure you have sufficient disk space and memory
    echo.
)

echo.
echo Press any key to close this window...
pause >nul