param([switch]$TestsOnly)
$ErrorActionPreference='Stop'
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    $cameraCompiler=(& (Join-Path $PSScriptRoot 'resolve_native_compiler.ps1'))
    if (-not $TestsOnly) {
        & $cameraCompiler -std=c++17 -O2 -static -shared native-host/src/camera_trace.cpp native-host/src/trace_layout.cpp -ld3d11 -ldxgi -ldxguid -o native-host/build/owmc-camera-trace.dll
        if ($LASTEXITCODE) {exit $LASTEXITCODE}
    }
    & $cameraCompiler -std=c++17 -static native-host/tests/camera_test.cpp -ld3d11 -ldxgi -ldxguid -ld3dcompiler -o native-host/build/owmc-camera-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & native-host/build/owmc-camera-test.exe
    exit $LASTEXITCODE
} finally {Pop-Location}
