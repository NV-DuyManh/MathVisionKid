@echo off
setlocal
title MathVision Kids - Setup
set "PSModulePath=%SystemRoot%\System32\WindowsPowerShell\v1.0\Modules;%PSModulePath%"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\dev\setup-local.ps1" %*
set "SETUP_EXIT=%ERRORLEVEL%"
echo.
pause >nul
exit /b %SETUP_EXIT%
