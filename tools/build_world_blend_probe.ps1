$ErrorActionPreference='Stop'
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    New-Item -ItemType Directory -Force -Path native-host/build | Out-Null
    $blendCompiler=(& (Join-Path $PSScriptRoot 'resolve_native_compiler.ps1'))
    $blendFlags=@('-std=c++17','-O2','-static','-Wall','-Wextra','-Werror')
    & $blendCompiler @blendFlags native-host/tests/world_blend_test.cpp native-host/src/world_blend.cpp -ld3d11 -ldxgi -ldxguid -ld3dcompiler -o native-host/build/world-blend-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & native-host/build/world-blend-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & $blendCompiler @blendFlags -DOWMC_WORLD_BLEND -shared native-host/src/hand_depth_probe.cpp native-host/src/world_blend.cpp native-host/src/trace_layout.cpp -ld3d11 -ldxgi -ldxguid -ld3dcompiler -o native-host/build/owmc-world-blend-probe.dll
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & $blendCompiler @blendFlags -DOWMC_WORLD_BLEND native-host/tests/hand_depth_test.cpp -ld3d11 -ldxgi -ldxguid -ld3dcompiler -o native-host/build/owmc-hand-depth-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & native-host/build/owmc-hand-depth-test.exe
    exit $LASTEXITCODE
} finally {Pop-Location}
