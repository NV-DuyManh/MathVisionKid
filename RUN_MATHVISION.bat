@echo off
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"

echo ============================================================
echo  MathVision Kids -- Complete Local Ecosystem Launcher
echo ============================================================
echo [1/3] Starting Core Stack Services...
call "%SCRIPT_DIR%scripts\start-all.bat"
if errorlevel 1 (
    echo [ERROR] Core stack failed to start.
    exit /b %ERRORLEVEL%
)

echo.
echo [2/3] Starting Student Mobile Metro Bundler (LAN Mode)...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%scripts\start-student-metro.ps1"
if errorlevel 1 (
    echo [ERROR] Failed to launch Student Metro.
    exit /b %ERRORLEVEL%
)

echo.
echo [3/3] Verifying Complete Ecosystem Diagnostics...
set "PY_EXE=%SCRIPT_DIR%services\ai-service\.venv\Scripts\python.exe"
if not exist "%PY_EXE%" set "PY_EXE=python"
"%PY_EXE%" "%SCRIPT_DIR%tools\diagnostics\check_runtime.py"

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

exit /b 0
