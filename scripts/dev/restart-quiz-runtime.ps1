param([ValidateSet('fastapi','spring','metro')][string]$Service)
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
. (Join-Path $PSScriptRoot 'local-env.ps1')
$logDir = Join-Path $RepoRoot 'infra/local-runtime/logs'
$pidDir = Join-Path $RepoRoot 'infra/local-runtime/pids'
New-Item -ItemType Directory -Force -Path $logDir,$pidDir | Out-Null
$port = switch ($Service) { 'fastapi' {8000} 'spring' {8080} 'metro' {8081} }
$owners = @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique)
foreach ($ownerId in $owners) {
    $running = Get-CimInstance Win32_Process -Filter "ProcessId = $ownerId"
    $command = ([string]$running.CommandLine).Replace('\','/').ToLowerInvariant()
    $rootPattern = [regex]::Escape($RepoRoot.Replace('\','/').ToLowerInvariant())
    $expected = switch ($Service) { 'fastapi' {'uvicorn.*app\.main:app'} 'spring' {'business-api.*\.jar|com\.mathvisionkids\.api\.businessapiapplication'} 'metro' {'expo.*start'} }
    $verified = $command -match $rootPattern -and $command -match $expected
    if (-not $verified -and $Service -eq 'fastapi' -and $command -match $expected) {
        $parent = Get-CimInstance Win32_Process -Filter "ProcessId = $($running.ParentProcessId)"
        $parentCommand = ([string]$parent.CommandLine).Replace('\','/').ToLowerInvariant()
        $verified = $parent.Name -eq 'python.exe' -and $parentCommand -match ($rootPattern + '/ai/runtime/\.venv/scripts/python\.exe') -and $parent.CreationDate -le $running.CreationDate
    }
    if (-not $verified) { throw "PORT_CONFLICT: refusing to stop an unverified process on $port" }
    Stop-Process -Id $ownerId -ErrorAction Stop
    Write-Host "Stopped verified $Service PID $ownerId"
}
for ($attempt=0; $attempt -lt 30; $attempt++) {
    if (-not (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)) { break }
    Start-Sleep -Milliseconds 200
}
if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) { throw "Port $port was not released" }
if ($Service -eq 'fastapi') {
    $working = Join-Path $RepoRoot 'ai/runtime'
    Invoke-WithLocalSpeechTools -Action {
        $script:startedFastApi = Start-Process -FilePath (Join-Path $working '.venv/Scripts/python.exe') -ArgumentList '-m uvicorn app.main:app --host 127.0.0.1 --port 8000' -WorkingDirectory $working -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logDir 'fastapi-runtime.log') -RedirectStandardError (Join-Path $logDir 'fastapi-runtime.err.log') -PassThru
    }
    $process = $script:startedFastApi
} elseif ($Service -eq 'spring') {
    $working = Join-Path $RepoRoot 'backend/business-api'
    $allowed = @('DB_URL','DB_USERNAME','DB_PASSWORD','JWT_SECRET','JWT_EXPIRATION','UPLOAD_ROOT','CORS_ALLOWED_ORIGINS','MINIO_ENDPOINT','MINIO_ACCESS_KEY','MINIO_SECRET_KEY','MINIO_BUCKET','AI_GATEWAY_MODE','AI_SERVICE_URL','AI_SERVICE_BASE_URL','INTERNAL_API_KEY')
    Invoke-WithLocalEnvironment -Files @((Join-Path $RepoRoot '.env'),(Join-Path $working '.env')) -AllowedKeys $allowed -Action {
        $builtJar = Join-Path $working 'build/libs/business-api.jar'
        $digest = (Get-FileHash -LiteralPath $builtJar -Algorithm SHA256).Hash.Substring(0,16).ToLowerInvariant()
        $runtimeDir = Join-Path $working 'build/runtime'
        New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null
        $jarPath = Join-Path $runtimeDir "business-api-$digest.jar"
        if (-not (Test-Path -LiteralPath $jarPath)) { Copy-Item -LiteralPath $builtJar -Destination $jarPath }
        $script:startedSpring = Start-Process -FilePath 'java.exe' -ArgumentList "-Xms64m -Xmx512m -jar `"$jarPath`" --ai.gateway.mode=FASTAPI --spring.profiles.active=dev --server.address=0.0.0.0 --server.port=8080" -WorkingDirectory $working -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logDir 'spring-runtime.log') -RedirectStandardError (Join-Path $logDir 'spring-runtime.err.log') -PassThru
    }
    $process = $script:startedSpring
} else {
    $working = Join-Path $RepoRoot 'apps/student-mobile'
    $expo = Join-Path $RepoRoot 'node_modules/expo/bin/cli'
    $process = Start-Process -FilePath 'node.exe' -ArgumentList "`"$expo`" start --lan --go --port 8081 --clear --max-workers 2" -WorkingDirectory $working -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logDir 'student-metro-runtime.log') -RedirectStandardError (Join-Path $logDir 'student-metro-runtime.err.log') -PassThru
}
Set-Content -LiteralPath (Join-Path $pidDir "$Service.pid") -Value $process.Id
Write-Host "Started $Service PID $($process.Id) on $port; readiness still needs verification"
