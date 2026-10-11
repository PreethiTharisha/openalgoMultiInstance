# Sandbox Test - Complete Working Example

## Your Error Analysis

From your error output:
```
BROKER_API_SECRET = eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9...
BROKER_API_KEY = wxyz123
HOST_SERVER = http://127.0.0.1:5000

{'status': 'error', 'message': 'HTTP 400: {"message":{"apikey":["Length must be between 1 and 256."]},"status":"error"}\n', 'code': 400, 'error_type': 'http_error'}
```

### The Problem

1. **`BROKER_API_KEY = wxyz123`** - This is a **placeholder/dummy key**, only 8 characters
2. **API validation requires 1-256 characters** - Your key is too short
3. **The actual OpenAlgo API key is different** - It's a 64-character hexadecimal string, not the broker API key

### The Confusion

- **`BROKER_API_KEY`** = Your broker's API key (for broker authentication)
- **`OPENALGO_API_KEY`** = OpenAlgo's API key (for OpenAlgo platform authentication) ← **This is what you need**

---

## Complete Working Example

### Step 1: Get Your OpenAlgo API Key

1. Start OpenAlgo: `http://127.0.0.1:5000`
2. Log in with your broker credentials
3. Go to **Settings** → **API Key** (or `/apikey` route)
4. **Copy the full 64-character key**

Example valid key:
```
0aac0bae37a2458241ff0405084b17c54368ea461b9ea5e65a2a44e2fae9a165
```

### Step 2: Create Your Test Script

Create a file named `sandbox_test.py`:

