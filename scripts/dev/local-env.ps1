# Literal dotenv loading for a single child-service launch. Never evaluates file contents.
function Invoke-WithLocalSpeechTools {
    param([scriptblock]$Action)
    $speechTools = Join-Path $PSScriptRoot '../../infra/local-runtime/tools/ffmpeg/bin'
    $previousPath = $env:PATH
    try {
        if (Test-Path -LiteralPath (Join-Path $speechTools 'ffmpeg.exe')) { $env:PATH = "$speechTools;$previousPath" }
        & $Action
    } finally { $env:PATH = $previousPath }
}

# The unified launcher binds the AI service to 8000. Do not let a generic PORT
# inherited from a shell or hosting tool override that service's settings.
function Invoke-WithLocalAiPort {
    param([scriptblock]$Action)
    $previousPort = [Environment]::GetEnvironmentVariable('PORT', 'Process')
    try {
        $env:PORT = '8000'
        & $Action
    } finally {
        if ($null -eq $previousPort) {
            Remove-Item -LiteralPath 'Env:PORT' -ErrorAction SilentlyContinue
        } else {
            [Environment]::SetEnvironmentVariable('PORT', $previousPort, 'Process')
        }
    }
}

function Invoke-WithLocalEnvironment {
    param(
        [string[]]$Files,
        [string[]]$AllowedKeys,
        [scriptblock]$Action
    )
    $values = @{}
    foreach ($file in $Files) {
        if (-not (Test-Path -LiteralPath $file)) { continue }
        $lineNumber = 0
        foreach ($line in [System.IO.File]::ReadAllLines($file)) {
            $lineNumber++
            if ($line -match '^\s*(#.*)?$') { continue }
            if ($line -notmatch '^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
                throw "Invalid dotenv syntax in $file at line $lineNumber (value withheld)."
            }
            $key = $matches[1]
            $value = $matches[2].Trim()
            if ($key -notin $AllowedKeys) { continue }
            if ($value.StartsWith('"') -or $value.StartsWith("'")) {
                $quote = $value.Substring(0, 1)
                if ($value.Length -lt 2 -or -not $value.EndsWith($quote)) {
                    throw "Unclosed dotenv quote in $file at line $lineNumber (value withheld)."
                }
                $value = $value.Substring(1, $value.Length - 2)
            } else {
                $value = ($value -replace '\s+#.*$', '').TrimEnd()
            }
            $values[$key] = $value
        }
    }
    $previous = @{}
    try {
        foreach ($key in $values.Keys) {
            # Explicit parent-process settings always win over dotenv files.
            $current = [Environment]::GetEnvironmentVariable($key, 'Process')
            if ($null -ne $current) { continue }
            $previous[$key] = $current
            [Environment]::SetEnvironmentVariable($key, $values[$key], 'Process')
        }
        & $Action
    } finally {
        foreach ($key in $previous.Keys) {
            # PowerShell can coerce null to an empty string in the .NET call.
            # Remove absent variables so the next scope can load them again.
            if ($null -eq $previous[$key]) {
                Remove-Item -LiteralPath ('Env:' + $key) -ErrorAction SilentlyContinue
            } else {
                [Environment]::SetEnvironmentVariable($key, $previous[$key], 'Process')
            }
        }
    }
}
