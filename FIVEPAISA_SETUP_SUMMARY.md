# FivePaisa Instance Setup - Complete Summary

## ✅ Batch File Created

Successfully created `run_instance3.bat` for the FivePaisa instance.

## Quick Start

### Step 1: Verify `.env.fivepaisa` Configuration

Ensure your `.env.fivepaisa` has these critical settings:

```
FLASK_PORT=5005
HOST_SERVER=http://127.0.0.1:5005
WEBSOCKET_PORT=8769
WEBSOCKET_URL=ws://127.0.0.1:8769
DATABASE_URL=sqlite:///db/openalgo_fivepaisa.db
APP_KEY=<unique_random_key>
API_KEY_PEPPER=<unique_random_pepper>
BROKER_API_KEY=<your_fivepaisa_key>
BROKER_API_SECRET=<your_fivepaisa_secret>
```

### Step 2: Run the Batch File

```bash
run_instance3.bat
```

### Step 3: Access the Instance

- **Web:** http://127.0.0.1:5005
- **WebSocket:** ws://127.0.0.1:8769

## All Three Instances

### Instance 1 - IndMoney
- **Batch File:** `run_instance1.bat`
- **Port:** 5003
- **WebSocket:** 8767
- **URL:** http://127.0.0.1:5003

### Instance 2 - Zerodha
- **Batch File:** `run_instance2.bat`
- **Port:** 5004
- **WebSocket:** 8768
- **URL:** http://127.0.0.1:5004

### Instance 3 - FivePaisa
- **Batch File:** `run_instance3.bat`
- **Port:** 5005
- **WebSocket:** 8769
- **URL:** http://127.0.0.1:5005

## Running All Three Simultaneously

Open three separate terminals/command prompts:

**Terminal 1:**
```bash
run_instance1.bat
```

**Terminal 2:**
```bash
run_instance2.bat
```

**Terminal 3:**
```bash
run_instance3.bat
```

## Configuration Checklist for FivePaisa

- [ ] `FLASK_PORT=5005` (unique)
- [ ] `HOST_SERVER=http://127.0.0.1:5005` (matches FLASK_PORT)
- [ ] `WEBSOCKET_PORT=8769` (unique)
- [ ] `WEBSOCKET_URL=ws://127.0.0.1:8769` (matches WEBSOCKET_PORT)
- [ ] `DATABASE_URL=sqlite:///db/openalgo_fivepaisa.db` (unique)
- [ ] `APP_KEY=<unique_key>` (different from other instances)
- [ ] `API_KEY_PEPPER=<unique_pepper>` (different from other instances)
- [ ] `BROKER_API_KEY=<fivepaisa_key>`
- [ ] `BROKER_API_SECRET=<fivepaisa_secret>`
- [ ] All other required variables from `.sample.env`

## Port Summary

| Instance | FLASK | WebSocket | Web URL | WS URL |
|----------|-------|-----------|---------|--------|
| IndMoney | 5003 | 8767 | http://127.0.0.1:5003 | ws://127.0.0.1:8767 |
| Zerodha | 5004 | 8768 | http://127.0.0.1:5004 | ws://127.0.0.1:8768 |
| FivePaisa | 5005 | 8769 | http://127.0.0.1:5005 | ws://127.0.0.1:8769 |

## Critical Requirements

### 1. HOST_SERVER Must Match FLASK_PORT
```
FLASK_PORT=5005
HOST_SERVER=http://127.0.0.1:5005  ← MUST MATCH
```

### 2. Unique Ports
- No two instances can use the same FLASK_PORT
- No two instances can use the same WEBSOCKET_PORT

### 3. Unique Databases
- Each instance must use different DATABASE_URL
- Prevents data conflicts

### 4. Unique Secret Keys
- Each instance must have unique APP_KEY
- Each instance must have unique API_KEY_PEPPER

## Batch File Details

The `run_instance3.bat` file:

1. Sets `OPENALGO_ENV_FILE=%cd%\.env.fivepaisa`
2. Validates `.env.fivepaisa` exists
3. Loads all environment variables from `.env.fivepaisa`
4. Displays loaded configuration
5. Starts Flask application

## Troubleshooting

### Port Already in Use
```bash
# Check if port 5005 is in use
netstat -ano | findstr :5005

# If in use, change FLASK_PORT to 5006 and update HOST_SERVER
FLASK_PORT=5006
HOST_SERVER=http://127.0.0.1:5006
```

### .env.fivepaisa Not Found
- Ensure `.env.fivepaisa` exists in OpenAlgo root directory
- Check file name spelling

### Database Locked
- Ensure `DATABASE_URL` is unique
- Close other instances using same database

### Login Redirects to Wrong Port
- Verify `HOST_SERVER=http://127.0.0.1:5005`
- Clear browser cookies for `127.0.0.1`
- Restart instance

### Session Conflicts
- Verify each instance has unique `APP_KEY`
- Verify each instance has unique `API_KEY_PEPPER`
- Clear browser cookies
- Restart instances

## Files Created/Modified

| File | Type | Purpose |
|------|------|---------|
| `run_instance3.bat` | Created | Start FivePaisa instance |
| `MULTI_INSTANCE_SETUP.md` | Updated | Added FivePaisa information |
| `FIVEPAISA_INSTANCE_CONFIG.md` | Created | FivePaisa configuration guide |
| `FIVEPAISA_BATCH_FILE_CREATED.md` | Created | Batch file documentation |
| `FIVEPAISA_SETUP_SUMMARY.md` | Created | This file |

## Documentation Files

For more detailed information, see:

1. **`QUICK_START_MULTI_INSTANCE.md`**
   - Quick reference guide
   - Common mistakes
   - Key configuration values

2. **`MULTI_INSTANCE_SETUP.md`**
   - Complete setup guide
   - Detailed configuration
   - Troubleshooting section

3. **`MULTI_INSTANCE_SESSION_FIX.md`**
   - Technical explanation
   - Root cause analysis
   - How the fix works

4. **`SETUP_VERIFICATION_CHECKLIST.md`**
   - Comprehensive verification checklist
   - Step-by-step verification
   - Success criteria

5. **`FIVEPAISA_INSTANCE_CONFIG.md`**
   - FivePaisa-specific configuration
   - FivePaisa troubleshooting
   - FivePaisa verification

## Next Steps

1. **Verify `.env.fivepaisa` Configuration**
   - Check all required variables
   - Ensure ports are unique
   - Ensure `HOST_SERVER` matches `FLASK_PORT`

2. **Run the Batch File**
   ```bash
   run_instance3.bat
   ```

3. **Test the Instance**
   - Open http://127.0.0.1:5005
   - Login with FivePaisa credentials
   - Verify broker connection

4. **Verify Session Isolation**
   - Open other instances in different tabs
   - Verify each maintains its own session
   - Verify logging out doesn't affect others

## Support

For issues:
1. Check `FIVEPAISA_INSTANCE_CONFIG.md`
2. Review `MULTI_INSTANCE_SETUP.md` troubleshooting
3. Use `SETUP_VERIFICATION_CHECKLIST.md` for verification
4. Refer to `MULTI_INSTANCE_SESSION_FIX.md` for technical details

## Success Criteria

✅ **Setup is successful if:**
- [ ] `run_instance3.bat` starts without errors
- [ ] Instance is accessible at http://127.0.0.1:5005
- [ ] Login works with FivePaisa credentials
- [ ] Session is isolated from other instances
- [ ] Broker connection is working
- [ ] WebSocket connection is working

---

**Status:** ✅ FivePaisa batch file created and ready to use!
