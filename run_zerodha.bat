@echo off
REM OpenAlgo Instance 2 Startup Script
REM This script loads environment variables from .env.zerodha and starts Instance 2

setlocal enabledelayedexpansion
cd /d "%~dp0"

REM Set the environment file path FIRST (before loading variables)
set OPENALGO_ENV_FILE=%cd%\.env.zerodha

REM Check if the .env file exists
if not exist "%OPENALGO_ENV_FILE%" (
    echo Error: %OPENALGO_ENV_FILE% not found!
    echo Please ensure .env.zerodha exists in the current directory.
    pause
    exit /b 1
)

echo Loading environment variables from .env.zerodha...
for /f "usebackq tokens=1* delims==" %%a in ("%OPENALGO_ENV_FILE%") do (
    if not "%%a"=="" (
        if not "%%a:~0,1%%"=="#" (
            set "%%a=%%b"
        )
    )
)

echo.
echo Starting OpenAlgo Instance 2 (Zerodha)...
echo FLASK_PORT=%FLASK_PORT%
echo WEBSOCKET_PORT=%WEBSOCKET_PORT%
echo DATABASE_URL=%DATABASE_URL%
echo OPENALGO_ENV_FILE=%OPENALGO_ENV_FILE%
echo.

python app.py

pause
