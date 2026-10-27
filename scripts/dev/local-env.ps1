# Literal dotenv loading for a single child-service launch. Never evaluates file contents.
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
            [Environment]::SetEnvironmentVariable($key, $previous[$key], 'Process')
        }
    }
}
