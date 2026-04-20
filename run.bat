@echo off
title Options Lotto Toolkit
cd /d "%~dp0"

echo.
echo  ==========================================
echo   OPTIONS LOTTO TOOLKIT
echo  ==========================================
echo.

:: Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    py --version >nul 2>&1
    if errorlevel 1 (
        echo  ERROR: Python not found.
        echo  Install from https://www.python.org/downloads/
        echo  Make sure to check "Add Python to PATH" during install.
        echo.
        pause
        exit /b 1
    )
    set PYTHON=py
) else (
    set PYTHON=python
)

:: Install / update dependencies silently
echo  Checking dependencies...
%PYTHON% -m pip install -r requirements.txt -q --disable-pip-version-check
echo  Dependencies OK.
echo.

:: Open browser after 2 seconds in background
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:5000"

echo  Starting server at http://localhost:5000
echo  Press Ctrl+C to stop.
echo.

%PYTHON% app.py

echo.
echo  Server stopped.
pause
