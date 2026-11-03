$ErrorActionPreference='Stop'
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    New-Item -ItemType Directory -Force -Path native-host/build | Out-Null
    $handCompiler=(& (Join-Path $PSScriptRoot 'resolve_native_compiler.ps1'))
    & $handCompiler -std=c++17 -O2 -static -Wall -Wextra -Werror -shared native-host/src/hand_depth_probe.cpp native-host/src/trace_layout.cpp -ld3d11 -ldxgi -ldxguid -ld3dcompiler -o native-host/build/owmc-hand-depth-probe.dll
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & $handCompiler -std=c++17 -O2 -static -Wall -Wextra -Werror native-host/tests/hand_depth_test.cpp -ld3d11 -ldxgi -ldxguid -ld3dcompiler -o native-host/build/owmc-hand-depth-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & native-host/build/owmc-hand-depth-test.exe
    exit $LASTEXITCODE
} finally {Pop-Location}
