$ErrorActionPreference='Stop'
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    $selectionCompiler=(& (Join-Path $PSScriptRoot 'resolve_native_compiler.ps1'))
    & $selectionCompiler -std=c++17 -O2 -static -DOWMC_SELECTION_TRACE -shared native-host/src/camera_trace.cpp native-host/src/trace_layout.cpp -ld3d11 -ldxgi -ldxguid -o native-host/build/owmc-selection-trace-v1.dll
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & $selectionCompiler -std=c++17 -static -DOWMC_SELECTION_TRACE native-host/tests/camera_test.cpp -ld3d11 -ldxgi -ldxguid -ld3dcompiler -o native-host/build/owmc-camera-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & native-host/build/owmc-camera-test.exe
    exit $LASTEXITCODE
} finally {Pop-Location}
