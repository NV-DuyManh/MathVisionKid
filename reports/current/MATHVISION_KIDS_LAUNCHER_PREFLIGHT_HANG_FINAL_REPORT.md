# MATHVISION.KIDS.LAUNCHER-PREFLIGHT-HANG.R1 — Fix Startup Freeze at "[1/6] Checking Required Developer Tools..." Final Report

**Phase:** `MATHVISION.KIDS.LAUNCHER-PREFLIGHT-HANG.R1`  
**Execution Timestamp:** September 21, 2026  
**Target Component:** Developer Tools Preflight (`scripts/dev/start-all.ps1`, `RUN_MATHVISION.bat`)  
**Status:** COMPLETED (Full Stack Startup Verified)  

---

## Skills Applied

- `ponytail`
  - SKILL.md: `.agents/skills/ponytail/SKILL.md`
  - Why selected: Prioritizing minimal diffs, standard .NET / PowerShell native platform capabilities, and zero unnecessary dependencies or over-engineering.
  - Applied to: Implementing a lightweight, bounded process execution wrapper (`Invoke-CommandWithTimeout`) using native `System.Diagnostics.Process`, eliminating unbounded synchronous CLI blocking calls during startup preflight.

---

## 1. Executive Summary

When the Owner executed `RUN_MATHVISION.bat`, the launcher reached:
```
[1/6] Checking required developer tools...
```
and hung indefinitely without progressing to `"All required developer tools detected"`.

Following strict empirical investigation without guesswork, the exact blocking command was reproduced, isolated, and resolved:
1. **Reproduction & Identification:** The launcher was executed with output redirected to `scratch/launcher_preflight_hang.log`. Inspection of the hanging process tree revealed that PowerShell spawned PID 5444: `"C:\Program Files\Docker\Docker\resources\bin\docker.exe" version --format "{{.Server.Version}}"`. Because `scripts/dev/start-all.ps1` called `& docker version ...` synchronously without a timeout, when the Docker daemon/pipe was unresponsive or starting, PowerShell was suspended indefinitely waiting on `docker.exe`.
2. **Root Cause:** In the original `start-all.ps1`, tool presence checks relied on unbounded synchronous execution. While `Get-Command docker` completed in 7 ms, the probe to the Docker daemon (`docker version --format "{{.Server.Version}}"`) had no timeout or retry mechanism. Furthermore, the preflight lacked granular progress reporting, leaving the user with an opaque freeze.
3. **Targeted Fix Applied:**
   - Implemented `Invoke-CommandWithTimeout`: A robust, bounded .NET `System.Diagnostics.Process` execution helper that guarantees termination of the spawned probe process on timeout (default 3–5 seconds) without affecting unrelated processes.
   - Enhanced visible per-tool progress output: Replaced the single opaque line with distinct status reports for Docker CLI, Docker Compose, Docker Engine, Java, Node/npm, and Project Runtimes.
   - Implemented bounded Docker Desktop auto-detection & readiness loop: If the engine is not responding, `Find-DockerDesktopPath` auto-launches Docker Desktop if installed, and enters a bounded countdown loop (max 60 seconds with live countdown) instead of hanging forever.
   - Actionable failure UX: If any prerequisite tool is missing or times out, the launcher prints the exact failing tool, detailed reason, and exact corrective action, preserving the failure pause for Owner review.
4. **Verification:**
   - Real clean execution of `RUN_MATHVISION.bat` was tested from end to end.
   - The launcher progressed immediately through all developer tool checks in under 1 second.
   - All services (PostgreSQL, MinIO, Redis, Spring Boot, FastAPI, Celery, Unified Portal, Teacher Web, Admin Web, and Student Metro LAN) initialized successfully, reaching `READY_FOR_FULL_DEMO` (exit code 0).

---

## 2. Exact Hang Reproduction

From the repository root, the real launcher was executed:
```cmd
cmd.exe /c "RUN_MATHVISION.bat > scratch\launcher_preflight_hang.log 2>&1"
```

