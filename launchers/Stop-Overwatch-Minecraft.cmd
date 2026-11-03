@echo off
cd /d "%~dp0.."
"%~dp0..\.venv\Scripts\python.exe" "%~dp0..\tools\stop_passthrough_session.py"
if errorlevel 1 pause
