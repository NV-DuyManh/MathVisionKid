# scripts/dev/start-student-metro.ps1
# Starts the Student Mobile Metro bundler in LAN mode in a dedicated visible console window
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot 'toolchain.ps1')
Use-MathVisionToolchain
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)

$RepoRoot = if (Test-Path "$PSScriptRoot\..\..\package.json") {
    (Resolve-Path "$PSScriptRoot\..\..").Path
} else {
    (Resolve-Path "$PSScriptRoot\..").Path
}
Set-Location $RepoRoot

$PidDir = Join-Path $RepoRoot "infra\local-runtime\pids"
if (-not (Test-Path $PidDir)) { New-Item -ItemType Directory -Path $PidDir -Force | Out-Null }
$MetroPidFile = Join-Path $PidDir "student-metro.pid"

. (Join-Path $PSScriptRoot 'local-ports.ps1')
$ports = Get-LocalPorts
$metroPort = Select-LocalPort -Name 'Student Metro' -Preferred $ports.metro -Default 8081 `
    -Reserved @($ports.spring, $ports.ai, $ports.portal, $ports.teacher, $ports.admin) -IsOwned {
        param($ownerId)
        $ownerId -eq (Get-TrackedMetroListener -Port $ports.metro -PidFile $MetroPidFile)
    }
$running = Get-TrackedMetroListener -Port $metroPort -PidFile $MetroPidFile
if ($running -and $ports.metroSpring -eq $ports.spring) {
    Write-Host "  Student Metro is already running on port $metroPort (PID: $running)." -ForegroundColor Green
    & node (Join-Path $RepoRoot 'scripts/dev/show-student-qr.cjs') $metroPort
    exit $LASTEXITCODE
}
if ($running) {
    $original = Get-Process -Id $running -ErrorAction SilentlyContinue
    if ($original -and $running -eq (Get-TrackedMetroListener -Port $metroPort -PidFile $MetroPidFile)) {
        Stop-Process -InputObject $original
        $original.WaitForExit(5000) | Out-Null
    }
    if (-not (Test-FreeLocalPort $metroPort)) { throw 'Metro could not reload the new API port.' }
}
$env:EXPO_PUBLIC_DEV_API_PORT = [string]$ports.spring
Write-Host "  Launching Student Metro in visible LAN terminal..." -ForegroundColor Cyan

# Launch in a visible cmd window so Expo's REAL LAN QR code is directly visible to the user
$windowTitle = "MathVision Kids - Student Mobile (Metro LAN)"
$proc = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/k `"title $windowTitle && npm run start:device -- --go --port $metroPort`"" `
    -WorkingDirectory (Join-Path $RepoRoot "apps\student-mobile") `
    -PassThru

if ($proc) {
    Set-Content -Path $MetroPidFile -Value $proc.Id -Force
    Write-Host "  Student Metro launched (PID: $($proc.Id), title: '$windowTitle')" -ForegroundColor Green
}

# Wait for this Metro process to own the selected listener.
Write-Host "  Waiting for Metro Bundler to accept connections on port $metroPort..." -ForegroundColor Yellow
$metroReady = $false
for ($i = 0; $i -lt 45; $i++) {
    Start-Sleep -Seconds 1
    if (Get-TrackedMetroListener -Port $metroPort -PidFile $MetroPidFile) {
        $metroReady = $true
        break
    }
}

if ($metroReady) {
    Write-Host "  Student Metro Bundler is READY on port $metroPort (LAN mode)." -ForegroundColor Green
    & node (Join-Path $RepoRoot 'scripts/dev/show-student-qr.cjs') $metroPort
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    $ports.metro = $metroPort
    $ports.metroSpring = $ports.spring
    Save-LocalPorts $ports
    exit 0
} else {
    Write-Host "  WARN: Student Metro took longer than 45s to open port $metroPort. Check visible terminal." -ForegroundColor DarkYellow
    exit 1
}
