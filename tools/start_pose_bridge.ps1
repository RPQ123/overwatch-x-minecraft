$ErrorActionPreference = 'Stop'
$poseWorkspace = Split-Path -Parent $PSScriptRoot
$poseExpectedPaths = @(
    (Join-Path $poseWorkspace 'overwatch-2015\Overwatch Beta 0.8.0.24919\GameClientApp.patched.exe'),
    (Join-Path $poseWorkspace 'overwatch-2015\offline-lab\GameClientApp.patched.exe')
)
$poseProcesses = @(Get-CimInstance Win32_Process -Filter "Name='GameClientApp.patched.exe'" |
    Where-Object { $_.ExecutablePath -in $poseExpectedPaths })
if ($poseProcesses.Count -ne 1) {
    Write-Host 'Open exactly one workspace Overwatch research client and Minecraft, then start the bridge.'
    exit 1
}
Write-Host 'Connecting original research-game pose telemetry to the local Minecraft diagnostic mod. Ctrl+C stops the bridge.'
& python (Join-Path $PSScriptRoot 'observe_overwatch.py') --pid $poseProcesses[0].ProcessId --samples 0 --forward
exit $LASTEXITCODE
