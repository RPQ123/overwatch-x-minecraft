@echo off
"%~dp0..\..\.venv\Scripts\python.exe" "%~dp0..\..\tools\relay_prometheus.py" --listen
if errorlevel 1 pause
