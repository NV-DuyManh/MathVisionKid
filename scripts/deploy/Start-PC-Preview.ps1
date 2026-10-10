[CmdletBinding()]
param(
    [string]$OwnerEmail = '',
    [switch]$PublishWeb
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'PC-Preview.Common.ps1')

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Install and start Docker Desktop first.' }
$pythonPath = Join-Path $RepoRoot 'ai\runtime\.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { throw 'Python 3.12 or the existing AI runtime environment is required.' }
    $pythonPath = (& uv python find 3.12 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $pythonPath)) { throw 'Python 3.12 was not found.' }
}
$null = New-Item -ItemType Directory -Path $PreviewState -Force
$identity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
& icacls $PreviewState /inheritance:r /grant:r "${identity}:(OI)(CI)F" 'SYSTEM:(OI)(CI)F' | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Cannot protect the private preview configuration directory.' }
$initializationArgs = @((Join-Path $PSScriptRoot 'init_pc_preview.py'))
if ($OwnerEmail) { $initializationArgs += @('--owner-email', $OwnerEmail) }
& $pythonPath @initializationArgs
if ($LASTEXITCODE -ne 0) { throw 'Preview initialization failed. Existing configuration was preserved.' }
Invoke-PreviewCompose -ComposeArguments @('config', '--quiet')

$gatewayId = (& docker @PreviewCompose ps -q gateway | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Cannot inspect the existing preview gateway.' }
$listener = Get-NetTCPConnection -LocalPort 18081 -State Listen -ErrorAction SilentlyContinue
if ($listener -and -not $gatewayId) { throw 'Port 18081 is occupied by another service; it was not stopped.' }
Write-Host 'Starting the isolated PC preview stack; existing preview data is retained.'
if (Test-Path -LiteralPath $PreviewTunnelState) {
    $legacyState = Get-Content -LiteralPath $PreviewTunnelState -Raw | ConvertFrom-Json
    if ($legacyState.pid) {
        $legacyProcess = Get-OwnedPreviewTunnel -State $legacyState
        if ($legacyProcess) { Stop-Process -Id $legacyProcess.ProcessId -ErrorAction Stop }
    }
}
Invoke-PreviewCompose -ComposeArguments @('up', '-d', '--no-build', '--wait', '--wait-timeout', '240')

# Verify the owner only while provisioning, so a later password change does not break restarts.
$needsBootstrapCleanup = [bool](Select-String -LiteralPath $PreviewEnv -Pattern '^BOOTSTRAP_ADMIN_ENABLED=(?:"true"|true)$' -Quiet)
if ($needsBootstrapCleanup) {
    $credentials = Get-Content -LiteralPath (Join-Path $PreviewState 'owner-credentials.json') -Raw | ConvertFrom-Json
    try {
        $ownerLogin = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:18081/api/v1/auth/login' -ContentType 'application/json' `
            -Body (@{ email = $credentials.email; password = $credentials.password } | ConvertTo-Json -Compress) -TimeoutSec 30
        $owner = Invoke-RestMethod -Uri 'http://127.0.0.1:18081/api/v1/me' `
            -Headers @{ Authorization = "Bearer $($ownerLogin.accessToken)" } -TimeoutSec 30
        if ($owner.role -ne 'ADMIN') { throw 'The owner account is not an administrator.' }
    } catch { throw 'Private owner login could not be verified; bootstrap configuration was retained for recovery.' }
    & $pythonPath (Join-Path $PSScriptRoot 'init_pc_preview.py') --finish-bootstrap
    if ($LASTEXITCODE -ne 0) { throw 'Could not remove the one-time bootstrap credentials.' }
    Invoke-PreviewCompose -ComposeArguments @('up', '-d', '--no-build', '--no-deps', '--wait', '--wait-timeout', '180', 'backend')
}
$credentials = $null
$ownerLogin = $null
try {
    $health = Invoke-RestMethod -Uri 'http://127.0.0.1:18081/actuator/health' -TimeoutSec 15
    if ($health.status -ne 'UP') { throw 'Gateway is not healthy.' }
} catch { throw 'The private API gateway did not pass readiness.' }

$tunnelState = Get-PreviewContainerTunnel
if (-not (Test-PreviewPublicApi -ApiOrigin $tunnelState.apiOrigin -Attempts 3)) {
    Write-Host 'The container tunnel is unreachable. Restarting this preview service only.'
    Invoke-PreviewCompose -ComposeArguments @('restart', 'cloudflared')
    $tunnelState = Get-PreviewContainerTunnel
}
$tunnelState | ConvertTo-Json | Set-Content -LiteralPath $PreviewTunnelState -Encoding utf8
if ($tunnelState.apiOrigin -notmatch '^https://[a-z0-9-]+\.trycloudflare\.com$') { throw 'Invalid saved public API hostname.' }
if (-not (Test-PreviewPublicApi -ApiOrigin $tunnelState.apiOrigin)) {
    throw 'The public API is not reachable. No web publication was started; check Internet access and the private tunnel log, then run the launcher again.'
}
Write-Host "Public API origin: $($tunnelState.apiOrigin)"
Write-Host 'Keep this PC and Docker running while testing the website.'
if ($PublishWeb) {
    $publishScript = Join-Path $PSScriptRoot 'Publish-Vercel-Web.ps1'
    if (-not (Test-Path -LiteralPath $publishScript)) { throw 'The web publishing script is missing.' }
    & $publishScript -ApiOrigin $tunnelState.apiOrigin
} else {
    Write-Host 'Run Start-PC-Preview.ps1 -PublishWeb to rebuild the web apps for this API hostname.'
}
