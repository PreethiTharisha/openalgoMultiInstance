# NIFTY Futures Expiry - September 2026

## Current Situation

**Current Date:** September 2026
**Expired Expiry:** NIFTY25JAN26FUT (January 2026 - already expired)

---

## Available NIFTY Expiries in September 2026

### Current Month Expiry
```
NIFTY25SEP26FUT  - September 25, 2026 (Current month)
```

### Next Month Expiry
```
NIFTY25OCT26FUT  - October 25, 2026 (Next month)
```

### Further Expiries
```
NIFTY25NOV26FUT  - November 25, 2026
NIFTY25DEC26FUT  - December 25, 2026
NIFTY25JAN27FUT  - January 25, 2027
```

---

## NIFTY Futures Expiry Schedule

### Format
```
NIFTY + EXPIRY_DATE + FUT
```

### Monthly Expiry Dates
- **25th of every month** is the standard expiry date for NIFTY Futures
- Last Thursday of the month (if 25th is not a trading day)

### 2026 Expiry Dates
| Month | Expiry Date | Symbol |
|-------|-------------|--------|
| January | 25 Jan | NIFTY25JAN26FUT ❌ (Expired) |
| February | 25 Feb | NIFTY25FEB26FUT ❌ (Expired) |
| March | 25 Mar | NIFTY25MAR26FUT ❌ (Expired) |
| April | 25 Apr | NIFTY25APR26FUT ❌ (Expired) |
| May | 25 May | NIFTY25MAY26FUT ❌ (Expired) |
| June | 25 Jun | NIFTY25JUN26FUT ❌ (Expired) |
| July | 25 Jul | NIFTY25JUL26FUT ❌ (Expired) |
| August | 25 Aug | NIFTY25AUG26FUT ❌ (Expired) |
| **September** | **25 Sep** | **NIFTY25SEP26FUT** ✅ (Current) |
| October | 25 Oct | NIFTY25OCT26FUT ✅ (Next) |
| November | 25 Nov | NIFTY25NOV26FUT ✅ |
| December | 25 Dec | NIFTY25DEC26FUT ✅ |

---

## What to Use Now

### For September 2026
```python
SYMBOL = 'NIFTY25SEP26FUT'  # Current month expiry
```

### For October 2026 (After Sept 25)
```python
SYMBOL = 'NIFTY25OCT26FUT'  # Next month expiry
```

---

## How to Find Current Expiry

### Method 1: Check OpenAlgo Dashboard
1. Open `http://127.0.0.1:5000`
2. Go to **Trading** or **Market Data**
3. Search for "NIFTY"
4. See available expiries listed
5. Use the current/next month expiry

### Method 2: Check NSE Website
1. Visit NSE website
2. Look for NIFTY Futures contract specifications
3. Find current expiry dates

### Method 3: Use Your Broker's Terminal
1. Open your broker's trading terminal
2. Search for NIFTY Futures
3. See available expiries

---

## Updated Script Configuration

### Current (September 2026)
```python
SYMBOL = 'NIFTY25SEP26FUT'  # Use this now
EXCHANGE = 'NFO'
PRODUCT = 'NRML'
QUANTITY = 1
```

### After September 25, 2026
```python
SYMBOL = 'NIFTY25OCT26FUT'  # Switch to this
EXCHANGE = 'NFO'
PRODUCT = 'NRML'
QUANTITY = 1
```

---

## How to Update Your Script

### Option 1: Hardcode the Symbol
Edit `continuous_trading_bot_nifty.py`:

```python
# Change this line:
SYMBOL = os.getenv('SYMBOL', 'NIFTY25JAN26FUT')

# To this:
SYMBOL = os.getenv('SYMBOL', 'NIFTY25SEP26FUT')
```

### Option 2: Use Environment Variable
Set before running:

**Windows PowerShell:**
```powershell
$env:SYMBOL = "NIFTY25SEP26FUT"
python strategies/examples/continuous_trading_bot_nifty.py
```

**Windows Command Prompt:**
```cmd
set SYMBOL=NIFTY25SEP26FUT
python strategies/examples/continuous_trading_bot_nifty.py
```

**Linux/Mac:**
```bash
export SYMBOL="NIFTY25SEP26FUT"
python strategies/examples/continuous_trading_bot_nifty.py
```

### Option 3: Add to .env File
Edit `D:\OpenAlgo\openalgo\.env`:

```env
# NIFTY Futures Configuration
NIFTY_SYMBOL=NIFTY25SEP26FUT
```

Then in script:
```python
SYMBOL = os.getenv('NIFTY_SYMBOL', 'NIFTY25SEP26FUT')
```

---

## Why Expiry Matters

### Expired Contracts
- ❌ Cannot place new orders
- ❌ Cannot trade
- ❌ Contract is settled
- ❌ No liquidity

### Active Contracts
- ✅ Can place orders
- ✅ Good liquidity
- ✅ Can trade freely
- ✅ Expiry is in future

---

## Liquidity Considerations

### Most Liquid
- **Current month expiry** (NIFTY25SEP26FUT)
- Highest trading volume
- Tightest bid-ask spread
- Best for scalping/trading

### Good Liquidity
- **Next month expiry** (NIFTY25OCT26FUT)
- Good volume
- Reasonable spreads
- Good for swing trading

### Lower Liquidity
- **Further expiries** (NIFTY25NOV26FUT, etc.)
- Lower volume
- Wider spreads
- Better for long-term positions

---

## Recommended Strategy

### For Day Trading/Scalping
```python
SYMBOL = 'NIFTY25SEP26FUT'  # Current month - highest liquidity
```

### For Swing Trading
```python
SYMBOL = 'NIFTY25OCT26FUT'  # Next month - good liquidity
```

### For Long-term Positions
```python
SYMBOL = 'NIFTY25NOV26FUT'  # Further expiry
```

---

## Quick Reference

**Today (September 2026):**
- Use: `NIFTY25SEP26FUT`
- Expiry: September 25, 2026
- Days left: ~10 days (depends on exact date)

**After September 25:**
- Use: `NIFTY25OCT26FUT`
- Expiry: October 25, 2026

---

## Error You'll Get with Expired Contract

If you try to use `NIFTY25JAN26FUT`:

```
[ERROR] BUY order failed: Symbol not found
[ERROR] SELL order failed: Symbol not found
```

**Solution:** Update to current expiry `NIFTY25SEP26FUT`

---

## Summary

| Item | Value |
|------|-------|
| **Current Date** | September 2026 |
| **Expired Expiry** | NIFTY25JAN26FUT ❌ |
| **Current Expiry** | NIFTY25SEP26FUT ✅ |
| **Next Expiry** | NIFTY25OCT26FUT ✅ |
| **Recommended** | NIFTY25SEP26FUT (highest liquidity) |

---

**Status:** ✅ Update your script to use NIFTY25SEP26FUT
**Created:** 2026-09-15
