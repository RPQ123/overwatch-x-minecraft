@echo off
cd /d "%~dp0..\..\"
"%~dp0..\..\.venv\Scripts\python.exe" "%~dp0..\..\tools\launch_secondary_minecraft.py"
if errorlevel 1 pause
