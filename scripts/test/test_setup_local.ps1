$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$fixture = Join-Path $repoRoot ('.local-artifacts/setup-tests/clone with spaces ' + [guid]::NewGuid().ToString('N'))
$null = New-Item -ItemType Directory -Path (Join-Path $fixture 'scripts/dev') -Force
$python = Join-Path $fixture 'ai/runtime/.venv/Scripts/python.exe'
$basePython = Join-Path $PSHOME 'powershell.exe'
$script:commands = [System.Collections.Generic.List[object]]::new()
$script:installed = [System.Collections.Generic.List[string]]::new()
$script:failCommand = $false
$script:ffmpegReady = $false
$script:tools = [ordered]@{ Git = $true; Node = $true; Python = $basePython; Java = $true; Docker = $true }

function Assert-Setup {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw $Message }
}

function Assert-SetupFailure {
    param([scriptblock]$Action, [string]$Pattern)
    $caught = $null
    try { & $Action } catch { $caught = $_.Exception.Message }
    Assert-Setup ($caught -like $Pattern) "Expected failure $Pattern, got $caught"
}

try {
    $files = @('package.json', 'package-lock.json', 'ai/runtime/requirements.txt', 'ai/runtime/requirements-lock.txt',
               'backend/business-api/gradlew.bat', 'backend/business-api/gradle/wrapper/gradle-wrapper.jar',
               'scripts/dev/check_python_runtime.py', 'scripts/dev/install-local-quiz-speech.py', '.env',
               'ai/runtime/state/lesson-catalog.sqlite3', 'ai/runtime/models/private.pth')
    foreach ($file in $files) {
        $path = Join-Path $fixture $file
        $null = New-Item -ItemType Directory -Path (Split-Path $path) -Force
        [System.IO.File]::WriteAllText($path, 'keep-original-content')
    }
    Copy-Item -LiteralPath (Join-Path $repoRoot 'scripts/dev/setup-local.ps1') -Destination (Join-Path $fixture 'scripts/dev/setup-local.ps1')
    . (Join-Path $fixture 'scripts/dev/setup-local.ps1')
    $nativeCommand = ${function:Invoke-SetupCommand}
    $detector = ${function:Get-SetupTools}
    $probePython = Join-Path $fixture 'python-probe.exe'
    [System.IO.File]::WriteAllText($probePython, 'test-interpreter')
    function Get-Command { param([string]$Name) return [pscustomobject]@{ Source = $Name } }
    function Get-SetupProbe {
        param([string]$FilePath, [string[]]$Arguments)
        if ($FilePath -eq 'node.exe') { return $script:nodeVersion }
        if ($FilePath -eq 'py.exe') { return $probePython }
        if ($FilePath -eq 'javac.exe') { return 'javac 21.0.9' }
        if ($FilePath -like '*java.exe') { return 'openjdk 21.0.9 LTS' }
        if ($FilePath -in @('npm.cmd', 'git.exe', 'docker.exe')) { return 'available' }
        return $null
    }
    foreach ($case in @(@('18.20.0', $false), @('22.12.0', $false), @('22.19.0', $true),
                         @('24.2.0', $false), @('24.3.0', $true), @('26.0.0', $true), @('27.0.0', $false))) {
        $script:nodeVersion = $case[0]
        $detected = & $detector $fixture
        Assert-Setup ($detected.Node -eq $case[1]) "Incorrect Node support for $($case[0])."
        Assert-Setup ($detected.Python -eq $probePython -and $detected.Java) 'Python/JDK prerequisite detection failed.'
    }
    Remove-Item -LiteralPath 'function:Get-Command'

    function Get-SetupTools { param([string]$RepoRoot) return $script:tools }
    function Install-SetupTool {
        param([string]$PackageId)
        $script:installed.Add($PackageId)
        $script:tools.Node = $true
    }
    function Get-SetupProbe { param([string]$FilePath, [string[]]$Arguments) return $script:ffmpegReady }
    function Invoke-SetupCommand {
        param([string]$FilePath, [string[]]$Arguments)
        $script:commands.Add([pscustomobject]@{ File = $FilePath; Args = $Arguments; Cwd = $PWD.Path })
        if ($script:failCommand -and $FilePath -eq 'npm.cmd') { throw 'simulated npm failure' }
        if ($Arguments -contains 'venv') {
            $null = New-Item -ItemType Directory -Path (Split-Path $python) -Force
            [System.IO.File]::WriteAllText($python, 'test-interpreter')
            $script:tools.Python = $python
        }
        if ($Arguments -contains 'scripts/dev/install-local-quiz-speech.py') { $script:ffmpegReady = $true }
    }

    $originalDirectory = $PWD.Path
    Invoke-MathVisionSetup -CheckOnly
    Assert-Setup ($script:commands.Count -eq 0 -and $script:installed.Count -eq 0) 'CheckOnly changed dependencies.'
    $script:tools.Node = $false
    Assert-SetupFailure { Invoke-MathVisionSetup -CheckOnly } '*Missing or incompatible Node*'
    Assert-Setup ($script:installed.Count -eq 0) 'CheckOnly invoked WinGet.'

    Invoke-MathVisionSetup
    Assert-Setup ($script:installed.Count -eq 1 -and $script:installed[0] -eq 'OpenJS.NodeJS.22') 'Missing prerequisite was not installed once.'
    Assert-Setup ($PWD.Path -eq $originalDirectory) 'Setup did not restore its working directory.'
    Assert-Setup (@($script:commands | Where-Object { $_.Args -contains 'venv' -and $_.File -eq $basePython }).Count -eq 1) 'Setup used the wrong Python to create the environment.'
    $npm = @($script:commands | Where-Object File -eq 'npm.cmd')
    Assert-Setup ($npm.Count -eq 1 -and $npm[0].Cwd -eq $fixture -and $npm[0].Args[0] -eq 'ci') 'Workspaces were not installed once from the checkout root.'
    Assert-Setup ($npm[0].Args -contains '--include=dev') 'Development libraries can be omitted by NODE_ENV.'
    $pipBootstrap = @($script:commands | Where-Object { $_.Args -contains 'pip==26.3' })
    Assert-Setup ($pipBootstrap.Count -eq 1 -and $pipBootstrap[0].File -eq $python) 'Pinned resumable pip was not prepared in the project environment.'
    $pip = @($script:commands | Where-Object { $_.Args -contains 'install' -and $_.Args -contains '-r' })
    Assert-Setup ($pip.Count -eq 1 -and $pip[0].File -eq $python) 'pip ran outside the project environment.'
    Assert-Setup ($pip[0].Args -contains '--resume-retries' -and $pip[0].Args -contains '--timeout') 'Large wheel downloads cannot resume after a network stall.'
    Assert-Setup (($pip[0].Args -join ' ') -like '*-r ai/runtime/requirements.txt -c ai/runtime/requirements-lock.txt*') 'Speech or locked packages were omitted.'
    Assert-Setup (@($script:commands | Where-Object { $_.Args -contains 'scripts/dev/check_python_runtime.py' }).Count -eq 1) 'Critical pin verification was omitted.'
    Assert-Setup (@($script:commands | Where-Object { $_.Args -contains 'scripts/dev/install-local-quiz-speech.py' }).Count -eq 1) 'Missing speech decoder was omitted.'
    $gradle = @($script:commands | Where-Object File -eq '.\gradlew.bat')
    Assert-Setup ($gradle.Count -eq 1 -and $gradle[0].Cwd -eq (Join-Path $fixture 'backend/business-api')) 'Backend used the wrong Gradle wrapper directory.'
    Assert-Setup ($gradle[0].Args -contains 'bootJar' -and $gradle[0].Args -contains 'testClasses') 'Backend dependencies were not prepared.'

    $script:commands.Clear()
    Invoke-MathVisionSetup
    Assert-Setup (@($script:commands | Where-Object { $_.Args -contains 'venv' }).Count -eq 0) 'Rerun recreated the existing environment.'
    Assert-Setup (@($script:commands | Where-Object { $_.Args -contains 'scripts/dev/install-local-quiz-speech.py' }).Count -eq 0) 'Rerun replaced the existing speech decoder.'
    foreach ($file in $files) {
        Assert-Setup ([System.IO.File]::ReadAllText((Join-Path $fixture $file)) -eq 'keep-original-content') "Setup changed $file."
    }

    $script:commands.Clear()
    $script:failCommand = $true
    Assert-SetupFailure { Invoke-MathVisionSetup } '*simulated npm failure*'
    Assert-Setup ($script:commands.Count -eq 1) 'Setup continued after a failed installation.'
    Assert-Setup ($PWD.Path -eq $originalDirectory) 'Failure left the working directory changed.'
    $script:failCommand = $false
    $script:tools.Python = 'another-python.exe'
    $script:commands.Clear()
    Assert-SetupFailure { Invoke-MathVisionSetup } '*existing ai/runtime/.venv is incompatible*'
    Assert-Setup ($script:commands.Count -eq 0) 'A damaged existing environment was overwritten.'

    $script:tools.Python = $python
    $heldLock = [System.IO.File]::Open((Join-Path $fixture '.local-artifacts/setup/install.lock'),
        [System.IO.FileMode]::Open, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
    try {
        Assert-SetupFailure { Invoke-MathVisionSetup } '*Another setup is using this checkout*'
        Assert-Setup ($script:commands.Count -eq 0) 'Concurrent setups changed the same environment.'
    } finally {
        $heldLock.Dispose()
    }

    ${function:Invoke-SetupCommand} = $nativeCommand
    Assert-SetupFailure { Invoke-SetupCommand $env:ComSpec @('/d', '/c', 'exit /b 7') } '*exit code 7*'
    Invoke-SetupCommand $env:ComSpec @('/d', '/c', 'echo ordinary native warning 1>&2 & exit /b 0')
    Write-Host 'PASS: setup dry run, installation order, lockfiles, private files, rerun, decoder and failure handling.' -ForegroundColor Green
} finally {
    $resolved = (Resolve-Path -LiteralPath $fixture).Path
    $allowed = [System.IO.Path]::GetFullPath((Join-Path $repoRoot '.local-artifacts/setup-tests')) + [System.IO.Path]::DirectorySeparatorChar
    if (-not $resolved.StartsWith($allowed, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe test cleanup path.' }
    Remove-Item -LiteralPath $resolved -Recurse -Force
}
