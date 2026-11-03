$ErrorActionPreference='Stop'
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    New-Item -ItemType Directory -Force -Path native-host/build | Out-Null
    $poseCompiler=(& (Join-Path $PSScriptRoot 'resolve_native_compiler.ps1'))
    $poseFlags=@('-std=c++17','-O2','-static','-Wall','-Wextra','-Werror')
    & $poseCompiler @poseFlags native-host/tests/host_pose_test.cpp -o native-host/build/host-pose-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & native-host/build/host-pose-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & $poseCompiler @poseFlags -shared native-host/tests/pose_atomic.cpp -o native-host/build/pose-atomic.dll
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & $poseCompiler @poseFlags -shared native-host/src/pose_observer.cpp native-host/src/trace_layout.cpp -ld3d11 -ldxgi -ldxguid -o native-host/build/owmc-pose-observer-v1.dll
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & $poseCompiler @poseFlags -DOWMC_POSE_OBSERVER native-host/tests/hand_depth_test.cpp -ld3d11 -ldxgi -ldxguid -ld3dcompiler -o native-host/build/owmc-hand-depth-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & native-host/build/owmc-hand-depth-test.exe
    exit $LASTEXITCODE
} finally {Pop-Location}
