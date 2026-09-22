# scripts/dev/start-student-metro.ps1
# Starts the Student Mobile Metro bundler in LAN mode in a dedicated visible console window
$ErrorActionPreference = "Stop"

$RepoRoot = if (Test-Path "$PSScriptRoot\..\..\package.json") {
    (Resolve-Path "$PSScriptRoot\..\..").Path
} else {
    (Resolve-Path "$PSScriptRoot\..").Path
}
Set-Location $RepoRoot

$PidDir = Join-Path $RepoRoot "infra\local-runtime\pids"
if (-not (Test-Path $PidDir)) { New-Item -ItemType Directory -Path $PidDir -Force | Out-Null }
$MetroPidFile = Join-Path $PidDir "student-metro.pid"

# Check if port 8081 is already running and identify the process
$portInUse = $false
$pidHoldingPort = $null

$netstatOutput = netstat -ano | Select-String "\s+TCP\s+.*:8081\s+.*\s+LISTENING\s+(\d+)"
if ($netstatOutput) {
    if ($netstatOutput.Matches.Groups.Count -ge 2) {
        $pidHoldingPort = $netstatOutput.Matches.Groups[1].Value
        $portInUse = $true
    }
}

if ($portInUse) {
    try {
        $proc = Get-Process -Id $pidHoldingPort
        $wmiProc = Get-CimInstance Win32_Process -Filter "ProcessId = $pidHoldingPort"
        $isMetro = $false
        
        if ($proc.ProcessName -match "node" -and $wmiProc.CommandLine -match "react-native|expo|metro") {
            $isMetro = $true
        }

        if ($isMetro) {
            Write-Host "  Student Metro is already running on port 8081 (PID: $pidHoldingPort)." -ForegroundColor Green
            exit 0
        } else {
            Write-Host "  PORT_CONFLICT: Port 8081 is occupied by a NON_METRO_PROCESS ($($proc.ProcessName), PID: $pidHoldingPort)." -ForegroundColor Red
            Write-Host "  Student Metro launcher exiting safely without killing the unrelated process." -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host "  PORT_CONFLICT: Port 8081 is occupied by an unknown process (PID: $pidHoldingPort)." -ForegroundColor Red
        Write-Host "  Student Metro launcher exiting safely." -ForegroundColor Red
        exit 1
    }
}

Write-Host "  Launching Student Metro in visible LAN terminal..." -ForegroundColor Cyan

# Launch in a visible cmd window so Expo's REAL LAN QR code is directly visible to the user
$windowTitle = "MathVision Kids - Student Mobile (Metro LAN)"
$proc = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c `"title $windowTitle && npm run start:device`"" `
    -WorkingDirectory (Join-Path $RepoRoot "apps\student-mobile") `
    -PassThru

if ($proc) {
    Set-Content -Path $MetroPidFile -Value $proc.Id -Force
    Write-Host "  Student Metro launched (PID: $($proc.Id), title: '$windowTitle')" -ForegroundColor Green
}

# Wait for Metro Bundler on port 8081 (up to 45s)
Write-Host "  Waiting for Metro Bundler to accept connections on port 8081..." -ForegroundColor Yellow
$metroReady = $false
for ($i = 0; $i -lt 45; $i++) {
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
    Write-Host "  WARN: Student Metro took longer than 45s to open port 8081. Check visible terminal." -ForegroundColor DarkYellow
    exit 0
}