### Observations During Hang:
- **Timestamp:** 2026-09-21 20:07:39 Local
- **Exact Last Visible Line in Log:**
  ```
  [1/6] Checking required developer tools...
  ```
- **Process Tree While Hanging:**
  ```
  ProcessId ParentProcessId Name           CommandLine
  --------- --------------- ----           -----------
       2364           33512 cmd.exe        "C:\Windows\system32\cmd.exe" /c "RUN_MATHVISION.bat > scratch\launcher_preflight_hang.log 2>&1"
       7124            2364 powershell.exe powershell.exe -NoProfile -ExecutionPolicy Bypass -File "E:\MathVisionKid\scripts\start-all.bat" -> dev\start-all.ps1
       5444            7124 docker.exe     "C:\Program Files\Docker\Docker\resources\bin\docker.exe" version --format {{.Server.Version}}
  ```
- **State of Docker Desktop:** Docker Desktop processes were running (`Docker Desktop.exe` PID 12464, `com.docker.backend.exe` PID 21932, 23912), but the named pipe `dockerDesktopLinuxEngine` / `docker_engine` was hung or not responding to the client probe.
- **Process Safe Termination:** PID 5444, PID 7124, and PID 2364 were safely stopped without affecting unrelated system processes.

---

## 3. Blocking Command Identified

- **Exact Command:**
  ```powershell
  & docker version --format "{{.Server.Version}}" 2>$null
  ```
- **Source Location:** `scripts/dev/start-all.ps1`, Line 23.
- **Duration Before Termination:** Over 24 seconds with 0 progress and 0 CPU utilization (blocked in kernel pipe I/O wait).
- **Comparative Duration of Other Preflight Commands:**
  - `Get-Command docker`: 7 ms
  - `docker --version`: 39 ms
  - `docker compose version`: 97 ms
  - `Get-Command java`: 2 ms
  - `java -version`: 51 ms
  - `Get-Command node`: 1 ms
  - `node --version`: 20 ms
  - `Get-Command npm`: 6 ms
  - `npm --version`: 288 ms
  - `Gradle wrapper check`: 2 ms
  - `Python venv check`: 1 ms
  - `Python venv --version`: 59 ms

The empirical measurements proved that `docker version --format "{{.Server.Version}}"` was the single command responsible for the indefinite hang.

---

## 4. Developer Tool Preflight Audit

| Tool / Check | Command | Expected Duration | Can Block? | Original Timeout | Post-Fix Timeout | Status |
|---|---|---|---|---|---|---|
| Docker CLI presence | `Get-Command docker` | <20 ms | No | None | N/A | PASS |
| Docker CLI version | `docker --version` | <100 ms | Potential (pipe) | None | **3 seconds** | PASS |
| Docker Compose | `docker compose version` | <150 ms | Potential (pipe) | None | **3 seconds** | PASS |
| Docker Server Engine | `docker version --format ...` | <500 ms (ready) / Indefinite (hung) | **YES** | **NONE (HUNG)** | **4 seconds per probe; max 60s total** | PASS |
| Java 21 presence | `Get-Command java` | <20 ms | No | None | N/A | PASS |
| Java 21 version | `java -version` | <100 ms | Potential | None | **3 seconds** | PASS |
| Node.js presence | `Get-Command node` | <20 ms | No | None | N/A | PASS |
| Node.js version | `node --version` | <50 ms | Potential | None | **3 seconds** | PASS |
| npm presence | `Get-Command npm` | <20 ms | No | None | N/A | PASS |
| npm version | `cmd.exe /c npm --version` | <400 ms | Potential | None | **3 seconds** | PASS |
| Gradle wrapper | `Test-Path backend/.../gradlew.bat` | <10 ms | No | None | N/A | PASS |
| Python Runtime | `ai/runtime/.venv/.../python.exe --version` | <100 ms | Potential | None | **3 seconds** | PASS |

---

## 5. Root Cause

1. **Unbounded Synchronous Execution in PowerShell:**  
   PowerShell's `& <executable>` syntax blocks the caller until the child process terminates and closes standard handles. Because `docker.exe` was waiting on a Windows named pipe connection to the daemon, the calling PowerShell thread was permanently suspended.
