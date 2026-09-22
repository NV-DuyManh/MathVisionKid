# scripts/reset-local-data.ps1 (forwarder)
param (
    [switch]$Force
)
& "$PSScriptRoot\dev\reset-local-data.ps1" @PSBoundParameters
exit $LASTEXITCODE

