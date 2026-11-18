# Discover installed compatible tools without changing the user's global PATH/JAVA_HOME.
function Get-MathVisionToolProbe {
    param([string]$FilePath, [string[]]$Arguments)
    $previousPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $output = & $FilePath @Arguments 2>$null
        if ($LASTEXITCODE -eq 0) { return ($output -join "`n").Trim() }
    } catch {} finally { $ErrorActionPreference = $previousPreference }
    return $null
}

function Get-MathVisionToolCandidates {
    param([string]$Name)
    $paths = @(Get-Command $Name -All -ErrorAction SilentlyContinue | ForEach-Object { $_.Source })
    if ($Name -eq 'node.exe') {
        foreach ($base in @($env:ProgramFiles, $env:LOCALAPPDATA)) {
            if ($base) { $paths += Join-Path $base 'nodejs/node.exe'; $paths += Join-Path $base 'Programs/nodejs/node.exe' }
        }
        if ($env:NVM_HOME -and (Test-Path -LiteralPath $env:NVM_HOME)) {
            $paths += @(Get-ChildItem -LiteralPath $env:NVM_HOME -Directory -ErrorAction SilentlyContinue |
                Sort-Object Name -Descending | ForEach-Object { Join-Path $_.FullName 'node.exe' })
        }
    } elseif ($Name -eq 'java.exe') {
        if ($env:JAVA_HOME) { $paths = @((Join-Path $env:JAVA_HOME 'bin/java.exe')) + $paths }
        foreach ($base in @($env:ProgramFiles, $(if ($env:LOCALAPPDATA) { Join-Path $env:LOCALAPPDATA 'Programs' }))) {
            if (-not $base) { continue }
            foreach ($vendor in @('Eclipse Adoptium', 'Java', 'Microsoft')) {
                $directory = Join-Path $base $vendor
                if (Test-Path -LiteralPath $directory) {
                    $paths += @(Get-ChildItem -LiteralPath $directory -Directory -ErrorAction SilentlyContinue |
                        Sort-Object Name -Descending | ForEach-Object { Join-Path $_.FullName 'bin/java.exe' })
                }
            }
        }
    } elseif ($Name -eq 'python.exe') {
        foreach ($base in @($env:LOCALAPPDATA, $env:ProgramFiles)) {
            if ($base) { $paths += Join-Path $base 'Programs/Python/Python312/python.exe'; $paths += Join-Path $base 'Python312/python.exe' }
        }
    } elseif ($Name -eq 'docker.exe') {
        foreach ($base in @($env:ProgramFiles, $env:LOCALAPPDATA)) {
            if ($base) {
                foreach ($suffix in @('Docker/Docker/resources/bin/docker.exe', 'Programs/Docker/Docker/resources/bin/docker.exe', 'Programs/DockerDesktop/resources/bin/docker.exe')) {
                    $paths += Join-Path $base $suffix
                }
            }
        }
    } elseif ($Name -eq 'git.exe') {
        foreach ($base in @($env:ProgramFiles, $env:LOCALAPPDATA)) {
            if ($base) { $paths += Join-Path $base 'Git/cmd/git.exe'; $paths += Join-Path $base 'Programs/Git/cmd/git.exe' }
        }
    }
    return @($paths | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) } | Select-Object -Unique)
}

function Use-MathVisionToolchain {
    foreach ($name in @('node.exe', 'java.exe', 'python.exe', 'docker.exe', 'git.exe')) {
        foreach ($candidate in @(Get-MathVisionToolCandidates $name)) {
            $directory = Split-Path -Parent $candidate
            $valid = $false
            if ($name -eq 'node.exe') {
                $text = Get-MathVisionToolProbe $candidate @('-p', 'process.versions.node')
                $version = $null
                $valid = [version]::TryParse($text, [ref]$version) -and
                    (($version.Major -eq 22 -and $version.Minor -ge 13) -or ($version.Major -eq 24 -and $version.Minor -ge 3) -or $version.Major -eq 26) -and
                    (Test-Path -LiteralPath (Join-Path $directory 'npm.cmd')) -and
                    ((Get-MathVisionToolProbe $candidate @('-p', 'process.arch')) -eq 'x64')
            } elseif ($name -eq 'java.exe') {
                $java = Get-MathVisionToolProbe $candidate @('--version')
                $javac = Get-MathVisionToolProbe (Join-Path $directory 'javac.exe') @('--version')
                $valid = ($java -match '^(?:openjdk|java) 21[.\s]') -and ($javac -match '^javac 21[.\s]')
                if ($valid) { $env:JAVA_HOME = Split-Path -Parent $directory }
            } elseif ($name -eq 'python.exe') {
                if ($candidate -match '[\\/]Microsoft[\\/]WindowsApps[\\/]') { continue }
                $valid = [bool](Get-MathVisionToolProbe $candidate @('-c', 'import sys; print(sys.executable); sys.exit(0 if sys.version_info[:2] == (3, 12) and sys.maxsize > 2**32 else 1)'))
            } else { $valid = [bool](Get-MathVisionToolProbe $candidate @('--version')) }
            if ($valid) {
                $parts = @($env:PATH -split ';' | Where-Object { $_ -and $_ -ne $directory })
                $env:PATH = (@($directory) + $parts) -join ';'
                break
            }
        }
    }
}
