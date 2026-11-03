@echo off
rem 备用入口：日常请双击根目录的「ow x mc 启动器.exe」。
cd /d "%~dp0.."
powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0..\tools\open_project_launcher.ps1"
if errorlevel 1 pause
