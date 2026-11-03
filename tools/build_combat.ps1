param([string[]]$Tasks = @('build'))
$ErrorActionPreference = 'Stop'
$combatRoot = Split-Path -Parent $PSScriptRoot
$combatJava = Join-Path $combatRoot 'minecraft-1.21.1\runtime\java-runtime-delta\windows-x64\java-runtime-delta'
$env:JAVA_HOME = $combatJava
$env:GRADLE_USER_HOME = Join-Path $combatRoot 'tools\gradle-cache'
& (Join-Path $combatRoot 'tools\gradle\gradle-8.10.2\bin\gradle.bat') -p (Join-Path $combatRoot 'combat') --console=plain --no-daemon @Tasks
exit $LASTEXITCODE
