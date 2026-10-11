@echo off
cd /d "%~dp0"

echo Loading environment variables from .env.indmoney...
for /f "usebackq tokens=1* delims==" %%a in (.env.indmoney) do (
    if not "%%a"=="" (
        if not "%%a:~0,1%%"=="#" (
            set "%%a=%%b"
        )
    )
)

set OPENALGO_ENV_FILE=%cd%\.env.indmoney

echo FLASK_PORT=%FLASK_PORT%
echo WEBSOCKET_PORT=%WEBSOCKET_PORT%
echo DATABASE_URL=%DATABASE_URL%
echo OPENALGO_ENV_FILE=%OPENALGO_ENV_FILE%

python -c "import os; print('OPENALGO_ENV_FILE from Python:', os.getenv('OPENALGO_ENV_FILE'))"
