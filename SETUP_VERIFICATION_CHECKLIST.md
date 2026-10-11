# Multi-Instance Setup Verification Checklist

Use this checklist to verify your multi-instance OpenAlgo setup is correct.

## Pre-Setup Verification

- [ ] You have two separate `.env` files (`.env.indmoney` and `.env.zerodha`)
- [ ] Both `.env` files are in the OpenAlgo root directory
- [ ] You have generated unique APP_KEY and API_KEY_PEPPER for each instance
- [ ] You have unique broker credentials for each broker

## Instance 1 (.env.indmoney) Configuration

### Port Configuration
- [ ] `FLASK_PORT=5003` (or your chosen port, not 5000)
- [ ] `HOST_SERVER=http://127.0.0.1:5003` (matches FLASK_PORT)
- [ ] `WEBSOCKET_PORT=8767` (unique, not used by Instance 2)
- [ ] `WEBSOCKET_URL=ws://127.0.0.1:8767` (matches WEBSOCKET_PORT)

### Database Configuration
- [ ] `DATABASE_URL=sqlite:///db/openalgo_indmoney.db` (unique database file)

### Security Configuration
- [ ] `APP_KEY=<unique_random_key>` (at least 32 characters)
- [ ] `API_KEY_PEPPER=<unique_random_pepper>` (different from Instance 2)

### Broker Configuration
- [ ] `BROKER_API_KEY=<indmoney_key>` (your IndMoney API key)
- [ ] `BROKER_API_SECRET=<indmoney_secret>` (your IndMoney API secret)
- [ ] Broker is set to IndMoney (check BROKER_NAME or similar)

### Other Configuration
- [ ] All other required variables are present (copy from .sample.env)
- [ ] No comments or syntax errors in the file

## Instance 2 (.env.zerodha) Configuration

### Port Configuration
- [ ] `FLASK_PORT=5004` (or your chosen port, different from Instance 1)
- [ ] `HOST_SERVER=http://127.0.0.1:5004` (matches FLASK_PORT)
- [ ] `WEBSOCKET_PORT=8768` (unique, not used by Instance 1)
- [ ] `WEBSOCKET_URL=ws://127.0.0.1:8768` (matches WEBSOCKET_PORT)

### Database Configuration
- [ ] `DATABASE_URL=sqlite:///db/openalgo_zerodha.db` (unique database file, different from Instance 1)

### Security Configuration
- [ ] `APP_KEY=<unique_random_key>` (at least 32 characters, different from Instance 1)
- [ ] `API_KEY_PEPPER=<unique_random_pepper>` (different from Instance 1)

### Broker Configuration
- [ ] `BROKER_API_KEY=<zerodha_key>` (your Zerodha API key)
- [ ] `BROKER_API_SECRET=<zerodha_secret>` (your Zerodha API secret)
- [ ] Broker is set to Zerodha (check BROKER_NAME or similar)

### Other Configuration
- [ ] All other required variables are present (copy from .sample.env)
- [ ] No comments or syntax errors in the file

## Port Uniqueness Verification

- [ ] Instance 1 FLASK_PORT (5003) ≠ Instance 2 FLASK_PORT (5004)
- [ ] Instance 1 WEBSOCKET_PORT (8767) ≠ Instance 2 WEBSOCKET_PORT (8768)
- [ ] No other applications are using ports 5003, 5004, 8767, 8768

To check if ports are in use:
```bash
netstat -ano | findstr :5003
netstat -ano | findstr :5004
netstat -ano | findstr :8767
netstat -ano | findstr :8768
```

## Database Uniqueness Verification

- [ ] Instance 1 DATABASE_URL: `sqlite:///db/openalgo_indmoney.db`
- [ ] Instance 2 DATABASE_URL: `sqlite:///db/openalgo_zerodha.db`
- [ ] Both database files are different (not using the same file)

## Security Key Verification

- [ ] Instance 1 APP_KEY ≠ Instance 2 APP_KEY
- [ ] Instance 1 API_KEY_PEPPER ≠ Instance 2 API_KEY_PEPPER
- [ ] Both APP_KEYs are at least 32 characters long
- [ ] Both API_KEY_PEPPERs are at least 32 characters long

To generate random keys:
```python
import secrets
print(secrets.token_hex(32))
```

## Batch File Verification

### run_instance1.bat
- [ ] File exists in OpenAlgo root directory
- [ ] Contains: `set OPENALGO_ENV_FILE=%cd%\.env.indmoney`
- [ ] Contains: `python app.py`
- [ ] No syntax errors

### run_instance2.bat
- [ ] File exists in OpenAlgo root directory
- [ ] Contains: `set OPENALGO_ENV_FILE=%cd%\.env.zerodha`
- [ ] Contains: `python app.py`
- [ ] No syntax errors

## Pre-Startup Verification

### Browser Cleanup
- [ ] Opened DevTools (F12)
- [ ] Went to Application → Cookies
- [ ] Deleted all cookies for `127.0.0.1`
- [ ] Closed all browser tabs with `127.0.0.1:5000`, `127.0.0.1:5003`, `127.0.0.1:5004`

### Environment Variable Check
- [ ] No global `OPENALGO_ENV_FILE` environment variable set (should be set by batch file)
- [ ] No global `FLASK_PORT` environment variable set (should be set by batch file)

