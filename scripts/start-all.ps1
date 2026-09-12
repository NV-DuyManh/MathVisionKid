# scripts/start-all.ps1
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location $RepoRoot

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " MathVision Kids -- Unified Local Launcher" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Repository root: $RepoRoot"

# 1. Dependency checks
Write-Host "`n[1/6] Checking required developer tools..." -ForegroundColor Yellow
$MissingDeps = @()

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    $MissingDeps += "Docker CLI"
} else {
    $dockerVer = & docker version --format "{{.Server.Version}}" 2>$null
    if (-not $dockerVer) { $MissingDeps += "Docker daemon running" }
}

if (-not (Get-Command java -ErrorAction SilentlyContinue)) { $MissingDeps += "Java 21" }
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { $MissingDeps += "Node.js" }
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { $MissingDeps += "npm" }

$GradlewPath = Join-Path $RepoRoot "services\business-api\gradlew.bat"
if (-not (Test-Path $GradlewPath)) { $MissingDeps += "Gradle wrapper in services/business-api" }

$PyVenvExe = Join-Path $RepoRoot "services\ai-service\.venv\Scripts\python.exe"
if (-not (Test-Path $PyVenvExe)) {
    Write-Host "  [NOTICE] Python venv not found at services/ai-service/.venv. Falling back to system python." -ForegroundColor DarkYellow
    $PyVenvExe = "python"
}

if ($MissingDeps.Count -gt 0) {
    Write-Host "ERROR: Missing required dependencies:" -ForegroundColor Red
    foreach ($d in $MissingDeps) { Write-Host "  - $d" -ForegroundColor Red }
    exit 1
}
Write-Host "  All required developer tools detected." -ForegroundColor Green

# 2. Runtime directories and stale PID cleanup
Write-Host "`n[2/6] Preparing runtime directories..." -ForegroundColor Yellow
$LogDir = Join-Path $RepoRoot "runtime\logs"
$PidDir = Join-Path $RepoRoot "runtime\pids"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }
if (-not (Test-Path $PidDir)) { New-Item -ItemType Directory -Path $PidDir -Force | Out-Null }

# Clean up stale PID files
if (Test-Path $PidDir) {
    Get-ChildItem -Path $PidDir -Filter *.pid | ForEach-Object {
        $pidFile = $_.FullName
        $procId = (Get-Content $pidFile -ErrorAction SilentlyContinue).Trim()
        if ($procId -match '^\d+$') {
            $p = Get-Process -Id $procId -ErrorAction SilentlyContinue
            if (-not $p) {
                Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
            }
        } else {
            Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
        }
    }
}

# 3. Infrastructure (Docker Compose)
Write-Host "`n[3/6] Starting infrastructure (PostgreSQL, MinIO, Redis)..." -ForegroundColor Yellow
$ComposeFile = Join-Path $RepoRoot "services\business-api\docker-compose.yml"
& docker compose -f $ComposeFile up -d postgres minio redis
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to start docker-compose infrastructure." -ForegroundColor Red
    exit 1
}

# Wait for infrastructure readiness
Write-Host "  Waiting for infrastructure to accept connections..."
$infraReady = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    $pgOk = $false
    $minioOk = $false
    $redisOk = $false
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $tcp.Connect("127.0.0.1", 5432)
        $pgOk = $tcp.Connected
        $tcp.Close()
    } catch {}
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $tcp.Connect("127.0.0.1", 9000)
        $minioOk = $tcp.Connected
        $tcp.Close()
    } catch {}
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $tcp.Connect("127.0.0.1", 6379)
        $redisOk = $tcp.Connected
        $tcp.Close()
    } catch {}

    if ($pgOk -and $minioOk -and $redisOk) {
        $infraReady = $true
        break
    }
}

if (-not $infraReady) {
    Write-Host "WARN: Infrastructure took longer than 30s to initialize. Continuing..." -ForegroundColor DarkYellow
} else {
    Write-Host "  PostgreSQL, MinIO, and Redis are ready." -ForegroundColor Green
}

# Ensure MinIO bucket exists
try {
    & docker exec mathvision-minio mc alias set local http://127.0.0.1:9000 minioadmin minioadmin123 2>&1 | Out-Null
    & docker exec mathvision-minio mc mb --ignore-existing local/mathvision 2>&1 | Out-Null
} catch {}

# Global list of tracked launched services
$TrackedProcesses = [System.Collections.Generic.List[PSCustomObject]]::new()

