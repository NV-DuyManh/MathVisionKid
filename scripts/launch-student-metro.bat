@echo off
title MathVision Kids - Student Mobile (Metro LAN)
cd /d "%~dp0.."
echo ============================================================
echo  Starting Expo Metro Bundler on LAN (Default / Detected LAN IP:8081)
echo ============================================================
call npx expo start --lan --clear
pause
