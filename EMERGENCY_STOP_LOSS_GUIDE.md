# Emergency Stop Loss - Complete Guide

## Overview

Both smart bots now include **Emergency Stop Loss** feature:
- ✅ Monitors all open positions continuously
- ✅ Calculates loss percentage for each position
- ✅ **Automatically squares off ALL positions if any position hits 10% loss**
- ✅ Uses MARKET orders for immediate execution
- ✅ Prevents further losses
- ✅ Stops placing new orders

---

## How It Works

### Loss Calculation

For **BUY positions:**
```
Loss % = ((Entry Price - Current Price) / Entry Price) × 100
```

Example:
```
Entry Price: Rs. 100
Current Price: Rs. 90
Loss % = ((100 - 90) / 100) × 100 = 10%
```

For **SELL positions:**
```
Loss % = ((Current Price - Entry Price) / Entry Price) × 100
```

Example:
```
Entry Price: Rs. 100
Current Price: Rs. 110
Loss % = ((110 - 100) / 100) × 100 = 10%
```

---

## Emergency Stop Loss Trigger

### Condition
```
IF any_position.loss_percent > 10% THEN
    square_off_all_positions()
    stop_placing_new_orders()
END IF
```

### What Happens

**When 10% Loss is Detected:**

1. **Immediate Alert:**
   ```
   [EMERGENCY] Position 26091589228293 loss: 10.5% (exceeds 10%)
   ```

2. **Square Off All Positions:**
   ```
   [EMERGENCY STOP] Squaring off all positions immediately!
   
   [SQUARE OFF] Closing position 26091589228293...
   [OK] Square off order placed!
        Order ID: 26091589228294
        Action: SELL
        Entry Price: Rs.100.00
        Current Price: Rs.89.50
        Loss: 10.50%
   ```

3. **Stop New Orders:**
   ```
   [STATUS] EMERGENCY STOP TRIGGERED - No new orders!
   ```

4. **Continue Monitoring:**
   - Monitors existing orders
   - Waits for square-off execution
   - No new orders placed

---

## Configuration

### Default Settings

```python
# Risk Management - Emergency Stop Loss
MAX_LOSS_PERCENT = 10.0  # Stop all trading if loss exceeds 10%
EMERGENCY_STOP_LOSS = True  # Enable emergency stop loss
```

### Customize Loss Threshold

**Change to 5% loss:**
```python
MAX_LOSS_PERCENT = 5.0
```

**Change to 15% loss:**
```python
MAX_LOSS_PERCENT = 15.0
```

**Disable emergency stop loss:**
```python
EMERGENCY_STOP_LOSS = False
```

---

## Example Scenarios

### Scenario 1: BUY Order Hits 10% Loss

```
[PRICE] Current LTP: Rs.979.70

[ORDER] Placing BUY order at Rs.974.70...
[OK] BUY order placed!
     Order ID: 26091589228293
     Price: Rs.974.70
     Target: Rs.984.70
     Stop Loss: Rs.969.70
     Emergency Stop Loss: 10%

[FILLED] BUY Order FILLED at Rs.974.70

[PRICE] Current LTP: Rs.977.00
[STATUS] Position Details:
         BUY @ Rs.974.70 | Loss: 0.24%

[PRICE] Current LTP: Rs.975.00
[STATUS] Position Details:
         BUY @ Rs.974.70 | Loss: 0.03%

[PRICE] Current LTP: Rs.972.00
[STATUS] Position Details:
         BUY @ Rs.974.70 | Loss: 0.28%

[PRICE] Current LTP: Rs.970.00
[STATUS] Position Details:
         BUY @ Rs.974.70 | Loss: 0.48%

[PRICE] Current LTP: Rs.960.00
[STATUS] Position Details:
         BUY @ Rs.974.70 | Loss: 1.51%

[PRICE] Current LTP: Rs.930.00
[STATUS] Position Details:
         BUY @ Rs.974.70 | Loss: 4.58%

[PRICE] Current LTP: Rs.875.00
[STATUS] Position Details:
         BUY @ Rs.974.70 | Loss: 10.20%

[EMERGENCY] Position 26091589228293 loss: 10.20% (exceeds 10%)

================================================================================
[EMERGENCY STOP] Squaring off all positions immediately!
================================================================================

[SQUARE OFF] Closing position 26091589228293...
[OK] Square off order placed!
     Order ID: 26091589228294
     Action: SELL
     Entry Price: Rs.974.70
     Current Price: Rs.875.00
     Loss: 10.20%

[STATUS] EMERGENCY STOP TRIGGERED - No new orders!

[PRICE] Current LTP: Rs.875.10
[PRICE] Current LTP: Rs.875.20

[FILLED] SELL Order FILLED at Rs.875.00

[STATUS] Open Positions: 0
[STATUS] EMERGENCY STOP TRIGGERED - No new orders!
```

### Scenario 2: Multiple Positions, One Hits 10% Loss

