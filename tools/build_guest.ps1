param([string[]]$Tasks = @('build'))
$ErrorActionPreference = 'Stop'
$guestRoot = Split-Path -Parent $PSScriptRoot
$guestPython = Join-Path $guestRoot '.venv\Scripts\python.exe'
$guestJavaJson = & $guestPython -B (Join-Path $guestRoot 'tools\modpack\config.py') --get java --json
if ($LASTEXITCODE -ne 0) { throw 'Unable to resolve configured Java runtime.' }
$guestJava = $guestJavaJson | ConvertFrom-Json
$env:JAVA_HOME = Split-Path -Parent (Split-Path -Parent $guestJava)
$env:GRADLE_USER_HOME = Join-Path $guestRoot 'tools\gradle-cache'
# Windows PowerShell turns javac's informational stderr into ErrorRecords.
# The native exit code decides success; deprecation notices must not abort it.
$guestPreviousErrorAction = $ErrorActionPreference
try {
    $ErrorActionPreference = 'Continue'
    & (Join-Path $guestRoot 'tools\gradle\gradle-8.10.2\bin\gradle.bat') -p (Join-Path $guestRoot 'guest') --console=plain --no-daemon @Tasks
    $guestExitCode = $LASTEXITCODE
}
finally { $ErrorActionPreference = $guestPreviousErrorAction }
exit $guestExitCode