# Helper function to start background process safely with tracking
function Start-TrackedService {
    param(
        [string]$Name,
        [string]$FilePath,
        [string]$ArgumentList,
        [string]$WorkingDirectory,
        [string]$LogFile,
        [string]$PidFile,
        [int]$PortCheck = 0
    )
    if ($PortCheck -gt 0) {
        $portOpen = $false
        try {
            $tcp = New-Object System.Net.Sockets.TcpClient
            $tcp.Connect("127.0.0.1", $PortCheck)
            $portOpen = $tcp.Connected
            $tcp.Close()
        } catch {}
        if ($portOpen) {
            Write-Host "  $Name is already running on port $PortCheck." -ForegroundColor Green
            return
        }
    }

    Write-Host "  Starting $Name..." -ForegroundColor Cyan
    $errLog = $LogFile -replace "\.log$", ".err.log"
    $proc = Start-Process -FilePath $FilePath `
        -ArgumentList $ArgumentList `
        -WorkingDirectory $WorkingDirectory `
        -RedirectStandardOutput $LogFile `
        -RedirectStandardError $errLog `
        -WindowStyle Hidden `
        -PassThru

    Set-Content -Path $PidFile -Value $proc.Id -Force
    Write-Host "  $Name launched (PID: $($proc.Id), log: $LogFile)" -ForegroundColor Green

    # Immediate early-exit check
    Start-Sleep -Milliseconds 600
    if ($proc.HasExited) {
        Write-Host "  ERROR: $Name exited immediately with exit code $($proc.ExitCode)!" -ForegroundColor Red
        Write-Host "    Stdout: $LogFile" -ForegroundColor Yellow
        Write-Host "    Stderr: $errLog" -ForegroundColor Yellow
        if (Test-Path $errLog) {
            $errTail = Get-Content $errLog -Tail 15 -ErrorAction SilentlyContinue
            if ($errTail) {
                Write-Host "    Stderr detail:" -ForegroundColor DarkRed
                $errTail | ForEach-Object { Write-Host "      $_" -ForegroundColor DarkRed }
            }
        }
        exit 1
    }

    $TrackedProcesses.Add([PSCustomObject]@{
        Name = $Name
        Process = $proc
        LogFile = $LogFile
        ErrLog = $errLog
    })
}

# 4. Start Application Services
Write-Host "`n[4/6] Starting application services..." -ForegroundColor Yellow

# A. Spring Boot
$SpringDir = Join-Path $RepoRoot "services\business-api"
$SpringPid = Join-Path $PidDir "spring.pid"
$SpringLog = Join-Path $LogDir "spring.log"
Start-TrackedService -Name "Spring Boot" `
    -FilePath "cmd.exe" `
    -ArgumentList '/c gradlew.bat bootRun --args="--ai.gateway.mode=FASTAPI --spring.profiles.active=dev"' `
    -WorkingDirectory $SpringDir `
    -LogFile $SpringLog `
    -PidFile $SpringPid `
    -PortCheck 8080

# B. FastAPI
$AiDir = Join-Path $RepoRoot "services\ai-service"
$FastApiPid = Join-Path $PidDir "fastapi.pid"
$FastApiLog = Join-Path $LogDir "fastapi.log"
$UvicornExe = Join-Path $AiDir ".venv\Scripts\uvicorn.exe"
if (-not (Test-Path $UvicornExe)) { $UvicornExe = "uvicorn" }
Start-TrackedService -Name "FastAPI AI Runtime" `
    -FilePath $UvicornExe `
    -ArgumentList "app.main:app --host 127.0.0.1 --port 8000" `
    -WorkingDirectory $AiDir `
    -LogFile $FastApiLog `
    -PidFile $FastApiPid `
    -PortCheck 8000

# C. Celery Worker
$CeleryPid = Join-Path $PidDir "celery.pid"
$CeleryLog = Join-Path $LogDir "celery.log"
$CeleryExe = Join-Path $AiDir ".venv\Scripts\celery.exe"
if (-not (Test-Path $CeleryExe)) { $CeleryExe = "celery" }
$celeryActive = $false
try {
    $res = & $PyVenvExe -c "from app.jobs.celery_app import celery_app; print(bool(celery_app.control.ping(timeout=1.0)))" 2>$null
    if ($res -match "True") { $celeryActive = $true }
} catch {}

