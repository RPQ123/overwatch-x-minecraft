param([switch]$Stream)
$ErrorActionPreference='Stop'
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    $layerCompiler=(& (Join-Path $PSScriptRoot 'resolve_native_compiler.ps1'))
    $layerName='native-host/build/owhero-layer-probe-v1.dll'
    $layerDefines=@()
    if ($Stream) {$layerName='native-host/build/owhero-layer-stream-v3.dll';$layerDefines=@('-DOWMC_HERO_STREAM')}
    & $layerCompiler -std=c++17 -O2 -static -shared @layerDefines native-host/src/hero_layer_probe.cpp native-host/src/hero_stream.cpp native-host/src/trace_layout.cpp -ld3d11 -ldxgi -ldxguid -ld3dcompiler -o $layerName
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & $layerCompiler -std=c++17 -static native-host/tests/hero_layer_test.cpp -ld3d11 -ldxgi -ldxguid -ld3dcompiler -o native-host/build/owmc-layer-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & native-host/build/owmc-layer-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & $layerCompiler -std=c++17 -static native-host/tests/hero_stream_test.cpp native-host/src/hero_stream.cpp -ld3d11 -ldxgi -ldxguid -ld3dcompiler -o native-host/build/hero-stream-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & native-host/build/hero-stream-test.exe
    exit $LASTEXITCODE
} finally {Pop-Location}
