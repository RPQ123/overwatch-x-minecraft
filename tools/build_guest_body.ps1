$ErrorActionPreference='Stop'
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    $bodyCompiler=(& (Join-Path $PSScriptRoot 'resolve_native_compiler.ps1'))
    # PowerShell5 wraps native stderr as ErrorRecords. The compiler's exit
    # code decides failure; retain its complete diagnostics in build logs.
    $ErrorActionPreference='Continue'
    $bodyFlags=@('-std=c++17','-O2','-static','-Wall','-Wextra','-Werror')
    foreach($bodyTest in @('guest_body','body_fields','hero_camera_definition','native_flight','native_blink','local_bucket_compat','native_gameplay_view','native_state_lifetime','native_meter_display','native_deadeye_presentation','native_recall_completion','native_recall_ammo','native_wraith_completion','native_shadow_completion','native_weapon_slots','native_pickup_scrap','native_placement_actions','native_winston_actions','native_hero_audio_gain')) {
        & $bodyCompiler @bodyFlags "native-host/tests/${bodyTest}_test.cpp" -o "native-host/build/${bodyTest}-test.exe"
        if($LASTEXITCODE){exit $LASTEXITCODE}
        & "native-host/build/${bodyTest}-test.exe"
        if($LASTEXITCODE){exit $LASTEXITCODE}
    }
    $bodyVersion=[regex]::Match((Get-Content tools/native_body_version.py -Raw),'(?m)^VERSION=(\d+)\s*$')
    if (!$bodyVersion.Success) {throw 'No selected native logic owner version.'}
    $bodyOutput=Join-Path (Get-Location) "native-host/build/owmc-guest-body-v$($bodyVersion.Groups[1].Value).dll"
    foreach ($bodyProcess in (Get-Process -Name 'GameClientApp.patched' -ErrorAction SilentlyContinue)) {
        if ($bodyProcess.Path -ne (Join-Path (Get-Location) 'overwatch-2015/Overwatch Beta 0.8.0.24919/GameClientApp.patched.exe')) {continue}
        foreach ($bodyModule in $bodyProcess.Modules) {if ($bodyModule.FileName -eq $bodyOutput) {throw 'Logic owner DLL is loaded; normal restoration/stop required.'}}
    }
    & $bodyCompiler @bodyFlags -shared native-host/src/guest_body_probe.cpp -o $bodyOutput
    exit $LASTEXITCODE
} finally {Pop-Location}
