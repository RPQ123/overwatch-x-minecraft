$ErrorActionPreference='Stop'
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    $heroCompiler=(& (Join-Path $PSScriptRoot 'resolve_native_compiler.ps1'))
    & $heroCompiler -std=c++17 -O2 -static -Wall -Wextra -Werror -shared native-host/src/local_hero_probe.cpp native-host/src/trace_layout.cpp -ldxgi -ldxguid -o native-host/build/owmc-local-hero-spawn-v1.dll
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & $heroCompiler -std=c++17 -O2 -static -Wall -Wextra -Werror native-host/tests/local_hero_probe_test.cpp -ld3d11 -ldxgi -ldxguid -o native-host/build/owmc-local-hero-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & native-host/build/owmc-local-hero-test.exe
    exit $LASTEXITCODE
} finally {Pop-Location}
