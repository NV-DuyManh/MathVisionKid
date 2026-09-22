# scripts/dev/start-all.ps1
$ErrorActionPreference = "Stop"

$RepoRoot = if (Test-Path "$PSScriptRoot\..\..\package.json") {
    (Resolve-Path "$PSScriptRoot\..\..").Path
} else {
    (Resolve-Path "$PSScriptRoot\..").Path
}
Set-Location $RepoRoot

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " MathVision Kids -- Unified Local Launcher" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Repository root: $RepoRoot"

# Helper to run external commands with strict timeout to prevent indefinite startup hangs
function Invoke-CommandWithTimeout {
    param(
        [string]$FilePath,
        [string[]]$ArgumentList = @(),
        [int]$TimeoutSeconds = 5
    )

    $targetFile = $FilePath
    $targetArgs = $ArgumentList
    if ($FilePath -match '\.(cmd|bat)$' -or $FilePath -eq 'npm') {
        $targetFile = "cmd.exe"
        $targetArgs = @("/c", $FilePath) + $ArgumentList
    }

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $targetFile
    if ($targetArgs.Count -gt 0) {
        $psi.Arguments = $targetArgs -join ' '
    }
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $psi

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        if (-not $process.Start()) {
            return [PSCustomObject]@{
                Success    = $false
                TimedOut   = $false
                ExitCode   = -1
                Stdout     = ""
                Stderr     = "Failed to start process: $FilePath"
                DurationMs = $sw.ElapsedMilliseconds
            }
        }
    } catch {
        return [PSCustomObject]@{
            Success    = $false
            TimedOut   = $false
            ExitCode   = -1
            Stdout     = ""
            Stderr     = $_.Exception.Message
            DurationMs = $sw.ElapsedMilliseconds
        }
    }

    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()

    $completed = $process.WaitForExit($TimeoutSeconds * 1000)
    $sw.Stop()

    if ($completed) {
        $null = [System.Threading.Tasks.Task]::WaitAll(@($stdoutTask, $stderrTask), 1000)
        return [PSCustomObject]@{
            Success    = ($process.ExitCode -eq 0)
            TimedOut   = $false
            ExitCode   = $process.ExitCode
            Stdout     = $stdoutTask.Result.Trim()
            Stderr     = $stderrTask.Result.Trim()
            DurationMs = $sw.ElapsedMilliseconds
        }
    } else {
        try { $process.Kill() } catch {}
        return [PSCustomObject]@{
            Success    = $false
            TimedOut   = $true
            ExitCode   = -1
            Stdout     = ""
            Stderr     = "Command timed out after $TimeoutSeconds seconds"
            DurationMs = $sw.ElapsedMilliseconds
        }
    }
}