## Startup Verification

### Instance 1 Startup
- [ ] Opened Command Prompt/PowerShell
- [ ] Navigated to OpenAlgo root directory
- [ ] Ran `run_instance1.bat`
- [ ] Saw output: `Loading environment variables from .env.indmoney...`
- [ ] Saw output: `FLASK_PORT=5003`
- [ ] Saw output: `WEBSOCKET_PORT=8767`
- [ ] Saw output: `DATABASE_URL=sqlite:///db/openalgo_indmoney.db`
- [ ] Application started without errors
- [ ] Saw: `Status Ready`

### Instance 2 Startup
- [ ] Opened new Command Prompt/PowerShell
- [ ] Navigated to OpenAlgo root directory
- [ ] Ran `run_instance2.bat`
- [ ] Saw output: `Loading environment variables from .env.zerodha...`
- [ ] Saw output: `FLASK_PORT=5004`
- [ ] Saw output: `WEBSOCKET_PORT=8768`
- [ ] Saw output: `DATABASE_URL=sqlite:///db/openalgo_zerodha.db`
- [ ] Application started without errors
- [ ] Saw: `Status Ready`

## Functional Verification

### Instance 1 Login
- [ ] Opened http://127.0.0.1:5003 in browser
- [ ] Login page loaded successfully
- [ ] Logged in with IndMoney credentials
- [ ] Dashboard loaded
- [ ] Stayed logged in on port 5003

### Instance 2 Login
- [ ] Opened http://127.0.0.1:5004 in new browser tab
- [ ] Login page loaded successfully
- [ ] Logged in with Zerodha credentials
- [ ] Dashboard loaded
- [ ] Stayed logged in on port 5004

### Session Isolation Verification
- [ ] Switched back to port 5003 tab
- [ ] Still logged in with IndMoney account
- [ ] Switched to port 5004 tab
- [ ] Still logged in with Zerodha account
- [ ] Logging out on port 5003 doesn't affect port 5004
- [ ] Logging out on port 5004 doesn't affect port 5003

### Cookie Domain Verification
- [ ] Opened DevTools (F12) on port 5003 tab
- [ ] Went to Application → Cookies
- [ ] Found session cookie with domain: `127.0.0.1:5003`
- [ ] Opened DevTools on port 5004 tab
- [ ] Went to Application → Cookies
- [ ] Found session cookie with domain: `127.0.0.1:5004`
- [ ] Cookies have different domains (not shared)

## Troubleshooting Verification

### If Instance 1 Fails to Start
- [ ] Check if port 5003 is already in use: `netstat -ano | findstr :5003`
- [ ] Verify `.env.indmoney` file exists and is readable
- [ ] Verify `FLASK_PORT=5003` is set in `.env.indmoney`
- [ ] Check for syntax errors in `.env.indmoney`
- [ ] Verify all required variables are present

### If Instance 2 Fails to Start
- [ ] Check if port 5004 is already in use: `netstat -ano | findstr :5004`
- [ ] Verify `.env.zerodha` file exists and is readable
- [ ] Verify `FLASK_PORT=5004` is set in `.env.zerodha`
- [ ] Check for syntax errors in `.env.zerodha`
- [ ] Verify all required variables are present

### If Login Redirects to Wrong Port
- [ ] Verify `HOST_SERVER=http://127.0.0.1:5003` in `.env.indmoney`
- [ ] Verify `HOST_SERVER=http://127.0.0.1:5004` in `.env.zerodha`
- [ ] Clear browser cookies for `127.0.0.1`
- [ ] Restart both instances
- [ ] Try login again

### If Sessions Are Shared Between Ports
- [ ] Verify `HOST_SERVER` matches `FLASK_PORT` in both files
- [ ] Clear browser cookies for `127.0.0.1`
- [ ] Verify cookie domain in DevTools is `127.0.0.1:5003` for Instance 1
- [ ] Verify cookie domain in DevTools is `127.0.0.1:5004` for Instance 2
- [ ] Restart both instances

## Final Verification

- [ ] Both instances are running without errors
- [ ] Instance 1 is accessible at http://127.0.0.1:5003
- [ ] Instance 2 is accessible at http://127.0.0.1:5004
- [ ] Each instance maintains its own session
- [ ] Logging out on one instance doesn't affect the other
- [ ] Cookie domains are properly isolated (5003 and 5004)
- [ ] WebSocket connections work on both instances
- [ ] Broker connections work on both instances

## Success Criteria

✅ **Setup is successful if:**
1. Both instances start without errors
2. Each instance is accessible on its own port
3. Sessions are isolated between instances
4. Cookie domains are separate (127.0.0.1:5003 and 127.0.0.1:5004)
5. Logging out on one instance doesn't affect the other
6. Both brokers are connected and working

## Next Steps

If all checks pass:
- ✅ Your multi-instance setup is complete!
- ✅ You can now run both instances simultaneously
- ✅ Each instance has its own session and configuration

If any checks fail:
- ❌ Review the troubleshooting section
- ❌ Check the documentation files:
  - `QUICK_START_MULTI_INSTANCE.md` - Quick reference
  - `MULTI_INSTANCE_SETUP.md` - Detailed setup guide
  - `MULTI_INSTANCE_SESSION_FIX.md` - Technical details
- ❌ Verify all configuration values match the checklist
