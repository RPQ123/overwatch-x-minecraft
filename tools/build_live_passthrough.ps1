param([switch]$NativeForegroundCandidate,[switch]$CameraKeyCandidate)
$ErrorActionPreference='Stop'
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    New-Item -ItemType Directory -Force -Path native-host/build | Out-Null
    if ($NativeForegroundCandidate -and $CameraKeyCandidate) {throw 'Select one candidate.'}
    $selectedVersion=[regex]::Match((Get-Content tools/native_compositor_version.py -Raw),'(?m)^VERSION=(\d+)\s*$')
    if (!$selectedVersion.Success) {throw 'No selected compositor version.'}
    $liveVersion=if ($CameraKeyCandidate) {33} elseif ($NativeForegroundCandidate) {32} else {[int]$selectedVersion.Groups[1].Value}
if ($liveVersion -notin @(31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51)) {throw 'Unsupported compositor build version.'}
    $liveOutput=Join-Path (Get-Location) "native-host/build/owmc-live-passthrough-v$liveVersion.dll"
    $liveExe=Join-Path (Get-Location) 'overwatch-2015/Overwatch Beta 0.8.0.24919/GameClientApp.patched.exe'
    foreach ($liveProcess in (Get-Process -Name 'GameClientApp.patched' -ErrorAction SilentlyContinue)) {
        if ($liveProcess.Path -ne $liveExe) {continue}
        foreach ($liveModule in $liveProcess.Modules) {
            if ($liveModule.FileName -eq $liveOutput) {
                throw 'Target compositor DLL is loaded. Complete normal session restoration/shutdown before rebuilding.'
            }
        }
    }
    $liveCompiler=(& (Join-Path $PSScriptRoot 'resolve_native_compiler.ps1'))
    $liveFlags=@('-std=c++17','-O2','-static','-Wall','-Wextra','-Werror')
    $moduleFlags=@("-DOWMC_LIVE_VERSION=$liveVersion")
    foreach ($liveFixture in @('tracer_viewmodel_lens','native_deadeye_input','hand_mask_trace','guest_body','host_pose')) {
        $liveFixtureOut=Join-Path (Get-Location) "native-host/build/$liveFixture-check.exe"
        & $liveCompiler @liveFlags "native-host/tests/$($liveFixture)_test.cpp" -o $liveFixtureOut
        if ($LASTEXITCODE) {exit $LASTEXITCODE}
        & $liveFixtureOut
        if ($LASTEXITCODE) {exit $LASTEXITCODE}
    }
    & $liveCompiler @liveFlags native-host/tests/native_deadeye_presentation_test.cpp -o native-host/build/native-deadeye-presentation-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & native-host/build/native-deadeye-presentation-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & $liveCompiler @liveFlags native-host/tests/native_slot_filter_test.cpp -o native-host/build/native-slot-filter-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & native-host/build/native-slot-filter-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & $liveCompiler @liveFlags native-host/tests/native_meter_display_test.cpp -o native-host/build/native-meter-display-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & native-host/build/native-meter-display-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & $liveCompiler @liveFlags native-host/tests/slot_input_policy_test.cpp -o native-host/build/slot-input-policy-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & native-host/build/slot-input-policy-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    if ($liveVersion -ge 32) {$moduleFlags+='-DOWMC_NATIVE_FOREGROUND_CANDIDATE'}
    if ($liveVersion -ge 33) {$moduleFlags+='-DOWMC_CAMERA_KEY_LIGHT'}
    & $liveCompiler @liveFlags native-host/tests/native_view_light_test.cpp -o native-host/build/native-view-light-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & native-host/build/native-view-light-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & $liveCompiler @liveFlags native-host/tests/native_frame_limit_test.cpp -o native-host/build/native-frame-limit-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & native-host/build/native-frame-limit-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & $liveCompiler @liveFlags native-host/tests/genji_viewmodel_lens_test.cpp -o native-host/build/genji-viewmodel-lens-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & native-host/build/genji-viewmodel-lens-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & $liveCompiler @liveFlags native-host/tests/live_world_blend_test.cpp native-host/src/live_world_blend.cpp native-host/src/frame_compositor.cpp -ld3d11 -ldxgi -ldxguid -ld3dcompiler -lgdi32 -o native-host/build/live-world-blend-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & native-host/build/live-world-blend-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & $liveCompiler @liveFlags @moduleFlags -DOWMC_LIVE_BLEND -shared native-host/src/pose_observer.cpp native-host/src/live_world_blend.cpp native-host/src/frame_compositor.cpp native-host/src/trace_layout.cpp -ld3d11 -ldxgi -ldxguid -ld3dcompiler -lgdi32 -o $liveOutput
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & $liveCompiler @liveFlags @moduleFlags -DOWMC_LIVE_BLEND native-host/tests/hand_depth_test.cpp -ld3d11 -ldxgi -ldxguid -ld3dcompiler -o native-host/build/owmc-hand-depth-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & native-host/build/owmc-hand-depth-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & $liveCompiler @liveFlags @moduleFlags -DOWMC_LIVE_BLEND -DOWMC_SELECTION_FIXTURE native-host/tests/hand_depth_test.cpp -ld3d11 -ldxgi -ldxguid -ld3dcompiler -o native-host/build/owmc-hand-depth-test.exe
    if ($LASTEXITCODE) {exit $LASTEXITCODE}
    & native-host/build/owmc-hand-depth-test.exe
    exit $LASTEXITCODE
} finally {Pop-Location}
