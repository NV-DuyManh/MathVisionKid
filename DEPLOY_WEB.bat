@echo off
setlocal
chcp 65001 >nul
title MathVision Kids - Deploy Web
set "PSModulePath=%SystemRoot%\System32\WindowsPowerShell\v1.0\Modules;%PSModulePath%"
cd /d "%~dp0"

echo ============================================================
echo  MathVision Kids -- Deploy Web
echo ============================================================
if not exist "%~dp0infra\local-runtime\pc-preview\.env.preview" (
    echo [ERROR] This checkout has no private web deployment configuration.
    echo Follow docs\PC_PREVIEW_DEPLOYMENT.md for first-time setup.
    goto :failed
)
echo Building the API and OCR services, then publishing the websites.
echo Keep this window open until deployment completes.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\deploy\Start-PC-Preview.ps1" -Build -PublishWeb
if errorlevel 1 goto :failed

echo.
echo WEB DEPLOYMENT COMPLETE
echo https://mathvisionkid-portal.vercel.app
echo https://mathvisionkid-teacher.vercel.app
echo https://mathvisionkid-admin.vercel.app
echo Keep this PC awake and Docker running for login and OCR.
echo Stop public services: scripts\deploy\Stop-PC-Preview.ps1
pause >nul
exit /b 0

:failed
echo.
echo [ERROR] WEB DEPLOYMENT FAILED. Review the error above.
echo Existing data and configuration are retained.
pause >nul
exit /b 1
