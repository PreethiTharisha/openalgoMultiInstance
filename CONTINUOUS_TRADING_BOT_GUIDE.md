# Continuous Trading Bot - Guide

## Overview

The **Continuous Trading Bot** automatically places BUY and SELL orders continuously with:
- **BUY Order:** Current Price - 5 rupees (with 10 rupees profit target)
- **SELL Order:** Current Price + 5 rupees (with 10 rupees profit target)
- **Interval:** Every 30 seconds (configurable)

---

## Features

✅ **Continuous Trading**
- Places BUY and SELL orders at regular intervals
- Automatically calculates prices based on current LTP

✅ **Risk Management**
- Stop Loss: 5 rupees
- Profit Target: 10 rupees
- Limit orders (not market orders)

✅ **Real-time Monitoring**
- Gets current market price
- Displays order status
- Tracks total trades

✅ **Genuine Orders**
- Uses LIMIT orders (not MARKET)
- Orders placed at specific prices
- Can be accepted or rejected by market

---

## How It Works

### Step 1: Get Current Price
```
Current LTP: Rs.980.90
```

### Step 2: Calculate Order Prices
```
BUY Price:  Rs.975.90  (Current - 5)
SELL Price: Rs.985.90  (Current + 5)
```

### Step 3: Place Orders
```
BUY Order:
  - Price: Rs.975.90
  - Target: Rs.985.90 (profit of 10)
  - Stop Loss: Rs.970.90 (loss of 5)

SELL Order:
  - Price: Rs.985.90
  - Target: Rs.975.90 (profit of 10)
  - Stop Loss: Rs.990.90 (loss of 5)
```

### Step 4: Wait & Repeat
```
Wait 30 seconds, then repeat from Step 1
```

---

## Running the Bot

### Step 1: Set Environment Variable

**Windows PowerShell:**
```powershell
$env:OPENALGO_API_KEY = "your_64_char_key"
```

**Windows Command Prompt:**
```cmd
set OPENALGO_API_KEY=your_64_char_key
```

**Linux/Mac:**
```bash
export OPENALGO_API_KEY="your_64_char_key"
```

### Step 2: Run the Script

```bash
python strategies/examples/continuous_trading_bot.py
```

### Step 3: Expected Output

```
================================================================================
=== Continuous Trading Bot ===
=== Started at 2026-09-15 11:30:00 IST ===
================================================================================

[BOT] Continuous Trading Bot Started
[BOT] Host: http://127.0.0.1:5000
[BOT] Symbol: SBIN on NSE
[BOT] Quantity: 1
[BOT] Stop Loss: Rs.5.0
[BOT] Profit Target: Rs.10.0
[BOT] Order Interval: 30 seconds

[BOT] Starting trading loop...
[BOT] Orders will be placed every 30 seconds
[BOT] Press Ctrl+C to stop

[PRICE] Current LTP: Rs.980.90
[CALC] Buy Price: Rs.975.90 (Current - 5)
[CALC] Sell Price: Rs.985.90 (Current + 5)

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
[STATUS] 2026-09-15 11:30:15
[STATUS] Total Trades: 2 | BUY: 1 | SELL: 1
================================================================================

[BOT] Waiting 30 seconds before next orders...
```

---

## Configuration

You can customize the bot by modifying these variables:

### Symbol
```python
SYMBOL = os.getenv('SYMBOL', 'SBIN')
```

Change to any symbol:
```bash
export SYMBOL="RELIANCE"
python strategies/examples/continuous_trading_bot.py
```

### Quantity
```python
QUANTITY = 1  # Change to desired quantity
```

### Stop Loss Amount
```python
STOPLOSS_AMOUNT = 5.0  # Change to desired loss amount
```

### Profit Target
```python
PROFIT_TARGET = 10.0  # Change to desired profit amount
```

### Order Interval
```python
INTERVAL_SECONDS = 30  # Change to desired interval
```

---

## Understanding the Orders

### BUY Order Example

```
Current Price: Rs.980.90

BUY Order:
  Price: Rs.975.90 (5 rupees below current)
  Quantity: 1
  Type: LIMIT
  
If executed:
  Entry: Rs.975.90
  Target: Rs.985.90 (profit of 10)
  Stop Loss: Rs.970.90 (loss of 5)
```

### SELL Order Example

