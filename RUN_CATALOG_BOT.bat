@echo off
setlocal
cd /d "%~dp0"
set "CATALOG_PY=ai\runtime\.venv\Scripts\python.exe"
if not exist "%CATALOG_PY%" set "CATALOG_PY=python"
set "CATALOG_DB=%LESSON_CATALOG_PATH%"
if not defined CATALOG_DB set "CATALOG_DB=ai\runtime\state\lesson-catalog.sqlite3"
"%CATALOG_PY%" ai\runtime\scripts\catalog_bot.py --database "%CATALOG_DB%"
set "CATALOG_EXIT=%ERRORLEVEL%"
if /I "%~1"=="--no-open" exit /b %CATALOG_EXIT%
if %CATALOG_EXIT% GTR 1 (
  echo The bot did not run. An older report will not be opened.
  pause
  exit /b %CATALOG_EXIT%
)
if not exist ".local-artifacts\catalog-bot\index.html" (
  echo Catalog report could not be created. Check the Python installation.
  pause
  exit /b %CATALOG_EXIT%
)
start "" ".local-artifacts\catalog-bot\index.html"
if not "%CATALOG_EXIT%"=="0" (
  echo The catalog needs attention. See the report that just opened.
  pause
)
exit /b %CATALOG_EXIT%
