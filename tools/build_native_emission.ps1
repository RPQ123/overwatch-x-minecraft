$ErrorActionPreference='Stop'
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    $emissionTarget=Join-Path (Get-Location) 'native-host/build/owmc-native-emission-v17.dll'
    foreach($emissionProcess in Get-Process){
        try {$emissionModules=$emissionProcess.Modules}catch{continue}
        if($emissionModules | Where-Object {$_.FileName -ieq $emissionTarget}){throw 'Refusing to overwrite a mapped emission DLL. Stop normally first.'}
    }
    $emissionCompiler=(& (Join-Path $PSScriptRoot 'resolve_native_compiler.ps1'))
    $emissionFlags=@('-std=c++17','-O2','-static','-Wall','-Wextra','-Werror')
    & $emissionCompiler @emissionFlags native-host/tests/native_barrage_motion_test.cpp -o native-host/build/native-barrage-motion-test.exe
    if($LASTEXITCODE){exit $LASTEXITCODE}
    & native-host/build/native-barrage-motion-test.exe
    if($LASTEXITCODE){exit $LASTEXITCODE}
    & $emissionCompiler @emissionFlags native-host/tests/native_emission_test.cpp -o native-host/build/native-emission-test.exe
    if($LASTEXITCODE){exit $LASTEXITCODE}
    & native-host/build/native-emission-test.exe
    if($LASTEXITCODE){exit $LASTEXITCODE}
    & $emissionCompiler @emissionFlags native-host/tests/native_beam_phase_test.cpp -o native-host/build/native-beam-phase-test.exe
    if($LASTEXITCODE){exit $LASTEXITCODE}
    & native-host/build/native-beam-phase-test.exe
    if($LASTEXITCODE){exit $LASTEXITCODE}
    & $emissionCompiler @emissionFlags native-host/tests/native_armory_test.cpp -o native-host/build/native-armory-test.exe
    if($LASTEXITCODE){exit $LASTEXITCODE}
    & native-host/build/native-armory-test.exe
    if($LASTEXITCODE){exit $LASTEXITCODE}
    & $emissionCompiler @emissionFlags native-host/tests/native_roadhog_test.cpp -o native-host/build/native-roadhog-test.exe
    if($LASTEXITCODE){exit $LASTEXITCODE}
    & native-host/build/native-roadhog-test.exe
    if($LASTEXITCODE){exit $LASTEXITCODE}
    & $emissionCompiler @emissionFlags -shared native-host/src/native_emission_probe.cpp -o native-host/build/owmc-native-emission-v17.dll
    if($LASTEXITCODE){exit $LASTEXITCODE}
    & $emissionCompiler @emissionFlags native-host/tests/native_emission_lifecycle_test.cpp -o native-host/build/owmc-emission-lifecycle-test.exe
    if($LASTEXITCODE){exit $LASTEXITCODE}
    & native-host/build/owmc-emission-lifecycle-test.exe
    exit $LASTEXITCODE
} finally {Pop-Location}
