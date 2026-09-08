# scripts/restart-all.ps1
$RepoRoot = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location $RepoRoot

Write-Host "Restarting MathVision Kids Local Environment..." -ForegroundColor Cyan

& "$PSScriptRoot\stop-all.ps1"
Start-Sleep -Seconds 2
& "$PSScriptRoot\start-all.ps1"
exit $LASTEXITCODE
