@echo off
setlocal
title MathVision Kids - Setup
set "PSModulePath=%SystemRoot%\System32\WindowsPowerShell\v1.0\Modules;%PSModulePath%"
set "SETUP_PS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if exist "%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe" set "SETUP_PS=%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe"
"%SETUP_PS%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\dev\setup-local.ps1" %*
set "SETUP_EXIT=%ERRORLEVEL%"
echo.
if /i "%~1"=="-NoPause" goto :setup_exit
pause >nul
:setup_exit
exit /b %SETUP_EXIT%
