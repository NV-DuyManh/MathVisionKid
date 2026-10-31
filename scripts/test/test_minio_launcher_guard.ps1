$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$tokens = $null
$errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $repoRoot 'scripts/dev/start-all.ps1'), [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw $errors[0] }
$guard = $ast.Find({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Assert-LocalMinioImage' }, $true)
if (-not $guard) { throw 'Missing MinIO guard.' }
Invoke-Expression $guard.Extent.Text
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

# Exercise fresh-clone provisioning and legacy retention without touching Docker.
$resolver = $ast.Find({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Resolve-LocalMinioImage' }, $true)
if (-not $resolver) { throw 'Missing portable MinIO resolver.' }
Invoke-Expression $resolver.Extent.Text
$compose = Get-Content (Join-Path $repoRoot 'infra/docker/docker-compose.yml') -Raw
if (-not $compose.Contains('image: ${MATHVISION_MINIO_IMAGE:-mathvision-storage:2024.01.28}') -or $compose -notmatch 'pull_policy: never') {
    throw 'Fresh-clone Compose must use the shared build, not a machine-specific or retired registry tag.'
}
function Invoke-CommandWithTimeout {
    param($FilePath, $ArgumentList, $TimeoutSeconds)
    $operation = $ArgumentList[0]; $script:calls += $operation
    switch ($operation) {
        'container' { return @{ Success=$script:case.Existing; Stdout=(@{ Config=@{ Image='legacy-verified:2024.01.28' } } | ConvertTo-Json -Depth 4) } }
        'volume' { return @{ Success=$script:case.Volume; Stdout='' } }
        'image' { return @{ Success=($script:case.Cached -or $script:built); Stdout=(@{ Architecture=($script:case.Arch); Id='sha256:current' } | ConvertTo-Json) } }
        'build' { $script:built=$script:case.BuildOK; return @{ Success=$script:built } }
        'run' {
            if ($script:case.LegacyPath -and $ArgumentList[-1] -eq '/usr/local/bin/mc') { return @{ Success=$false; Stdout='' } }
            $server=if ($script:case.BadHash) { '0'*64 } else { 'b0638a7f484c53c2d22777f9d8d777d600a321aaeff526bf42a8524c89bfec5e' }
            return @{ Success=$true; Stdout="$server  minio`nfc195c3ad5c19b91d96bbb42d79af94173aa491ebcda9ca372c4f382546135ec  mc" }
        }
        default { throw "Unexpected Docker action: $operation" }
    }
}
$portableCases = @(
    @{ Name='existing verified image reference is retained'; Existing=$true; Cached=$true; LegacyPath=$true; Arch='amd64'; Builds=0 },
    @{ Name='empty clone builds from checked-in Dockerfile'; BuildOK=$true; Arch='amd64'; Builds=1 },
    @{ Name='cached shared build is reused'; Cached=$true; Arch='amd64'; Builds=0 },
    @{ Name='orphan data blocks even the first build'; Volume=$true; Error='MINIO_RECOVERY_REVIEW_REQUIRED'; Builds=0 },
    @{ Name='existing data image is never replaced'; Existing=$true; Error='MINIO_LOCAL_IMAGE_MISSING'; Builds=0 },
    @{ Name='different storage binaries are rejected'; Cached=$true; BadHash=$true; Arch='amd64'; Error='MINIO_BINARY_MISMATCH'; Builds=0 },
    @{ Name='unsupported architecture is rejected'; Cached=$true; Arch='unknown'; Error='MINIO_ARCHITECTURE_UNSUPPORTED'; Builds=0 },
    @{ Name='failed initial download does not attach data'; BuildOK=$false; Error='MINIO_BUILD_FAILED'; Builds=1 }
)
foreach ($case in $portableCases) {
    $script:case=$case; $script:built=$false; $script:calls=@(); $failure=$null; $selected=$null
    try { $selected=Resolve-LocalMinioImage -Image 'mathvision-storage:2024.01.28' -Container 'test-minio' -Volume 'test-data' -BuildContext 'C:\repo with spaces\infra\production\storage' }
    catch { $failure=$_.Exception.Message }
    if ($case.Error) {
        if (-not $failure -or $failure -notmatch $case.Error) { throw "Expected $($case.Error): $($case.Name)" }
    } elseif ($failure) { throw $failure }
    elseif ($selected -ne $(if ($case.Existing) { 'legacy-verified:2024.01.28' } else { 'mathvision-storage:2024.01.28' })) { throw 'Unexpected selected image' }
    if (@($script:calls | Where-Object { $_ -eq 'build' }).Count -ne $case.Builds) { throw "Unexpected build: $($case.Name)" }
    if ($script:calls -contains 'pull') { throw 'Retired registry must not be pulled' }
    Write-Host "PASS: $($case.Name)"
}
Write-Host "PASS: $($portableCases.Count) portable setup cases."
