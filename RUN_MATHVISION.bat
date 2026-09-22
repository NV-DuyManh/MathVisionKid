@echo off
setlocal enabledelayedexpansion

:: 1. Determine repository root safely
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: 2. Startup Banner
echo ============================================================
echo  MathVision Kids -- Complete Local Ecosystem Launcher
echo ============================================================
echo  Repository root: %SCRIPT_DIR%
echo.

:: 3. Pre-flight verification of required runtime files
echo [*] Verifying launcher prerequisites...
if not exist "infra\docker\docker-compose.yml" (
    set "FAIL_REASON=Prerequisite missing: infra\docker\docker-compose.yml"
    goto :launcher_failed
)
if not exist "backend\business-api\gradlew.bat" (
    set "FAIL_REASON=Prerequisite missing: backend\business-api\gradlew.bat"
    goto :launcher_failed
)
if not exist "apps\student-mobile\package.json" (
    set "FAIL_REASON=Prerequisite missing: apps\student-mobile\package.json"
    goto :launcher_failed
)
if not exist "apps\portal-web\package.json" (
    set "FAIL_REASON=Prerequisite missing: apps\portal-web\package.json"
    goto :launcher_failed
)
if not exist "tools\diagnostics\check_runtime.py" (
    set "FAIL_REASON=Prerequisite missing: tools\diagnostics\check_runtime.py"
    goto :launcher_failed
)
echo     Prerequisites verified successfully.
echo.

:: 4. Start Core Stack Services (Infrastructure, APIs, Web Portals)
echo [1/3] Starting Core Stack Services (Infrastructure, APIs, Web)...
call "%SCRIPT_DIR%scripts\start-all.bat"
if errorlevel 1 (
    set "FAIL_REASON=Core stack services failed to start or verify readiness"
    goto :launcher_failed
)

:: 5. Start Student Mobile Metro Bundler (LAN Mode)
echo.
echo [2/3] Starting Student Mobile Metro Bundler (LAN Mode)...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%scripts\start-student-metro.ps1"
if errorlevel 1 (
    set "FAIL_REASON=Failed to launch Student Metro Bundler"
    goto :launcher_failed
)

:: 6. Run Complete Ecosystem Diagnostics
echo.
echo [3/3] Verifying Complete Ecosystem Diagnostics...
set "PY_EXE=%SCRIPT_DIR%ai\runtime\.venv\Scripts\python.exe"
if not exist "%PY_EXE%" set "PY_EXE=python"
"%PY_EXE%" "%SCRIPT_DIR%tools\diagnostics\check_runtime.py"

:: 7. Launch Unified Portal Web in default browser
echo.
echo Launching Unified Portal Web in default browser...
start http://localhost:5172

echo.
echo ============================================================
echo  MathVision Kids -- Full Ecosystem Ready!
echo ============================================================
echo  - Unified Portal:  http://localhost:5172  (Main Entry)
echo  - Teacher Portal:  http://localhost:5173
echo  - Admin Portal:    http://localhost:5174
echo  - Student Mobile:  Visible Metro window (Scan QR with Expo Go)
echo  - Stop All:        scripts\stop-all.bat
echo ============================================================
echo.

exit /b 0

:launcher_failed
echo.
echo ============================================================
echo  [ERROR] MATHVISION KIDS STARTUP FAILED!
echo  Failing component: %FAIL_REASON%
echo  Log directory:     %SCRIPT_DIR%infra\local-runtime\logs\
echo ============================================================
echo.
echo The launcher will now pause so you can review the error details.
echo Press any key to exit...
pause >nul
exit /b 1
