@echo off
rem Archived direct developer entry. Prefer Launch-Overwatch-Minecraft.cmd at root.
cd /d "%~dp0..\..\"
if not exist "%~dp0..\..\.venv\Scripts\python.exe" (
    echo Run tools\setup_environment.ps1 first to prepare Python 3.13.
    pause
    exit /b 1
)
"%~dp0..\..\.venv\Scripts\python.exe" "%~dp0..\..\tools\launch_passthrough_session.py"
if errorlevel 1 pause
