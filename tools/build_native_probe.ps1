param([switch]$TestsOnly, [ValidateSet('owmc-render-probe.dll','owmc-render-probe-v2.dll','owmc-render-probe-v3.dll','owmc-render-probe-v4.dll','owmc-render-probe-v5.dll','owmc-render-probe-v6.dll','owmc-render-probe-v7.dll','owmc-render-probe-v8.dll','owmc-render-probe-v9.dll')][string]$DllName='owmc-render-probe-v9.dll')
$ErrorActionPreference = 'Stop'
$nativeRoot = Split-Path -Parent $PSScriptRoot
Push-Location $nativeRoot
try {
    New-Item -ItemType Directory -Path 'native-host/build' -Force | Out-Null
    $nativeCompiler=(& (Join-Path $PSScriptRoot 'resolve_native_compiler.ps1'))
    & $nativeCompiler -std=c++17 -static 'native-host/tests/projection_test.cpp' -o 'native-host/build/projection-test.exe'
    if ($LASTEXITCODE) { exit $LASTEXITCODE }
    & 'native-host/build/projection-test.exe'
    if ($LASTEXITCODE) { exit $LASTEXITCODE }
    & $nativeCompiler -std=c++17 -static 'native-host/tests/scene_projection_test.cpp' -o 'native-host/build/scene-projection-test.exe'
    if ($LASTEXITCODE) { exit $LASTEXITCODE }
    & 'native-host/build/scene-projection-test.exe'
    if ($LASTEXITCODE) { exit $LASTEXITCODE }
    & $nativeCompiler -std=c++17 -static 'native-host/tests/mesh_test.cpp' -o 'native-host/build/mesh-test.exe'
    if ($LASTEXITCODE) { exit $LASTEXITCODE }
    & 'native-host/build/mesh-test.exe'
    if ($LASTEXITCODE) { exit $LASTEXITCODE }
    & $nativeCompiler -std=c++17 -static 'native-host/tests/patch_test.cpp' -o 'native-host/build/patch-test.exe'
    if ($LASTEXITCODE) { exit $LASTEXITCODE }
    & 'native-host/build/patch-test.exe'
    if ($LASTEXITCODE) { exit $LASTEXITCODE }
    & $nativeCompiler -std=c++17 -static 'native-host/tests/collision_test.cpp' -o 'native-host/build/collision-test.exe'
    if ($LASTEXITCODE) { exit $LASTEXITCODE }
    & 'native-host/build/collision-test.exe'
    if ($LASTEXITCODE) { exit $LASTEXITCODE }
    & $nativeCompiler -std=c++17 -static 'native-host/tests/creative_motion_test.cpp' -o 'native-host/build/creative-motion-test.exe'
    if ($LASTEXITCODE) { exit $LASTEXITCODE }
    & 'native-host/build/creative-motion-test.exe'
    if ($LASTEXITCODE) { exit $LASTEXITCODE }
    & $nativeCompiler -std=c++17 -static 'native-host/tests/native_collision_test.cpp' 'native-host/src/native_collision.cpp' -o 'native-host/build/owmc-collision-test.exe'
    if ($LASTEXITCODE) { exit $LASTEXITCODE }
    & 'native-host/build/owmc-collision-test.exe'
    if ($LASTEXITCODE) { exit $LASTEXITCODE }
    if (-not $TestsOnly) {
        & $nativeCompiler -std=c++17 -O2 -static -shared 'native-host/src/plugin.cpp' 'native-host/src/render.cpp' 'native-host/src/trace_layout.cpp' 'native-host/src/native_collision.cpp' -ld3d11 -ldxgi -ldxguid -ld3dcompiler -o (Join-Path 'native-host/build' $DllName)
        if ($LASTEXITCODE) { exit $LASTEXITCODE }
    }
    & $nativeCompiler -std=c++17 -static 'native-host/tests/gpu_test.cpp' 'native-host/src/render.cpp' -ld3d11 -ldxgi -ldxguid -ld3dcompiler -o 'native-host/build/gpu-test.exe'
    if ($LASTEXITCODE) { exit $LASTEXITCODE }
    & 'native-host/build/gpu-test.exe' 'native-host/build/stone-mesh.bin'
    if ($LASTEXITCODE) { exit $LASTEXITCODE }
    & $nativeCompiler -std=c++17 -static 'native-host/tests/host_test.cpp' -ld3d11 -ldxgi -ldxguid -ld3dcompiler -o 'native-host/build/owmc-host-test.exe'
    if ($LASTEXITCODE) { exit $LASTEXITCODE }
    & 'native-host/build/owmc-host-test.exe' (Join-Path 'native-host/build' $DllName)
    exit $LASTEXITCODE
} finally { Pop-Location }
