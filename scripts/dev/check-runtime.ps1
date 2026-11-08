# Run diagnostics with the same scoped internal credential as the core launcher.
$ErrorActionPreference = 'Stop'
$RepoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
. (Join-Path $PSScriptRoot 'local-env.ps1')

$python = Join-Path $RepoRoot 'ai/runtime/.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $python)) { $python = 'python' }
$envFiles = @(
    (Join-Path $RepoRoot '.env'),
    (Join-Path $RepoRoot '.env.local'),
    (Join-Path $RepoRoot 'backend/business-api/.env'),
    (Join-Path $RepoRoot 'backend/business-api/.env.local')
)
$script:diagnosticExitCode = 1
Invoke-WithLocalEnvironment -Files $envFiles -AllowedKeys @('INTERNAL_API_KEY') -Action {
    Invoke-WithLocalAiPort -Action {
        & $python (Join-Path $RepoRoot 'tools/diagnostics/check_runtime.py')
        $script:diagnosticExitCode = $LASTEXITCODE
    }
}
exit $script:diagnosticExitCode
