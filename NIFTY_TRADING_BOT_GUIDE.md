# NIFTY Continuous Trading Bot - Guide

## Overview

The **NIFTY Continuous Trading Bot** automatically places BUY and SELL orders on **NIFTY Futures** continuously with:
- **BUY Order:** Current Price - 5 rupees (with 10 rupees profit target)
- **SELL Order:** Current Price + 5 rupees (with 10 rupees profit target)
- **Interval:** Every 30 seconds (configurable)

---

## Key Differences from Equity Trading

### Symbol Format
```
Equity (NSE):     SBIN, RELIANCE, TCS
NIFTY Futures:    NIFTY25JAN26FUT
```

### Exchange
```
Equity:           NSE
NIFTY Futures:    NFO (Futures & Options)
```

### Product Type
```
Equity:           MIS (Intraday) or CNC (Delivery)
NIFTY Futures:    NRML (Normal)
```

### Lot Size
```
NIFTY Futures:    1 lot = 50 units
If QUANTITY=1:    You're trading 50 NIFTY contracts
```

---

## NIFTY Futures Symbol Format

### Format
```
NIFTY + EXPIRY_DATE + FUT
```

### Examples

| Symbol | Expiry | Details |
|--------|--------|---------|
| NIFTY25JAN26FUT | 25 Jan 2026 | January 2026 expiry |
| NIFTY29JAN26FUT | 29 Jan 2026 | January 2026 expiry (29th) |
| NIFTY05FEB26FUT | 5 Feb 2026 | February 2026 expiry |
| NIFTY19FEB26FUT | 19 Feb 2026 | February 2026 expiry |

### How to Find Current Expiry

1. Open OpenAlgo: `http://127.0.0.1:5000`
2. Go to **Trading** or **Market Data**
3. Search for NIFTY
4. See available expiries
5. Use the current month expiry

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
python strategies/examples/continuous_trading_bot_nifty.py
```

### Step 3: Expected Output

```
================================================================================
=== Continuous Trading Bot - NIFTY Futures ===
=== Started at 2026-09-15 11:30:00 IST ===
================================================================================

[BOT] Continuous Trading Bot - NIFTY Futures Started
[BOT] Host: http://127.0.0.1:5000
[BOT] Symbol: NIFTY25JAN26FUT on NFO
[BOT] Quantity: 1
[BOT] Product: NRML
[BOT] Stop Loss: Rs.5.0
[BOT] Profit Target: Rs.10.0
[BOT] Order Interval: 30 seconds

[BOT] Starting trading loop...
[BOT] Orders will be placed every 30 seconds
[BOT] Press Ctrl+C to stop

[PRICE] Current LTP: Rs.25950.50
[CALC] Buy Price: Rs.25945.50 (Current - 5)
[CALC] Sell Price: Rs.25955.50 (Current + 5)

[ORDER] Placing BUY order at Rs.25945.50...
[OK] BUY order placed!
     Order ID: 26091596939790
     Price: Rs.25945.50
     Target: Rs.25955.50
     Stop Loss: Rs.25940.50

[ORDER] Placing SELL order at Rs.25955.50...
[OK] SELL order placed!
     Order ID: 26091528333781
     Price: Rs.25955.50
     Target: Rs.25945.50
     Stop Loss: Rs.25960.50

================================================================================
[STATUS] 2026-09-15 11:30:15
[STATUS] Total Trades: 2 | BUY: 1 | SELL: 1
================================================================================

[BOT] Waiting 30 seconds before next orders...
```

---

## Configuration

### Change NIFTY Expiry

Edit the script and change:
```python
SYMBOL = 'NIFTY25JAN26FUT'  # Change expiry date
```

Or use environment variable:
```bash
export SYMBOL="NIFTY29JAN26FUT"
python strategies/examples/continuous_trading_bot_nifty.py
```

### Change Quantity

```python
QUANTITY = 1  # 1 lot = 50 NIFTY contracts
QUANTITY = 2  # 2 lots = 100 NIFTY contracts
QUANTITY = 5  # 5 lots = 250 NIFTY contracts
```

### Change Stop Loss / Profit

```python
STOPLOSS_AMOUNT = 5.0   # 5 rupees loss
PROFIT_TARGET = 10.0   # 10 rupees profit

# Or for larger moves:
STOPLOSS_AMOUNT = 20.0  # 20 rupees loss
PROFIT_TARGET = 50.0   # 50 rupees profit
```

### Change Order Interval

```python
INTERVAL_SECONDS = 30   # Every 30 seconds
INTERVAL_SECONDS = 60   # Every 60 seconds
INTERVAL_SECONDS = 10   # Every 10 seconds (faster)
```

---

## Understanding NIFTY Futures

### What is NIFTY?
- **NIFTY 50** is India's primary stock market index
- Comprises 50 large-cap stocks
- Traded on NSE (National Stock Exchange)

### NIFTY Futures
- Derivative contracts based on NIFTY index
- Traded on **NFO (Futures & Options)** segment
- Leverage trading (margin required)
- Expiry dates (monthly, weekly)

### Lot Size
- 1 NIFTY Futures lot = 50 NIFTY units
- If NIFTY = 25,950, 1 lot value = 25,950 × 50 = 12,97,500 rupees
- Margin required (typically 10-15% of contract value)

---

## Order Examples

### BUY Order Example

```
Current NIFTY: 25,950.50