```
Current Price: Rs.980.90

SELL Order:
  Price: Rs.985.90 (5 rupees above current)
  Quantity: 1
  Type: LIMIT
  
If executed:
  Entry: Rs.985.90
  Target: Rs.975.90 (profit of 10)
  Stop Loss: Rs.990.90 (loss of 5)
```

---

## Order Status

### Pending Orders
- Orders placed at LIMIT prices
- May or may not be executed
- Depends on market movement

### Executed Orders
- When price reaches your limit price
- Order is filled at that price
- Position is opened

### Monitoring
- Check OpenAlgo dashboard at `http://127.0.0.1:5000`
- View all orders and trades
- See real-time P&L

---

## Stopping the Bot

Press **Ctrl+C** to stop:

```
[BOT] Shutting down...

================================================================================
[STATUS] 2026-09-15 11:35:45
[STATUS] Total Trades: 12 | BUY: 6 | SELL: 6
================================================================================

[BOT] Trading stopped
```

---

## Advanced Configuration

### Change All Parameters

```bash
export OPENALGO_API_KEY="your_64_char_key"
export SYMBOL="RELIANCE"
export EXCHANGE="NSE"

# Then modify in script:
# QUANTITY = 5
# STOPLOSS_AMOUNT = 3.0
# PROFIT_TARGET = 8.0
# INTERVAL_SECONDS = 60

python strategies/examples/continuous_trading_bot.py
```

### Different Symbols

```bash
# SBIN
export SYMBOL="SBIN"
python strategies/examples/continuous_trading_bot.py

# RELIANCE
export SYMBOL="RELIANCE"
python strategies/examples/continuous_trading_bot.py

# TCS
export SYMBOL="TCS"
python strategies/examples/continuous_trading_bot.py
```

---

## Monitoring

### View Orders in OpenAlgo Dashboard

1. Open `http://127.0.0.1:5000`
2. Go to **Trading** or **Orders**
3. See all placed orders
4. Monitor execution status
5. Check P&L

### Console Output

The bot displays:
- Current LTP
- Calculated order prices
- Order placement status
- Trade count
- Execution details

---

## Important Notes

⚠️ **Limit Orders**
- Orders are placed at specific LIMIT prices
- May not execute if price doesn't reach
- Check dashboard to see pending orders

⚠️ **Sandbox Mode**
- All orders are in "analyze" mode
- No real money is used
- Good for testing

⚠️ **Market Hours**
- Orders only execute during market hours
- Outside hours, orders remain pending
- Check NSE market timings

⚠️ **Broker Connectivity**
- Ensure broker is connected
- Check login status in OpenAlgo
- Verify market data is flowing

---

## Troubleshooting

### Orders Not Executing

**Possible Causes:**
1. Price doesn't reach limit price
2. Market is closed
3. Insufficient liquidity
4. Broker connection issue

**Solution:**
- Check OpenAlgo dashboard
- Verify market hours
- Check broker connection
- Adjust limit prices closer to current price

### "Could not get current price"

**Possible Causes:**
1. Market data not available
2. Broker not connected
3. Symbol not found

**Solution:**
- Verify broker is logged in
- Check symbol format
- Restart OpenAlgo

### Orders Rejected

**Possible Causes:**
1. Invalid symbol
2. Invalid quantity
3. Insufficient funds
4. Order validation failed

**Solution:**
- Check symbol format
- Verify quantity is valid
- Check account balance
- Review error message

---

## Reference

- **Order Constants:** `docs/prompt/order-constants.md`
- **Symbol Format:** `docs/prompt/symbol-format.md`
- **Python SDK:** `docs/prompt/openalgo python sdk.md`
- **API Documentation:** `docs/api/README.md`

---

## Example Scenarios

### Scenario 1: Scalping Strategy

```python
STOPLOSS_AMOUNT = 2.0   # 2 rupees loss
PROFIT_TARGET = 5.0    # 5 rupees profit
INTERVAL_SECONDS = 10  # Every 10 seconds
```

### Scenario 2: Swing Trading

```python
STOPLOSS_AMOUNT = 10.0  # 10 rupees loss
PROFIT_TARGET = 20.0   # 20 rupees profit
INTERVAL_SECONDS = 300 # Every 5 minutes
```

### Scenario 3: High Volume

```python
QUANTITY = 10          # 10 shares per order
STOPLOSS_AMOUNT = 5.0
PROFIT_TARGET = 10.0
INTERVAL_SECONDS = 30
```

---

**Status:** ✅ Ready to use
**Created:** 2026-09-15
**Last Updated:** 2026-09-15
