$RepoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$PreviewState = Join-Path $RepoRoot 'infra\local-runtime\pc-preview'
$PreviewEnv = Join-Path $PreviewState '.env.preview'
$PreviewTunnelState = Join-Path $PreviewState 'tunnel.json'
$PreviewCompose = @('compose', '--project-name', 'mathvision-pc-preview', '--env-file', $PreviewEnv,
    '-f', (Join-Path $RepoRoot 'infra\production\compose.yml'),
    '-f', (Join-Path $RepoRoot 'infra\production\compose.pc-preview.yml'))

function Get-OwnedPreviewTunnel {
    param($State)
    if ($State.pid -notmatch '^\d+$') { throw 'Invalid preview tunnel PID state; no process was stopped.' }
    $process = Get-CimInstance Win32_Process -Filter "ProcessId = $($State.pid)"
    if (-not $process) { return $null }
    if ($process.ExecutablePath -ne $State.executable -or
        $process.CommandLine -notmatch '(?:^|\s)tunnel(?:\s|$)' -or
        $process.CommandLine -notmatch '--url\s+http://127\.0\.0\.1:18081(?:\s|$)' -or
        [string]$process.CreationDate.ToUniversalTime().Ticks -ne [string]$State.createdTicks) {
        throw 'Tunnel PID belongs to another process; no unrelated process was stopped.'
    }
    return $process
}

function Invoke-PreviewCompose {
    param([string[]]$ComposeArguments)
    & docker @PreviewCompose @ComposeArguments
    if ($LASTEXITCODE -ne 0) { throw 'The isolated PC preview Docker operation failed.' }
}

function Get-PreviewContainerTunnel {
    $containerId = (& docker @PreviewCompose ps -q cloudflared | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $containerId -notmatch '^[a-f0-9]{64}$') {
        throw 'The preview connection container is missing.'
    }
    $container = & docker inspect --format '{{json .State}}' $containerId | ConvertFrom-Json
    if ($LASTEXITCODE -ne 0 -or -not $container.Running) {
        throw 'The preview connection container is not running.'
    }
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        $log = & docker @PreviewCompose logs --no-color --since $container.StartedAt --tail 300 cloudflared | Out-String
        if ($LASTEXITCODE -ne 0) { throw 'Cannot read the current preview connection log.' }
        $addresses = [regex]::Matches($log, 'https://[a-z0-9-]+\.trycloudflare\.com\b')
        if ($addresses.Count) {
            return @{ containerId = $containerId; startedAt = $container.StartedAt; apiOrigin = $addresses[$addresses.Count - 1].Value }
        }
        Start-Sleep -Seconds 1
    }
    throw 'The container tunnel hostname was not ready; inspect the preview connection log.'
}

function Test-PreviewPublicApi {
    param([string]$ApiOrigin, [int]$Attempts = 18)
    if ($ApiOrigin -notmatch '^https://[a-z0-9-]+\.trycloudflare\.com$') { return $false }
    for ($attempt = 0; $attempt -lt $Attempts; $attempt++) {
        try {
            $health = Invoke-RestMethod -Uri "$ApiOrigin/actuator/health" -TimeoutSec 5
            if ($health.status -eq 'UP') { return $true }
        } catch {}
        if ($attempt + 1 -lt $Attempts) { Start-Sleep -Seconds 2 }
    }
    return $false
}
