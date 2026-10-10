param(
    [Parameter(Mandatory = $true)][string]$ApiOrigin,
    [string]$Scope = 'manh15',
    [ValidateSet('portal', 'teacher', 'admin')][string[]]$Apps = @('portal', 'teacher', 'admin')
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$state = Join-Path $repo 'infra/local-runtime/pc-preview'
$apiUri = $null
if (-not [Uri]::TryCreate($ApiOrigin, [UriKind]::Absolute, [ref]$apiUri) -or
    $apiUri.Scheme -ne 'https' -or $apiUri.IsLoopback -or $apiUri.UserInfo -or
    $apiUri.AbsolutePath -ne '/' -or $apiUri.Query -or $apiUri.Fragment -or
    $apiUri.Host -notmatch '\.' -or $apiUri.Host -match '(\.local|\.example|\.test|\.invalid)$') {
    throw 'ApiOrigin must be a public HTTPS origin without credentials, a path, or query.'
}
$ApiOrigin = $apiUri.GetLeftPart([UriPartial]::Authority)
$health = Invoke-RestMethod "$ApiOrigin/actuator/health" -TimeoutSec 20
if ($health.status -ne 'UP') { throw 'The public API is not healthy; no web deployment was started.' }
if (-not (Get-Command vercel -ErrorAction SilentlyContinue)) { throw 'Install and authenticate the Vercel CLI first.' }
$previous = @{}
$keys = @('VITE_API_BASE_URL', 'VITE_PORTAL_URL', 'VITE_TEACHER_URL', 'VITE_ADMIN_URL', 'VITE_USE_MOCK', 'VITE_SHOW_DEV_TOOLS', 'EXPO_PUBLIC_API_BASE_URL', 'EXPO_PUBLIC_USE_MOCK', 'EXPO_NO_DOTENV', 'MATHVISION_WEB_EXPORT')
foreach ($key in $keys) { $previous[$key] = [Environment]::GetEnvironmentVariable($key, 'Process') }
try {
    $env:VITE_PORTAL_URL = 'https://mathvisionkid-portal.vercel.app'
    $env:VITE_TEACHER_URL = 'https://mathvisionkid-teacher.vercel.app'
    $env:VITE_ADMIN_URL = 'https://mathvisionkid-admin.vercel.app'
    $env:VITE_USE_MOCK = 'false'
    $env:VITE_SHOW_DEV_TOOLS = 'false'
    $deployments = @()
    foreach ($app in $Apps) {
        $projectName = "mathvisionkid-$app"
        # Browsers keep a stable address; only Vercel's upstream changes after a PC restart.
        $webOrigin = "https://$projectName.vercel.app"
        $env:VITE_API_BASE_URL = "$webOrigin/api/v1"
        $projectJson = & vercel api "/v9/projects/$projectName" --scope $Scope
        if ($LASTEXITCODE -ne 0) { throw "Cannot access $projectName in the selected team." }
        $project = $projectJson | ConvertFrom-Json
        if ($project.name -ne $projectName -or -not $project.accountId -or -not $project.id) { throw 'Unexpected project identity.' }
        $source = Join-Path $repo "apps/$app-web"
        Push-Location $source
        try {
            npm.cmd run test:config
            if ($LASTEXITCODE -ne 0) { throw "$app configuration checks failed." }
            npm.cmd run build
            if ($LASTEXITCODE -ne 0) { throw "$app production build failed." }
            npm.cmd run test:production
            if ($LASTEXITCODE -ne 0) { throw "$app production bundle checks failed." }
        } finally { Pop-Location }

        if ($app -eq 'portal') {
            node (Join-Path $repo 'scripts/deploy/test_student_web.mjs')
            if ($LASTEXITCODE -ne 0) { throw 'Student website configuration checks failed.' }
            $env:EXPO_PUBLIC_API_BASE_URL = "$webOrigin/api/v1"
            $env:EXPO_PUBLIC_USE_MOCK = 'false'
            $env:EXPO_NO_DOTENV = '1'
            $env:MATHVISION_WEB_EXPORT = 'true'
            $studentExport = Join-Path $state 'student-web-export'
            Push-Location (Join-Path $repo 'apps/student-mobile')
            try {
                npx.cmd expo export --platform web --clear --output-dir $studentExport
                if ($LASTEXITCODE -ne 0) { throw 'The shared student website export failed.' }
            } finally { Pop-Location }
            if (-not (Test-Path -LiteralPath (Join-Path $studentExport 'index.html'))) { throw 'Student website output is missing.' }
            node (Join-Path $repo 'scripts/deploy/check_student_export.mjs') $studentExport $env:EXPO_PUBLIC_API_BASE_URL
            if ($LASTEXITCODE -ne 0) { throw 'Student website contains a stale service address; no upload was started.' }
        }

        # Upload only the tested static output. Private runtime state and source datasets stay local.
        $staging = Join-Path $state "web-staging/$app"
        $output = Join-Path $staging '.vercel/output'
        if (Test-Path -LiteralPath $output) {
            $resolved = (Resolve-Path -LiteralPath $output).Path
            $allowed = [IO.Path]::GetFullPath((Join-Path $state 'web-staging')) + [IO.Path]::DirectorySeparatorChar
            if (-not $resolved.StartsWith($allowed, [StringComparison]::OrdinalIgnoreCase)) { throw 'Build output is outside the staging directory.' }
            Remove-Item -LiteralPath $resolved -Recurse -Force
        }
        $static = Join-Path $output 'static'
        New-Item -ItemType Directory -Path $static -Force | Out-Null
        Get-ChildItem -LiteralPath (Join-Path $source 'dist') -Force | Copy-Item -Destination $static -Recurse
        if ($app -eq 'portal') {
            $studentStatic = Join-Path $static 'study'
            New-Item -ItemType Directory -Path $studentStatic -Force | Out-Null
            Get-ChildItem -LiteralPath $studentExport -Force | Copy-Item -Destination $studentStatic -Recurse
        }
        $headers = @{
            'X-Content-Type-Options' = 'nosniff'; 'X-Frame-Options' = 'DENY'
            'Referrer-Policy' = 'no-referrer'; 'Strict-Transport-Security' = 'max-age=31536000'
        }
        $config = @{
            version = 3
            routes = @(
                @{ src = '/(.*)'; headers = $headers; continue = $true },
                @{ src = '^/api/v1/(.*)$'; dest = $ApiOrigin + '/api/v1/$1'; headers = @{
                    'Cache-Control' = 'no-store'; 'CDN-Cache-Control' = 'no-store'
                    'Vercel-CDN-Cache-Control' = 'no-store'; 'x-vercel-enable-rewrite-caching' = '0'
                } },
                @{ src = '/assets/(.*)'; headers = @{ 'Cache-Control' = 'public, max-age=31536000, immutable' }; continue = $true },
                @{ src = '/index.html'; headers = @{ 'Cache-Control' = 'no-cache' }; continue = $true },
                @{ handle = 'filesystem' },
                @{ src = '/study(?:/.*)?'; dest = '/study/index.html'; headers = @{ 'Cache-Control' = 'no-cache' } },
                @{ src = '/(.*)'; dest = '/index.html'; headers = @{ 'Cache-Control' = 'no-store' } }
            )
        }
        $utf8 = [Text.UTF8Encoding]::new($false)
        [IO.File]::WriteAllText((Join-Path $output 'config.json'), ($config | ConvertTo-Json -Depth 12), $utf8)
        $link = @{ orgId = $project.accountId; projectId = $project.id; projectName = $project.name }
        [IO.File]::WriteAllText((Join-Path $staging '.vercel/project.json'), ($link | ConvertTo-Json), $utf8)
        $result = & vercel deploy --cwd $staging --scope $Scope --prebuilt --prod --yes --json
        if ($LASTEXITCODE -ne 0) { throw "$app deployment failed; previously published apps were retained." }
        $deployment = $result | ConvertFrom-Json
        $deployments += @{ app = $app; origin = $webOrigin; deployment = $deployment }
    }
    $recordPath = Join-Path $state 'web-deployments.json'
    if (Test-Path -LiteralPath $recordPath) {
        $existing = Get-Content -LiteralPath $recordPath -Raw | ConvertFrom-Json
        $deployments += @($existing.apps | Where-Object { $_.app -notin $Apps })
    }
    $record = @{ apiOrigin = $ApiOrigin; deployedAtUtc = [DateTime]::UtcNow.ToString('o'); scope = $Scope; apps = $deployments }
    [IO.File]::WriteAllText((Join-Path $state 'web-deployments.json'), ($record | ConvertTo-Json -Depth 20), [Text.UTF8Encoding]::new($false))
    Write-Host "Published $($Apps -join ', ') with the current API origin."
} finally {
    foreach ($key in $keys) { [Environment]::SetEnvironmentVariable($key, $previous[$key], 'Process') }
}
