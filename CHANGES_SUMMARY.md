# Multi-Instance Support - Changes Summary

## Problem
When running multiple OpenAlgo instances on different ports (e.g., 5000 and 5003):
- Login on port 5003 redirects to port 5000
- Session from port 5000 interferes with port 5003
- Logging out on one port logs out the user on all ports
- OAuth callbacks redirect to the wrong port

## Root Causes
1. **Missing SESSION_COOKIE_DOMAIN**: Flask was sharing session cookies across all ports on localhost
2. **HOST_SERVER Mismatch**: Environment files had `HOST_SERVER=http://127.0.0.1:5000` hardcoded, not matching the instance's port

## Solution Overview
1. Modified `app.py` to automatically set `SESSION_COOKIE_DOMAIN` based on `HOST_SERVER`
2. Updated environment loading to support `OPENALGO_ENV_FILE` variable
3. Enhanced batch files with better error handling
4. Created comprehensive documentation

## Files Modified

### 1. `app.py` (Lines 229-275)
**Changes:**
- Added automatic `SESSION_COOKIE_DOMAIN` configuration based on `HOST_SERVER`
- Extracts port from `HOST_SERVER` URL and sets cookie domain to `hostname:port`
- Applied same domain to CSRF cookies for consistency
- Only applies domain isolation on localhost/127.0.0.1 (production deployments use different domains)

**Code:**
```python
# For multi-instance deployments: set SESSION_COOKIE_DOMAIN to include the port
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

### 2. `utils/env_check.py` (Lines 105-130 and 1140-1176)
**Changes:**
- Modified `check_env_version_compatibility()` to check for `OPENALGO_ENV_FILE` environment variable
- Modified `load_and_check_env_variables()` to load from `OPENALGO_ENV_FILE` if set
- Falls back to default `.env` if `OPENALGO_ENV_FILE` is not set
- Prints informational message about which file is being loaded

**Code:**
```python
# Support multi-instance deployments: check for OPENALGO_ENV_FILE environment variable
openalgo_env_file = os.getenv("OPENALGO_ENV_FILE")
if openalgo_env_file:
    env_path = openalgo_env_file
    print(f"[INFO] Loading environment from OPENALGO_ENV_FILE: {env_path}")
else:
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
```

### 3. `run_instance1.bat`
**Changes:**
- Added `setlocal enabledelayedexpansion` for proper variable expansion
- Set `OPENALGO_ENV_FILE` **before** loading variables
- Added file existence check with error handling
- Improved variable loading with proper quoting
- Better error messages

### 4. `run_instance2.bat`
**Changes:**
- Same improvements as `run_instance1.bat`
- Uses `.env.zerodha` instead of `.env.indmoney`

### 5. Documentation Files (NEW)
Created three new documentation files:

#### `MULTI_INSTANCE_SETUP.md`
- Complete setup guide for multi-instance deployments
- Step-by-step configuration instructions
- Port configuration examples
- Troubleshooting section
- Configuration checklist

#### `MULTI_INSTANCE_SESSION_FIX.md`
- Technical explanation of the root cause
- Detailed description of the fix
- Before/after diagrams
- Testing instructions
- Verification steps

#### `QUICK_START_MULTI_INSTANCE.md`
- Quick reference guide
- TL;DR setup instructions
- Common mistakes and how to avoid them
- Key configuration values
- Troubleshooting quick links

## How It Works

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

## Configuration Requirements

### Critical: HOST_SERVER Must Match FLASK_PORT

**Instance 1 (.env.indmoney):**
```
FLASK_PORT=5003
HOST_SERVER=http://127.0.0.1:5003  ← MUST MATCH FLASK_PORT
WEBSOCKET_PORT=8767
WEBSOCKET_URL=ws://127.0.0.1:8767  ← MUST MATCH WEBSOCKET_PORT
DATABASE_URL=sqlite:///db/openalgo_indmoney.db
```

**Instance 2 (.env.zerodha):**
```
FLASK_PORT=5004
HOST_SERVER=http://127.0.0.1:5004  ← MUST MATCH FLASK_PORT
WEBSOCKET_PORT=8768
WEBSOCKET_URL=ws://127.0.0.1:8768  ← MUST MATCH WEBSOCKET_PORT
DATABASE_URL=sqlite:///db/openalgo_zerodha.db
```

## Testing the Fix

### Step 1: Update Environment Files
Ensure `HOST_SERVER` matches `FLASK_PORT` in both `.env.indmoney` and `.env.zerodha`

### Step 2: Clear Browser Cookies
1. Open DevTools (F12)
2. Application → Cookies
3. Delete all cookies for `127.0.0.1`

### Step 3: Start Instances
```bash
# Terminal 1
run_instance1.bat