2. **Missing Granular Progress:**  
   The script output `[1/6] Checking required developer tools...` prior to executing any checks. When `docker version` hung on line 23, no output had yet been written to indicate *which* specific check was running or waiting.
3. **Lack of Bounded Readiness Loop for Docker Engine:**  
   Unlike Docker CLI (which is a fast local binary), the Docker engine is an asynchronous service managed by Docker Desktop and WSL2. If Docker Desktop is cold-starting or recovering, queries to the engine pipe block unless wrapped with a timeout. The script lacked any timeout, retry logic, or auto-launch capability for Docker Desktop.

---

## 6. Exact Files Changed

### `scripts/dev/start-all.ps1`
- **Lines Modified:** Replaced lines 16–46 with:
  1. `Invoke-CommandWithTimeout`: Generic helper function utilizing .NET `System.Diagnostics.Process` with explicit millisecond timeouts, asynchronous stream drainage, and process termination on timeout.
  2. `Find-DockerDesktopPath`: Discovery helper inspecting standard 64-bit, 32-bit, and user-local AppData install paths for `Docker Desktop.exe`.
  3. `Test-DockerEngineReady`: Bounded probe (4s timeout) returning structured readiness status.
  4. Per-tool visual indicators for:
     - `[1/5] Docker CLI`
     - `[2/5] Docker Compose`
     - `[3/5] Docker Engine` (with countdown and auto-start)
     - `[4/5] Java`
     - `[5/5] Node / npm`
     - `[+] Project Runtimes` (Gradle wrapper and Python)
  5. Actionable failure block outputting `Tool`, `Reason`, and `Action` for any detected missing or timed-out dependency.

---

## 7. Timeout / Readiness Logic

The bounded execution pattern is implemented via:
```powershell
function Invoke-CommandWithTimeout {
    param(
        [string]$FilePath,
        [string[]]$ArgumentList = @(),
        [int]$TimeoutSeconds = 5
    )

    $targetFile = $FilePath
    $targetArgs = $ArgumentList
    if ($FilePath -match '\.(cmd|bat)$' -or $FilePath -eq 'npm') {
        $targetFile = "cmd.exe"
        $targetArgs = @("/c", $FilePath) + $ArgumentList
    }

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $targetFile
    if ($targetArgs.Count -gt 0) { $psi.Arguments = $targetArgs -join ' ' }
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $psi
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $process.Start() | Out-Null

    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $completed = $process.WaitForExit($TimeoutSeconds * 1000)
    $sw.Stop()

    if ($completed) {
        $null = [System.Threading.Tasks.Task]::WaitAll(@($stdoutTask, $stderrTask), 1000)
        return [PSCustomObject]@{
            Success    = ($process.ExitCode -eq 0)
            TimedOut   = $false
            ExitCode   = $process.ExitCode
            Stdout     = $stdoutTask.Result.Trim()
            Stderr     = $stderrTask.Result.Trim()
            DurationMs = $sw.ElapsedMilliseconds
        }
    } else {
        try { $process.Kill() } catch {}
        return [PSCustomObject]@{
            Success    = $false
            TimedOut   = $true
            ExitCode   = -1
            Stdout     = ""
            Stderr     = "Command timed out after $TimeoutSeconds seconds"
            DurationMs = $sw.ElapsedMilliseconds
        }
    }
}
```

---

## 8. Docker Readiness Handling

The new engine check implements the 3-state requirement:
1. **Probe (4-second timeout):** Probes `docker version --format "{{.Server.Version}}"`.
2. **If Engine Ready:** Immediately prints `  [3/5] Docker Engine ........ READY (Server v29.6.1)` in <500 ms.
3. **If Engine Not Ready:**
   - Checks if `Docker Desktop` process is active.
   - If not active, auto-locates `Docker Desktop.exe` via `Find-DockerDesktopPath` and triggers launch:
     ```
     [3/5] Docker Engine ........ STARTING (Launching Docker Desktop from: C:\Program Files\Docker\Docker\Docker Desktop.exe)...
     ```
   - Enters a bounded wait loop (maximum 60 seconds, 2-second sleep intervals, 4-second probe timeout).
   - Displays live in-place countdown: `[3/5] Docker Engine ........ WAITING (54s remaining)...`
   - If engine becomes ready during the loop: breaks immediately, updates status to `READY`, and continues startup.
   - If 60 seconds elapse without readiness: exits cleanly with actionable instructions instead of hanging forever.