function Find-DockerDesktopPath {
    $candidates = @(
        (Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"),
        (if ($env:ProgramFilesX86) { Join-Path $env:ProgramFilesX86 "Docker\Docker\Docker Desktop.exe" }),
        (if (${env:ProgramFiles(x86)}) { Join-Path ${env:ProgramFiles(x86)} "Docker\Docker\Docker Desktop.exe" }),
        (Join-Path $env:LOCALAPPDATA "Programs\Docker\Docker\Docker Desktop.exe")
    )
    foreach ($p in $candidates) {
        if ($p -and (Test-Path $p)) { return $p }
    }
    return $null
}

function Test-DockerEngineReady {
    $res = Invoke-CommandWithTimeout -FilePath "docker" -ArgumentList @("version", "--format", "'{{.Server.Version}}'") -TimeoutSeconds 4
    if ($res.Success -and $res.Stdout) {
        $v = $res.Stdout.Trim("'`"")
        return @{ Ready = $true; Version = $v; Error = "" }
    }
    $errMsg = if ($res.TimedOut) { "Docker daemon probe timed out (>4s)" } else { $res.Stderr }
    return @{ Ready = $false; Version = ""; Error = $errMsg }
}

# 1. Dependency checks
Write-Host "`n[1/6] Checking required developer tools..." -ForegroundColor Yellow
$MissingDeps = @()

# [1/5] Docker CLI
$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCmd) {
    Write-Host "  [1/5] Docker CLI ............ MISSING" -ForegroundColor Red
    $MissingDeps += @{
        Tool   = "Docker CLI"
        Reason = "docker executable not found in PATH"
        Fix    = "Install Docker Desktop for Windows and ensure 'docker' is in system PATH."
    }
} else {
    $cliVer = Invoke-CommandWithTimeout -FilePath "docker" -ArgumentList @("--version") -TimeoutSeconds 3
    $verText = if ($cliVer.Success) { ($cliVer.Stdout.Split("`n")[0]) } else { "FOUND" }
    Write-Host "  [1/5] Docker CLI ............ FOUND ($verText)" -ForegroundColor Green
}

# [2/5] Docker Compose
if ($dockerCmd) {
    $composeRes = Invoke-CommandWithTimeout -FilePath "docker" -ArgumentList @("compose", "version") -TimeoutSeconds 3
    if ($composeRes.Success) {
        $compText = $composeRes.Stdout.Split("`n")[0]
        Write-Host "  [2/5] Docker Compose ....... FOUND ($compText)" -ForegroundColor Green
    } else {
        Write-Host "  [2/5] Docker Compose ....... MISSING" -ForegroundColor Red
        $MissingDeps += @{
            Tool   = "Docker Compose"
            Reason = "docker compose subcommand failed or timed out: $($composeRes.Stderr)"
            Fix    = "Update Docker Desktop to ensure Docker Compose v2 is installed."
        }
    }
} else {
    Write-Host "  [2/5] Docker Compose ....... SKIPPED (Docker CLI missing)" -ForegroundColor DarkYellow
}

# [3/5] Docker Engine Readiness
if ($dockerCmd) {
    $probe = Test-DockerEngineReady
    if ($probe.Ready) {
        Write-Host "  [3/5] Docker Engine ........ READY (Server v$($probe.Version))" -ForegroundColor Green
    } else {
        $ddProc = Get-Process -Name "*docker desktop*" -ErrorAction SilentlyContinue
        $ddPath = Find-DockerDesktopPath
        if (-not $ddProc -and $ddPath) {
            Write-Host "  [3/5] Docker Engine ........ STARTING (Launching Docker Desktop from: $ddPath)..." -ForegroundColor Yellow
            try {
                Start-Process -FilePath $ddPath
            } catch {
                Write-Host "  [3/5] Docker Engine ........ Failed to launch Docker Desktop: $($_.Exception.Message)" -ForegroundColor Red
            }
        } else {
            Write-Host "  [3/5] Docker Engine ........ WAITING (Engine not responding; waiting for readiness)..." -ForegroundColor Yellow
        }

        $engineReady = $false
        $maxWaitSeconds = 60
        $swWait = [System.Diagnostics.Stopwatch]::StartNew()
        while ($swWait.Elapsed.TotalSeconds -lt $maxWaitSeconds) {
            $remaining = [int]($maxWaitSeconds - $swWait.Elapsed.TotalSeconds)
            Write-Host -NoNewline "`r  [3/5] Docker Engine ........ WAITING ($remaining`s remaining)... "
            Start-Sleep -Seconds 2
            $probe = Test-DockerEngineReady
            if ($probe.Ready) {
                $engineReady = $true
                Write-Host "`r  [3/5] Docker Engine ........ READY (Server v$($probe.Version), took $([int]$swWait.Elapsed.TotalSeconds)s)        " -ForegroundColor Green
                break
            }
        }

        if (-not $engineReady) {
            Write-Host "`r  [3/5] Docker Engine ........ NOT READY (Timed out after $maxWaitSeconds`s)        " -ForegroundColor Red
            $MissingDeps += @{
                Tool   = "Docker Engine"
                Reason = "Docker daemon/engine did not respond within $maxWaitSeconds seconds."
                Fix    = "Start or restart Docker Desktop manually. Verify the engine icon in the system tray shows green/running."
            }
        }
    }
}

# [4/5] Java
$javaCmd = Get-Command java -ErrorAction SilentlyContinue
if (-not $javaCmd) {
    Write-Host "  [4/5] Java ................. MISSING" -ForegroundColor Red
    $MissingDeps += @{
        Tool   = "Java 21"
        Reason = "java executable not found in PATH"
        Fix    = "Install JDK 21 and configure JAVA_HOME in your environment variables."
    }
} else {
    $javaRes = Invoke-CommandWithTimeout -FilePath "java" -ArgumentList @("-version") -TimeoutSeconds 3
    $javaOut = if ($javaRes.Stderr) { $javaRes.Stderr } else { $javaRes.Stdout }
    $firstLine = if ($javaOut) { $javaOut.Split("`n")[0].Trim() } else { "java found" }
    Write-Host "  [4/5] Java ................. FOUND ($firstLine)" -ForegroundColor Green
}

# [5/5] Node / npm
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
$npmCmd = Get-Command npm -ErrorAction SilentlyContinue
if (-not $nodeCmd -or -not $npmCmd) {
    Write-Host "  [5/5] Node / npm ........... MISSING" -ForegroundColor Red
    if (-not $nodeCmd) {
        $MissingDeps += @{
            Tool   = "Node.js"
            Reason = "node executable not found in PATH"
            Fix    = "Install Node.js 20+ from https://nodejs.org/"
        }
    }
    if (-not $npmCmd) {
        $MissingDeps += @{
            Tool   = "npm"
            Reason = "npm executable not found in PATH"
            Fix    = "Ensure npm is installed and added to PATH alongside Node.js."
        }
    }
} else {
    $nodeRes = Invoke-CommandWithTimeout -FilePath "node" -ArgumentList @("--version") -TimeoutSeconds 3
    $npmRes = Invoke-CommandWithTimeout -FilePath "npm" -ArgumentList @("--version") -TimeoutSeconds 3
    $nodeVer = if ($nodeRes.Success) { $nodeRes.Stdout } else { "node found" }
    $npmVer = if ($npmRes.Success) { $npmRes.Stdout } else { "npm found" }
    Write-Host "  [5/5] Node / npm ........... FOUND (node $nodeVer, npm $npmVer)" -ForegroundColor Green
}

# Project Runtimes (Gradle wrapper & Python)
$GradlewPath = Join-Path $RepoRoot "backend\business-api\gradlew.bat"
if (-not (Test-Path $GradlewPath)) {
    $MissingDeps += @{
        Tool   = "Gradle wrapper"
        Reason = "backend/business-api/gradlew.bat not found"
        Fix    = "Ensure the repository was cloned completely including backend/business-api/gradlew.bat."
    }
}

$PyVenvExe = Join-Path $RepoRoot "ai\runtime\.venv\Scripts\python.exe"
if (Test-Path $PyVenvExe) {
    $pyRes = Invoke-CommandWithTimeout -FilePath $PyVenvExe -ArgumentList @("--version") -TimeoutSeconds 3
    $pyVer = if ($pyRes.Success) { $pyRes.Stdout } else { "Python venv" }
    Write-Host "  [+] Project Runtimes ....... FOUND (Gradle wrapper, $pyVer)" -ForegroundColor Green
} else {
    Write-Host "  [NOTICE] Python venv not found at ai/runtime/.venv. Falling back to system python." -ForegroundColor DarkYellow
    $PyVenvExe = "python"
    $pySys = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pySys) {
        $MissingDeps += @{
            Tool   = "Python"
            Reason = "Neither ai/runtime/.venv nor system python executable found"
            Fix    = "Set up python virtual environment in ai/runtime/.venv or install Python 3.10+ in PATH."
        }
    } else {
        Write-Host "  [+] Project Runtimes ....... FOUND (Gradle wrapper, system python)" -ForegroundColor Green
    }
}

