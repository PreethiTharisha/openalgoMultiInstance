# Sandbox Test - Troubleshooting Guide

## Common Issues & Solutions

### Issue 1: "OPENALGO_API_KEY environment variable is not set!"

**Error:**
```
ERROR: OPENALGO_API_KEY environment variable is not set!
```

**Solution:**
1. Get your API key from `http://127.0.0.1:5000/apikey`
2. Set environment variable:

**Windows PowerShell:**
```powershell
$env:OPENALGO_API_KEY = "your_64_char_key"
python strategies/examples/sandboxtest_fixed.py
```

**Windows Command Prompt:**
```cmd
set OPENALGO_API_KEY=your_64_char_key
python strategies/examples/sandboxtest_fixed.py
```

**Linux/Mac:**
```bash
export OPENALGO_API_KEY="your_64_char_key"
python strategies/examples/sandboxtest_fixed.py
```

---

### Issue 2: "API key must be 64 characters"

**Error:**
```
ERROR: API key must be 64 characters, got XX
```

**Solution:**
- Your API key is not 64 characters
- Get a new one from `http://127.0.0.1:5000/apikey`
- Make sure you copy the ENTIRE key without extra spaces
- Verify: `echo $OPENALGO_API_KEY | wc -c` should show 65 (64 + newline)

---

### Issue 3: "Connection refused" or "Cannot connect to OpenAlgo"

**Error:**
```
✗ Failed to initialize client: Connection refused
```

**Solution:**
1. **Verify OpenAlgo is running:**
   - Open `http://127.0.0.1:5000` in your browser
   - Should show OpenAlgo dashboard
   
2. **If not running, start it:**
   ```bash
   python app.py
   # or
   uv run app.py
   ```

3. **Check firewall:**
   - Ensure port 5000 is accessible
   - Windows: Check Windows Defender Firewall

4. **Check host configuration:**
   - Default: `http://127.0.0.1:5000`
   - If using different host, set environment variable:
   ```bash
   export HOST_SERVER="http://your_host:5000"
   ```

---

### Issue 4: "Unauthorized" or "Invalid API key"

**Error:**
```
✗ BUY order failed: Unauthorized
```

**Solution:**
1. **Regenerate API key:**
   - Go to `http://127.0.0.1:5000/apikey`
   - Click "Regenerate" or create new key
   - Copy the new 64-character key

2. **Update environment variable:**
   ```bash
   export OPENALGO_API_KEY="new_64_char_key"
   ```

3. **Verify broker is connected:**
   - Login page should show "Connected" status
   - If not, log in with broker credentials first

---

### Issue 5: "Insufficient funds" or "Order rejected"

**Error:**
```
✗ BUY order failed: Insufficient funds
```

**Solution:**
- This is normal in sandbox mode
- Sandbox account has limited balance
- Check account funds first:
  ```bash
  # Modify script to check funds before placing order
  funds = client.funds()
  print(f"Available funds: {funds}")
  ```

---

### Issue 6: "Symbol not found" or "Invalid exchange"

**Error:**
```
✗ BUY order failed: Symbol SBIN not found
```

**Solution:**
1. **Verify symbol format:**
   - NSE equity: `SBIN` (correct)
   - NSE futures: `SBIN25JAN26FUT` (format: SYMBOL+EXPIRY+FUT)
   - NSE options: `SBIN25JAN2650CE` (format: SYMBOL+EXPIRY+STRIKE+OPTTYPE)

2. **Verify exchange:**
   - NSE (equity): `NSE`
   - NSE futures/options: `NFO`
   - BSE: `BSE`
   - MCX: `MCX`

3. **Check broker supports symbol:**
   - Different brokers support different symbols
   - Try a popular symbol like `RELIANCE`, `TCS`, `INFY`

---

### Issue 7: "ModuleNotFoundError: No module named 'openalgo'"

**Error:**
```
ModuleNotFoundError: No module named 'openalgo'
```

**Solution:**
1. **Install OpenAlgo SDK:**
   ```bash
   pip install openalgo
   ```

