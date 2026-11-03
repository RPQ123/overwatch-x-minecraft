# 编译《ow x mc 启动器.exe》到指定目录（默认仓库根目录）。
param([string]$Output = '')
$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
$root = (Resolve-Path -LiteralPath (Join-Path $here '..\..')).Path
if (-not $Output) { $Output = $root }
$gpp = & (Join-Path $root 'tools\resolve_native_compiler.ps1') | Select-Object -Last 1
$bin = Split-Path -Parent $gpp
$gcc = Join-Path $bin 'gcc.exe'
$windres = Join-Path $bin 'windres.exe'
$build = Join-Path $root 'data\tmp\launcher-exe'
$null = New-Item -ItemType Directory -Force -Path $build
Push-Location $here
try {
    & $windres --codepage=65001 -O coff -i owmc_launcher.rc -o (Join-Path $build 'res.o')
    if ($LASTEXITCODE) { throw "windres 失败：$LASTEXITCODE" }
    $exe = Join-Path $build 'launcher.exe'
    & $gcc -O2 -municode -mwindows -static -s owmc_launcher.c (Join-Path $build 'res.o') -o $exe
    if ($LASTEXITCODE) { throw "gcc 失败：$LASTEXITCODE" }
} finally { Pop-Location }
$target = Join-Path $Output 'ow x mc 启动器.exe'
Copy-Item -LiteralPath $exe -Destination $target -Force
Write-Output $target
