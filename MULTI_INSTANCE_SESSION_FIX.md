# Multi-Instance Session Isolation Fix

## Problem Description

When running two OpenAlgo instances on different ports (e.g., 5000 and 5003):
- Login on port 5003 redirects to port 5000
- Session from port 5000 interferes with port 5003
- Logging out on port 5000 logs out the user on port 5003
- OAuth callbacks redirect to the wrong port

## Root Cause

### Issue 1: Missing SESSION_COOKIE_DOMAIN

Flask's default session cookie behavior is to share cookies across all ports on the same hostname. When you have:
- Instance 1 running on `http://127.0.0.1:5000`
- Instance 2 running on `http://127.0.0.1:5003`

Both instances share the same session cookie because `SESSION_COOKIE_DOMAIN` was not set. This means:
1. Browser stores one session cookie for `127.0.0.1` (no port specified)
2. Both instances read the same cookie
3. Session from port 5000 is used on port 5003

### Issue 2: HOST_SERVER Mismatch

The `HOST_SERVER` environment variable was hardcoded to `http://127.0.0.1:5000` in `.sample.env`. When copied to `.env.indmoney` or `.env.zerodha`, it wasn't updated to match the new port. This caused:
1. OAuth callbacks to redirect to port 5000 instead of the instance's port
2. External links (emails, alerts) to point to port 5000
3. Session cookie domain to be calculated incorrectly

## Solution

### Fix 1: Set SESSION_COOKIE_DOMAIN Based on HOST_SERVER

Modified `app.py` to automatically set `SESSION_COOKIE_DOMAIN` based on the `HOST_SERVER` configuration:

```python
# For multi-instance deployments: set SESSION_COOKIE_DOMAIN to include the port
# This prevents session cookies from being shared across different ports on localhost
session_cookie_domain = None
if "localhost" in HOST_SERVER or "127.0.0.1" in HOST_SERVER:
    from urllib.parse import urlparse
    parsed = urlparse(HOST_SERVER)
    if parsed.port:
        session_cookie_domain = f"{parsed.hostname}:{parsed.port}"
    else:
        session_cookie_domain = parsed.hostname

app.config.update(
    SESSION_COOKIE_DOMAIN=session_cookie_domain,
    WTF_CSRF_COOKIE_DOMAIN=session_cookie_domain,
    # ... other config
)
```

**Result:** 
- Instance 1 (port 5003): Session cookie domain = `127.0.0.1:5003`
- Instance 2 (port 5004): Session cookie domain = `127.0.0.1:5004`
- Browser stores separate cookies for each port

### Fix 2: Update HOST_SERVER in Environment Files

Each `.env` file must have `HOST_SERVER` matching its `FLASK_PORT`:

**`.env.indmoney`:**
```
FLASK_PORT=5003
HOST_SERVER=http://127.0.0.1:5003
WEBSOCKET_PORT=8767
WEBSOCKET_URL=ws://127.0.0.1:8767
```

**`.env.zerodha`:**
```
FLASK_PORT=5004
HOST_SERVER=http://127.0.0.1:5004
WEBSOCKET_PORT=8768
WEBSOCKET_URL=ws://127.0.0.1:8768
```

## How It Works Now

### Before Fix
```
Browser (127.0.0.1)
    ↓
Session Cookie: "session=abc123" (domain: 127.0.0.1, no port)
    ↓
Port 5000 AND Port 5003 both read the same cookie
    ↓
Conflict: Both instances use the same session
```

### After Fix
```
Browser (127.0.0.1)
    ↓
Instance 1 (Port 5003):
  - Session Cookie: "session=abc123" (domain: 127.0.0.1:5003)
  
Instance 2 (Port 5004):
  - Session Cookie: "session=xyz789" (domain: 127.0.0.1:5004)
    ↓
Each instance has its own session
```

## Testing the Fix

### Step 1: Update Environment Files

**`.env.indmoney`:**
```bash
FLASK_PORT=5003
HOST_SERVER=http://127.0.0.1:5003
WEBSOCKET_PORT=8767
WEBSOCKET_URL=ws://127.0.0.1:8767
DATABASE_URL=sqlite:///db/openalgo_indmoney.db
# ... other variables
```

**`.env.zerodha`:**
```bash
FLASK_PORT=5004
HOST_SERVER=http://127.0.0.1:5004
WEBSOCKET_PORT=8768
WEBSOCKET_URL=ws://127.0.0.1:8768
DATABASE_URL=sqlite:///db/openalgo_zerodha.db
# ... other variables
```

### Step 2: Clear Browser Cookies

1. Open Developer Tools (F12)
2. Go to Application → Cookies
3. Delete all cookies for `127.0.0.1`

### Step 3: Start Instances

**Terminal 1:**
```bash
run_instance1.bat
```

**Terminal 2:**
```bash
run_instance2.bat
```

### Step 4: Test Login

1. Open `http://127.0.0.1:5003` in one browser tab
2. Login with IndMoney credentials
3. Open `http://127.0.0.1:5004` in another browser tab
4. Login with Zerodha credentials
5. Verify:
   - Port 5003 stays logged in with IndMoney
   - Port 5004 stays logged in with Zerodha
   - Logging out on one doesn't affect the other

## Files Modified

1. **`app.py`** (Lines 229-275):
   - Added `SESSION_COOKIE_DOMAIN` configuration
   - Added `WTF_CSRF_COOKIE_DOMAIN` configuration
   - Extracts port from `HOST_SERVER` for domain isolation

2. **`MULTI_INSTANCE_SETUP.md`**:
   - Updated documentation with `HOST_SERVER` requirement
   - Added troubleshooting section for this issue
   - Added configuration checklist

## Verification

To verify the fix is working:

1. **Check Session Cookie Domain:**
   - Open DevTools → Application → Cookies
   - Instance 1 cookie domain: `127.0.0.1:5003`
   - Instance 2 cookie domain: `127.0.0.1:5004`

2. **Check Application Logs:**
   ```
   [INFO] Loading environment from OPENALGO_ENV_FILE: D:\path\to\.env.indmoney
   ```

3. **Test Session Isolation:**
   - Login on port 5003
   - Open port 5004 in new tab
   - Verify port 5003 session is not used on port 5004

## Important Notes

- **This fix only applies to localhost/127.0.0.1 deployments**
- For production deployments on different domains, cookies are automatically isolated by domain
- The fix is backward compatible - existing single-instance deployments continue to work
- `HOST_SERVER` must match `FLASK_PORT` for the fix to work correctly

## Related Issues

This fix addresses:
- Session sharing across ports on localhost
- OAuth callback redirect issues
- External link generation (emails, alerts)
- CSRF token validation across instances
