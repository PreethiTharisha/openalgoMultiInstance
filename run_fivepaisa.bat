@echo off
REM OpenAlgo Instance 3 Startup Script
REM This script loads environment variables from .env.fivepaisa and starts Instance 3

setlocal enabledelayedexpansion
cd /d "%~dp0"

REM Set the environment file path FIRST (before loading variables)
set OPENALGO_ENV_FILE=%cd%\.env.fivepaisa

REM Check if the .env file exists
if not exist "%OPENALGO_ENV_FILE%" (
    echo Error: %OPENALGO_ENV_FILE% not found!
    echo Please ensure .env.fivepaisa exists in the current directory.
    pause
    exit /b 1
)

echo Loading environment variables from .env.fivepaisa...
for /f "usebackq tokens=1* delims==" %%a in ("%OPENALGO_ENV_FILE%") do (
    if not "%%a"=="" (
        if not "%%a:~0,1%%"=="#" (
            set "%%a=%%b"
        )
    )
)

echo.
echo Starting OpenAlgo Instance 3 (FivePaisa)...
echo FLASK_PORT=%FLASK_PORT%
echo WEBSOCKET_PORT=%WEBSOCKET_PORT%
echo DATABASE_URL=%DATABASE_URL%
echo OPENALGO_ENV_FILE=%OPENALGO_ENV_FILE%
echo.

python app.py

pause
