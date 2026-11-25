function Get-LocalPorts {
    param([switch]$Defaults)
    $ports = @{ spring = 8080; ai = 8000; portal = 5172; teacher = 5173; admin = 5174; metro = 8081; metroSpring = 8080 }
    $file = Join-Path $RepoRoot 'infra/local-runtime/ports.json'
    if (-not $Defaults -and (Test-Path -LiteralPath $file)) {
        $saved = Get-Content -LiteralPath $file -Raw | ConvertFrom-Json
        foreach ($name in @($ports.Keys)) {
            $port = 0
            if ([int]::TryParse([string]$saved.$name, [ref]$port) -and $port -ge 1024 -and $port -le 65535) {
                $ports[$name] = $port
            }
        }
    }
    return $ports
}

function Save-LocalPorts($Ports) {
    $file = Join-Path $RepoRoot 'infra/local-runtime/ports.json'
    $dir = Split-Path -Parent $file
    $null = New-Item -ItemType Directory -Path $dir -Force
    $temp = Join-Path $dir ("ports.$([guid]::NewGuid()).tmp")
    try {
        [IO.File]::WriteAllText($temp, ($Ports | ConvertTo-Json -Compress))
        if ([IO.File]::Exists($file)) { [IO.File]::Replace($temp, $file, [NullString]::Value) }
        else { [IO.File]::Move($temp, $file) }
    } finally {
        if ([IO.File]::Exists($temp)) { [IO.File]::Delete($temp) }
    }
}

function Get-LocalPortOwners([int]$Port) {
    Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
}

function Test-FreeLocalPort([int]$Port) {
    # Bind before assigning the port to catch excluded ports and IPv6-only listeners.
    $dualStack = [Net.Sockets.Socket]::OSSupportsIPv6
    $address = if ($dualStack) { [Net.IPAddress]::IPv6Any } else { [Net.IPAddress]::Any }
    $listener = [Net.Sockets.TcpListener]::new($address, $Port)
    try {
        if ($dualStack) { $listener.Server.DualMode = $true }
        $listener.ExclusiveAddressUse = $true
        $listener.Start()
        return $true
    } catch [Net.Sockets.SocketException] {
        return $false
    } finally {
        $listener.Stop()
    }
}

function Select-LocalPort {
    param([string]$Name, [int]$Preferred, [int]$Default,
          [int[]]$Reserved, [scriptblock]$IsOwned)
    foreach ($candidate in @($Preferred) + @($Default..($Default + 99) | Where-Object { $_ -ne $Preferred })) {
        if ($candidate -in $Reserved) { continue }
        if (Test-FreeLocalPort $candidate) {
            if ($candidate -ne $Preferred) {
                Write-Host "  $Name port $Preferred unavailable. Using port $candidate." -ForegroundColor Yellow
            }
            return $candidate
        }
        if ($candidate -eq $Preferred -and $IsOwned) {
            $owners = @(Get-LocalPortOwners $candidate)
            if ($owners.Count -gt 0 -and @($owners | Where-Object { -not (& $IsOwned $_) }).Count -eq 0) {
                return $candidate
            }
        }
    }
    throw "PORT_CONFLICT: No free local port for $Name near $Default."
}

function Get-TrackedMetroListener {
    param([int]$Port, [string]$PidFile)
    if (-not (Test-Path -LiteralPath $PidFile)) { return }
    $tracked = (Get-Content -LiteralPath $PidFile -Raw).Trim()
    if ($tracked -notmatch '^\d+$') { return }
    $ownerIds = @(Get-LocalPortOwners $Port)
    if ($ownerIds.Count -ne 1) { return }
    $process = Get-CimInstance Win32_Process -Filter "ProcessId = $($ownerIds[0])"
    if ($process.Name -ne 'node.exe' -or $process.CommandLine -notmatch '\bexpo\b') { return }
    for ($depth = 0; $process -and $depth -lt 8; $depth++) {
        if ($process.ProcessId -eq [int]$tracked) {
            if ($process.CommandLine -match "\bexpo\b|\bstart:device\b" -and
                $process.CreationDate -and
                $process.CreationDate.ToUniversalTime() -le (Get-Item -LiteralPath $PidFile).LastWriteTimeUtc) {
                return $ownerIds[0]
            }
            return
        }
        $parent = Get-CimInstance Win32_Process -Filter "ProcessId = $($process.ParentProcessId)"
        if (-not $parent -or $parent.CreationDate -gt $process.CreationDate) { return }
        $process = $parent
    }
}
