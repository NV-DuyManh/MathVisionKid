# Self-check ownership validation without launching or stopping any process.
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'PC-Preview.Common.ps1')
function Get-CimInstance { param($ClassName, $Filter) return $script:fixtureProcess }
$started = [datetime]'2026-10-09T00:00:00Z'
$state = @{ pid = 4242; executable = 'C:\preview\cloudflared.exe'; createdTicks = [string]$started.ToUniversalTime().Ticks }
$script:fixtureProcess = [pscustomobject]@{
    ProcessId = 4242; ExecutablePath = $state.executable; CreationDate = $started
    CommandLine = 'C:\preview\cloudflared.exe tunnel --no-autoupdate --url http://127.0.0.1:18081'
}
if (-not (Get-OwnedPreviewTunnel $state)) { throw 'Expected owned process was rejected.' }
foreach ($field in @('ExecutablePath', 'CreationDate', 'CommandLine')) {
    $original = $script:fixtureProcess.$field
    $script:fixtureProcess.$field = switch ($field) {
        ExecutablePath { 'C:\unrelated\program.exe' }
        CreationDate { $started.AddMinutes(1) }
        CommandLine { 'cloudflared.exe tunnel --url http://127.0.0.1:8000' }
    }
    $rejected = $false
    try { $null = Get-OwnedPreviewTunnel $state } catch { $rejected = $true }
    if (-not $rejected) { throw "Unrelated process $field was accepted." }
    $script:fixtureProcess.$field = $original
}
$script:fixtureProcess = $null
if (Get-OwnedPreviewTunnel $state) { throw 'A dead process must not be reused.' }
Write-Output 'PASS: owned process accepted; executable, recycled PID and target URL mismatches rejected; dead process not reused.'

# A live process alone is insufficient after sleep or a lost Quick Tunnel.
function Invoke-RestMethod {
    param($Uri, $TimeoutSec)
    $script:healthCalls++
    if ($Uri -ne 'https://test-preview.trycloudflare.com/actuator/health' -or $TimeoutSec -ne 5) { throw 'Unexpected health probe.' }
    if ($script:healthCalls -le $script:failUntil) { throw 'Network unavailable.' }
    return @{ status = $script:healthStatus }
}
function Start-Sleep { param($Seconds) }
foreach ($case in @(
    @{ FailUntil=0; Status='UP'; Expected=$true; Calls=1 },
    @{ FailUntil=2; Status='UP'; Expected=$true; Calls=3 },
    @{ FailUntil=9; Status='UP'; Expected=$false; Calls=3 },
    @{ FailUntil=0; Status='DOWN'; Expected=$false; Calls=3 }
)) {
    $script:healthCalls = 0
    $script:failUntil = $case.FailUntil
    $script:healthStatus = $case.Status
    if ((Test-PreviewPublicApi -ApiOrigin 'https://test-preview.trycloudflare.com' -Attempts 3) -ne $case.Expected -or
        $script:healthCalls -ne $case.Calls) { throw 'Public API readiness or retry bound failed.' }
}
$script:healthCalls = 0
foreach ($invalid in @('', 'http://test-preview.trycloudflare.com', 'https://localhost', 'https://test-preview.trycloudflare.com/path')) {
    if (Test-PreviewPublicApi -ApiOrigin $invalid) { throw 'An invalid public origin was accepted.' }
}
if ($script:healthCalls -ne 0) { throw 'An invalid public origin triggered a request.' }
Write-Output 'PASS: healthy API and delayed readiness accepted; unreachable, DOWN and invalid origins rejected with bounded retries.'

# Container state and logs are scoped to this Compose project and this start time.
function docker {
    $arguments = $args -join ' '
    $global:LASTEXITCODE = 0
    if ($arguments -match ' ps -q cloudflared$') {
        if ($arguments -notmatch '--project-name mathvision-pc-preview') { throw 'Wrong project scope.' }
        if ($script:containerMissing) { return '' }
        return ('b' * 64)
    }
    if ($arguments -match '^inspect ') {
        return (@{ Running = $script:containerRunning; StartedAt = '2026-10-10T12:00:00Z' } | ConvertTo-Json -Compress)
    }
    if ($arguments -match ' logs ') {
        if ($arguments -notmatch '--since 2026-10-10T12:00:00Z --tail 300 cloudflared$') { throw 'Old container logs were included.' }
        $script:containerLogCalls++
        if ($script:containerLogCalls -le $script:containerLogDelay) { return 'Waiting for connection' }
        return 'Current tunnel: https://current-container.trycloudflare.com'
    }
    throw 'Unexpected Docker command.'
}
foreach ($case in @(
    @{ Missing=$false; Running=$true; Delay=0; Rejected=$false; LogCalls=1 },
    @{ Missing=$false; Running=$true; Delay=2; Rejected=$false; LogCalls=3 },
    @{ Missing=$true; Running=$true; Delay=0; Rejected=$true; LogCalls=0 },
    @{ Missing=$false; Running=$false; Delay=0; Rejected=$true; LogCalls=0 },
    @{ Missing=$false; Running=$true; Delay=60; Rejected=$true; LogCalls=60 }
)) {
    $script:containerMissing = $case.Missing
    $script:containerRunning = $case.Running
    $script:containerLogDelay = $case.Delay
    $script:containerLogCalls = 0
    $rejected = $false
    try { $containerState = Get-PreviewContainerTunnel } catch { $rejected = $true }
    if ($rejected -ne $case.Rejected -or $script:containerLogCalls -ne $case.LogCalls) { throw 'Container readiness check failed.' }
    if (-not $rejected -and $containerState.apiOrigin -ne 'https://current-container.trycloudflare.com') { throw 'Incorrect current container origin.' }
}
Write-Output 'PASS: current container origin and delayed readiness accepted; missing, stopped and unready containers rejected; old log entries excluded.'
