@echo off
"%~dp0..\..\.venv\Scripts\python.exe" "%~dp0..\..\tools\launch_minecraft.py"
if errorlevel 1 pause
