[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'PC-Preview.Common.ps1')
if (Test-Path -LiteralPath $PreviewTunnelState) {
    $state = Get-Content -LiteralPath $PreviewTunnelState -Raw | ConvertFrom-Json
    if ($state.pid) {
        $process = Get-OwnedPreviewTunnel -State $state
        if ($process) { Stop-Process -Id $process.ProcessId -ErrorAction Stop }
    }
    Remove-Item -LiteralPath $PreviewTunnelState
}
if (Test-Path -LiteralPath $PreviewEnv) {
    # Named volumes intentionally survive; never use -v or a global Docker cleanup.
    Invoke-PreviewCompose -ComposeArguments @('down')
}
Write-Host 'PC preview stopped. Uploaded images, accounts and preview database are retained.'