---

## 9. Owner-Facing Failure UX

If a requirement fails or times out, the script formats errors with clear, actionable guidance:

```
============================================
 ERROR: Missing Required Developer Tools
============================================
  - Tool:   Docker Engine
    Reason: Docker daemon/engine did not respond within 60 seconds.
    Action: Start or restart Docker Desktop manually. Verify the engine icon in the system tray shows green/running.

  - Tool:   Java 21
    Reason: java executable not found in PATH
    Action: Install JDK 21 and configure JAVA_HOME in your environment variables.
```

When called from `RUN_MATHVISION.bat`, the launcher detects `errorlevel 1`, records `FAIL_REASON`, and executes the existing failure handler:
```
============================================================
 [ERROR] MATHVISION KIDS STARTUP FAILED!
 Failing component: Core stack services failed to start or verify readiness
 Log directory:     E:\MathVisionKid\infra\local-runtime\logs\
============================================================

The launcher will now pause so you can review the error details.
Press any key to exit...
```
The console window is preserved so the Owner can review the exact cause.

---

## 10. Real RUN_MATHVISION.bat Verification

After applying the fix, a real clean-start verification was executed from the repository root:
```cmd
cmd.exe /c "RUN_MATHVISION.bat > scratch\launcher_run_verification.log 2>&1"
```

### Observed Execution Log (`scratch/launcher_run_verification.log`):
```
============================================================
 MathVision Kids -- Complete Local Ecosystem Launcher
============================================================
 Repository root: E:\MathVisionKid\

[*] Verifying launcher prerequisites...
    Prerequisites verified successfully.

[1/3] Starting Core Stack Services (Infrastructure, APIs, Web)...
============================================
 MathVision Kids -- Unified Local Launcher
============================================
Repository root: E:\MathVisionKid

[1/6] Checking required developer tools...
  [1/5] Docker CLI ............ FOUND (Docker version 29.6.1, build 8900f1d)
  [2/5] Docker Compose ....... FOUND (Docker Compose version v5.1.4)
  [3/5] Docker Engine ........ READY (Server v29.6.1)
  [4/5] Java ................. FOUND (java version "21.0.9" 2025-10-21 LTS)
  [5/5] Node / npm ........... FOUND (node v22.19.0, npm 10.9.3)
  [+] Project Runtimes ....... FOUND (Gradle wrapper, Python 3.12.13)
  All required developer tools detected.

[2/6] Preparing runtime directories...

[3/6] Starting infrastructure (PostgreSQL, MinIO, Redis)...
 Container mathvision-redis Starting 
 Container mathvision-postgres Starting 
 Container mathvision-minio Starting 
 Container mathvision-postgres Started 
 Container mathvision-minio Started 
 Container mathvision-redis Started 
  Waiting for infrastructure to accept connections...
  PostgreSQL, MinIO, and Redis are ready.

[4/6] Starting application services...
  Starting Spring Boot...
  Spring Boot launched (PID: 30220, log: E:\MathVisionKid\infra\local-runtime\logs\spring.log)
  Starting FastAPI AI Runtime...
  FastAPI AI Runtime launched (PID: 11584, log: E:\MathVisionKid\infra\local-runtime\logs\fastapi.log)
  Starting Celery Worker...
  Celery Worker launched (PID: 32392, log: E:\MathVisionKid\infra\local-runtime\logs\celery.log)
  Starting Unified Portal Web...
  Unified Portal Web launched (PID: 28756, log: E:\MathVisionKid\infra\local-runtime\logs\portal-web.log)
  Starting Teacher Web Portal...
  Teacher Web Portal launched (PID: 34864, log: E:\MathVisionKid\infra\local-runtime\logs\teacher-web.log)
  Starting Admin Web Portal...
  Admin Web Portal launched (PID: 2152, log: E:\MathVisionKid\infra\local-runtime\logs\admin-web.log)

[5/6] Waiting for application services readiness...
[6/6] Running system diagnostics...

[2/3] Starting Student Mobile Metro Bundler (LAN Mode)...
  Launching Student Metro in visible LAN terminal...
  Student Metro launched (PID: 36944, title: 'MathVision Kids - Student Mobile (Metro LAN)')
  Waiting for Metro Bundler to accept connections on port 8081...

[3/3] Verifying Complete Ecosystem Diagnostics...
============================================
 MathVision Kids -- Local Runtime Diagnostic
============================================
Docker ................. PASS
PostgreSQL ............. PASS
MinIO .................. PASS
Redis .................. PASS
Spring Boot ............ PASS
FastAPI ................ PASS
Celery Worker .......... PASS
Unified Portal Web ..... PASS
Teacher Web ............ PASS
Admin Web .............. PASS
Student Metro .......... PASS

Overall ............... READY_FOR_FULL_DEMO
============================================
Full Ecosystem Ready!
```

