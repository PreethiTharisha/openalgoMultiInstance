# API Key Regeneration - Complete Guide

## Current Status

**Error:** `HTTP 403: Invalid openalgo apikey`

**Current API Key in .env:**
```
APP_KEY = '1971a163ce161565609db8a4adc323afb2a64a757d22c034b74fbf58477513ce'
```

**Status:** ❌ This is a **PLACEHOLDER** key - NOT valid for actual API calls

---

## Why This Happened

When OpenAlgo starts for the first time, it auto-generates placeholder security keys:
- `APP_KEY` - Used for Flask session cookies and CSRF tokens
- `API_KEY_PEPPER` - Used for hashing sensitive data

These placeholders are **NOT** the same as your **OpenAlgo API Key** used for trading.

Your **OpenAlgo API Key** is generated when you:
1. Log in with broker credentials
2. Go to Settings → API Key page
3. Get a fresh 64-character key

---

## Solution: Get Fresh API Key

### Step 1: Ensure OpenAlgo is Running

Open in browser:
```
http://127.0.0.1:5000
```

Should show the OpenAlgo login page or dashboard.

### Step 2: Log In with Broker Credentials

1. Enter your **broker username** (NOT OpenAlgo username)
2. Enter your **broker password**
3. Click **Login**

You should see the OpenAlgo dashboard with your broker name and account details.

### Step 3: Navigate to API Key Page

**Option A: Via Settings Menu**
1. Click **Settings** (usually top-right corner)
2. Click **API Key**

**Option B: Direct URL**
```
http://127.0.0.1:5000/apikey
```

### Step 4: Copy Your API Key

You should see a **64-character hexadecimal key** displayed.

Example format:
```
0aac0bae37a2458241ff0405084b17c54368ea461b9ea5e65a2a44e2fae9a165
```

**Important:**
- ✅ Must be exactly **64 characters**
- ✅ Must be **hexadecimal** (0-9, a-f)
- ✅ Copy the **entire key** without spaces

### Step 5: Update .env File

1. Open: `D:\OpenAlgo\openalgo\.env`
2. Find the line:
   ```
   APP_KEY = '1971a163ce161565609db8a4adc323afb2a64a757d22c034b74fbf58477513ce'
   ```
3. Replace with your new key:
   ```
   APP_KEY = '0aac0bae37a2458241ff0405084b17c54368ea461b9ea5e65a2a44e2fae9a165'
   ```
4. **Save the file**

### Step 6: Run Your Script

```bash
python strategies/examples/sandboxtest_fixed.py
```

---

## Verification

### Check API Key Format

Your API key should be:
- ✅ Exactly **64 characters**
- ✅ **Hexadecimal** (0-9, a-f only)
- ✅ **No spaces** or special characters
- ✅ **No quotes** inside (only around it in .env)

### Verify .env File

```bash
grep APP_KEY D:\OpenAlgo\openalgo\.env
```

Should show:
```
APP_KEY = '0aac0bae37a2458241ff0405084b17c54368ea461b9ea5e65a2a44e2fae9a165'
```

### Test the API Key

Run the test script:
```bash
python strategies/examples/sandboxtest_fixed.py
```

**Expected Success Output:**
```
[OK] Client initialized successfully
[OK] Funds retrieved: {'status': 'success', ...}
[OK] Quote retrieved - LTP: 980.90
[OK] BUY order placed successfully!
[OK] SELL order placed successfully!
[OK] Sandbox Test Completed
```

---

## All Scripts Using APP_KEY

Once you update `.env`, **all these scripts will work:**

✅ `strategies/examples/sandboxtest_fixed.py`
✅ `strategies/examples/continuous_trading_bot.py`
✅ `strategies/examples/continuous_trading_bot_nifty.py`

---

## Troubleshooting

### Issue 1: "Cannot find API Key page"

**Cause:** Not logged in or page not accessible

**Solution:**
1. Make sure you're logged in with broker credentials
2. Check broker shows "Connected" status
3. Try direct URL: `http://127.0.0.1:5000/apikey`
4. Try incognito/private browser window

### Issue 2: "API Key page is blank"

**Cause:** Broker session not established

