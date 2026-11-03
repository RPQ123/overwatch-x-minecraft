$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    if (-not (Test-Path '.venv/Scripts/python.exe')) {
        & uv venv .venv --python 3.13
        if ($LASTEXITCODE) { throw 'Python environment creation failed' }
    }
    & uv pip install --python .venv/Scripts/python.exe -r tools/requirements-dev.txt
    if ($LASTEXITCODE) { throw 'Python dependency installation failed' }
    & .venv/Scripts/python.exe tools/check_environment.py
    exit $LASTEXITCODE
} finally { Pop-Location }