2. **Verify installation:**
   ```bash
   python -c "from openalgo import api; print('OpenAlgo installed!')"
   ```

3. **If using virtual environment:**
   ```bash
   # Activate virtual environment first
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   
   # Then install
   pip install openalgo
   ```

---

### Issue 8: "WebSocket connection failed"

**Error:**
```
⚠ Could not get quote: WebSocket connection failed
```

**Solution:**
1. **Verify WebSocket port:**
   - Default: `ws://127.0.0.1:8765`
   - Check if port 8765 is accessible

2. **Check WebSocket proxy:**
   - WebSocket proxy should be running
   - Check OpenAlgo logs for WebSocket errors

3. **Firewall:**
   - Ensure port 8765 is not blocked by firewall

---

### Issue 9: "Timeout" errors

**Error:**
```
✗ Exception placing BUY order: Timeout
```

**Solution:**
1. **Increase timeout:**
   - Edit `sandboxtest_fixed.py`
   - Change `timeout=120.0` to `timeout=180.0` or higher

2. **Check network:**
   - Verify internet connection
   - Check if OpenAlgo server is responsive

3. **Check server load:**
   - If server is busy, requests may timeout
   - Try again after a few seconds

---

### Issue 10: "JSON decode error" or "Invalid response"

**Error:**
```
✗ Exception placing BUY order: JSON decode error
```

**Solution:**
1. **Verify OpenAlgo is running:**
   - Check `http://127.0.0.1:5000` loads
   - Check OpenAlgo logs for errors

2. **Check API response:**
   - Add debug logging to see actual response
   - Print `buy_response` to see what's returned

3. **Restart OpenAlgo:**
   ```bash
   # Stop OpenAlgo (Ctrl+C)
   # Then restart
   python app.py
   ```

---

## Debugging Steps

### Step 1: Verify Environment
```bash
# Check API key is set
echo $OPENALGO_API_KEY  # Linux/Mac
echo %OPENALGO_API_KEY% # Windows

# Check API key length
python -c "import os; key = os.getenv('OPENALGO_API_KEY'); print(f'Length: {len(key) if key else 0}')"
```

### Step 2: Verify OpenAlgo is Running
```bash
# Check if port 5000 is listening
netstat -an | grep 5000  # Linux/Mac
netstat -ano | findstr :5000  # Windows

# Or open in browser
# http://127.0.0.1:5000
```

### Step 3: Test API Connection
```python
from openalgo import api
import os

api_key = os.getenv('OPENALGO_API_KEY')
client = api(api_key=api_key, host='http://127.0.0.1:5000')

# Test funds call
funds = client.funds()
print(f"Funds: {funds}")
```

### Step 4: Enable Verbose Logging
```python
# Modify sandboxtest_fixed.py
client = api(
    api_key=OPENALGO_API_KEY,
    host=HOST_SERVER,
    verbose=True  # Enable verbose logging
)
```

---

## Quick Checklist

Before running the script:

- [ ] OpenAlgo is running (`http://127.0.0.1:5000` loads)
- [ ] You're logged in with broker credentials
- [ ] API key is copied from `/apikey` page
- [ ] API key is **exactly 64 characters**
- [ ] Environment variable is set correctly
- [ ] No extra spaces or quotes in key
- [ ] Broker shows "Connected" status
- [ ] Port 5000 is accessible
- [ ] Port 8765 is accessible (for WebSocket)

---

## Getting Help

If you're still having issues:

1. **Share the exact error message** you're seeing
2. **Share the full output** from running the script
3. **Check OpenAlgo logs** for server-side errors
4. **Verify broker connection** is active
5. **Try a different symbol** to isolate the issue

---

## Reference

- **API Documentation:** `docs/prompt/openalgo python sdk.md`
- **Order Constants:** `docs/prompt/order-constants.md`
- **Symbol Format:** `docs/prompt/symbol-format.md`
- **WebSocket Format:** `docs/prompt/websockets-format.md`

---

**Last Updated:** 2026-09-15
**Status:** Ready to help troubleshoot
