# OpenAlgo Multi-Instance Setup Guide

This guide explains how to run multiple OpenAlgo instances on the same machine with different brokers and configurations.

## Overview

OpenAlgo now supports running multiple instances simultaneously, each with:
- Different broker configurations (e.g., IndMoney, Zerodha, FivePaisa)
- Different port numbers (Flask and WebSocket)
- Different databases
- Different API keys and secrets

**Supported Instances:**
- Instance 1: IndMoney (Port 5003)
- Instance 2: Zerodha (Port 5004)
- Instance 3: FivePaisa (Port 5005)
- Additional instances can be added following the same pattern

## Setup Instructions

### 1. Create Environment Files

Create separate `.env` files for each instance:

**For Instance 1 (IndMoney):**
- File: `.env.indmoney`
- Configure with:
  - `FLASK_PORT=5003`
  - `HOST_SERVER=http://127.0.0.1:5003` ⚠️ **IMPORTANT: Must match FLASK_PORT**
  - `WEBSOCKET_PORT=8767`
  - `WEBSOCKET_URL=ws://127.0.0.1:8767` ⚠️ **IMPORTANT: Must match WEBSOCKET_PORT**
  - `DATABASE_URL=sqlite:///db/openalgo_indmoney.db`
  - Broker credentials for IndMoney
  - Other required variables (copy from `.sample.env`)

**For Instance 2 (Zerodha):**
- File: `.env.zerodha`
- Configure with:
  - `FLASK_PORT=5004`
  - `HOST_SERVER=http://127.0.0.1:5004` ⚠️ **IMPORTANT: Must match FLASK_PORT**
  - `WEBSOCKET_PORT=8768`
  - `WEBSOCKET_URL=ws://127.0.0.1:8768` ⚠️ **IMPORTANT: Must match WEBSOCKET_PORT**
  - `DATABASE_URL=sqlite:///db/openalgo_zerodha.db`
  - Broker credentials for Zerodha
  - Other required variables (copy from `.sample.env`)

**For Instance 3 (FivePaisa):**
- File: `.env.fivepaisa`
- Configure with:
  - `FLASK_PORT=5005`
  - `HOST_SERVER=http://127.0.0.1:5005` ⚠️ **IMPORTANT: Must match FLASK_PORT**
  - `WEBSOCKET_PORT=8769`
  - `WEBSOCKET_URL=ws://127.0.0.1:8769` ⚠️ **IMPORTANT: Must match WEBSOCKET_PORT**
  - `DATABASE_URL=sqlite:///db/openalgo_fivepaisa.db`
  - Broker credentials for FivePaisa
  - Other required variables (copy from `.sample.env`)

### 2. Update Port Numbers and HOST_SERVER

Ensure each instance uses **unique port numbers** and **matching HOST_SERVER**:

```
Instance 1 (IndMoney):
  - FLASK_PORT=5003
  - HOST_SERVER=http://127.0.0.1:5003  ⚠️ MUST MATCH FLASK_PORT
  - WEBSOCKET_PORT=8767
  - WEBSOCKET_URL=ws://127.0.0.1:8767  ⚠️ MUST MATCH WEBSOCKET_PORT
  - DATABASE_URL=sqlite:///db/openalgo_indmoney.db

Instance 2 (Zerodha):
  - FLASK_PORT=5004
  - HOST_SERVER=http://127.0.0.1:5004  ⚠️ MUST MATCH FLASK_PORT
  - WEBSOCKET_PORT=8768
  - WEBSOCKET_URL=ws://127.0.0.1:8768  ⚠️ MUST MATCH WEBSOCKET_PORT
  - DATABASE_URL=sqlite:///db/openalgo_zerodha.db

Instance 3 (FivePaisa):
  - FLASK_PORT=5005
  - HOST_SERVER=http://127.0.0.1:5005  ⚠️ MUST MATCH FLASK_PORT
  - WEBSOCKET_PORT=8769
  - WEBSOCKET_URL=ws://127.0.0.1:8769  ⚠️ MUST MATCH WEBSOCKET_PORT
  - DATABASE_URL=sqlite:///db/openalgo_fivepaisa.db
```

**⚠️ CRITICAL:** The `HOST_SERVER` variable **MUST** match the `FLASK_PORT`. This is used for:
- Session cookie domain isolation (prevents cookies from being shared across ports)
- OAuth callback URLs
- External links in emails and alerts

### 3. Update Secret Keys

Each instance should have **unique secret keys**:

```
Instance 1:
  - APP_KEY=<unique_random_key_1>
  - API_KEY_PEPPER=<unique_random_pepper_1>

Instance 2:
  - APP_KEY=<unique_random_key_2>
  - API_KEY_PEPPER=<unique_random_pepper_2>
```

