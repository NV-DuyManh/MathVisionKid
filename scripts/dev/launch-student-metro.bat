@echo off
title MathVision Kids - Student Mobile (Metro LAN)
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%..\..\apps\student-mobile"
echo ============================================================
echo  Starting Expo Metro Bundler on LAN (Default / Detected LAN IP:8081)
echo ============================================================
call npx expo start --lan --clear
pause
