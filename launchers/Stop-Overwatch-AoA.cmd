@echo off
cd /d "%~dp0.."
".venv\Scripts\python.exe" "tools\aoa3_passthrough_lab.py" --stop
if errorlevel 1 pause
