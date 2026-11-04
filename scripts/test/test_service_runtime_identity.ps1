$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$launcher = Join-Path $repoRoot 'scripts/dev/start-all.ps1'
$tokens = $null
$parseErrors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($launcher, [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count) { throw $parseErrors[0] }
$identityFunction = $ast.Find({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Test-ServiceCommandIdentity' }, $true)
Invoke-Expression $identityFunction.Extent.Text
$processIdentityFunction = $ast.Find({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Test-ServiceProcessIdentity' }, $true)
Invoke-Expression $processIdentityFunction.Extent.Text
$startFunction = $ast.Find({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Start-TrackedService' }, $true)
Invoke-Expression $startFunction.Extent.Text

$cases = @(
    @{ Kind='spring'; Path='E:\MathVisionKid\backend\business-api'; Command='java -cp E:\MathVisionKid\backend\business-api\build\classes\java\main com.mathvisionkids.api.BusinessApiApplication'; Expected=$true },
    @{ Kind='spring'; Path='E:\MathVisionKid\backend\business-api'; Command='java -cp E:\OtherProject\backend\build\classes\java\main com.mathvisionkids.api.BusinessApiApplication'; Expected=$false },
    @{ Kind='spring'; Path='E:\MathVisionKid\backend\business-api'; Command='java -cp E:\MathVisionKid\backend\business-api-old\build\classes\java\main com.mathvisionkids.api.BusinessApiApplication'; Expected=$false },
    @{ Kind='spring'; Path='E:\Project With Spaces\backend\business-api'; Command='java -cp "E:\Project With Spaces\backend\business-api\build\classes\java\main" com.mathvisionkids.api.BusinessApiApplication'; Expected=$true },
    @{ Kind='spring'; Path='E:\MathVisionKid\backend\business-api'; Command='python E:\MathVisionKid\backend\business-api\server.py'; Expected=$false },
    @{ Kind='fastapi'; Path='E:\MathVisionKid\ai\runtime'; Command='python "E:\MathVisionKid\ai\runtime\.venv\Scripts\uvicorn.exe" app.main:app --port 8000'; Expected=$true },
    @{ Kind='fastapi'; Path='E:\MathVisionKid\ai\runtime'; Command='python "E:\OtherProject\ai\runtime\.venv\Scripts\uvicorn.exe" app.main:app --port 8000'; Expected=$false },
    @{ Kind='fastapi'; Path='E:\MathVisionKid\ai\runtime'; Command='python E:\MathVisionKid\ai\runtime\server.py'; Expected=$false }
)
foreach ($case in $cases) {
    $actual = Test-ServiceCommandIdentity -CommandLine $case.Command -WorkingDirectory $case.Path -IdentityKind $case.Kind
    if ($actual -ne $case.Expected) { throw "Runtime identity assertion failed: $($case.Kind), expected $($case.Expected)." }
}
Write-Host "PASS: $($cases.Count) runtime identity cases; another checkout cannot satisfy the launcher guard."

Add-Type -AssemblyName System.IO.Compression, System.IO.Compression.FileSystem
$jarPath = Join-Path ([IO.Path]::GetTempPath()) ("mathvision-classpath-" + [guid]::NewGuid().ToString('N') + '.jar')
$jarCases = @(
    @{ Classpath='file:/E:/MathVisionKid/backend/business-api/build/classes/java/main/ file:/E:/MathVisionKid/backend/business-api/build/resources/main/'; Expected=$true },
    @{ Classpath="file:/E:/MathVisionKid/backend/business-api/build/classes/java/`r`n main/ file:/E:/MathVisionKid/backend/business-api/build/resources/main/"; Expected=$true },
    @{ Classpath='file:/E:/OtherProject/backend/business-api/build/classes/java/main/ file:/E:/OtherProject/backend/business-api/build/resources/main/'; Expected=$false },
    @{ Classpath='file:/E:/MathVisionKid/backend/business-api-old/build/classes/java/main/ file:/E:/MathVisionKid/backend/business-api-old/build/resources/main/'; Expected=$false },
    @{ Classpath='file:/E:/MathVisionKid/backend/business-api/build/classes/java/main/'; Expected=$false },
    @{ Classpath='build/classes/java/main/ build/resources/main/'; Expected=$false }
)
try {
    foreach ($case in $jarCases) {
        $zip = [IO.Compression.ZipFile]::Open($jarPath, [IO.Compression.ZipArchiveMode]::Create)
        $writer = [IO.StreamWriter]::new($zip.CreateEntry('META-INF/MANIFEST.MF').Open())
        $writer.Write("Manifest-Version: 1.0`r`nClass-Path: $($case.Classpath)`r`n`r`n")
        $writer.Dispose(); $zip.Dispose()
        $java = [PSCustomObject]@{ CommandLine="java -cp `"$jarPath`" com.mathvisionkids.api.BusinessApiApplication" }
        $actual = Test-ServiceProcessIdentity -Process $java -WorkingDirectory 'E:\MathVisionKid\backend\business-api' -IdentityKind 'spring'
        if ($actual -ne $case.Expected) { throw 'Gradle manifest classpath identity assertion failed.' }
        Remove-Item -LiteralPath $jarPath
    }
    if (Test-ServiceProcessIdentity -Process $java -WorkingDirectory 'E:\MathVisionKid\backend\business-api' -IdentityKind 'spring') {
        throw 'A missing classpath JAR was accepted.'
    }
    Write-Host 'PASS: 7 Gradle classpath JAR cases; foreign, prefix-collision, partial, relative and missing paths rejected.'
} finally {
    if (Test-Path -LiteralPath $jarPath) { Remove-Item -LiteralPath $jarPath }
}

$runtimePath = Join-Path $repoRoot 'ai/runtime'
$venvPython = Join-Path $runtimePath '.venv/Scripts/python.exe'
$foreignPython = Join-Path ([IO.Path]::GetTempPath()) 'OtherProject/ai/runtime/.venv/Scripts/python.exe'
$pythonChild = [PSCustomObject]@{
    Name='python.exe'; ExecutablePath='C:\Python\python.exe'; ParentProcessId=123;
    CommandLine='"C:\Python\python.exe" -m uvicorn app.main:app --port 8000';
    CreationDate=[datetime]'2026-10-03T20:00:01'
}
$validParent = @{
    ExecutablePath=$venvPython;
    CommandLine="`"$venvPython`" -m uvicorn app.main:app --port 8000";
    CreationDate=[datetime]'2026-10-03T20:00:00'
}
$parentCases = @(
    @{ Parent=$validParent; Expected=$true },
    @{ Parent=@{ ExecutablePath=$foreignPython; CommandLine="`"$foreignPython`" -m uvicorn app.main:app"; CreationDate=$validParent.CreationDate }; Expected=$false },
    @{ Parent=@{ ExecutablePath="$runtimePath-old/.venv/Scripts/python.exe"; CommandLine="`"$runtimePath-old/.venv/Scripts/python.exe`" -m uvicorn app.main:app"; CreationDate=$validParent.CreationDate }; Expected=$false },
    @{ Parent=@{ ExecutablePath='C:\Windows\powershell.exe'; CommandLine="powershell `"$venvPython -m uvicorn app.main:app`""; CreationDate=$validParent.CreationDate }; Expected=$false },
    @{ Parent=@{ ExecutablePath=$validParent.ExecutablePath; CommandLine="`"$venvPython`" other.py"; CreationDate=$validParent.CreationDate }; Expected=$false },
    @{ Parent=@{ ExecutablePath=$validParent.ExecutablePath; CommandLine=$validParent.CommandLine; CreationDate=[datetime]'2026-10-03T20:00:02' }; Expected=$false },
    @{ Parent=$null; Expected=$false }
)
function Get-CimInstance { param($ClassName, $Filter, $ErrorAction) return $script:fakeParent }
try {
    foreach ($case in $parentCases) {
        $script:fakeParent = if ($case.Parent) { [PSCustomObject]$case.Parent } else { $null }
        $actual = Test-ServiceProcessIdentity -Process $pythonChild -WorkingDirectory $runtimePath -IdentityKind 'fastapi'
        if ($actual -ne $case.Expected) { throw 'Windows Python parent identity assertion failed.' }
    }
    $script:fakeParent = [PSCustomObject]$validParent
    $differentChild = $pythonChild.PSObject.Copy()
    $differentChild.CommandLine = '"C:\Python\python.exe" -m http.server 8000'
    if (Test-ServiceProcessIdentity -Process $differentChild -WorkingDirectory $runtimePath -IdentityKind 'fastapi') {
        throw 'A different child module was incorrectly accepted.'
    }
    Write-Host 'PASS: 8 Windows Python redirector cases; foreign, reused, missing and unrelated parents rejected.'
} finally {
    Remove-Item Function:Get-CimInstance
}

$stopFunction = $ast.Find({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Stop-VerifiedWorkerTree' }, $true)
if (-not $stopFunction) { throw 'Missing verified worker stop function.' }
Invoke-Expression $stopFunction.Extent.Text
$worker = [PSCustomObject]@{
    ProcessId=12345; Name='python.exe'; ExecutablePath=$venvPython;
    CommandLine="`"$venvPython`" -m celery -A app.jobs.celery_app worker";
    CreationDate=[datetime]'2026-10-03T20:00:00'
}
$reused = $worker.PSObject.Copy(); $reused.CreationDate = $worker.CreationDate.AddSeconds(1)
$foreign = $worker.PSObject.Copy(); $foreign.CommandLine = 'python C:\OtherProject\server.py'
$stopCases = @(
    @{ Name='already exited before stop'; Before=$null; Calls=0 },
    @{ Name='reused PID is left alone'; Before=$reused; Calls=0 },
    @{ Name='changed command is rejected'; Before=$foreign; Calls=0; Error='WORKER_IDENTITY_CHANGED' },
    @{ Name='successful tree stop'; Before=$worker; After=$null; Success=$true; Calls=1 },
    @{ Name='exited between lookup and taskkill'; Before=$worker; After=$null; Success=$false; Calls=1 },
    @{ Name='failed stop of active worker blocks replacement'; Before=$worker; After=$worker; Calls=1; Error='WORKER_STOP_FAILED' },
    @{ Name='success exit cannot hide an active worker'; Before=$worker; After=$worker; Success=$true; Calls=1; Error='WORKER_STOP_FAILED' },
    @{ Name='timed out stop blocks replacement'; Before=$worker; After=$worker; Calls=1; TimedOut=$true; Error='WORKER_STOP_FAILED' },
    @{ Name='PID reused after old worker exits is left alone'; Before=$worker; After=$reused; Calls=1 }
)
function Get-CimInstance {
    param($ClassName, $Filter, $ErrorAction)
    if ($script:stopCalls -eq 0) { return $script:stopCase.Before }
    return $script:stopCase.After
}
function Invoke-CommandWithTimeout {
    param($FilePath, $ArgumentList, $TimeoutSeconds)
    if ($FilePath -ne 'taskkill.exe' -or ($ArgumentList -join ' ') -ne '/PID 12345 /T /F' -or $TimeoutSeconds -ne 10) {
        throw 'Worker stop used an unexpected process or command.'
    }
    $script:stopCalls++
    return [PSCustomObject]@{ Success=[bool]$script:stopCase.Success; TimedOut=[bool]$script:stopCase.TimedOut; ExitCode=$(if ($script:stopCase.Success) { 0 } else { 1 }) }
}
try {
    foreach ($case in $stopCases) {
        $script:stopCase=$case; $script:stopCalls=0; $failure=$null
        try { Stop-VerifiedWorkerTree -ObservedProcess $worker -WorkingDirectory $runtimePath }
        catch { $failure=$_.Exception.Message }
        if ($case.Error) {
            if ($failure -notmatch $case.Error) { throw "Expected $($case.Error): $($case.Name)" }
        } elseif ($failure) { throw $failure }
        if ($script:stopCalls -ne $case.Calls) { throw "Unexpected termination calls: $($case.Name)" }
    }
    Write-Host "PASS: $($stopCases.Count) worker stop races; exited/reused PIDs tolerated, foreign or still-active workers protected."
} finally {
    Remove-Item Function:Get-CimInstance
    Remove-Item Function:Invoke-CommandWithTimeout
}

# Exercise native stderr capture on both shells, targeting only an absent PID.
$absentId = [int]::MaxValue
if (Get-CimInstance Win32_Process -Filter "ProcessId = $absentId") { throw 'Native stderr test target unexpectedly exists.' }
$commandFunction = $ast.Find({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Invoke-CommandWithTimeout' }, $true)
Invoke-Expression $commandFunction.Extent.Text
$nativeResult = Invoke-CommandWithTimeout -FilePath 'taskkill.exe' -ArgumentList @('/PID', "$absentId", '/T', '/F') -TimeoutSeconds 5
if ($nativeResult.Success -or $nativeResult.TimedOut -or -not $nativeResult.Stderr) { throw 'Expected captured native process-not-found error.' }
Write-Host 'PASS: Real taskkill process-not-found stderr captured without terminating PowerShell.'

$listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
try {
    $listener.Start()
    $port = $listener.LocalEndpoint.Port
    $rejected = $false
    try {
        Start-TrackedService -Name 'Spring Boot test' -FilePath 'must-never-start.exe' -ArgumentList '' `
            -WorkingDirectory (Join-Path $repoRoot 'backend/business-api') -LogFile '' -PidFile '' `
            -PortCheck $port -IdentityKind 'spring'
    } catch {
        if ($_.Exception.Message -notmatch 'PORT_CONFLICT') { throw }
        $rejected = $true
    }
    if (-not $rejected) { throw 'A foreign listener was incorrectly accepted as Spring Boot.' }
    $connection = [System.Net.Sockets.TcpClient]::new('127.0.0.1', $port)
    $connection.Close()
    Write-Host 'PASS: Real foreign TCP listener rejected and left running; no replacement process started.'
} finally {
    $listener.Stop()
}
