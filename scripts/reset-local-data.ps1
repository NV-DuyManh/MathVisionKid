# scripts/reset-local-data.ps1
param (
    [switch]$Force
)

$RepoRoot = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location $RepoRoot

Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "  WARNING: DESTRUCTIVE ACTION -- RESET LOCAL DEMO DATA" -ForegroundColor Red
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "This will stop the MathVision Kids local stack and DELETE:"
Write-Host "  - PostgreSQL database volume (mathvision db: classrooms, users, submissions)"
Write-Host "  - MinIO storage volume (mathvision bucket images)"
Write-Host "  - Redis transient cache volume"
Write-Host "  - Local upload directory (.data/uploads/)"
Write-Host "  - Transient runtime logs and PIDs"
Write-Host ""
Write-Host "NOTE: Only MathVision Kids volumes will be removed."
Write-Host "      Unrelated Docker volumes on your machine will NOT be touched."
Write-Host "============================================================" -ForegroundColor Yellow

if (-not $Force) {
    $confirmation = Read-Host "Are you sure you want to proceed? [Y/N]"
    if ($confirmation -notmatch "^[Yy]$") {
        Write-Host "Reset cancelled. No data was modified." -ForegroundColor Green
        exit 0
    }
}

Write-Host "`nStopping MathVision Kids local stack..." -ForegroundColor Cyan
& "$PSScriptRoot\stop-all.ps1"

Write-Host "`nRemoving MathVision Kids Docker volumes..." -ForegroundColor Cyan
$ComposeFile = Join-Path $RepoRoot "services\business-api\docker-compose.yml"
& docker compose -f $ComposeFile down -v
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to tear down Docker volumes." -ForegroundColor Red
    exit 1
}

Write-Host "`nCleaning local uploads..." -ForegroundColor Cyan
$UploadsDir = Join-Path $RepoRoot "services\business-api\.data\uploads"
if (Test-Path $UploadsDir) {
    Remove-Item -Path "$UploadsDir\*" -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "`nCleaning runtime logs and PIDs..." -ForegroundColor Cyan
$LogDir = Join-Path $RepoRoot "runtime\logs"
$PidDir = Join-Path $RepoRoot "runtime\pids"
if (Test-Path $LogDir) { Remove-Item -Path "$LogDir\*" -Recurse -Force -ErrorAction SilentlyContinue }
if (Test-Path $PidDir) { Remove-Item -Path "$PidDir\*" -Recurse -Force -ErrorAction SilentlyContinue }

Write-Host "`n============================================================" -ForegroundColor Green
Write-Host "MathVision Kids local demo data has been cleanly reset." -ForegroundColor Green
Write-Host "Run 'scripts\start-all.bat' to initialize a fresh environment." -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
exit 0
