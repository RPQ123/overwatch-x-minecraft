@echo off
cd /d "%~dp0.."
powershell.exe -NoProfile -WindowStyle Hidden -Command "Start-Process -FilePath (Join-Path (Get-Location) '.venv\Scripts\python.exe') -ArgumentList 'tools/aoa3_passthrough_lab.py' -WorkingDirectory (Get-Location).Path -WindowStyle Hidden"
