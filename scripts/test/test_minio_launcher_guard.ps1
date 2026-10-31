$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$tokens = $null
$errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $repoRoot 'scripts/dev/start-all.ps1'), [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw $errors[0] }
$guard = $ast.Find({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Assert-LocalMinioImage' }, $true)
if (-not $guard) { throw 'Missing MinIO guard.' }
Invoke-Expression $guard.Extent.Text
# Catch a Compose regression before it can break the real launcher again.
$compose = Get-Content (Join-Path $repoRoot 'infra/docker/docker-compose.yml') -Raw
$minio = [regex]::Match($compose, '(?ms)^  minio:\r?\n(?<service>.*?)(?=^  \S|\z)').Groups['service'].Value
if ($minio -notmatch '(?m)^    image: mathvision-minio-local:2024\.01\.28\s*$' -or
    $minio -notmatch '(?m)^    pull_policy: never\s*$') {
    throw 'MinIO Compose must use the verified local image with pull_policy: never.'
}
Write-Host 'PASS: Compose preserves the verified local MinIO image and never pulls a replacement.'
function Invoke-CommandWithTimeout {
    param($FilePath, $ArgumentList, $TimeoutSeconds)
    $operation = $ArgumentList[0]
    $script:calls += $operation
    switch ($operation) {
        'image' { return @{ Success=$script:case.Cached; Stdout='sha256:current' } }
        'container' {
            $mount = @{ Destination='/data'; Type=$script:case.MountType; Name=$script:case.Mount }
            return @{ Success=$script:case.Container; Stdout=(@{ Image=$script:case.Image; Mounts=@($mount) } | ConvertTo-Json -Depth 4) }
        }
        'volume' { return @{ Success=$script:case.Volume; Stdout='' } }
        default { throw 'Guard must only inspect Docker state, never pull, recreate, or migrate.' }
    }
}
$cases = @(
    @{ Name='same cached image and data volume'; Cached=$true; Container=$true; Image='sha256:current'; Mount='business-api_miniodata'; MountType='volume'; Volume=$true; Error=$null },
    @{ Name='fresh empty installation with verified cache'; Cached=$true; Container=$false; Volume=$false; Error=$null },
    @{ Name='missing image never pulls a replacement'; Cached=$false; Error='MINIO_LOCAL_IMAGE_MISSING' },
    @{ Name='another image cannot mount existing data'; Cached=$true; Container=$true; Image='sha256:different'; Error='MINIO_IMAGE_CHANGE_BLOCKED' },
    @{ Name='orphan data volume requires recovery review'; Cached=$true; Container=$false; Volume=$true; Error='MINIO_RECOVERY_REVIEW_REQUIRED' },
    @{ Name='different named volume is preserved'; Cached=$true; Container=$true; Image='sha256:current'; Mount='another-volume'; MountType='volume'; Error='MINIO_VOLUME_CHANGE_BLOCKED' },
    @{ Name='bind mount cannot silently become a named volume'; Cached=$true; Container=$true; Image='sha256:current'; Mount='business-api_miniodata'; MountType='bind'; Error='MINIO_VOLUME_CHANGE_BLOCKED' }
)
foreach ($case in $cases) {
    $script:case = $case
    $script:calls = @()
    $failure = $null
    try { Assert-LocalMinioImage -Image 'mathvision-minio-local:2024.01.28' -Container 'mathvision-minio' -Volume 'business-api_miniodata' }
    catch { $failure = $_.Exception.Message }
    if ($case.Error) {
        if (-not $failure -or $failure -notmatch $case.Error) { throw "Expected $($case.Error): $($case.Name)" }
    } elseif ($failure) { throw $failure }
    if (-not $case.Cached -and $script:calls.Count -ne 1) { throw 'Missing image must stop before inspecting or changing storage.' }
    Write-Host "PASS: $($case.Name)"
}
Write-Host "PASS: $($cases.Count) MinIO preservation cases; no state-changing Docker operation in the guard."
