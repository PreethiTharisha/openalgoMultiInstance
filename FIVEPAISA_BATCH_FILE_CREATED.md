# FivePaisa Batch File Created

## Summary

Successfully created `run_instance3.bat` for the FivePaisa instance.

## File Details

**File:** `run_instance3.bat`
**Location:** OpenAlgo root directory
**Purpose:** Start OpenAlgo Instance 3 with FivePaisa broker configuration

## What the Batch File Does

1. **Sets Environment File Path:**
   ```batch
   set OPENALGO_ENV_FILE=%cd%\.env.fivepaisa
   ```

2. **Validates File Exists:**
   - Checks if `.env.fivepaisa` exists
   - Shows error if file is missing
   - Exits with error code if file not found

3. **Loads Environment Variables:**
   - Reads all variables from `.env.fivepaisa`
   - Skips empty lines and comments (lines starting with #)
   - Sets each variable in the batch environment

4. **Displays Configuration:**
   ```
   FLASK_PORT=5005
   WEBSOCKET_PORT=8769
   DATABASE_URL=sqlite:///db/openalgo_fivepaisa.db
   OPENALGO_ENV_FILE=D:\path\to\.env.fivepaisa
   ```

5. **Starts Application:**
   ```batch
   python app.py
   ```

## How to Use

### Basic Usage
```bash
run_instance3.bat
```

### Running All Three Instances

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

## Configuration Checklist

Before running the batch file, ensure `.env.fivepaisa` has:

- [ ] `FLASK_PORT=5005`
- [ ] `HOST_SERVER=http://127.0.0.1:5005`
- [ ] `WEBSOCKET_PORT=8769`
- [ ] `WEBSOCKET_URL=ws://127.0.0.1:8769`
- [ ] `DATABASE_URL=sqlite:///db/openalgo_fivepaisa.db`
- [ ] `APP_KEY=<unique_random_key>`
- [ ] `API_KEY_PEPPER=<unique_random_pepper>`
- [ ] `BROKER_API_KEY=<your_fivepaisa_key>`
- [ ] `BROKER_API_SECRET=<your_fivepaisa_secret>`
- [ ] All other required variables from `.sample.env`

## Port Configuration

| Instance | FLASK_PORT | WEBSOCKET_PORT | Web URL | WebSocket URL |
|----------|-----------|-----------------|---------|---------------|
| IndMoney | 5003 | 8767 | http://127.0.0.1:5003 | ws://127.0.0.1:8767 |
| Zerodha | 5004 | 8768 | http://127.0.0.1:5004 | ws://127.0.0.1:8768 |
| FivePaisa | 5005 | 8769 | http://127.0.0.1:5005 | ws://127.0.0.1:8769 |

## Important Notes

1. **HOST_SERVER Must Match FLASK_PORT**
   - Critical for session isolation
   - Example: `FLASK_PORT=5005` → `HOST_SERVER=http://127.0.0.1:5005`

2. **Unique Ports Required**
   - Each instance must use different ports
   - No two instances can share the same FLASK_PORT or WEBSOCKET_PORT

3. **Unique Database Required**
   - Each instance should use separate database file
   - Prevents data conflicts between instances

4. **Unique Secret Keys Required**
   - Each instance should have unique APP_KEY
   - Each instance should have unique API_KEY_PEPPER

5. **Clear Browser Cookies**
   - After changing ports or configurations
   - Delete all cookies for `127.0.0.1`

## Troubleshooting

### Error: ".env.fivepaisa not found"
- Ensure `.env.fivepaisa` exists in OpenAlgo root directory
- Check file name spelling

### Error: "Port 5005 already in use"
- Change `FLASK_PORT` to unused port (e.g., 5006)
- Update `HOST_SERVER` to match new port

### Error: "Database locked"
- Ensure `DATABASE_URL` is unique
- Close other instances using same database

### Login redirects to wrong port
- Verify `HOST_SERVER=http://127.0.0.1:5005` in `.env.fivepaisa`
- Clear browser cookies
- Restart instance

## Files Modified/Created

| File | Type | Change |
|------|------|--------|
| `run_instance3.bat` | Created | New batch file for FivePaisa |
| `MULTI_INSTANCE_SETUP.md` | Updated | Added FivePaisa instance information |
| `FIVEPAISA_INSTANCE_CONFIG.md` | Created | FivePaisa-specific configuration guide |
| `FIVEPAISA_BATCH_FILE_CREATED.md` | Created | This file |

## Next Steps

1. **Verify `.env.fivepaisa` Configuration:**
   - Check all required variables are set
   - Ensure ports are unique (5005, 8769)
   - Ensure `HOST_SERVER` matches `FLASK_PORT`

2. **Run the Batch File:**
   ```bash
   run_instance3.bat
   ```

3. **Access the Instance:**
   - Web: http://127.0.0.1:5005
   - WebSocket: ws://127.0.0.1:8769

4. **Verify It Works:**
   - Login with FivePaisa credentials
   - Check that session is isolated from other instances
   - Verify broker connection is working

## Related Documentation

- `QUICK_START_MULTI_INSTANCE.md` - Quick reference guide
- `MULTI_INSTANCE_SETUP.md` - Complete setup guide
- `MULTI_INSTANCE_SESSION_FIX.md` - Technical details
- `SETUP_VERIFICATION_CHECKLIST.md` - Verification checklist
- `FIVEPAISA_INSTANCE_CONFIG.md` - FivePaisa-specific guide

## Support

For issues or questions:
1. Check `FIVEPAISA_INSTANCE_CONFIG.md` for FivePaisa-specific setup
2. Review `MULTI_INSTANCE_SETUP.md` troubleshooting section
3. Refer to `SETUP_VERIFICATION_CHECKLIST.md` for verification steps
