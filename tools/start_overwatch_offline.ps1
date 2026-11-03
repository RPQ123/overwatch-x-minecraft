param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$owTaskRoot = [System.IO.Directory]::GetParent($PSScriptRoot).FullName
$owLab = Join-Path $owTaskRoot 'overwatch-2015\offline-lab'
$owExe = Join-Path $owLab 'GameClientApp.patched.exe'
$owReportFile = Join-Path $owTaskRoot 'research\overwatch-lab-preparation.json'
if (-not (Test-Path -LiteralPath $owExe)) { throw 'Prepare the research lab first.' }
$owReport = Get-Content -LiteralPath $owReportFile -Raw | ConvertFrom-Json
if ((Get-FileHash -LiteralPath $owExe -Algorithm SHA256).Hash.ToLowerInvariant() -ne $owReport.patched_sha256) {
    throw 'Research executable checksum changed; inspect before starting.'
}
$owPrincipal = [Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())
$owAdmin = $owPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]544)
if ($CheckOnly) {
    [pscustomobject]@{Executable=$owExe;ChecksumVerified=$true;Elevated=$owAdmin;NetworkRulesApplied=$false} | ConvertTo-Json
    exit 0
}
if (-not $owAdmin) {
    throw 'Elevated rights are needed to isolate this research executable with Windows Firewall.'
}
if (@(Get-NetFirewallProfile | Where-Object { -not $_.Enabled }).Count -gt 0) {
    throw 'A Windows Firewall profile is disabled; no modified client was started.'
}
if ((Get-Service -Name MpsSvc).Status -ne 'Running') {
    throw 'Windows Firewall service is not running; no modified client was started.'
}
$owPrograms = @($owExe)
$owPrograms += @(Get-ChildItem -LiteralPath (Join-Path $owLab 'ErrorReporting') -Recurse -Filter '*.exe' | Select-Object -ExpandProperty FullName)
$owRuleNames = @()
for ($owIndex = 0; $owIndex -lt $owPrograms.Count; $owIndex++) {
    foreach ($owDirection in @('Inbound','Outbound')) {
        $owRuleName = 'Codex-OW2015-Lab-' + $owIndex + '-' + $owDirection
        $owRuleNames += $owRuleName
        $owRule = Get-NetFirewallRule -Name $owRuleName -ErrorAction SilentlyContinue
        if ($owRule) {
            $owFilter = $owRule | Get-NetFirewallApplicationFilter
            if ($owFilter.Program -ne $owPrograms[$owIndex] -or $owRule.Action -ne 'Block' -or $owRule.Enabled -ne 'True') {
                throw ('Existing rule does not match the research lab: ' + $owRuleName)
            }
        } else {
            New-NetFirewallRule -Name $owRuleName -DisplayName $owRuleName -Program $owPrograms[$owIndex] `
                -Direction $owDirection -Action Block -Profile Any -Enabled True | Out-Null
        }
    }
}
foreach ($owRuleName in $owRuleNames) {
    $owActiveRule = Get-NetFirewallRule -PolicyStore ActiveStore -Name $owRuleName -ErrorAction SilentlyContinue
    if (-not $owActiveRule -or $owActiveRule.Enabled -ne 'True' -or $owActiveRule.Action -ne 'Block') {
        throw ('Research isolation rule is not active: ' + $owRuleName)
    }
}
$owProcess = Start-Process -FilePath $owExe -WorkingDirectory $owLab -WindowStyle Hidden -PassThru
[pscustomobject]@{ProcessId=$owProcess.Id;StartedAt=(Get-Date -Format o);Executable=$owExe;FirewallRules=$owRuleNames} |
    ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $owTaskRoot 'research\overwatch-offline-start.json') -Encoding utf8
Write-Output ('Offline research client process: ' + $owProcess.Id)
