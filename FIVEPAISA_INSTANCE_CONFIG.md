# FivePaisa Instance Configuration Guide

## Quick Setup for Instance 3 (FivePaisa)

### Step 1: Verify `.env.fivepaisa` Configuration

Ensure your `.env.fivepaisa` file has the following critical settings:

```
# Port Configuration
FLASK_PORT=5005
HOST_SERVER=http://127.0.0.1:5005
WEBSOCKET_PORT=8769
WEBSOCKET_URL=ws://127.0.0.1:8769

# Database Configuration
DATABASE_URL=sqlite:///db/openalgo_fivepaisa.db

# Security Configuration
APP_KEY=<unique_random_key>
API_KEY_PEPPER=<unique_random_pepper>

# Broker Configuration
BROKER_API_KEY=<your_fivepaisa_key>
BROKER_API_SECRET=<your_fivepaisa_secret>

# Other required variables (copy from .sample.env)
```

### Step 2: Verify Port Numbers Are Unique

Check that FivePaisa instance uses unique ports:

| Instance | FLASK_PORT | WEBSOCKET_PORT |
|----------|-----------|-----------------|
| IndMoney | 5003 | 8767 |
| Zerodha | 5004 | 8768 |
| FivePaisa | 5005 | 8769 |

### Step 3: Run the FivePaisa Instance

```bash
run_instance3.bat
```

The batch file will:
1. Load environment variables from `.env.fivepaisa`
2. Set `OPENALGO_ENV_FILE` environment variable
3. Display the loaded configuration
4. Start the Flask application

### Step 4: Access the Instance

Once running, access FivePaisa instance at:
- **Web:** http://127.0.0.1:5005
- **WebSocket:** ws://127.0.0.1:8769

## Configuration Checklist for FivePaisa

- [ ] `FLASK_PORT=5005` (unique, not used by other instances)
- [ ] `HOST_SERVER=http://127.0.0.1:5005` (matches FLASK_PORT)
- [ ] `WEBSOCKET_PORT=8769` (unique, not used by other instances)
- [ ] `WEBSOCKET_URL=ws://127.0.0.1:8769` (matches WEBSOCKET_PORT)
- [ ] `DATABASE_URL=sqlite:///db/openalgo_fivepaisa.db` (unique database)
- [ ] `APP_KEY=<unique_random_key>` (different from other instances)
- [ ] `API_KEY_PEPPER=<unique_random_pepper>` (different from other instances)
- [ ] `BROKER_API_KEY=<your_fivepaisa_key>` (FivePaisa credentials)
- [ ] `BROKER_API_SECRET=<your_fivepaisa_secret>` (FivePaisa credentials)
- [ ] All other required variables are present

## Running All Three Instances

To run all three instances simultaneously:

### Terminal 1 (IndMoney - Port 5003)
```bash
run_instance1.bat
```

### Terminal 2 (Zerodha - Port 5004)
```bash
run_instance2.bat
```

### Terminal 3 (FivePaisa - Port 5005)
```bash
run_instance3.bat
```

## Accessing All Instances

Once all three are running:

| Broker | URL | WebSocket |
|--------|-----|-----------|
| IndMoney | http://127.0.0.1:5003 | ws://127.0.0.1:8767 |
| Zerodha | http://127.0.0.1:5004 | ws://127.0.0.1:8768 |
| FivePaisa | http://127.0.0.1:5005 | ws://127.0.0.1:8769 |

## Troubleshooting

### Error: ".env.fivepaisa not found"
- Ensure `.env.fivepaisa` exists in the OpenAlgo root directory
- Check the file name spelling (case-sensitive on some systems)

### Error: "Port 5005 already in use"
- Change `FLASK_PORT` to an unused port (e.g., 5006)
- Update `HOST_SERVER` to match the new port
- Ensure no other applications are using the port

### Error: "Database locked"
- Ensure `DATABASE_URL` is unique and different from other instances
- Close any other instances using the same database

### Login redirects to wrong port
- Verify `HOST_SERVER=http://127.0.0.1:5005` in `.env.fivepaisa`
- Clear browser cookies for `127.0.0.1`
- Restart the instance

### Session conflicts with other instances
- Verify `HOST_SERVER` matches `FLASK_PORT`
- Clear browser cookies for `127.0.0.1`
- Verify each instance has unique `APP_KEY` and `API_KEY_PEPPER`

## Important Notes

1. **HOST_SERVER must match FLASK_PORT** - Critical for session isolation
2. **Each instance needs unique ports** - No two instances can use the same port
3. **Each instance needs unique database** - Prevents data conflicts
4. **Each instance needs unique secret keys** - For security isolation
5. **Clear browser cookies** - After changing ports or configurations

## Batch File Details

The `run_instance3.bat` file:
- Sets `OPENALGO_ENV_FILE=%cd%\.env.fivepaisa`
- Loads all variables from `.env.fivepaisa`
- Displays the loaded configuration
- Starts the Flask application with the loaded configuration

## Next Steps

1. Verify `.env.fivepaisa` configuration matches the checklist
2. Run `run_instance3.bat`
3. Access http://127.0.0.1:5005
4. Login with FivePaisa credentials
5. Verify the instance works independently from other instances

## Support

For detailed multi-instance setup information, see:
- `QUICK_START_MULTI_INSTANCE.md` - Quick reference
- `MULTI_INSTANCE_SETUP.md` - Detailed setup guide
- `MULTI_INSTANCE_SESSION_FIX.md` - Technical details
- `SETUP_VERIFICATION_CHECKLIST.md` - Verification checklist
