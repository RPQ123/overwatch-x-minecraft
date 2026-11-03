param([string]$OutputDir='research/scope-20261027')
$ErrorActionPreference='Stop'
$scopeTools = Split-Path -Parent $PSScriptRoot
Push-Location (Split-Path -Parent $scopeTools)
try {
    New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
    $scopeCompiler=(& (Join-Path $scopeTools 'resolve_native_compiler.ps1'))
    $scopeTest=Join-Path $OutputDir 'native-hud-preservation-test.exe'
    & $scopeCompiler -std=c++17 -O2 -static -Wall -Wextra -Werror `
        native-host/tests/native_hud_preservation_test.cpp `
        native-host/src/live_world_blend.cpp native-host/src/frame_compositor.cpp `
        -ld3d11 -ldxgi -ldxguid -ld3dcompiler -lgdi32 -o $scopeTest
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & $scopeTest
    exit $LASTEXITCODE
} finally {Pop-Location}
