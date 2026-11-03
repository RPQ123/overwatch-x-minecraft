param([ValidateSet('owmc-movement-probe.dll','owmc-movement-probe-v2.dll')][string]$DllName='owmc-movement-probe-v2.dll')
$ErrorActionPreference='Stop'
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    & (& (Join-Path $PSScriptRoot 'resolve_native_compiler.ps1')) -std=c++17 -O2 -static -shared 'native-host/src/movement_probe.cpp' -o (Join-Path 'native-host/build' $DllName)
    if ($LASTEXITCODE) { exit $LASTEXITCODE }
    & (& (Join-Path $PSScriptRoot 'resolve_native_compiler.ps1')) -std=c++17 -static 'native-host/tests/movement_test.cpp' -o 'native-host/build/owmc-movement-test.exe'
    if ($LASTEXITCODE) { exit $LASTEXITCODE }
    & 'native-host/build/owmc-movement-test.exe' (Join-Path 'native-host/build' $DllName)
    exit $LASTEXITCODE
} finally { Pop-Location }