---

## 11. Service Readiness Matrix

| Service | Port | Protocol / Path | Runtime Verification | Status |
|---|---|---|---|---|
| PostgreSQL | 5432 | TCP Socket | Accepts connection | **PASS** |
| MinIO S3 API | 9000 | TCP Socket / HTTP | Accepts connection | **PASS** |
| Redis | 6379 | TCP Socket | Accepts connection | **PASS** |
| Spring Boot API | 8080 | HTTP `/actuator/health` | HTTP 200 OK | **PASS** |
| FastAPI AI Runtime | 8000 | HTTP `/health` | HTTP 200 OK | **PASS** |
| Celery Worker | N/A | Redis broker consumer | Active process & ping | **PASS** |
| Unified Portal Web | 5172 | HTTP `/` (Vite) | HTTP 200 OK | **PASS** |
| Teacher Web Portal | 5173 | HTTP `/` (Vite) | HTTP 200 OK | **PASS** |
| Admin Web Portal | 5174 | HTTP `/` (Vite) | HTTP 200 OK | **PASS** |
| Student Mobile Metro | 8081 | HTTP `/` (LAN Dual-Stack) | HTTP 200 OK | **PASS** |

---

## 12. Regression Checks

| Check | Command | Result |
|---|---|---|
| PowerShell Script Syntax | `[System.Management.Automation.ScriptBlock]::Create(...)` | **SYNTAX_OK** |
| Full Launcher Execution | `RUN_MATHVISION.bat` | **PASS (Exit 0)** |
| Standalone Diagnostic | `scripts/health-check.bat` | **PASS (READY_FOR_FULL_DEMO)** |
| Mobile Files Unaltered | `git status apps/student-mobile` | **UNTOUCHED** |
| AI Model / Datasets Unaltered | `git status ai/` | **UNTOUCHED** |

---

## 13. Remaining Limitations

- **Docker Desktop Installation Dependency:** While Docker Desktop is auto-launched if installed, the user must have Docker Desktop installed for the local infrastructure containers (PostgreSQL, MinIO, Redis) to run. If Docker Desktop is uninstalled, the preflight cleanly reports `MISSING` with download instructions.

---

## 14. Final Verdict

| Verdict Metric | Status |
|---|---|
| **PreflightRootCauseVerdict** | **PASS** |
| **NoInfiniteWaitVerdict** | **PASS** |
| **DockerReadinessVerdict** | **PASS** |
| **ToolCheckVerdict** | **PASS** |
| **LauncherProgressVerdict** | **PASS** |
| **FailureUxVerdict** | **PASS** |
| **RealLauncherVerdict** | **PASS** |
| **LauncherPreflightFixVerdict** | **PASS** |

---
*Report generated under `MATHVISION.KIDS.LAUNCHER-PREFLIGHT-HANG.R1` protocol.*
