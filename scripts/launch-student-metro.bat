@echo off
title MathVision Kids - Student Mobile (Metro LAN)
cd /d "D:\nhom6\TRAINT~1\MathVisionKid"
set REACT_NATIVE_PACKAGER_HOSTNAME=192.168.88.56
echo ============================================================
echo  Starting Expo Metro Bundler on LAN (192.168.88.56:8081)
echo ============================================================
set "PATH=D:\z6;%PATH%"
call "D:\z6\npx.cmd" expo start --lan --clear
pause