```python
#!/usr/bin/env python
"""
OpenAlgo Sandbox Test - Complete Working Example
Tests basic order placement in sandbox mode
"""

import os
import sys
from datetime import datetime

# Add parent directory to path if running from strategies/scripts/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from openalgo import api

# ============================================================================
# CONFIGURATION
# ============================================================================

# Get API key from environment variable
OPENALGO_API_KEY = os.getenv('OPENALGO_API_KEY')

# Fallback to hardcoded key (NOT RECOMMENDED for production)
if not OPENALGO_API_KEY:
    print("⚠️  WARNING: OPENALGO_API_KEY environment variable not set!")
    print("   Set it with: export OPENALGO_API_KEY='your_64_char_key'")
    print()
    print("   Using default example key (will fail if not your actual key)...")
    OPENALGO_API_KEY = "0aac0bae37a2458241ff0405084b17c54368ea461b9ea5e65a2a44e2fae9a165"

# Server configuration
HOST_SERVER = os.getenv('HOST_SERVER', 'http://127.0.0.1:5000')
WEBSOCKET_URL = os.getenv('WEBSOCKET_URL', 'ws://127.0.0.1:8765')

# Trading configuration
STRATEGY_NAME = "SandboxTest"
SYMBOL = "SBIN"
EXCHANGE = "NSE"
QUANTITY = 1
PRODUCT = "MIS"  # Intraday Square Off

# ============================================================================
# VALIDATION
# ============================================================================

def validate_api_key(api_key):
    """Validate API key format"""
    if not api_key:
        return False, "API key is empty"
    
    if len(api_key) != 64:
        return False, f"API key must be 64 characters, got {len(api_key)}"
    
    # Check if it's hexadecimal
    try:
        int(api_key, 16)
        return True, "Valid"
    except ValueError:
        return False, "API key must be hexadecimal (0-9, a-f)"

# ============================================================================
# MAIN TEST
# ============================================================================

def main():
    print("=" * 80)
    print("OpenAlgo Sandbox Test - Starting at", datetime.now().strftime("%Y-%m-%d %H:%M:%S IST"))
    print("=" * 80)
    print()
    
    # Validate API key
    print("[1] Validating API Key...")
    is_valid, message = validate_api_key(OPENALGO_API_KEY)
    
    if not is_valid:
        print(f"    ✗ API Key validation failed: {message}")
        print(f"    ✗ Received: {OPENALGO_API_KEY[:16]}...{OPENALGO_API_KEY[-16:]}")
        print()
        print("    ACTION REQUIRED:")
        print("    1. Go to http://127.0.0.1:5000/apikey")
        print("    2. Copy the 64-character API key")
        print("    3. Set environment variable: export OPENALGO_API_KEY='your_key'")
        return False
    
    print(f"    ✓ API Key is valid: {OPENALGO_API_KEY[:8]}...{OPENALGO_API_KEY[-8:]}")
    print()
    
    # Initialize client
    print("[2] Initializing OpenAlgo Client...")
    try:
        client = api(
            api_key=OPENALGO_API_KEY,
            host=HOST_SERVER,
            version='v1',
            timeout=120.0,
            ws_port=8765,
            ws_url=WEBSOCKET_URL,
            verbose=False,
            auto_reconnect=True
        )
        print(f"    ✓ Client initialized")
        print(f"    ✓ Host: {HOST_SERVER}")
        print(f"    ✓ WebSocket: {WEBSOCKET_URL}")
    except Exception as e:
        print(f"    ✗ Failed to initialize client: {e}")
        return False
    
    print()
    
    # Get account info
    print("[3] Getting Account Information...")
    try:
        funds = client.funds()
        if funds.get('status') == 'success':
            print(f"    ✓ Account funds retrieved")
            print(f"    ✓ Response: {funds}")
        else:
            print(f"    ⚠ Funds call returned: {funds}")
    except Exception as e:
        print(f"    ⚠ Could not get funds: {e}")
    
    print()
    
    # Get market quote
    print(f"[4] Getting Market Quote for {SYMBOL}...")
    try:
        quote = client.quotes(symbol=SYMBOL, exchange=EXCHANGE)
        if quote.get('status') == 'success':
            data = quote.get('data', {})
            ltp = data.get('ltp', 'N/A')
            print(f"    ✓ Quote retrieved")
            print(f"    ✓ LTP: {ltp}")
        else:
            print(f"    ⚠ Quote call returned: {quote}")
    except Exception as e:
        print(f"    ⚠ Could not get quote: {e}")
    
    print()
    
    # Place BUY order
    print(f"[5] Placing BUY Order...")
    print(f"    Symbol: {SYMBOL}")
    print(f"    Exchange: {EXCHANGE}")
    print(f"    Quantity: {QUANTITY}")
    print(f"    Product: {PRODUCT}")
    print(f"    Strategy: {STRATEGY_NAME}")
    
    try:
        buy_response = client.placeorder(
            strategy=STRATEGY_NAME,
            symbol=SYMBOL,
            action="BUY",
            exchange=EXCHANGE,
            price_type="MARKET",
            product=PRODUCT,
            quantity=QUANTITY
        )
        
        print(f"    Response: {buy_response}")
        
        if buy_response.get('status') == 'success':
            order_id = buy_response.get('orderid')
            print(f"    ✓ BUY order placed successfully!")
            print(f"    ✓ Order ID: {order_id}")
            
            # Store order ID for later
            buy_order_id = order_id
        else:
            error_msg = buy_response.get('message', 'Unknown error')
            print(f"    ✗ BUY order failed: {error_msg}")
            return False
    
    except Exception as e:
        print(f"    ✗ Exception placing BUY order: {e}")
        return False
    
    print()
    
    # Place SELL order
    print(f"[6] Placing SELL Order...")
    print(f"    Symbol: {SYMBOL}")
    print(f"    Exchange: {EXCHANGE}")
    print(f"    Quantity: {QUANTITY}")
    print(f"    Product: {PRODUCT}")
    print(f"    Strategy: {STRATEGY_NAME}")
    
    try:
        sell_response = client.placeorder(
            strategy=STRATEGY_NAME,
            symbol=SYMBOL,
            action="SELL",
            exchange=EXCHANGE,
            price_type="MARKET",
            product=PRODUCT,
            quantity=QUANTITY
        )
        
        print(f"    Response: {sell_response}")
        
        if sell_response.get('status') == 'success':
            order_id = sell_response.get('orderid')
            print(f"    ✓ SELL order placed successfully!")
            print(f"    ✓ Order ID: {order_id}")
        else:
            error_msg = sell_response.get('message', 'Unknown error')
            print(f"    ✗ SELL order failed: {error_msg}")
            return False
    
    except Exception as e:
        print(f"    ✗ Exception placing SELL order: {e}")
        return False
    
    print()
    
    # Get order book
    print("[7] Getting Order Book...")
    try:
        orderbook = client.orderbook()
        if orderbook.get('status') == 'success':
            orders = orderbook.get('data', [])
            print(f"    ✓ Order book retrieved")
            print(f"    ✓ Total orders: {len(orders)}")
            for order in orders[:5]:  # Show first 5
                print(f"       - {order.get('symbol')}: {order.get('action')} {order.get('quantity')} @ {order.get('order_status')}")
        else:
            print(f"    ⚠ Order book call returned: {orderbook}")
    except Exception as e:
        print(f"    ⚠ Could not get order book: {e}")
    
    print()
    print("=" * 80)
    print("✓ Sandbox Test Completed Successfully!")
    print("=" * 80)
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
```

### Step 3: Run the Test

**Set environment variable and run:**

