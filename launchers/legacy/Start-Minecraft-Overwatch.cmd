@echo off
cd /d "%~dp0..\..\"
"%~dp0..\..\.venv\Scripts\python.exe" tools\launch_combat.py --minecraft-world
if errorlevel 1 pause
