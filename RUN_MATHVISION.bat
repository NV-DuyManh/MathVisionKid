@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title MathVision Kids - Local, Vercel and Expo Go QR

:: Windows PowerShell must load its own modules even when launched from PowerShell 7.
:: setlocal confines this search-path adjustment to the launcher and its children.
set "PSModulePath=%SystemRoot%\System32\WindowsPowerShell\v1.0\Modules;%PSModulePath%"

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
echo [1/4] Starting Core Stack Services (Infrastructure, APIs, Web)...
call "%SCRIPT_DIR%scripts\start-all.bat"
if errorlevel 1 (
    set "FAIL_REASON=Core stack services failed to start or verify readiness"
    goto :launcher_failed
)

:: 5. Start Student Mobile Metro Bundler (LAN Mode)
echo.
echo [2/4] Starting Student Mobile Metro Bundler (LAN Mode)...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%scripts\start-student-metro.ps1"
if errorlevel 1 (
    set "FAIL_REASON=Failed to launch Student Metro Bundler"
    goto :launcher_failed
)

:: 6. Run Complete Ecosystem Diagnostics
echo.
echo [3/4] Verifying Complete Ecosystem Diagnostics...
set "PY_EXE=%SCRIPT_DIR%ai\runtime\.venv\Scripts\python.exe"
if not exist "%PY_EXE%" set "PY_EXE=python"
"%PY_EXE%" "%SCRIPT_DIR%tools\diagnostics\check_runtime.py"
if errorlevel 1 (
    set "FAIL_REASON=Complete ecosystem diagnostics did not pass"
    goto :launcher_failed
)

:: 7. Resume the configured owner's public website without changing private setup
echo.
set "PUBLIC_WEB_STATUS=NOT_CONFIGURED"
set "PUBLIC_WEB_EXIT=0"
if exist "%SCRIPT_DIR%infra\local-runtime\pc-preview\.env.preview" (
    echo [4/4] Starting public API and updating the Vercel websites...
    echo This step may take a few minutes. Keep this window open.
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%scripts\deploy\Start-PC-Preview.ps1" -PublishWeb
    if errorlevel 1 (
        set "PUBLIC_WEB_STATUS=FAILED"
        set "PUBLIC_WEB_EXIT=1"
        echo [WARNING] Public website startup failed. Local services and Expo are still running.
        echo Review the error above and run this launcher again after fixing it.
    ) else (
        set "PUBLIC_WEB_STATUS=READY"
    )
) else (
    echo [4/4] Public website skipped: this checkout has no configured PC preview.
    echo Setup guide: docs\PC_PREVIEW_DEPLOYMENT.md
)

:: 8. Launch Unified Portal Web in default browser
echo.
echo Launching Unified Portal Web in default browser...
start http://localhost:5172

echo.
echo ============================================================
echo  MathVision Kids -- Local Ecosystem Ready!
echo ============================================================
echo  - Unified Portal:  http://localhost:5172  (Main Entry)
echo  - Teacher Portal:  http://localhost:5173
echo  - Admin Portal:    http://localhost:5174
echo  - Student Mobile:  Scan the Expo Go QR code below
echo  - Public Website: !PUBLIC_WEB_STATUS!
if "!PUBLIC_WEB_STATUS!"=="READY" echo  - Vercel Portal:   https://mathvisionkid-portal.vercel.app
echo  - Stop All:        scripts\stop-all.bat
echo  - Stop Public API: scripts\deploy\Stop-PC-Preview.ps1
echo ============================================================
echo.

node "%SCRIPT_DIR%scripts\dev\show-student-qr.cjs"
if errorlevel 1 (
    set "FAIL_REASON=Could not read the Student Mobile connection for Expo Go"
    goto :launcher_failed
)
echo.
echo Keep this window open to scan the QR code above.
echo Press any key to close this launcher. Services will keep running.
if "!PUBLIC_WEB_STATUS!"=="READY" echo Keep this PC awake and Docker running for public login and OCR.
pause >nul
exit /b !PUBLIC_WEB_EXIT!

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