**Linux/Mac:**
```bash
export OPENALGO_API_KEY="0aac0bae37a2458241ff0405084b17c54368ea461b9ea5e65a2a44e2fae9a165"
python sandbox_test.py
```

**Windows PowerShell:**
```powershell
$env:OPENALGO_API_KEY = "0aac0bae37a2458241ff0405084b17c54368ea461b9ea5e65a2a44e2fae9a165"
python sandbox_test.py
```

**Windows Command Prompt:**
```cmd
set OPENALGO_API_KEY=0aac0bae37a2458241ff0405084b17c54368ea461b9ea5e65a2a44e2fae9a165
python sandbox_test.py
```

### Step 4: Expected Output

```
================================================================================
OpenAlgo Sandbox Test - Starting at 2026-09-15 09:05:00 IST
================================================================================

[1] Validating API Key...
    ✓ API Key is valid: 0aac0bae...fae9a165

[2] Initializing OpenAlgo Client...
    ✓ Client initialized
    ✓ Host: http://127.0.0.1:5000
    ✓ WebSocket: ws://127.0.0.1:8765

[3] Getting Account Information...
    ✓ Account funds retrieved
    ✓ Response: {'status': 'success', 'data': {...}}

[4] Getting Market Quote for SBIN...
    ✓ Quote retrieved
    ✓ LTP: 769.60

[5] Placing BUY Order...
    Symbol: SBIN
    Exchange: NSE
    Quantity: 1
    Product: MIS
    Strategy: SandboxTest
    Response: {'status': 'success', 'orderid': '250915000123456'}
    ✓ BUY order placed successfully!
    ✓ Order ID: 250915000123456

[6] Placing SELL Order...
    Symbol: SBIN
    Exchange: NSE
    Quantity: 1
    Product: MIS
    Strategy: SandboxTest
    Response: {'status': 'success', 'orderid': '250915000123457'}
    ✓ SELL order placed successfully!
    ✓ Order ID: 250915000123457

[7] Getting Order Book...
    ✓ Order book retrieved
    ✓ Total orders: 2
       - SBIN: BUY 1 @ complete
       - SBIN: SELL 1 @ complete

================================================================================
✓ Sandbox Test Completed Successfully!
================================================================================
```

---

## Troubleshooting

### Error: "Length must be between 1 and 256"
**Cause:** API key is empty, too short, or not set
**Fix:** 
1. Get valid API key from `/apikey`
2. Set environment variable: `export OPENALGO_API_KEY='your_key'`
3. Verify key is 64 characters

### Error: "HTTP 400: ... apikey ..."
**Cause:** API key validation failed
**Fix:**
1. Check API key format (must be hexadecimal)
2. Ensure no extra spaces or quotes
3. Regenerate key at `/apikey`

### Error: "Connection refused"
**Cause:** OpenAlgo server not running
**Fix:**
1. Start OpenAlgo: `python app.py` or `uv run app.py`
2. Verify it's accessible: `http://127.0.0.1:5000`
3. Check firewall allows port 5000

### Error: "Unauthorized"
**Cause:** API key is invalid or expired
**Fix:**
1. Regenerate API key at `/apikey`
2. Update environment variable
3. Restart your script

### Error: "Insufficient funds"
**Cause:** Sandbox account doesn't have enough balance
**Fix:**
1. This is normal in sandbox - it's testing mode
2. Orders will still be placed but may fail execution
3. Check account funds with `client.funds()`

---

## Key Differences: Broker API Key vs OpenAlgo API Key

| Aspect | Broker API Key | OpenAlgo API Key |
|--------|---|---|
| **Purpose** | Authenticate with broker | Authenticate with OpenAlgo platform |
| **Length** | Varies (8-256 chars) | 64 characters |
| **Format** | Broker-specific | Hexadecimal (0-9, a-f) |
| **Where to get** | Broker's website/app | OpenAlgo `/apikey` page |
| **Used in** | Broker authentication | OpenAlgo SDK/API calls |
| **Example** | `wxyz123` | `0aac0bae37a2458241ff0405084b17c54368ea461b9ea5e65a2a44e2fae9a165` |

---

## Next Steps

1. ✓ Get your OpenAlgo API key from `/apikey`
2. ✓ Run the sandbox test script above
3. ✓ Once working, modify for your trading strategy
4. ✓ Refer to `QUICK_REFERENCE.md` for all available methods

---

**Documentation References:**
- `docs/prompt/openalgo python sdk.md` - Full SDK reference
- `docs/prompt/order-constants.md` - All order constants
- `docs/prompt/symbol-format.md` - Symbol formats
- `QUICK_REFERENCE.md` - Quick lookup guide
- `APIKEY_VALIDATION_FIX.md` - API key troubleshooting
