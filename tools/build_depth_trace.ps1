$ErrorActionPreference='Stop'
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    $traceCompiler=(& (Join-Path $PSScriptRoot 'resolve_native_compiler.ps1'))
    & $traceCompiler -std=c++17 -O2 -static -shared 'native-host/src/trace_plugin.cpp' 'native-host/src/trace_layout.cpp' -ld3d11 -ldxgi -ldxguid -o 'native-host/build/owmc-depth-trace.dll'
    if ($LASTEXITCODE) { exit $LASTEXITCODE }
    & $traceCompiler -std=c++17 -static 'native-host/tests/trace_test.cpp' -ld3d11 -ldxgi -ldxguid -ld3dcompiler -o 'native-host/build/owmc-trace-test.exe'
    if ($LASTEXITCODE) { exit $LASTEXITCODE }
    & 'native-host/build/owmc-trace-test.exe'
    exit $LASTEXITCODE
} finally { Pop-Location }
