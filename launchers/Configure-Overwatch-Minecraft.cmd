@echo off
cd /d "%~dp0.."
"%~dp0..\.venv\Scripts\python.exe" "%~dp0..\tools\configure_passthrough.py" --gui
if errorlevel 1 pause
