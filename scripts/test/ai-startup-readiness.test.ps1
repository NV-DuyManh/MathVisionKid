$ErrorActionPreference = 'Stop'
$launcher = Join-Path $PSScriptRoot '../dev/start-all.ps1'
$tokens = $null; $parseErrors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile($launcher, [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count) { throw 'Launcher does not parse' }
$budget = $ast.Find({ param($node)
    $node -is [Management.Automation.Language.AssignmentStatementAst] -and $node.Left.Extent.Text -eq '$authTimeoutSeconds'
}, $true)
$loop = $ast.Find({ param($node)
    $node -is [Management.Automation.Language.WhileStatementAst] -and $node.Extent.Text.Contains('/internal/v1/tutor/runtime')
}, $true)
$failure = $ast.Find({ param($node)
    $node -is [Management.Automation.Language.IfStatementAst] -and $node.Extent.Text.StartsWith('if (-not $authReady)')
}, $true)
if (-not $budget -or -not $loop -or -not $failure) { throw 'Authenticated startup probe was not found' }
$probe = [scriptblock]::Create(($budget.Extent.Text, $loop.Extent.Text, $failure.Extent.Text -join "`n"))

function Test-StartupProbe {
    param([int]$ReadyAt = 0, [int]$RejectedStatus = 0, [bool]$Exited = $false)
    $authReady = $false
    # Mock only elapsed time, HTTP and process state; execute the real launcher loop.
    $authWait = [PSCustomObject]@{ Elapsed = [PSCustomObject]@{ TotalSeconds = 0 } }
    $calls = [PSCustomObject]@{ Count = 0 }
    $FastApiLog = 'synthetic-fastapi.log'
    $aiUrl = 'http://127.0.0.1:8003'
    $TrackedProcesses = @([PSCustomObject]@{
        Name = 'FastAPI AI Runtime'; Process = [PSCustomObject]@{ HasExited = $Exited }; ErrLog = 'synthetic-fastapi.err.log'
    })
    function Start-Sleep { param($Milliseconds) $authWait.Elapsed.TotalSeconds += 10 }
    function Invoke-WebRequest {
        param($Uri, $Headers, $TimeoutSec, [switch]$UseBasicParsing)
        $calls.Count++
        if ($Uri -ne 'http://127.0.0.1:8003/internal/v1/tutor/runtime' -or
            $Headers['X-Internal-API-Key'] -ne 'synthetic-startup-key' -or -not $UseBasicParsing) {
            throw 'Probe lost the authenticated, non-interactive request'
        }
        if ($RejectedStatus -or $authWait.Elapsed.TotalSeconds -lt $ReadyAt) {
            $exception = [Exception]::new('synthetic-private-service-message')
            $exception | Add-Member -NotePropertyName Response -NotePropertyValue ([PSCustomObject]@{ StatusCode = $RejectedStatus })
            throw $exception
        }
        return [PSCustomObject]@{ StatusCode = 200 }
    }
    $message = ''
    try { . $probe } catch { $message = $_.Exception.Message }
    if ($message.Contains('synthetic-startup-key') -or $message.Contains('synthetic-private-service-message')) {
        throw 'A startup error disclosed private values'
    }
    return [PSCustomObject]@{ Ready = $authReady; Elapsed = $authWait.Elapsed.TotalSeconds; Calls = $calls.Count; Message = $message }
}

$previousKey = [Environment]::GetEnvironmentVariable('INTERNAL_API_KEY', 'Process')
try {
    $env:INTERNAL_API_KEY = 'synthetic-startup-key'
    $slow = Test-StartupProbe -ReadyAt 40
    if (-not $slow.Ready -or $slow.Elapsed -ne 40 -or $slow.Calls -ne 5 -or $slow.Message) {
        throw 'A healthy cold start after 30 seconds was rejected'
    }
    foreach ($status in @(401, 403)) {
        $rejected = Test-StartupProbe -RejectedStatus $status
        if ($rejected.Ready -or $rejected.Calls -ne 1 -or $rejected.Elapsed -ne 0 -or $rejected.Message -notlike 'AI internal authentication check failed.*') {
            throw "Authentication failure $status did not fail immediately"
        }
    }
    $dead = Test-StartupProbe -Exited $true
    if ($dead.Ready -or $dead.Calls -ne 0 -or $dead.Message -notlike 'AI runtime exited*') { throw 'Dead AI process was retried' }
    $stalled = Test-StartupProbe -ReadyAt 999
    if ($stalled.Ready -or $stalled.Elapsed -ne 120 -or $stalled.Message -notlike '*within 120 seconds*synthetic-fastapi.err.log*') {
        throw 'Unreachable AI did not stop at its bounded deadline with log guidance'
    }
    Write-Output 'PASS: cold start after 30s, immediate 401/403, early process exit, bounded timeout and redacted errors (5 scenarios).'
} finally {
    if ($null -eq $previousKey) { Remove-Item -LiteralPath 'Env:INTERNAL_API_KEY' -ErrorAction SilentlyContinue }
    else { [Environment]::SetEnvironmentVariable('INTERNAL_API_KEY', $previousKey, 'Process') }
}
