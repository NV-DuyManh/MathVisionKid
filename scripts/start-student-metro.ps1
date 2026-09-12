# scripts/start-student-metro.ps1
# Starts the Student Mobile Metro bundler in LAN mode in a dedicated visible console window
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location $RepoRoot

$PidDir = Join-Path $RepoRoot "runtime\pids"
if (-not (Test-Path $PidDir)) { New-Item -ItemType Directory -Path $PidDir -Force | Out-Null }
$MetroPidFile = Join-Path $PidDir "student-metro.pid"

# Check if port 8081 is already running
$alreadyRunning = $false
try {
    $tcp = New-Object System.Net.Sockets.TcpClient
    $tcp.Connect("127.0.0.1", 8081)
    $alreadyRunning = $tcp.Connected
    $tcp.Close()
} catch {}

if ($alreadyRunning) {
    Write-Host "  Student Metro is already running on port 8081." -ForegroundColor Green
    exit 0
}

Write-Host "  Launching Student Metro in visible LAN terminal..." -ForegroundColor Cyan

# Launch in a visible cmd window so Expo's REAL LAN QR code is directly visible to the user
$windowTitle = "MathVision Kids - Student Mobile (Metro LAN)"
$proc = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c `"title $windowTitle && npm run start:device`"" `
    -WorkingDirectory $RepoRoot `
    -PassThru

if ($proc) {
    Set-Content -Path $MetroPidFile -Value $proc.Id -Force
    Write-Host "  Student Metro launched (PID: $($proc.Id), title: '$windowTitle')" -ForegroundColor Green
}

# Wait for Metro Bundler on port 8081 (up to 25s)
Write-Host "  Waiting for Metro Bundler to accept connections on port 8081..." -ForegroundColor Yellow
$metroReady = $false
for ($i = 0; $i -lt 25; $i++) {
    Start-Sleep -Seconds 1
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $tcp.Connect("127.0.0.1", 8081)
        if ($tcp.Connected) {
            $tcp.Close()
            $metroReady = $true
            break
        }
    } catch {}
}

if ($metroReady) {
    Write-Host "  Student Metro Bundler is READY on port 8081 (LAN mode)." -ForegroundColor Green
    exit 0
} else {
    Write-Host "  WARN: Student Metro took longer than 25s to open port 8081. Check visible terminal." -ForegroundColor DarkYellow
    exit 0
}
