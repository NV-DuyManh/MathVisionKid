@echo off
setlocal
title MathVision Kids - Stop
call "%~dp0scripts\stop-all.bat"
set "STOP_EXIT=%ERRORLEVEL%"
echo.
pause
exit /b %STOP_EXIT%
