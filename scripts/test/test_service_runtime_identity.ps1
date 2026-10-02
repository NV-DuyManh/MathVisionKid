$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$launcher = Join-Path $repoRoot 'scripts/dev/start-all.ps1'
$tokens = $null
$parseErrors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($launcher, [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count) { throw $parseErrors[0] }
$identityFunction = $ast.Find({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Test-ServiceCommandIdentity' }, $true)
Invoke-Expression $identityFunction.Extent.Text
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
