# Smart Bot with Time Limits - Complete Guide

## Overview

Both smart bots now include **time-based trading controls**:
- ✅ **Trading Hours:** 9:15 AM - 3:30 PM IST
- ✅ **Last Order Time:** 2:45 PM IST (no new orders after this)
- ✅ **Market Monitoring:** Continues until market close
- ✅ **Intelligent Order Management:** Only places when previous fills

---

## Time Limits Explained

### Trading Hours
```
9:15 AM  ─────────────────────────────────  3:30 PM
 ↑                                           ↑
 Market Opens                                Market Closes
```

### Order Placement Window
```
9:15 AM  ─────────────────────  2:45 PM  ─  3:30 PM
 ↑                               ↑           ↑
 Market Opens                    No New      Market
 Orders Placed                   Orders      Closes
```

### What Happens

**9:15 AM - 2:45 PM:**
- ✅ Place new BUY orders
- ✅ Place new SELL orders
- ✅ Monitor existing orders
- ✅ Execute trades

**2:45 PM - 3:30 PM:**
- ❌ NO new BUY orders
- ❌ NO new SELL orders
- ✅ Monitor existing orders
- ✅ Let pending orders execute
- ✅ Close out positions

**After 3:30 PM:**
- ❌ Market closed
- ✅ Wait for next trading day

---

## Scripts Available

### 1. Equity Trading Bot (SBIN, RELIANCE, etc.)
```bash
python strategies/examples/continuous_trading_bot_smart.py
```

**Features:**
- Smart order placement (only when previous fills)
- Time-based trading controls
- Equity trading (NSE)
- 5 rupees offset, 10 rupees profit target

### 2. NIFTY Futures Bot
```bash
python strategies/examples/continuous_trading_bot_nifty_smart.py
```

**Features:**
- Smart order placement (only when previous fills)
- Time-based trading controls
- NIFTY futures trading (NFO)
- 5 points offset, 10 points profit target
- Current expiry: NIFTY25SEP26FUT

---

## Expected Behavior

### Morning (9:15 AM - 2:45 PM)

```
[BOT] Starting smart trading loop...
[BOT] Trading Hours: 09:15 - 15:30 IST
[BOT] Last Order Time: 14:45 IST
[BOT] Monitoring price and order execution

[PRICE] Current LTP: Rs.979.70
[ORDER] Placing BUY order at Rs.974.70...
[OK] BUY order placed!

[PRICE] Current LTP: Rs.979.80
[PRICE] Current LTP: Rs.979.60

[FILLED] BUY Order FILLED at Rs.974.70

[ORDER] Placing BUY order at Rs.974.80...
[OK] BUY order placed!

[STATUS] BUY Orders: Placed=2 | Filled=1
[STATUS] SELL Orders: Placed=2 | Filled=1
[STATUS] Total Trades: 2
```

### Afternoon (2:45 PM - 3:30 PM)

```
[PRICE] Current LTP: Rs.980.50

[TIME LIMIT] 14:45:30 - No new orders after 2:45 PM. Monitoring existing orders only...

[PRICE] Current LTP: Rs.980.60
[PRICE] Current LTP: Rs.980.70

[FILLED] SELL Order FILLED at Rs.985.70

[STATUS] BUY Orders: Placed=3 | Filled=2
[STATUS] SELL Orders: Placed=3 | Filled=3
[STATUS] Total Trades: 5

[PRICE] Current LTP: Rs.980.80

[TIME LIMIT] 14:50:30 - No new orders after 2:45 PM. Monitoring existing orders only...

[MARKET CLOSED] 15:30:45 - Market is closed. Waiting for market open...
```

---

## Configuration

### Default Settings (Both Bots)

```python
# Trading Hours (IST)
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 15
MARKET_CLOSE_HOUR = 15  # 3:00 PM
MARKET_CLOSE_MINUTE = 30
LAST_ORDER_HOUR = 14  # 2:00 PM
LAST_ORDER_MINUTE = 45  # Stop placing new orders at 2:45 PM
```

### Customize Time Limits

**To change last order time to 3:00 PM:**
```python
LAST_ORDER_HOUR = 15
LAST_ORDER_MINUTE = 0
```

**To change last order time to 2:30 PM:**
```python
LAST_ORDER_HOUR = 14
LAST_ORDER_MINUTE = 30
```

**To change market close time to 4:00 PM:**
```python
MARKET_CLOSE_HOUR = 16
MARKET_CLOSE_MINUTE = 0
```

---

## Equity Bot Configuration

### File
```
strategies/examples/continuous_trading_bot_smart.py
```

### Default Settings
```python
SYMBOL = 'SBIN'           # Stock symbol
EXCHANGE = 'NSE'          # National Stock Exchange
QUANTITY = 1              # 1 share per order
PRODUCT = "MIS"           # Intraday Square Off

STOPLOSS_AMOUNT = 5.0     # 5 rupees loss
PROFIT_TARGET = 10.0      # 10 rupees profit
PRICE_OFFSET = 5.0        # Place order 5 Rs away
```

### Change Symbol
Edit the script:
```python
SYMBOL = 'RELIANCE'  # Instead of SBIN
```

Or use environment variable:
```bash
export SYMBOL="RELIANCE"
python strategies/examples/continuous_trading_bot_smart.py
```

---

