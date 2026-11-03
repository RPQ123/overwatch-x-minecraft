$ErrorActionPreference='Stop'
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    New-Item -ItemType Directory -Force -Path native-host/build | Out-Null
    $frameCompiler=(& (Join-Path $PSScriptRoot 'resolve_native_compiler.ps1'))
    $frameFlags=@('-std=c++17','-O2','-static','-Wall','-Wextra','-Werror')
    & $frameCompiler @frameFlags native-host/tests/frame_compositor_test.cpp native-host/src/frame_compositor.cpp -ld3d11 -ldxgi -ld3dcompiler -o native-host/build/frame-compositor-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & native-host/build/frame-compositor-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & $frameCompiler @frameFlags native-host/tests/frame_compositor_live.cpp native-host/src/frame_compositor.cpp -ld3d11 -ldxgi -ld3dcompiler -o native-host/build/frame-compositor-live.exe
    exit $LASTEXITCODE
} finally {Pop-Location}
