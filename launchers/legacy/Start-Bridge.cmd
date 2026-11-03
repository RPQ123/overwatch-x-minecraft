@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\..\tools\start_pose_bridge.ps1"
if errorlevel 1 pause