## NIFTY Bot Configuration

### File
```
strategies/examples/continuous_trading_bot_nifty_smart.py
```

### Default Settings
```python
SYMBOL = 'NIFTY25SEP26FUT'  # NIFTY Futures (September 2026)
EXCHANGE = 'NFO'            # Futures & Options
QUANTITY = 1                # 1 lot
PRODUCT = "NRML"            # Normal (for futures)

STOPLOSS_AMOUNT = 5.0       # 5 points loss
PROFIT_TARGET = 10.0        # 10 points profit
PRICE_OFFSET = 5.0          # Place order 5 points away
```

### Change NIFTY Expiry
Edit the script:
```python
SYMBOL = 'NIFTY25OCT26FUT'  # October 2026 expiry
```

---

## How Time Limits Work

### 1. Market Open Check
```python
def is_within_trading_hours(self):
    """Check if current time is within trading hours"""
    # Returns True if 9:15 AM - 3:30 PM
    # Returns False otherwise
```

### 2. Order Placement Check
```python
def can_place_new_order(self):
    """Check if we can place new orders (before 2:45 PM)"""
    # Returns True if before 2:45 PM
    # Returns False after 2:45 PM
```

### 3. Main Loop Logic
```python
# Check if market is open
if not self.is_within_trading_hours():
    print("Market is closed. Waiting...")
    time.sleep(60)
    continue

# Check if we can place new orders
if self.can_place_new_order():
    # Place new orders
    if self.should_place_new_order(self.last_buy_order_id):
        self.place_buy_order(buy_price)
else:
    # After 2:45 PM, only monitor
    print("No new orders after 2:45 PM. Monitoring only...")
```

---

## Benefits of Time Limits

✅ **Risk Management**
- No new orders near market close
- Reduces overnight risk
- Allows time to close positions

✅ **Regulatory Compliance**
- Follows market hours
- Respects trading windows
- Professional trading pattern

✅ **Operational Safety**
- Avoids last-minute orders
- Gives time for order execution
- Prevents rushed decisions

✅ **Better Statistics**
- Clear trading window
- Easier to track daily results
- Professional reporting

---

## Example Scenarios

### Scenario 1: Order Placed at 2:40 PM

```
[PRICE] Current LTP: Rs.980.50
[TIME] 14:40:15

[ORDER] Placing BUY order at Rs.975.50...
[OK] BUY order placed!
     Order ID: 26091589228293

[PRICE] Current LTP: Rs.980.60
[TIME] 14:45:00

[TIME LIMIT] 14:45:00 - No new orders after 2:45 PM. Monitoring only...

[FILLED] BUY Order FILLED at Rs.975.50
[TIME] 14:45:30

[ORDER] Placing BUY order at Rs.975.60...
❌ BLOCKED - After 2:45 PM, no new orders!

[STATUS] Monitoring existing orders only...
```

### Scenario 2: Order Pending at 2:45 PM

```
[PRICE] Current LTP: Rs.980.50
[TIME] 14:30:00

[ORDER] Placing BUY order at Rs.975.50...
[OK] BUY order placed!
     Order ID: 26091589228293
     Status: PENDING

[PRICE] Current LTP: Rs.980.60
[TIME] 14:45:00

[TIME LIMIT] 14:45:00 - No new orders after 2:45 PM. Monitoring only...

[PRICE] Current LTP: Rs.980.70
[TIME] 14:50:00

[FILLED] BUY Order FILLED at Rs.975.50
[TIME] 14:50:30

[STATUS] Previous order filled, but no new orders after 2:45 PM
[STATUS] Monitoring existing orders only...

[PRICE] Current LTP: Rs.980.80
[TIME] 15:00:00

[STATUS] Waiting for market close...
```

---

## Running the Bots

### Equity Bot
```bash
python strategies/examples/continuous_trading_bot_smart.py
```

### NIFTY Bot
```bash
python strategies/examples/continuous_trading_bot_nifty_smart.py
```

### With Custom Symbol
```bash
export SYMBOL="RELIANCE"
python strategies/examples/continuous_trading_bot_smart.py
```

---

## Stopping the Bot

Press **Ctrl+C**:

```
[BOT] Shutting down...

================================================================================
[STATUS] 2026-09-15 14:50:45
[STATUS] Current Price: Rs.980.50
[STATUS] BUY Orders: Placed=5 | Filled=4
[STATUS] SELL Orders: Placed=5 | Filled=4
[STATUS] Total Trades: 8
================================================================================

[BOT] Trading stopped
```

---

## Summary

| Feature | Equity Bot | NIFTY Bot |
|---------|-----------|-----------|
| **Symbol** | SBIN (NSE) | NIFTY25SEP26FUT (NFO) |
| **Exchange** | NSE | NFO |
| **Product** | MIS | NRML |
| **Offset** | 5 Rs | 5 points |
| **Profit** | 10 Rs | 10 points |
| **Time Limits** | 9:15 AM - 3:30 PM | 9:15 AM - 3:30 PM |
| **Last Order** | 2:45 PM | 2:45 PM |
| **Smart Logic** | ✅ Yes | ✅ Yes |

---

**Status:** ✅ **Ready to use!**

Both bots now have intelligent time-based trading controls. They will automatically stop placing new orders at 2:45 PM and only monitor existing orders until market close. 🎯