You can generate random keys using Python:
```python
import secrets
print(secrets.token_hex(32))
```

### 4. Running Instances

#### Option A: Using Batch Files (Windows)

**For Instance 1 (IndMoney):**
```batch
run_instance1.bat
```

**For Instance 2 (Zerodha):**
```batch
run_instance2.bat
```

**For Instance 3 (FivePaisa):**
```batch
run_instance3.bat
```

Each batch file will:
1. Load environment variables from the respective `.env` file
2. Set `OPENALGO_ENV_FILE` environment variable
3. Display the loaded configuration
4. Start the Flask application

#### Option B: Manual Command Line

**For Instance 1:**
```bash
set OPENALGO_ENV_FILE=D:\path\to\.env.indmoney
python app.py
```

**For Instance 2:**
```bash
set OPENALGO_ENV_FILE=D:\path\to\.env.zerodha
python app.py
```

#### Option C: Using Python Directly

```bash
OPENALGO_ENV_FILE=.env.indmoney python app.py
OPENALGO_ENV_FILE=.env.zerodha python app.py
```

## How It Works

### Environment Variable Loading

1. **Batch File Sets OPENALGO_ENV_FILE:**
   - The batch file sets the `OPENALGO_ENV_FILE` environment variable before launching Python
   - This variable points to the specific `.env` file for that instance

2. **Python Reads OPENALGO_ENV_FILE:**
   - `utils/env_check.py` checks for the `OPENALGO_ENV_FILE` environment variable
   - If set, it loads from that file instead of the default `.env`
   - If not set, it falls back to the default `.env` file

3. **Application Uses Loaded Variables:**
   - Flask uses `FLASK_PORT` and `FLASK_HOST_IP` from the loaded `.env`
   - WebSocket server uses `WEBSOCKET_PORT` from the loaded `.env`
   - Database uses `DATABASE_URL` from the loaded `.env`
   - Broker uses credentials from the loaded `.env`

## Batch File Details

### run_instance1.bat

```batch
@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

REM Set the environment file path FIRST
set OPENALGO_ENV_FILE=%cd%\.env.indmoney

REM Check if the .env file exists
if not exist "%OPENALGO_ENV_FILE%" (
    echo Error: %OPENALGO_ENV_FILE% not found!
    pause
    exit /b 1
)

REM Load environment variables from .env.indmoney
echo Loading environment variables from .env.indmoney...
for /f "usebackq tokens=1* delims==" %%a in ("%OPENALGO_ENV_FILE%") do (
    if not "%%a"=="" (
        if not "%%a:~0,1%%"=="#" (
            set "%%a=%%b"
        )
    )
)

REM Display loaded configuration
echo.
echo Starting OpenAlgo Instance 1 (IndMoney)...
echo FLASK_PORT=%FLASK_PORT%
echo WEBSOCKET_PORT=%WEBSOCKET_PORT%
echo DATABASE_URL=%DATABASE_URL%
echo OPENALGO_ENV_FILE=%OPENALGO_ENV_FILE%
echo.

REM Start the application
python app.py

pause
```

### run_instance2.bat

Same as above, but uses `.env.zerodha` instead of `.env.indmoney`.

## Troubleshooting

### Issue: Login on port 5003 redirects to port 5000 and logs out

**Cause:** The `HOST_SERVER` variable is not set correctly. It's still pointing to `http://127.0.0.1:5000` instead of the instance's port. This causes:
1. Session cookies to be shared across all ports (no domain isolation)
2. OAuth callbacks to redirect to the wrong port
3. The browser to use the session from port 5000 when accessing port 5003

**Solution:**
1. **Update `HOST_SERVER` in `.env.indmoney`:**
   ```
   HOST_SERVER=http://127.0.0.1:5003
   ```
2. **Update `HOST_SERVER` in `.env.zerodha`:**
   ```
   HOST_SERVER=http://127.0.0.1:5004
   ```
3. **Update `WEBSOCKET_URL` to match `WEBSOCKET_PORT`:**
   ```
   Instance 1: WEBSOCKET_URL=ws://127.0.0.1:8767
   Instance 2: WEBSOCKET_URL=ws://127.0.0.1:8768
   ```
4. **Clear browser cookies** for `127.0.0.1` (all ports)
5. **Restart both instances**

### Issue: Application still uses default port (5000)

**Cause:** The `OPENALGO_ENV_FILE` environment variable is not being set before Python starts.

