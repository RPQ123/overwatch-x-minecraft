$ErrorActionPreference='Stop'
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    New-Item -ItemType Directory -Force native-host/build | Out-Null
    $bootstrapCompiler=(& (Join-Path $PSScriptRoot 'resolve_native_compiler.ps1'))
    & $bootstrapCompiler -std=c++17 -O2 -static -Wall -Wextra -Werror -shared native-host/src/session_bootstrap.cpp native-host/src/trace_layout.cpp -ld3d11 -ldxgi -ldxguid -o native-host/build/owmc-session-bootstrap-v10.dll
    exit $LASTEXITCODE
} finally {Pop-Location}
