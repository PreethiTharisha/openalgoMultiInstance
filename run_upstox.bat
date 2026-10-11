@echo off
REM OpenAlgo Upstox Instance Startup Script
REM This script loads environment variables from .env.upstox and starts the application
REM
REM Usage:
REM   1. Create a .env.upstox file in the same directory as this script
REM   2. Add your Upstox broker configuration to .env.upstox
REM   3. Run this script to start OpenAlgo with Upstox environment variables

setlocal enabledelayedexpansion
cd /d "%~dp0"

REM Set the environment file path FIRST (before loading variables)
set OPENALGO_ENV_FILE=%cd%\.env.upstox

REM Check if the .env file exists
if not exist "%OPENALGO_ENV_FILE%" (
    echo Error: %OPENALGO_ENV_FILE% not found!
    echo.
    echo Please create .env.upstox in the current directory with your Upstox configuration.
    echo You can use .sample.env as a template and customize it for Upstox.
    echo.
    echo Example .env.upstox variables:
    echo   BROKER_API_KEY=your_upstox_api_key
    echo   BROKER_API_SECRET=your_upstox_api_secret
    echo   FLASK_PORT=5000
    echo   WEBSOCKET_PORT=8765
    echo.
    pause
    exit /b 1
)

echo Loading environment variables from .env.upstox...
for /f "usebackq tokens=1* delims==" %%a in ("%OPENALGO_ENV_FILE%") do (
    if not "%%a"=="" (
        if not "%%a:~0,1%%"=="#" (
            set "%%a=%%b"
        )
    )
)

echo.
echo Starting OpenAlgo with Upstox Configuration...
echo FLASK_PORT=%FLASK_PORT%
echo WEBSOCKET_PORT=%WEBSOCKET_PORT%
echo DATABASE_URL=%DATABASE_URL%
echo OPENALGO_ENV_FILE=%OPENALGO_ENV_FILE%
echo.

python app.py

pause
