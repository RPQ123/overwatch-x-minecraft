param([switch]$Settings, [switch]$WaitForExit, [string]$ReadyEvent = '')
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$launcherRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$launcherTemporary = Join-Path $launcherRoot 'data\tmp'
$null = New-Item -ItemType Directory -Path $launcherTemporary -Force
function Write-LauncherLog([string]$Text) {
    $line = [DateTime]::UtcNow.ToString('O') + ' pid=' + $PID + ' ' + $Text + [Environment]::NewLine
    $stream = $null
    try {
        $stream = [System.IO.FileStream]::new((Join-Path $launcherTemporary 'launcher-powershell.log'),
            [System.IO.FileMode]::Append, [System.IO.FileAccess]::Write, [System.IO.FileShare]::ReadWrite)
        $bytes = [System.Text.UTF8Encoding]::new($false).GetBytes($line)
        $stream.Write($bytes, 0, $bytes.Length)
    } catch {
        # A simultaneous double-click must not turn diagnostic IO into a failed launch.
        try { [Console]::Error.WriteLine('启动日志写入失败：' + $_.Exception.Message) } catch { }
    } finally {
        if ($null -ne $stream) { $stream.Dispose() }
    }
}
$launcherProcess = $null
$launcherReady = $null
try {
Write-LauncherLog ('begin root=' + $launcherRoot + ' readyEvent=' + $ReadyEvent)
$launcherPython = Join-Path $launcherRoot '.venv\Scripts\python.exe'
$launcherPack = Join-Path $launcherRoot 'modpack.json'
if (Test-Path -LiteralPath $launcherPack -PathType Leaf) {
    if (-not (Test-Path -LiteralPath (Join-Path $launcherRoot 'manifest.json') -PathType Leaf)) {
        throw '整合包不完整：缺少 manifest.json。请保留此目录，并使用新版本号重新构建。'
    }
    $launcherPython = Join-Path $launcherRoot 'runtime\python\python.exe'
}
$launcherConfig = Join-Path $launcherRoot 'config\launcher.json'
if (Test-Path -LiteralPath $launcherConfig -PathType Leaf) {
    $launcherValues = Get-Content -LiteralPath $launcherConfig -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($launcherValues.schemaVersion -ne 1) { throw '启动器配置版本不受支持，请保留配置后查看说明。' }
    if ($launcherValues.paths.python) {
        $launcherPython = [string]$launcherValues.paths.python
        if (-not [System.IO.Path]::IsPathRooted($launcherPython)) {
            $launcherPython = Join-Path $launcherRoot $launcherPython
        }
        $launcherPython = [System.IO.Path]::GetFullPath($launcherPython)
    }
}
$launcherScript = Join-Path $launcherRoot 'tools\project_launcher.py'
if ($Settings) {
    $launcherScript = Join-Path $launcherRoot 'tools\configure_passthrough.py'
}
if (-not (Test-Path -LiteralPath $launcherPython -PathType Leaf)) {
    throw '缺少 Python 3.13 和 Tk。请使用包含便携运行时的完整整合包；开发仓库请先运行 tools/setup_environment.ps1。'
}
if (-not (Test-Path -LiteralPath $launcherScript -PathType Leaf)) {
    throw '缺少启动器脚本，请检查整合包文件清单。'
}
# This venv's pythonw.exe is a console redirector. CreateNoWindow prevents a
# console from being created at all, including a brief first-frame flash.
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:OWMC_NO_CONSOLE = '1'
$env:TEMP = $launcherTemporary
$env:TMP = $launcherTemporary
if ($ReadyEvent) { $env:OWMC_LAUNCH_READY_EVENT = $ReadyEvent }
else { Remove-Item Env:OWMC_LAUNCH_READY_EVENT -ErrorAction SilentlyContinue }
$launcherArguments = @('-u', ('"' + $launcherScript + '"'))
if ($Settings) {
    $launcherArguments += @('--gui', '--settings-owned')
}
$launcherStart = New-Object System.Diagnostics.ProcessStartInfo
$launcherStart.FileName = $launcherPython
$launcherStart.Arguments = $launcherArguments -join ' '
$launcherStart.WorkingDirectory = $launcherRoot
$launcherStart.UseShellExecute = $false
$launcherStart.CreateNoWindow = $true
$launcherProcess = New-Object System.Diagnostics.Process
$launcherProcess.StartInfo = $launcherStart
if (-not $launcherProcess.Start()) {
    throw '无法启动启动器进程，请检查整合包文件。'
}
Write-LauncherLog ('python-started pid=' + $launcherProcess.Id + ' interpreter=' + $launcherPython)
if ($ReadyEvent) {
    $launcherReady = [System.Threading.EventWaitHandle]::OpenExisting($ReadyEvent)
    $launcherTimer = [System.Diagnostics.Stopwatch]::StartNew()
    $launcherConfirmed = $false
    while ($launcherTimer.ElapsedMilliseconds -lt 20000) {
        if ($launcherReady.WaitOne(100)) { $launcherConfirmed = $true; break }
        if ($launcherProcess.HasExited) {
            throw ('启动器界面未就绪，Python 已退出：' + $launcherProcess.ExitCode)
        }
    }
    if (-not $launcherConfirmed) { throw '启动器界面 20 秒内未就绪，详细原因见 launcher-ui.log / ui-errors.log。' }
    Write-LauncherLog ('ui-ready pid=' + $launcherProcess.Id)
}
if ($WaitForExit) {
    $launcherProcess.WaitForExit()
    $launcherExitCode = $launcherProcess.ExitCode
    exit $launcherExitCode
}
} catch {
    Write-LauncherLog ('failed ' + $_.Exception.Message + ' at ' + $_.InvocationInfo.PositionMessage)
    exit 1
} finally {
    if ($null -ne $launcherReady) { $launcherReady.Dispose() }
    if ($null -ne $launcherProcess) { $launcherProcess.Dispose() }
}