```
[ORDER] Placing BUY order at Rs.974.70...
[OK] BUY order placed!
     Order ID: 26091589228293

[ORDER] Placing SELL order at Rs.984.70...
[OK] SELL order placed!
     Order ID: 26091514280815

[FILLED] BUY Order FILLED at Rs.974.70
[FILLED] SELL Order FILLED at Rs.984.70

[STATUS] Open Positions: 2
[STATUS] Position Details:
         BUY @ Rs.974.70 | Loss: 0.50%
         SELL @ Rs.984.70 | Loss: 0.30%

[PRICE] Current LTP: Rs.960.00

[STATUS] Position Details:
         BUY @ Rs.974.70 | Loss: 1.51%
         SELL @ Rs.984.70 | Loss: 2.43%

[PRICE] Current LTP: Rs.875.00

[STATUS] Position Details:
         BUY @ Rs.974.70 | Loss: 10.20%
         SELL @ Rs.984.70 | Loss: 11.30%

[EMERGENCY] Position 26091589228293 loss: 10.20% (exceeds 10%)

================================================================================
[EMERGENCY STOP] Squaring off all positions immediately!
================================================================================

[SQUARE OFF] Closing position 26091589228293...
[OK] Square off order placed!
     Order ID: 26091589228294
     Action: SELL
     Entry Price: Rs.974.70
     Current Price: Rs.875.00
     Loss: 10.20%

[SQUARE OFF] Closing position 26091514280815...
[OK] Square off order placed!
     Order ID: 26091589228295
     Action: BUY
     Entry Price: Rs.984.70
     Current Price: Rs.875.00
     Loss: 11.30%

[STATUS] EMERGENCY STOP TRIGGERED - No new orders!
```

---

## Position Tracking

### Open Positions Dictionary

```python
self.open_positions = {
    '26091589228293': {
        'action': 'BUY',
        'entry_price': 974.70,
        'quantity': 1,
        'time': datetime.now()
    },
    '26091514280815': {
        'action': 'SELL',
        'entry_price': 984.70,
        'quantity': 1,
        'time': datetime.now()
    }
}
```

### Status Display

```
[STATUS] Open Positions: 2
[STATUS] Position Details:
         BUY @ Rs.974.70 | Loss: 0.50%
         SELL @ Rs.984.70 | Loss: 0.30%
```

---

## Key Functions

### 1. Calculate Position Loss
```python
def calculate_position_loss(self, entry_price, current_price, action):
    """Calculate loss percentage for a position"""
    if action == "BUY":
        loss_percent = ((entry_price - current_price) / entry_price) * 100
    else:  # SELL
        loss_percent = ((current_price - entry_price) / entry_price) * 100
    return loss_percent
```

### 2. Check Emergency Stop Loss
```python
def check_emergency_stop_loss(self):
    """Check if any position has exceeded max loss percentage"""
    for pos_id, pos_data in self.open_positions.items():
        loss_percent = self.calculate_position_loss(...)
        if loss_percent > MAX_LOSS_PERCENT:
            return True
    return False
```

### 3. Square Off All Positions
```python
def square_off_all_positions(self):
    """Square off all open positions immediately"""
    for pos_id, pos_data in self.open_positions.items():
        action = "SELL" if pos_data['action'] == "BUY" else "BUY"
        # Place MARKET order for immediate execution
        self.client.placeorder(..., price_type="MARKET", ...)
```

---

## Benefits

✅ **Automatic Risk Management**
- No manual intervention needed
- Immediate response to losses
- Prevents catastrophic losses

✅ **Protects Capital**
- Limits maximum loss to 10%
- Squares off all positions
- Stops further damage

✅ **Professional Trading**
- Risk-aware strategy
- Proper position management
- Disciplined execution

✅ **Peace of Mind**
- Automatic protection
- No need to monitor constantly
- Handles worst-case scenarios

---

## Important Notes

⚠️ **Market Orders**
- Uses MARKET orders for immediate execution
- Ensures positions are closed quickly
- May execute at slightly worse prices

⚠️ **Loss Calculation**
- Based on entry price vs current price
- Percentage loss, not absolute loss
- Calculated in real-time

⚠️ **Emergency Trigger**
- Triggers when ANY position hits 10% loss
- Squares off ALL positions immediately
- Stops placing new orders

⚠️ **No New Orders**
- After emergency stop, no new orders
- Only monitors existing positions
- Must restart bot for new trading

---

## Customization Examples

### Conservative (5% Loss)
```python
MAX_LOSS_PERCENT = 5.0
```
- Tighter risk control
- Exits earlier
- Preserves more capital

### Moderate (10% Loss) - Default
```python
MAX_LOSS_PERCENT = 10.0
```
- Balanced risk/reward
- Allows some fluctuation
- Standard practice

### Aggressive (15% Loss)
```python
MAX_LOSS_PERCENT = 15.0
```
- More tolerance for losses
- Allows larger swings
- Higher risk

### Disabled
```python
EMERGENCY_STOP_LOSS = False
```
- No automatic stop loss
- Manual management only
- Not recommended

---

## Summary

| Feature | Details |
|---------|---------|
| **Trigger** | Any position hits 10% loss |
| **Action** | Square off ALL positions |
| **Order Type** | MARKET (immediate) |
| **New Orders** | Stopped immediately |
| **Monitoring** | Continues until close |
| **Customizable** | Yes (MAX_LOSS_PERCENT) |
| **Default** | Enabled (10%) |

---

**Status:** ✅ **Ready to use!**

Both smart bots now have automatic emergency stop loss protection. They will immediately square off all positions if any position hits 10% loss, protecting your capital! 🛡️