BUY Order:
  Symbol: NIFTY25JAN26FUT
  Exchange: NFO
  Price: 25,945.50 (5 points below)
  Quantity: 1 (1 lot = 50 units)
  Type: LIMIT
  Product: NRML
  
If executed:
  Entry: 25,945.50
  Target: 25,955.50 (profit of 10 points)
  Stop Loss: 25,940.50 (loss of 5 points)
  
Profit/Loss per point: 50 rupees
If target hit: 10 × 50 = 500 rupees profit
If SL hit: 5 × 50 = 250 rupees loss
```

### SELL Order Example

```
Current NIFTY: 25,950.50

SELL Order:
  Symbol: NIFTY25JAN26FUT
  Exchange: NFO
  Price: 25,955.50 (5 points above)
  Quantity: 1 (1 lot = 50 units)
  Type: LIMIT
  Product: NRML
  
If executed:
  Entry: 25,955.50
  Target: 25,945.50 (profit of 10 points)
  Stop Loss: 25,960.50 (loss of 5 points)
  
Profit/Loss per point: 50 rupees
If target hit: 10 × 50 = 500 rupees profit
If SL hit: 5 × 50 = 250 rupees loss
```

---

## Monitoring

### View Orders in OpenAlgo Dashboard

1. Open `http://127.0.0.1:5000`
2. Go to **Trading** or **Orders**
3. Filter by symbol: `NIFTY25JAN26FUT`
4. See all placed orders
5. Monitor execution status
6. Check P&L

### Console Output

The bot displays:
- Current NIFTY LTP
- Calculated order prices
- Order placement status
- Trade count
- Execution details

---

## Important Notes

⚠️ **Market Hours**
- NIFTY Futures trading: 9:15 AM - 3:30 PM IST
- Orders only execute during these hours
- Check NSE market calendar for holidays

⚠️ **Limit Orders**
- Orders are placed at specific LIMIT prices
- May not execute if price doesn't reach
- Check dashboard to see pending orders

⚠️ **Leverage Risk**
- Futures trading involves leverage
- Losses can exceed initial margin
- Use stop losses (already configured)

⚠️ **Lot Size**
- 1 lot = 50 NIFTY units
- Minimum order = 1 lot
- Cannot trade fractional lots

⚠️ **Sandbox Mode**
- All orders are in "analyze" mode
- No real money is used
- Good for testing strategy

---

## Troubleshooting

### "Symbol not found" Error

**Cause:** Invalid NIFTY symbol or expiry

**Solution:**
1. Check OpenAlgo dashboard for available NIFTY symbols
2. Use correct format: `NIFTY25JAN26FUT`
3. Verify expiry date is valid
4. Check broker supports NIFTY futures

### Orders Not Executing

**Cause:** Price doesn't reach limit price

**Solution:**
- Adjust limit prices closer to current price
- Use smaller offset (e.g., 2 rupees instead of 5)
- Check market liquidity
- Verify market is open

### "Insufficient Margin" Error

**Cause:** Not enough margin for the trade

**Solution:**
- Reduce quantity (e.g., 1 lot instead of 2)
- Check account balance
- Ensure broker has sufficient margin
- Verify sandbox mode is active

### Cannot Get Quote

**Cause:** Market data not available

**Solution:**
- Verify broker is connected
- Check symbol format
- Ensure market is open
- Restart OpenAlgo

---

## Advanced Scenarios

### Scenario 1: High-Frequency Scalping

```python
STOPLOSS_AMOUNT = 2.0   # 2 points loss
PROFIT_TARGET = 5.0    # 5 points profit
INTERVAL_SECONDS = 10  # Every 10 seconds
QUANTITY = 1           # 1 lot
```

### Scenario 2: Swing Trading

```python
STOPLOSS_AMOUNT = 50.0  # 50 points loss
PROFIT_TARGET = 100.0  # 100 points profit
INTERVAL_SECONDS = 300 # Every 5 minutes
QUANTITY = 1           # 1 lot
```

### Scenario 3: Multi-Lot Trading

```python
STOPLOSS_AMOUNT = 5.0   # 5 points loss
PROFIT_TARGET = 10.0   # 10 points profit
INTERVAL_SECONDS = 30  # Every 30 seconds
QUANTITY = 5           # 5 lots = 250 units
```

---

## Reference

- **Order Constants:** `docs/prompt/order-constants.md`
- **Symbol Format:** `docs/prompt/symbol-format.md`
- **Python SDK:** `docs/prompt/openalgo python sdk.md`
- **API Documentation:** `docs/api/README.md`

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

**Status:** ✅ Ready to use
**Created:** 2026-09-15
**Last Updated:** 2026-09-15