if ($MissingDeps.Count -gt 0) {
    Write-Host "`n============================================" -ForegroundColor Red
    Write-Host " ERROR: Missing Required Developer Tools" -ForegroundColor Red
    Write-Host "============================================" -ForegroundColor Red
    foreach ($d in $MissingDeps) {
        Write-Host "  - Tool:   $($d.Tool)" -ForegroundColor Red
        Write-Host "    Reason: $($d.Reason)" -ForegroundColor DarkRed
        Write-Host "    Action: $($d.Fix)" -ForegroundColor Yellow
        Write-Host ""
    }
    exit 1
}
Write-Host "  All required developer tools detected.`n" -ForegroundColor Green

# 2. Runtime directories and stale PID cleanup
Write-Host "`n[2/6] Preparing runtime directories..." -ForegroundColor Yellow
$LogDir = Join-Path $RepoRoot "infra\local-runtime\logs"
$PidDir = Join-Path $RepoRoot "infra\local-runtime\pids"
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
$ComposeFile = Join-Path $RepoRoot "infra\docker\docker-compose.yml"
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
$SpringDir = Join-Path $RepoRoot "backend\business-api"
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
$AiDir = Join-Path $RepoRoot "ai\runtime"
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
$PortalDir = Join-Path $RepoRoot "apps\portal-web"
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
$TeacherDir = Join-Path $RepoRoot "apps\teacher-web"
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
$AdminDir = Join-Path $RepoRoot "apps\admin-web"
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
            Write-Host "Recommended fix: Inspect logs in infra/local-runtime/logs/ or run the service manually to see errors." -ForegroundColor Yellow
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
Write-Host "Logs:                infra\local-runtime\logs\"
Write-Host "Stop:                scripts\dev\stop-all.bat (or scripts\stop-all.bat)"
Write-Host "============================================" -ForegroundColor Cyan

exit $diagCode
