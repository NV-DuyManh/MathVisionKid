param([switch]$CheckOnly)

$ErrorActionPreference = 'Stop'

function Get-SetupProbe {
    param([string]$FilePath, [string[]]$Arguments = @())
    try {
        $output = & $FilePath @Arguments 2>$null
        if ($LASTEXITCODE -eq 0) { return ($output -join "`n").Trim() }
    } catch {}
    return $null
}

function Invoke-SetupCommand {
    param([string]$FilePath, [string[]]$Arguments = @())
    # Windows PowerShell 5.1 treats some ordinary native stderr as ErrorRecords.
    $previousPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & $FilePath @Arguments | Out-Host
        $commandExit = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousPreference
    }
    if ($commandExit -ne 0) {
        throw "Command failed with exit code $commandExit ($FilePath). Fix the error above, then run SETUP_MATHVISION.bat again."
    }
}

function Get-SetupTools {
    param([string]$RepoRoot)
    $tools = [ordered]@{ Git = $false; Node = $false; Python = $null; Java = $false; Docker = $false }
    if (Get-Command git.exe -ErrorAction SilentlyContinue) {
        $tools.Git = [bool](Get-SetupProbe git.exe @('--version'))
    }
    if ((Get-Command node.exe -ErrorAction SilentlyContinue) -and (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
        $versionText = Get-SetupProbe node.exe @('-p', 'process.versions.node')
        $version = $null
        if ([version]::TryParse($versionText, [ref]$version)) {
            $tools.Node = (($version.Major -eq 22 -and $version.Minor -ge 13) -or
                           ($version.Major -eq 24 -and $version.Minor -ge 3) -or $version.Major -eq 26) -and
                          [bool](Get-SetupProbe npm.cmd @('--version'))
        }
    }
    $pythonCheck = 'import sys; print(sys.executable); sys.exit(0 if sys.version_info[:2] == (3, 12) and sys.maxsize > 2**32 else 1)'
    $venvPython = Join-Path $RepoRoot 'ai/runtime/.venv/Scripts/python.exe'
    $candidates = @(
        @{ File = $venvPython; Args = @('-c', $pythonCheck) },
        @{ File = 'py.exe'; Args = @('-3.12', '-c', $pythonCheck) },
        @{ File = 'python.exe'; Args = @('-c', $pythonCheck) }
    )
    foreach ($candidate in $candidates) {
        $command = Get-Command $candidate.File -ErrorAction SilentlyContinue
        if (-not $command) { continue }
        # An unconfigured Windows Store alias can open the Store instead of Python.
        if ($candidate.File -eq 'python.exe' -and $command.Source -match '[\\/]Microsoft[\\/]WindowsApps[\\/]') { continue }
        $python = Get-SetupProbe $candidate.File $candidate.Args
        if ($python -and (Test-Path -LiteralPath $python -PathType Leaf)) {
            $tools.Python = $python
            break
        }
    }
    $java = Get-SetupProbe java.exe @('--version')
    $javac = Get-SetupProbe javac.exe @('--version')
    $tools.Java = ($java -match '^(?:openjdk|java) 21[.\s]') -and ($javac -match '^javac 21[.\s]')
    if ($env:JAVA_HOME) {
        $javaHomeVersion = Get-SetupProbe (Join-Path $env:JAVA_HOME 'bin/java.exe') @('--version')
        $tools.Java = $tools.Java -and ($javaHomeVersion -match '^(?:openjdk|java) 21[.\s]')
    }
    $tools.Docker = [bool](Get-SetupProbe docker.exe @('--version')) -and
                    [bool](Get-SetupProbe docker.exe @('compose', 'version'))
    return $tools
}

function Update-SetupEnvironment {
    $machinePath = [Environment]::GetEnvironmentVariable('PATH', 'Machine')
    $userPath = [Environment]::GetEnvironmentVariable('PATH', 'User')
    $env:PATH = "$machinePath;$userPath;$env:PATH"
    $javaHome = [Environment]::GetEnvironmentVariable('JAVA_HOME', 'User')
    if (-not $javaHome) { $javaHome = [Environment]::GetEnvironmentVariable('JAVA_HOME', 'Machine') }
    if ($javaHome) { $env:JAVA_HOME = $javaHome }
}

function Install-SetupTool {
    param([string]$PackageId)
    if (-not (Get-Command winget.exe -ErrorAction SilentlyContinue)) {
        throw "Missing $PackageId. Install Microsoft App Installer (WinGet), or the prerequisite listed in docs/LOCAL_SETUP.md, then run setup again."
    }
    Write-Host "Installing missing prerequisite $PackageId. Windows may ask for permission or license acceptance." -ForegroundColor Yellow
    Invoke-SetupCommand winget.exe @('install', '--id', $PackageId, '--exact', '--source', 'winget')
    Update-SetupEnvironment
}

function Invoke-MathVisionSetup {
    param([switch]$CheckOnly)
    $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
    $requiredFiles = @('package.json', 'package-lock.json', 'ai/runtime/requirements.txt',
                       'ai/runtime/requirements-lock.txt', 'scripts/dev/check_python_runtime.py',
                       'scripts/dev/install-local-quiz-speech.py',
                       'backend/business-api/gradlew.bat', 'backend/business-api/gradle/wrapper/gradle-wrapper.jar')
    foreach ($file in $requiredFiles) {
        if (-not (Test-Path -LiteralPath (Join-Path $repoRoot $file) -PathType Leaf)) {
            throw "Incomplete checkout, missing $file. Clone the complete repository before setup."
        }
    }

    Write-Host '============================================' -ForegroundColor Cyan
    Write-Host ' MathVision Kids -- First-time Setup' -ForegroundColor Cyan
    Write-Host '============================================' -ForegroundColor Cyan
    Write-Host "Repository root: $repoRoot"
    Write-Host '[1/5] Checking Git, supported Node/npm, Python 3.12 (64-bit), JDK 21 and Docker Compose...'
    $packages = [ordered]@{
        Git = 'Git.Git'
        Node = 'OpenJS.NodeJS.22'
        Python = 'Python.Python.3.12'
        Java = 'EclipseAdoptium.Temurin.21.JDK'
        Docker = 'Docker.DockerDesktop'
    }
    $tools = Get-SetupTools $repoRoot
    foreach ($name in $packages.Keys) {
        if ($tools[$name]) {
            Write-Host "  $name ready" -ForegroundColor Green
        } elseif ($CheckOnly) {
            throw "Missing or incompatible $name. Run SETUP_MATHVISION.bat without -CheckOnly to install prerequisites."
        } else {
            Install-SetupTool $packages[$name]
        }
    }
    $tools = Get-SetupTools $repoRoot
    $missing = @($packages.Keys | Where-Object { -not $tools[$_] })
    if ($missing.Count) {
        throw "Prerequisites still unavailable: $($missing -join ', '). Complete any installer/restart request and reopen setup. Check PATH and JAVA_HOME (JDK 21)."
    }
    if ($CheckOnly) {
        Write-Host 'Prerequisite checks passed. Run without -CheckOnly to install project libraries.' -ForegroundColor Green
        return
    }

    $setupDirectory = Join-Path $repoRoot '.local-artifacts/setup'
    $null = New-Item -ItemType Directory -Path $setupDirectory -Force
    try {
        $setupLock = [System.IO.File]::Open((Join-Path $setupDirectory 'install.lock'),
            [System.IO.FileMode]::OpenOrCreate, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
    } catch [System.IO.IOException] {
        throw 'Another setup is using this checkout. Wait for that setup to finish before retrying.'
    }
    Push-Location $repoRoot
    try {
        $python = Join-Path $repoRoot 'ai/runtime/.venv/Scripts/python.exe'
        if (Test-Path -LiteralPath (Join-Path $repoRoot 'ai/runtime/.venv')) {
            if ($tools.Python -ne $python) {
                throw 'The existing ai/runtime/.venv is incompatible or damaged. Move it aside, then run setup again to create a Python 3.12 environment.'
            }
        } else {
            Write-Host 'Creating the project Python 3.12 environment...'
            Invoke-SetupCommand $tools.Python @('-m', 'venv', 'ai/runtime/.venv')
        }

        Write-Host '[2/5] Installing all JavaScript workspaces from package-lock.json...'
        Invoke-SetupCommand npm.cmd @('ci', '--include=dev', '--include=optional', '--no-fund')

        Write-Host '[3/5] Installing AI, OCR and speech libraries with locked versions...'
        Invoke-SetupCommand $python @('-m', 'ensurepip', '--upgrade')
        # Bundled pip in Python 3.12 can abandon a large ML wheel on a brief
        # network stall. Pin a version with resumable downloads before installing.
        Invoke-SetupCommand $python @('-m', 'pip', 'install', '--disable-pip-version-check', '--no-input',
                                      '--timeout', '60', '--retries', '3', 'pip==26.3')
        Invoke-SetupCommand $python @('-m', 'pip', 'install', '--disable-pip-version-check', '--no-input',
                                      '--timeout', '60', '--retries', '3', '--resume-retries', '3',
                                      '-r', 'ai/runtime/requirements.txt', '-c', 'ai/runtime/requirements-lock.txt')
        Invoke-SetupCommand $python @('-m', 'pip', 'check')
        Invoke-SetupCommand $python @('scripts/dev/check_python_runtime.py')
        Invoke-SetupCommand $python @('-c', "import fastapi, uvicorn, celery, minio, edge_tts, torch, torchvision, cv2, ultralytics; print('AI runtime imports passed.')")
        $ffmpeg = Join-Path $repoRoot 'infra/local-runtime/tools/ffmpeg/bin/ffmpeg.exe'
        if (-not ((Get-SetupProbe $ffmpeg @('-version')) -or (Get-SetupProbe ffmpeg.exe @('-version')))) {
            Write-Host 'Installing the portable FFmpeg decoder for speech...'
            Invoke-SetupCommand $python @('scripts/dev/install-local-quiz-speech.py')
            if (-not (Get-SetupProbe $ffmpeg @('-version'))) {
                throw 'FFmpeg could not be verified. Rerun setup after fixing the download or antivirus error above.'
            }
        }

        Write-Host '[4/5] Downloading Java dependencies and compiling the backend...'
        Push-Location (Join-Path $repoRoot 'backend/business-api')
        try {
            Invoke-SetupCommand '.\gradlew.bat' @('bootJar', 'testClasses', '--no-daemon', '--console=plain')
        } finally {
            Pop-Location
        }

        Write-Host '[5/5] Dependency setup completed.' -ForegroundColor Green
        Write-Host 'Next: open Docker Desktop, then double-click RUN_MATHVISION.bat.'
        Write-Host 'The first launch prepares database/storage images and may need additional downloads.'
        Write-Host 'Real photo/OCR capabilities require your private API configuration or model weights. See docs/HUONG_DAN_CAI_DAT.md.'
    } finally {
        Pop-Location
        $setupLock.Dispose()
    }
}

if ($MyInvocation.InvocationName -ne '.') {
    try {
        Invoke-MathVisionSetup -CheckOnly:$CheckOnly
        exit 0
    } catch {
        Write-Host "[SETUP FAILED] $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}
