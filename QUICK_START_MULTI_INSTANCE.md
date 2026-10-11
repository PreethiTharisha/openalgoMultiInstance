# Quick Start: Multi-Instance OpenAlgo

## TL;DR - What You Need to Do

### 1. Create `.env.indmoney`
Copy from `.sample.env` and update:
```
FLASK_PORT=5003
HOST_SERVER=http://127.0.0.1:5003
WEBSOCKET_PORT=8767
WEBSOCKET_URL=ws://127.0.0.1:8767
DATABASE_URL=sqlite:///db/openalgo_indmoney.db
BROKER_API_KEY=<your_indmoney_key>
BROKER_API_SECRET=<your_indmoney_secret>
APP_KEY=<generate_new_key>
API_KEY_PEPPER=<generate_new_pepper>
```

### 2. Create `.env.zerodha`
Copy from `.sample.env` and update:
```
FLASK_PORT=5004
HOST_SERVER=http://127.0.0.1:5004
WEBSOCKET_PORT=8768
WEBSOCKET_URL=ws://127.0.0.1:8768
DATABASE_URL=sqlite:///db/openalgo_zerodha.db
BROKER_API_KEY=<your_zerodha_key>
BROKER_API_SECRET=<your_zerodha_secret>
APP_KEY=<generate_new_key>
API_KEY_PEPPER=<generate_new_pepper>
```

### 3. Generate Random Keys
```python
import secrets
print(secrets.token_hex(32))  # Run twice for APP_KEY and API_KEY_PEPPER
```

### 4. Start Instance 1
```bash
run_instance1.bat
```

### 5. Start Instance 2 (in new terminal)
```bash
run_instance2.bat
```

### 6. Access Instances
- Instance 1: http://127.0.0.1:5003
- Instance 2: http://127.0.0.1:5004

## Common Mistakes

❌ **DON'T:** Copy `.env.indmoney` and forget to update `HOST_SERVER`
```
FLASK_PORT=5003
HOST_SERVER=http://127.0.0.1:5000  ← WRONG! Should be 5003
```

✅ **DO:** Update `HOST_SERVER` to match `FLASK_PORT`
```
FLASK_PORT=5003
HOST_SERVER=http://127.0.0.1:5003  ← CORRECT
```

❌ **DON'T:** Use the same `APP_KEY` for both instances
```
Instance 1: APP_KEY=abc123...
Instance 2: APP_KEY=abc123...  ← WRONG! Should be different
```

✅ **DO:** Generate unique keys for each instance
```
Instance 1: APP_KEY=abc123...
Instance 2: APP_KEY=xyz789...  ← CORRECT
```

❌ **DON'T:** Use the same database for both instances
```
Instance 1: DATABASE_URL=sqlite:///db/openalgo.db
Instance 2: DATABASE_URL=sqlite:///db/openalgo.db  ← WRONG! Same database
```

✅ **DO:** Use separate databases
```
Instance 1: DATABASE_URL=sqlite:///db/openalgo_indmoney.db
Instance 2: DATABASE_URL=sqlite:///db/openalgo_zerodha.db  ← CORRECT
```

## Troubleshooting

### "Login on 5003 redirects to 5000"
→ Check that `HOST_SERVER=http://127.0.0.1:5003` in `.env.indmoney`

### "Port 5003 already in use"
→ Stop the instance running on 5003, or use a different port number

### "Database locked"
→ Make sure each instance uses a different `DATABASE_URL`

### "Session from 5000 is used on 5003"
→ Clear browser cookies and restart both instances

## Files to Update

| File | What to Change |
|------|-----------------|
| `.env.indmoney` | FLASK_PORT, HOST_SERVER, WEBSOCKET_PORT, WEBSOCKET_URL, DATABASE_URL, Broker credentials, APP_KEY, API_KEY_PEPPER |
| `.env.zerodha` | FLASK_PORT, HOST_SERVER, WEBSOCKET_PORT, WEBSOCKET_URL, DATABASE_URL, Broker credentials, APP_KEY, API_KEY_PEPPER |

## Key Configuration Values

```
Instance 1 (IndMoney):
  FLASK_PORT=5003
  HOST_SERVER=http://127.0.0.1:5003
  WEBSOCKET_PORT=8767
  WEBSOCKET_URL=ws://127.0.0.1:8767
  DATABASE_URL=sqlite:///db/openalgo_indmoney.db

Instance 2 (Zerodha):
  FLASK_PORT=5004
  HOST_SERVER=http://127.0.0.1:5004
  WEBSOCKET_PORT=8768
  WEBSOCKET_URL=ws://127.0.0.1:8768
  DATABASE_URL=sqlite:///db/openalgo_zerodha.db
```

## Why HOST_SERVER Matters

`HOST_SERVER` is used for:
1. **Session Cookie Domain** - Isolates sessions between ports
2. **OAuth Callbacks** - Redirects to the correct port after login
3. **External Links** - Emails, alerts, and API responses use this URL
4. **CSRF Protection** - Validates requests from the correct origin

If `HOST_SERVER` doesn't match `FLASK_PORT`, you'll get:
- Session conflicts between instances
- OAuth redirects to wrong port
- Links pointing to wrong port in emails

## Next Steps

1. Read `MULTI_INSTANCE_SETUP.md` for detailed setup instructions
2. Read `MULTI_INSTANCE_SESSION_FIX.md` to understand the technical details
3. Check `MULTI_INSTANCE_SETUP.md` troubleshooting section if you hit issues
