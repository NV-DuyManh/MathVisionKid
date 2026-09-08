@echo off
setlocal

:: Determine repository root
set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%.."
set "REPO_ROOT=%CD%"
popd

:: Locate Python
if exist "%REPO_ROOT%\services\ai-service\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%REPO_ROOT%\services\ai-service\.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

:: Execute diagnostic tool
"%PYTHON_EXE%" "%REPO_ROOT%\tools\diagnostics\check_runtime.py"
exit /b %ERRORLEVEL%