if ($celeryActive) {
    Write-Host "  Celery Worker is already active." -ForegroundColor Green
} else {
    Start-TrackedService -Name "Celery Worker" `
        -FilePath $CeleryExe `
        -ArgumentList "-A app.jobs.celery_app worker --loglevel=info --pool=solo -n worker1@$env:COMPUTERNAME" `
        -WorkingDirectory $AiDir `
        -LogFile $CeleryLog `
        -PidFile $CeleryPid
}

# D. Unified Portal Web
$PortalDir = Join-Path $RepoRoot "portal-web"
$PortalPid = Join-Path $PidDir "portal-web.pid"
$PortalLog = Join-Path $LogDir "portal-web.log"
Start-TrackedService -Name "Unified Portal Web" `
    -FilePath "cmd.exe" `
    -ArgumentList "/c npm run dev" `
    -WorkingDirectory $PortalDir `
    -LogFile $PortalLog `
    -PidFile $PortalPid `
    -PortCheck 5172

# E. Teacher Web
$TeacherDir = Join-Path $RepoRoot "teacher-web"
$TeacherPid = Join-Path $PidDir "teacher-web.pid"
$TeacherLog = Join-Path $LogDir "teacher-web.log"
Start-TrackedService -Name "Teacher Web Portal" `
    -FilePath "cmd.exe" `
    -ArgumentList "/c npm run dev" `
    -WorkingDirectory $TeacherDir `
    -LogFile $TeacherLog `
    -PidFile $TeacherPid `
    -PortCheck 5173

# F. Admin Web
$AdminDir = Join-Path $RepoRoot "admin-web"
$AdminPid = Join-Path $PidDir "admin-web.pid"
$AdminLog = Join-Path $LogDir "admin-web.log"
Start-TrackedService -Name "Admin Web Portal" `
    -FilePath "cmd.exe" `
    -ArgumentList "/c npm run dev" `
    -WorkingDirectory $AdminDir `
    -LogFile $AdminLog `
    -PidFile $AdminPid `
    -PortCheck 5174

# 5. Wait for readiness with early-exit detection
Write-Host "`n[5/6] Waiting for application services readiness..." -ForegroundColor Yellow
$timeoutSeconds = 45
$startTime = Get-Date
$allReady = $false

while ((Get-Date) - $startTime -lt (New-TimeSpan -Seconds $timeoutSeconds)) {
    # Check if any child process died during startup
    foreach ($svc in $TrackedProcesses) {
        if ($svc.Process.HasExited) {
            Write-Host "`nERROR: $($svc.Name) (PID: $($svc.Process.Id)) terminated unexpectedly during startup (Exit code: $($svc.Process.ExitCode))!" -ForegroundColor Red
            Write-Host "  Stdout: $($svc.LogFile)" -ForegroundColor Yellow
            Write-Host "  Stderr: $($svc.ErrLog)" -ForegroundColor Yellow
            if (Test-Path $svc.ErrLog) {
                $errTail = Get-Content $svc.ErrLog -Tail 15 -ErrorAction SilentlyContinue
                if ($errTail) {
                    Write-Host "  Recent stderr output:" -ForegroundColor DarkRed
                    $errTail | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkRed }
                }
            }
            Write-Host "Recommended fix: Inspect logs in runtime/logs/ or run the service manually to see errors." -ForegroundColor Yellow
            exit 1
        }
    }

    Start-Sleep -Seconds 2
    $springUp = $false
    $fastapiUp = $false
    $portalUp = $false
    $teacherUp = $false
    $adminUp = $false
    try {
        $resp = Invoke-RestMethod -Uri "http://127.0.0.1:8080/actuator/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
        if ($resp.status -eq "UP") { $springUp = $true }
    } catch {}
    try {
        $resp = Invoke-RestMethod -Uri "http://127.0.0.1:8000/ready" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
        if ($resp.status -eq "ready") { $fastapiUp = $true }
    } catch {}
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:5172" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
        if ($resp.StatusCode -eq 200) { $portalUp = $true }
    } catch {}
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:5173" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
        if ($resp.StatusCode -eq 200) { $teacherUp = $true }
    } catch {}
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:5174" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
        if ($resp.StatusCode -eq 200) { $adminUp = $true }
    } catch {}

    if ($springUp -and $fastapiUp -and $portalUp -and $teacherUp -and $adminUp) {
        $allReady = $true
        break
    }
}

if (-not $allReady) {
    Write-Host "WARN: Some services did not report ready within ${timeoutSeconds}s." -ForegroundColor DarkYellow
}

# 6. Run Diagnostic
Write-Host "`n[6/6] Running system diagnostics..." -ForegroundColor Yellow
$DiagScript = Join-Path $RepoRoot "tools\diagnostics\check_runtime.py"
& $PyVenvExe $DiagScript
$diagCode = $LASTEXITCODE

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host " MathVision Kids -- Core Stack Services" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Unified Portal Web:  http://localhost:5172  <-- [MAIN ENTRY]"
Write-Host "Admin Web Portal:    http://localhost:5174"
Write-Host "Teacher Web Portal:  http://localhost:5173"
Write-Host "Student Mobile:      Metro LAN (launch via RUN_MATHVISION.bat)"
Write-Host "Spring Business API: http://127.0.0.1:8080"
Write-Host "FastAPI AI Runtime:  http://127.0.0.1:8000"
Write-Host "MinIO Web Console:   http://127.0.0.1:9001 (minioadmin / minioadmin123)"
Write-Host "Logs:                runtime\logs\"
Write-Host "Stop:                scripts\stop-all.bat"
Write-Host "============================================" -ForegroundColor Cyan

exit $diagCode
