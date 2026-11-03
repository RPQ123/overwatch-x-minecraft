$ErrorActionPreference='Stop'
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    $weaponTarget=Join-Path (Get-Location) 'native-host/build/owmc-weapon-gate-v11.dll'
    foreach($weaponProcess in Get-Process){
        try {$weaponModules=$weaponProcess.Modules}catch{continue}
        if($weaponModules | Where-Object {$_.FileName -ieq $weaponTarget}){throw 'Refusing to overwrite a mapped weapon DLL. Stop normally first.'}
    }
    $weaponCompiler=(& (Join-Path $PSScriptRoot 'resolve_native_compiler.ps1'))
    $weaponFlags=@('-std=c++17','-O2','-static','-Wall','-Wextra','-Werror')
    & $weaponCompiler @weaponFlags native-host/tests/weapon_gate_test.cpp -o native-host/build/weapon-gate-test.exe
    if($LASTEXITCODE){exit $LASTEXITCODE}
    & native-host/build/weapon-gate-test.exe
    if($LASTEXITCODE){exit $LASTEXITCODE}
    & $weaponCompiler @weaponFlags -shared native-host/src/weapon_gate_shared.cpp -o native-host/build/owmc-weapon-gate-v11.dll
    if($LASTEXITCODE){exit $LASTEXITCODE}
    & $weaponCompiler @weaponFlags native-host/tests/weapon_gate_shared_test.cpp -o native-host/build/owmc-weapon-gate-shared-test.exe
    if($LASTEXITCODE){exit $LASTEXITCODE}
    & native-host/build/owmc-weapon-gate-shared-test.exe
    if($LASTEXITCODE){exit $LASTEXITCODE}
    exit $LASTEXITCODE
} finally {Pop-Location}
