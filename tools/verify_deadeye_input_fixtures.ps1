param([string]$OutputDirectory = '')
$ErrorActionPreference = 'Stop'
$fixtureRoot = Split-Path -Parent $PSScriptRoot
if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $fixtureRoot ('research\deadeye-input-lock-20261023\fixtures-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
}
$fixtureOut = [IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Force -Path $fixtureOut | Out-Null
$fixtureResults = [Collections.Generic.List[object]]::new()
function Invoke-Fixture([string]$Name, [string]$Executable, [string[]]$Arguments) {
    $fixtureLog = Join-Path $fixtureOut ($Name + '.log')
    & $Executable @Arguments *> $fixtureLog
    $fixtureCode = $LASTEXITCODE
    $fixtureResults.Add([pscustomobject]@{name=$Name; exitCode=$fixtureCode; passed=($fixtureCode -eq 0); log=$fixtureLog})
    if ($fixtureCode) {throw "$Name failed ($fixtureCode); see $fixtureLog"}
}
Push-Location $fixtureRoot
try {
    $fixtureCompiler = & (Join-Path $PSScriptRoot 'resolve_native_compiler.ps1')
    $fixtureFlags = @('-std=c++17','-O2','-static','-Wall','-Wextra','-Werror')
    foreach ($fixtureName in @('native_deadeye_input','guest_body','slot_input_policy','native_slot_filter','host_pose','hand_mask_trace')) {
        $fixtureSource = Join-Path $fixtureRoot ("native-host\tests\${fixtureName}_test.cpp")
        $fixtureExe = Join-Path $fixtureOut ($fixtureName + '-test.exe')
        Invoke-Fixture ($fixtureName + '-compile') $fixtureCompiler ($fixtureFlags + @($fixtureSource,'-o',$fixtureExe))
        Invoke-Fixture ($fixtureName + '-run') $fixtureExe @()
    }
    # Compile only: no DLL, JAR, installed artifact or live callback is changed.
    Invoke-Fixture 'pose-observer-syntax' $fixtureCompiler ($fixtureFlags + @('-fsyntax-only','-DOWMC_LIVE_VERSION=41','-DOWMC_LIVE_BLEND','-DOWMC_NATIVE_FOREGROUND_CANDIDATE','-DOWMC_CAMERA_KEY_LIGHT','native-host/src/pose_observer.cpp'))
    $fixtureJavaHome = Join-Path $fixtureRoot 'minecraft-1.21.1\runtime\java-runtime-delta\windows-x64\java-runtime-delta'
    $fixtureJars = @((Join-Path $fixtureRoot 'minecraft-1.21.1\libraries\net\java\dev\jna\jna\5.14.0\jna-5.14.0.jar'),
                     (Join-Path $fixtureRoot 'minecraft-1.21.1\libraries\org\joml\joml\1.10.5\joml-1.10.5.jar')) -join ';'
    $fixtureClasses = Join-Path $fixtureOut 'classes'
    New-Item -ItemType Directory -Force -Path $fixtureClasses | Out-Null
    $fixtureSources = @('guest/src/main/java/lab/owmcguest/NativeDeadeyeEvents.java',
                       'guest/src/main/java/lab/owmcguest/NativeDeadeyeInputLock.java',
                       'guest/src/main/java/lab/owmcguest/NativeDashPhase.java',
                       'guest/src/main/java/lab/owmcguest/NativeRollPhase.java',
                       'guest/src/client/java/lab/owmcguest/HostPoseReader.java',
                       'guest/src/test/java/lab/owmcguest/NativeDeadeyeEventsCheck.java',
                       'guest/src/test/java/lab/owmcguest/NativeDeadeyeInputLockCheck.java',
                       'guest/src/test/java/lab/owmcguest/NativeRollCheck.java',
                       'guest/src/test/java/lab/owmcguest/HostPoseCheck.java')
    Invoke-Fixture 'java-compile' (Join-Path $fixtureJavaHome 'bin\javac.exe') (@('-encoding','UTF-8','-cp',$fixtureJars,'-d',$fixtureClasses) + $fixtureSources)
    foreach ($fixtureMain in @('NativeDeadeyeEventsCheck','NativeDeadeyeInputLockCheck','NativeRollCheck','HostPoseCheck')) {
        Invoke-Fixture $fixtureMain (Join-Path $fixtureJavaHome 'bin\java.exe') @('-cp',($fixtureClasses + ';' + $fixtureJars),('lab.owmcguest.' + $fixtureMain))
    }
}
finally {
    Pop-Location
    $fixtureReport = [pscustomobject]@{fixtureOnly=$true; gameInputSent=$false; productionArtifactWritten=$false; output=$fixtureOut; steps=$fixtureResults}
    $fixtureReport | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $fixtureOut 'result.json') -Encoding utf8
}
Write-Output $fixtureOut
