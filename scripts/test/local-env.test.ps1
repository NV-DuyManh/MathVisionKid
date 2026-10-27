$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '../dev/local-env.ps1')
$folder = Join-Path ([IO.Path]::GetTempPath()) ([Guid]::NewGuid().ToString())
[IO.Directory]::CreateDirectory($folder) | Out-Null
$base = Join-Path $folder 'base.env'
$service = Join-Path $folder 'service.env'
$keys = @('MVK_ENV_TEST_VALUE', 'MVK_ENV_TEST_LITERAL', 'MVK_ENV_TEST_PARENT')
$oldParent = [Environment]::GetEnvironmentVariable('MVK_ENV_TEST_PARENT', 'Process')
try {
    [IO.File]::WriteAllText($base, "MVK_ENV_TEST_VALUE=base`nMVK_ENV_TEST_PARENT=file`nMVK_ENV_TEST_IGNORED=unrelated`n")
    [IO.File]::WriteAllText($service, 'MVK_ENV_TEST_VALUE="service"' + "`n" + 'MVK_ENV_TEST_LITERAL=''$(throw "evaluated")''' + "`n")
    [Environment]::SetEnvironmentVariable('MVK_ENV_TEST_PARENT', 'parent', 'Process')
    Invoke-WithLocalEnvironment -Files @($base, $service) -AllowedKeys $keys -Action {
        if ($env:MVK_ENV_TEST_VALUE -ne 'service') { throw 'Service precedence failed' }
        if ($env:MVK_ENV_TEST_PARENT -ne 'parent') { throw 'Process precedence failed' }
        if ($env:MVK_ENV_TEST_LITERAL -ne '$(throw "evaluated")') { throw 'Literal parsing failed' }
        if ($env:MVK_ENV_TEST_IGNORED) { throw 'Allowlist failed' }
        # Confirm child processes inherit loaded values without printing them.
        & $env:ComSpec /d /c 'if "%MVK_ENV_TEST_VALUE%"=="service" (exit 0) else (exit 1)'
        if ($LASTEXITCODE -ne 0) { throw 'Child inheritance failed' }
    }
    if ($env:MVK_ENV_TEST_VALUE -or $env:MVK_ENV_TEST_LITERAL) { throw 'Environment leaked after child launch' }
    try {
        Invoke-WithLocalEnvironment -Files @($base) -AllowedKeys $keys -Action { throw 'expected-test-error' }
    } catch { if ($_.Exception.Message -ne 'expected-test-error') { throw } }
    if ($env:MVK_ENV_TEST_VALUE) { throw 'Environment leaked on failure' }
    [IO.File]::WriteAllText($service, 'MVK_ENV_TEST_VALUE="unterminated')
    $rejected = $false
    try { Invoke-WithLocalEnvironment -Files @($service) -AllowedKeys $keys -Action {} }
    catch { $rejected = $_.Exception.Message -like '*value withheld*' }
    if (-not $rejected) { throw 'Invalid syntax was accepted or value was exposed' }
    Write-Output 'PASS: dotenv precedence, literal values, allowlist, child inheritance, cleanup on success/failure, redacted syntax errors.'
} finally {
    [Environment]::SetEnvironmentVariable('MVK_ENV_TEST_PARENT', $oldParent, 'Process')
    # Delete only the two exact temporary files created by this test.
    foreach ($file in @($base, $service)) { if (Test-Path -LiteralPath $file) { [IO.File]::Delete($file) } }
    [IO.Directory]::Delete($folder)
}