# Terminal 2
run_instance2.bat
```

### Step 4: Test Login
1. Open http://127.0.0.1:5003 and login with IndMoney
2. Open http://127.0.0.1:5004 and login with Zerodha
3. Verify each instance maintains its own session

### Step 5: Verify Cookie Domain
1. Open DevTools → Application → Cookies
2. Check Instance 1 cookie domain: `127.0.0.1:5003`
3. Check Instance 2 cookie domain: `127.0.0.1:5004`

## Backward Compatibility

- **Single Instance Deployments:** No changes needed, works as before
- **Production Deployments:** Cookies are isolated by domain, not affected by this change
- **Localhost Multi-Instance:** Now properly isolated by port

## Important Notes

1. **This fix only applies to localhost/127.0.0.1 deployments**
   - Production deployments on different domains automatically have isolated cookies

2. **HOST_SERVER must match FLASK_PORT**
   - Used for session cookie domain isolation
   - Used for OAuth callback URLs
   - Used for external links in emails and alerts

3. **Each instance needs unique configuration**
   - Unique FLASK_PORT and WEBSOCKET_PORT
   - Unique DATABASE_URL
   - Unique APP_KEY and API_KEY_PEPPER

4. **Environment variable OPENALGO_ENV_FILE**
   - Set by batch files before Python starts
   - Tells the app which .env file to load
   - Can be set manually if not using batch files

## Files Affected

| File | Type | Change |
|------|------|--------|
| `app.py` | Modified | Added SESSION_COOKIE_DOMAIN configuration |
| `utils/env_check.py` | Modified | Added OPENALGO_ENV_FILE support |
| `run_instance1.bat` | Modified | Enhanced with error handling |
| `run_instance2.bat` | Modified | Enhanced with error handling |
| `MULTI_INSTANCE_SETUP.md` | New | Complete setup guide |
| `MULTI_INSTANCE_SESSION_FIX.md` | New | Technical documentation |
| `QUICK_START_MULTI_INSTANCE.md` | New | Quick reference guide |
| `CHANGES_SUMMARY.md` | New | This file |

## Next Steps

1. **Update your `.env` files:**
   - Ensure `HOST_SERVER` matches `FLASK_PORT`
   - Ensure `WEBSOCKET_URL` matches `WEBSOCKET_PORT`
   - Use unique `DATABASE_URL` for each instance

2. **Clear browser cookies:**
   - Delete all cookies for `127.0.0.1`

3. **Restart instances:**
   - Use the updated batch files
   - Verify each instance has its own session

4. **Read documentation:**
   - `QUICK_START_MULTI_INSTANCE.md` for quick setup
   - `MULTI_INSTANCE_SETUP.md` for detailed instructions
   - `MULTI_INSTANCE_SESSION_FIX.md` for technical details

## Support

For issues or questions:
- Check `MULTI_INSTANCE_SETUP.md` troubleshooting section
- Review `QUICK_START_MULTI_INSTANCE.md` common mistakes
- Refer to `MULTI_INSTANCE_SESSION_FIX.md` for technical details
