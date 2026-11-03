# Shared portable MinGW-w64 lookup. Do not depend on the previous PC's E: drive.
$ErrorActionPreference = 'Stop'
$compilerRoot = Split-Path -Parent $PSScriptRoot
if ($env:OWMC_CXX) {
    $compilerCandidate = $env:OWMC_CXX
} elseif (Test-Path (Join-Path $compilerRoot 'tools/mingw64/bin/g++.exe')) {
    $compilerCandidate = Join-Path $compilerRoot 'tools/mingw64/bin/g++.exe'
} elseif (Test-Path (Join-Path $env:LOCALAPPDATA 'OWMC/toolchains/mingw64/bin/g++.exe')) {
    $compilerCandidate = Join-Path $env:LOCALAPPDATA 'OWMC/toolchains/mingw64/bin/g++.exe'
} else {
    $compilerCommand = Get-Command g++.exe -ErrorAction SilentlyContinue
    if (-not $compilerCommand) {
        throw 'MinGW-w64 is missing. Place it in tools/mingw64 or set OWMC_CXX to g++.exe.'
    }
    $compilerCandidate = $compilerCommand.Source
}
if (-not (Test-Path -LiteralPath $compilerCandidate -PathType Leaf)) {
    throw "C++ compiler does not exist: $compilerCandidate"
}
$compilerPath = (Resolve-Path -LiteralPath $compilerCandidate).Path
$compilerTarget = & $compilerPath -dumpmachine
if ($LASTEXITCODE -or $compilerTarget -ne 'x86_64-w64-mingw32') {
    throw "A 64-bit Windows MinGW-w64 compiler is required; received: $compilerTarget"
}
$compilerPath
