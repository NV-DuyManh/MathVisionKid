# scripts/stop-all.ps1
$RepoRoot = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location $RepoRoot

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " MathVision Kids -- Stopping Local Stack" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

$PidDir = Join-Path $RepoRoot "runtime\pids"

# 1. Stop tracked PIDs safely
if (Test-Path $PidDir) {
    Get-ChildItem -Path $PidDir -Filter *.pid | ForEach-Object {
        $pidFile = $_.FullName
        $procName = $_.BaseName
        $procId = (Get-Content $pidFile -ErrorAction SilentlyContinue).Trim()
        if ($procId -and ($procId -match '^\d+$')) {
            Write-Host "Stopping $procName (PID: $procId)..."
            & taskkill /PID $procId /T /F 2>$null | Out-Null
        }
        Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    }
}

# 2. Check MathVision specific ports and terminate lingering processes
$PortsToCheck = @(8080, 8000, 5173)
foreach ($port in $PortsToCheck) {
    try {
        $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        foreach ($conn in $conns) {
            $p = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
            if ($p -and ($p.ProcessName -match "java|python|node|cmd")) {
                Write-Host "Releasing port $port (Process: $($p.ProcessName), PID: $($p.Id))..."
                & taskkill /PID $p.Id /T /F 2>$null | Out-Null
            }
        }
    } catch {}
}

# 3. Stop Celery workers (clean up any orphaned Celery child processes)
try {
    $celeryProcs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "celery_app worker" }
    foreach ($proc in $celeryProcs) {
        Write-Host "Stopping Celery worker process (PID: $($proc.ProcessId))..."
        & taskkill /PID $proc.ProcessId /T /F 2>$null | Out-Null
    }
} catch {}

# 4. Stop Docker Compose infrastructure
Write-Host "Stopping Docker Compose infrastructure..."
$ComposeFile = Join-Path $RepoRoot "services\business-api\docker-compose.yml"
& docker compose -f $ComposeFile stop postgres minio redis 2>$null | Out-Null

Write-Host "All MathVision Kids local services stopped." -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