**Solution:**
1. Log out and log back in
2. Refresh the page (Ctrl+R)
3. Check broker connection status
4. Restart OpenAlgo if needed

### Issue 3: "Still getting 'Invalid apikey' error"

**Cause:** API key not updated correctly in .env

**Solution:**
1. Verify you copied the **entire 64-character key**
2. Check for **no extra spaces** in .env
3. Verify **no quotes inside** the key value
4. Save the .env file
5. Run script again

### Issue 4: "OpenAlgo won't start"

**Cause:** OpenAlgo server not running

**Solution:**
```bash
# Start OpenAlgo
python app.py
# or
uv run app.py
```

Wait for message:
```
Running on http://127.0.0.1:5000
```

Then access the API key page.

### Issue 5: "Broker login fails"

**Cause:** Wrong credentials or broker not supported

**Solution:**
1. Verify broker username and password
2. Check broker is supported by OpenAlgo
3. Try logging in directly to broker's website
4. Check internet connection

---

## Security Notes

⚠️ **Important:**

- **Never commit .env to git** - It contains sensitive keys
- **Keep API key confidential** - Don't share with others
- **Don't expose .env file** - Keep it local only
- **Regenerate if compromised** - Get a new key from dashboard
- **Use .env for local development only** - Not for production

---

## Understanding the Keys

### APP_KEY (in .env)
```
APP_KEY = '1971a163ce161565609db8a4adc323afb2a64a757d22c034b74fbf58477513ce'
```
- **Purpose:** Flask session cookies, CSRF tokens
- **Auto-generated:** On first OpenAlgo startup
- **Scope:** OpenAlgo application security
- **Update:** Rarely needed

### OpenAlgo API Key (from /apikey page)
```
0aac0bae37a2458241ff0405084b17c54368ea461b9ea5e65a2a44e2fae9a165
```
- **Purpose:** Trading API authentication
- **Generated:** When you log in with broker credentials
- **Scope:** API calls to broker
- **Update:** When you need a new key
- **This is what you need to update!**

---

## Step-by-Step Summary

1. **Open OpenAlgo:** `http://127.0.0.1:5000`
2. **Log in:** Broker username + password
3. **Go to API Key:** Settings → API Key
4. **Copy key:** 64-character hexadecimal string
5. **Update .env:** Replace APP_KEY value
6. **Save file:** Ctrl+S
7. **Run script:** `python strategies/examples/sandboxtest_fixed.py`

**Total time:** ~5 minutes

---

## Expected Success

After updating with correct API key:

```
================================================================================
=== Strategy Started at 2026-09-15 11:25:01 IST ===
=== Platform: windows ===
================================================================================

Strategy Configuration:
  API Key: 0aac0bae...fae9a165
  Host: http://127.0.0.1:5000
  WebSocket: ws://127.0.0.1:8765
  Strategy: SandboxTest
  Symbol: SBIN
  Exchange: NSE

Initializing OpenAlgo Client...
[OK] Client initialized successfully

Getting Account Funds...
[OK] Funds retrieved: {'status': 'success', 'data': {'availablecash': 10000000.0, ...}}

Getting Market Quote for SBIN...
[OK] Quote retrieved - LTP: 980.90

Placing BUY order...
BUY Response: {'status': 'success', 'orderid': '26091596939790'}
[OK] BUY order placed successfully!
[OK] Order ID: 26091596939790

Placing SELL order...
SELL Response: {'status': 'success', 'orderid': '26091528333781'}
[OK] SELL order placed successfully!
[OK] Order ID: 26091528333781

Getting Order Book...
[OK] Order book retrieved - Total orders: 2

================================================================================
[OK] Sandbox Test Completed
================================================================================
```

---

## Reference

- **OpenAlgo Dashboard:** `http://127.0.0.1:5000`
- **API Key Page:** `http://127.0.0.1:5000/apikey`
- **.env File:** `D:\OpenAlgo\openalgo\.env`
- **Scripts:** `D:\OpenAlgo\openalgo\strategies\examples\`

---

**Status:** ⚠️ Requires action - Get fresh API key
**Action:** Follow steps 1-7 above
**Time:** ~5 minutes
**Result:** All scripts will work with correct API key

