$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '../dev/toolchain.ps1')
. (Join-Path $PSScriptRoot '../dev/setup-local.ps1')
$originalPath = $env:PATH
$originalJava = $env:JAVA_HOME
$fixture = Join-Path ([IO.Path]::GetTempPath()) ('mathvision-toolchain-' + [guid]::NewGuid().ToString('N'))
try {
    $bad = Join-Path $fixture 'old tools'; $good = Join-Path $fixture 'compatible tools'
    foreach ($directory in @($bad, $good)) {
        $null = New-Item -ItemType Directory -Path $directory -Force
        [IO.File]::WriteAllText((Join-Path $directory 'npm.cmd'), 'synthetic stub')
    }
    $script:bad = $bad; $script:good = $good
    $script:badNodeVersion = '20.0.0'
    function Get-MathVisionToolCandidates {
        param([string]$Name)
        if ($Name -in @('node.exe', 'java.exe', 'python.exe')) { return @((Join-Path $script:bad $Name), (Join-Path $script:good $Name)) }
        return @()
    }
    function Get-MathVisionToolProbe {
        param([string]$FilePath, [string[]]$Arguments)
        if ($FilePath -like '*python.exe') {
            if ($FilePath.StartsWith($script:good)) { return $FilePath }
            return $null
        }
        if ($FilePath -like '*node.exe') {
            if ($Arguments -contains 'process.arch') {
                if ($FilePath.StartsWith($script:bad)) { return 'ia32' }
                return 'x64'
            }
            if ($FilePath.StartsWith($script:bad)) { return $script:badNodeVersion }
            return '22.19.0'
        }
        if ($FilePath -like '*javac.exe') {
            if ($FilePath.StartsWith($script:bad)) { return 'javac 17.0.1' }
            return 'javac 21.0.9'
        }
        if ($FilePath.StartsWith($script:bad)) { return 'openjdk 17.0.1' }
        return 'openjdk 21.0.9'
    }
    $env:PATH = "$bad;$good;$originalPath"
    $env:JAVA_HOME = Join-Path $fixture 'stale-jdk-17'
    Use-MathVisionToolchain
    if (($env:PATH -split ';')[0] -ne $good) { throw 'Compatible tools did not replace stale PATH precedence.' }
    if ($env:JAVA_HOME -ne (Split-Path -Parent $good)) { throw 'Stale JAVA_HOME was not corrected for the child process.' }
    $once = $env:PATH
    $script:badNodeVersion = '22.19.0'
    Use-MathVisionToolchain
    if ($env:PATH -ne $once) { throw 'Repeated discovery duplicates or reorders tool directories.' }
    $hostCheck = ${function:Assert-SetupHost}
    function Get-Item { param([string]$LiteralPath) return [pscustomobject]@{ PSDrive = [pscustomobject]@{ Name = 'synthetic'; Free = 1GB } } }
    try { & $hostCheck $fixture; throw 'Low-space preflight unexpectedly passed' }
    catch { if ($_.Exception.Message -notlike '*Not enough free space*') { throw } }
    & $hostCheck $fixture -CheckOnly -WarningAction SilentlyContinue
    Write-Host 'PASS: stale Node/JDK/Python selection, process JAVA_HOME, idempotence and low-disk failure.'
} finally {
    $env:PATH = $originalPath; $env:JAVA_HOME = $originalJava
    if ((Split-Path -Parent ([IO.Path]::GetFullPath($fixture))) -ne ([IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\')) -or (Split-Path -Leaf $fixture) -notlike 'mathvision-toolchain-*') { throw 'Unsafe fixture cleanup.' }
    Microsoft.PowerShell.Management\Remove-Item -LiteralPath $fixture -Recurse -Force
}
