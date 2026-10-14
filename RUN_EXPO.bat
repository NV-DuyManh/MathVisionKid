@echo off
setlocal
:: Reuse the local launcher; it never publishes the website.
call "%~dp0RUN_MATHVISION.bat"
exit /b %ERRORLEVEL%
