# Smart Continuous Trading Bot - Guide

## Overview

The **Smart Continuous Trading Bot** is an intelligent version that:
- ✅ Places orders at calculated prices
- ✅ **Waits and monitors** order execution
- ✅ **Only places new orders** when previous ones fill or price moves significantly
- ✅ **Avoids spam orders** - no continuous placement without monitoring
- ✅ Tracks order status continuously
- ✅ Displays real-time statistics

---

## How It Works

### Phase 1: Initial Order Placement

1. **Get Current Price:** Rs. 980.90
2. **Calculate Order Prices:**
   - BUY: 980.90 - 5 = Rs. 975.90
   - SELL: 980.90 + 5 = Rs. 985.90
3. **Place Orders:** Both BUY and SELL orders at calculated prices
4. **Status:** Waiting for execution

### Phase 2: Monitoring & Execution

1. **Monitor Current Price:** Check every 5 seconds
2. **Check Order Status:** Check every 10 seconds
3. **Wait for Execution:** If order fills, record it
4. **Track Statistics:** Count filled orders

### Phase 3: New Order Placement (Smart)

**Only place new order when:**
- ✅ Previous order has been **filled/executed**
- OR
- ✅ Current price has moved **2+ rupees** from last order price

**Do NOT place new order if:**
- ❌ Previous order is still pending
- ❌ Price hasn't moved significantly
- ❌ Just placed an order recently

---

## Example Scenario

### Scenario: Buying at Rs. 250

**Time 11:00:00**
- Current Price: Rs. 250.00
- Place BUY order at Rs. 245.00 (250 - 5)
- Status: **PENDING**

**Time 11:00:05 to 11:05:00**
- Monitor price: Rs. 250.00 → Rs. 251.00 → Rs. 252.00
- Check order status: Still PENDING
- **Do NOT place new order** (price moved only 2 Rs, order still pending)

**Time 11:05:00**
- Current Price: Rs. 252.00
- Order still PENDING at Rs. 245.00
- **Do NOT place new order** (order not filled yet)

**Time 11:10:00**
- Current Price: Rs. 245.00
- Order at Rs. 245.00 gets **FILLED**
- Status: **EXECUTED**
- Now ready to place new order

**Time 11:10:05**
- Current Price: Rs. 245.00
- Place NEW BUY order at Rs. 240.00 (245 - 5)
- Status: **PENDING**
- Repeat cycle...

---

## Key Differences from Basic Bot

### Basic Bot (❌ Problems)
```
[11:00:00] Place BUY order at 245
[11:00:30] Place BUY order at 245 (again!)
[11:01:00] Place BUY order at 245 (again!)
[11:01:30] Place BUY order at 245 (again!)
...
Result: 25 BUY orders placed, none filled!
```

### Smart Bot (✅ Intelligent)
```
[11:00:00] Place BUY order at 245
[11:00:05] Monitor: Price 250, Order PENDING → Wait
[11:00:10] Monitor: Price 251, Order PENDING → Wait
[11:00:15] Monitor: Price 252, Order PENDING → Wait
[11:05:00] Monitor: Price 245, Order FILLED → Success!
[11:05:05] Place NEW BUY order at 240
[11:05:10] Monitor: Price 245, Order PENDING → Wait
...
Result: 1 BUY order filled, then new order placed!
```

---

## Configuration

### Default Settings

```python
STOPLOSS_AMOUNT = 5.0          # 5 rupees loss
PROFIT_TARGET = 10.0           # 10 rupees profit
PRICE_OFFSET = 5.0             # Place order 5 Rs away from current price

PRICE_CHECK_INTERVAL = 5       # Check price every 5 seconds
ORDER_STATUS_CHECK_INTERVAL = 10  # Check order status every 10 seconds
SIGNIFICANT_PRICE_MOVE = 2.0   # If price moves 2+ Rs, place new order
```

### Customization

**For Faster Trading (Scalping):**
```python
PRICE_OFFSET = 2.0             # Closer to current price
PROFIT_TARGET = 5.0            # Smaller profit
STOPLOSS_AMOUNT = 2.0          # Smaller loss
PRICE_CHECK_INTERVAL = 2       # Check more frequently
SIGNIFICANT_PRICE_MOVE = 1.0   # Smaller move threshold
```

**For Swing Trading:**
```python
PRICE_OFFSET = 10.0            # Further from current price
PROFIT_TARGET = 20.0           # Larger profit
STOPLOSS_AMOUNT = 10.0         # Larger loss
PRICE_CHECK_INTERVAL = 30      # Check less frequently
SIGNIFICANT_PRICE_MOVE = 5.0   # Larger move threshold
```

---

## Running the Bot

### Start the Bot

```bash
python strategies/examples/continuous_trading_bot_smart.py
```

### Expected Output