**Solution:**
1. Verify the batch file is setting `OPENALGO_ENV_FILE` correctly
2. Check that the `.env.indmoney` or `.env.zerodha` file exists in the correct directory
3. Verify the port numbers are correctly set in the `.env` file
4. Run the batch file and check the output for the loaded port numbers

### Issue: "Error: .env file not found"

**Cause:** The `.env.indmoney` or `.env.zerodha` file doesn't exist.

**Solution:**
1. Create the missing `.env` file by copying from `.sample.env`
2. Update the configuration for your broker
3. Ensure the file is in the same directory as the batch file

### Issue: Port already in use

**Cause:** Another instance is already running on that port.

**Solution:**
1. Stop the other instance
2. Use different port numbers for each instance
3. Check which process is using the port:
   ```bash
   netstat -ano | findstr :5003
   ```

### Issue: Database locked error

**Cause:** Multiple instances are trying to use the same database file.

**Solution:**
1. Ensure each instance uses a different `DATABASE_URL`
2. Example:
   - Instance 1: `sqlite:///db/openalgo_indmoney.db`
   - Instance 2: `sqlite:///db/openalgo_zerodha.db`

## Accessing Instances

Once running, access each instance at:

**Instance 1 (IndMoney):**
- Web: http://127.0.0.1:5003
- WebSocket: ws://127.0.0.1:8767

**Instance 2 (Zerodha):**
- Web: http://127.0.0.1:5004
- WebSocket: ws://127.0.0.1:8768

**Instance 3 (FivePaisa):**
- Web: http://127.0.0.1:5005
- WebSocket: ws://127.0.0.1:8769

## Configuration Checklist

Before starting each instance, verify:

### Instance 1 (.env.indmoney)
- [ ] `FLASK_PORT=5003` (unique, not used by other instance)
- [ ] `HOST_SERVER=http://127.0.0.1:5003` (matches FLASK_PORT)
- [ ] `WEBSOCKET_PORT=8767` (unique, not used by other instance)
- [ ] `WEBSOCKET_URL=ws://127.0.0.1:8767` (matches WEBSOCKET_PORT)
- [ ] `DATABASE_URL=sqlite:///db/openalgo_indmoney.db` (unique database)
- [ ] `APP_KEY=<unique_random_key_1>` (different from Instance 2)
- [ ] `API_KEY_PEPPER=<unique_random_pepper_1>` (different from Instance 2)
- [ ] Broker credentials set (BROKER_API_KEY, BROKER_API_SECRET, etc.)

### Instance 2 (.env.zerodha)
- [ ] `FLASK_PORT=5004` (unique, not used by other instance)
- [ ] `HOST_SERVER=http://127.0.0.1:5004` (matches FLASK_PORT)
- [ ] `WEBSOCKET_PORT=8768` (unique, not used by other instance)
- [ ] `WEBSOCKET_URL=ws://127.0.0.1:8768` (matches WEBSOCKET_PORT)
- [ ] `DATABASE_URL=sqlite:///db/openalgo_zerodha.db` (unique database)
- [ ] `APP_KEY=<unique_random_key_2>` (different from Instance 1)
- [ ] `API_KEY_PEPPER=<unique_random_pepper_2>` (different from Instance 1)
- [ ] Broker credentials set (BROKER_API_KEY, BROKER_API_SECRET, etc.)

## Important Notes

1. **Unique Ports:** Each instance MUST use unique port numbers
2. **Matching HOST_SERVER:** `HOST_SERVER` MUST match the `FLASK_PORT` (critical for session isolation)
3. **Matching WEBSOCKET_URL:** `WEBSOCKET_URL` MUST match the `WEBSOCKET_PORT`
4. **Unique Databases:** Each instance SHOULD use separate database files
5. **Unique Secret Keys:** Each instance SHOULD have unique APP_KEY and API_KEY_PEPPER
6. **Environment Variables:** The `OPENALGO_ENV_FILE` variable must be set BEFORE Python starts
7. **Batch Files:** Always use the provided batch files or ensure the environment variable is set manually
8. **Browser Cookies:** Clear cookies after changing ports to avoid session conflicts

## Advanced: Running in Separate Terminals

To run multiple instances simultaneously:

1. **Terminal 1 (IndMoney):**
   ```bash
   run_instance1.bat
   ```

2. **Terminal 2 (Zerodha):**
   ```bash
   run_instance2.bat
   ```

3. **Terminal 3 (FivePaisa):**
   ```bash
   run_instance3.bat
   ```

All instances will run independently with their own configurations.

## Support

For issues or questions, refer to:
- OpenAlgo Documentation: https://docs.openalgo.in
- GitHub Issues: https://github.com/marketcalls/openalgo/issues
