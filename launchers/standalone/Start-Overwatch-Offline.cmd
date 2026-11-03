@echo off
echo This starts the separate 2015 research copy with per-program firewall isolation.
echo Run this file with elevated permissions. Your current Overwatch installation is not targeted.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\..\tools\start_overwatch_offline.ps1"
if errorlevel 1 pause