```
================================================================================
=== Smart Continuous Trading Bot ===
=== Started at 2026-09-15 11:00:00 IST ===
================================================================================

[BOT] Smart Continuous Trading Bot Started
[BOT] Host: http://127.0.0.1:5000
[BOT] Symbol: SBIN on NSE
[BOT] Quantity: 1
[BOT] Stop Loss: Rs.5.0
[BOT] Profit Target: Rs.10.0
[BOT] Price Offset: Rs.5.0
[BOT] Significant Price Move: Rs.2.0

[BOT] Starting smart trading loop...
[BOT] Monitoring price and order execution
[BOT] Press Ctrl+C to stop

[PRICE] Current LTP: Rs.980.90
[ORDER] Placing BUY order at Rs.975.90...
[OK] BUY order placed!
     Order ID: 26091596939790
     Price: Rs.975.90
     Target: Rs.985.90
     Stop Loss: Rs.970.90

[ORDER] Placing SELL order at Rs.985.90...
[OK] SELL order placed!
     Order ID: 26091528333781
     Price: Rs.985.90
     Target: Rs.975.90
     Stop Loss: Rs.990.90

================================================================================
[STATUS] 2026-09-15 11:00:15
[STATUS] Current Price: Rs.980.90
[STATUS] BUY Orders: Placed=1 | Filled=0
[STATUS] SELL Orders: Placed=1 | Filled=0
[STATUS] Total Trades: 0
[STATUS] Last BUY Order: 26091596939790 @ Rs.975.90
[STATUS] Last SELL Order: 26091528333781 @ Rs.985.90
================================================================================

[PRICE] Current LTP: Rs.981.00
[PRICE] Current LTP: Rs.981.50
[PRICE] Current LTP: Rs.982.00

[FILLED] BUY Order 26091596939790 FILLED at Rs.975.90

[SIGNAL] Price moved 6.10 Rs from last BUY order
[ORDER] Placing BUY order at Rs.976.00...
[OK] BUY order placed!
     Order ID: 26091596939791
     Price: Rs.976.00
     Target: Rs.986.00
     Stop Loss: Rs.971.00

================================================================================
[STATUS] 2026-09-15 11:00:30
[STATUS] Current Price: Rs.982.00
[STATUS] BUY Orders: Placed=2 | Filled=1
[STATUS] SELL Orders: Placed=1 | Filled=0
[STATUS] Total Trades: 1
[STATUS] Last BUY Order: 26091596939791 @ Rs.976.00
[STATUS] Last SELL Order: 26091528333781 @ Rs.985.90
================================================================================
```

---

## Monitoring Behavior

### Price Monitoring (Every 5 seconds)
```
[PRICE] Current LTP: Rs.980.90
[PRICE] Current LTP: Rs.981.00
[PRICE] Current LTP: Rs.981.50
[PRICE] Current LTP: Rs.982.00
```

### Order Status Monitoring (Every 10 seconds)
```
[FILLED] BUY Order 26091596939790 FILLED at Rs.975.90
[FILLED] SELL Order 26091528333781 FILLED at Rs.985.90
```

### Intelligent Order Placement
```
[SIGNAL] Price moved 6.10 Rs from last BUY order
[ORDER] Placing BUY order at Rs.976.00...
[OK] BUY order placed!
```

---

## Statistics Tracking

The bot tracks:
- **BUY Orders:** Placed count and Filled count
- **SELL Orders:** Placed count and Filled count
- **Total Trades:** Total number of filled orders
- **Current Price:** Real-time market price
- **Last Orders:** ID and price of last BUY/SELL orders

---

## Advantages Over Basic Bot

| Feature | Basic Bot | Smart Bot |
|---------|-----------|-----------|
| **Order Placement** | Continuous (spam) | Intelligent (monitored) |
| **Execution Check** | No | Yes |
| **Price Monitoring** | No | Yes (every 5s) |
| **Order Status Check** | No | Yes (every 10s) |
| **New Order Logic** | Always place | Only when needed |
| **Statistics** | Basic count | Detailed tracking |
| **Efficiency** | Low | High |
| **Real Orders** | Many pending | Few, mostly filled |

---

## Use Cases

### Day Trading
- Fast price movements
- Quick order execution
- Multiple trades per day

### Scalping
- Very tight stops (2-3 Rs)
- Quick profits (5-10 Rs)
- High frequency

### Swing Trading
- Wider stops (10-20 Rs)
- Larger profits (20-50 Rs)
- Fewer, larger trades

---

## Stopping the Bot

Press **Ctrl+C**:

```
[BOT] Shutting down...

================================================================================
[STATUS] 2026-09-15 11:05:45
[STATUS] Current Price: Rs.985.50
[STATUS] BUY Orders: Placed=5 | Filled=4
[STATUS] SELL Orders: Placed=5 | Filled=4
[STATUS] Total Trades: 8
================================================================================

[BOT] Trading stopped
```

---

## Important Notes

⚠️ **Limit Orders Only**
- Orders are placed at LIMIT prices
- May not execute if price doesn't reach
- Check dashboard to see pending orders

⚠️ **Sandbox Mode**
- All orders are in "analyze" mode
- No real money is used
- Good for testing

⚠️ **Market Hours**
- Orders only execute during market hours
- Outside hours, orders remain pending

⚠️ **Broker Connectivity**
- Ensure broker is connected
- Check login status in OpenAlgo
- Verify market data is flowing

---

## Reference

- **Order Constants:** `docs/prompt/order-constants.md`
- **Symbol Format:** `docs/prompt/symbol-format.md`
- **Python SDK:** `docs/prompt/openalgo python sdk.md`

---

**Status:** ✅ Ready to use
**Created:** 2026-09-15
**Type:** Smart Trading Bot
