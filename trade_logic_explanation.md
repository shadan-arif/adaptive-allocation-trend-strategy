# Adaptive Allocation Trend Strategy - Trade Logic Explanation

## Overview

The Adaptive Allocation Trend Strategy is a long-only, price-only strategy designed to maintain a stable allocation to BTC/ETH during sustained uptrends. It uses wide risk controls and periodic rebalancing to achieve robust returns while managing risk.

## Core Philosophy

This strategy is intentionally simple and robust:

- **Constant Allocation**: Maintains a fixed 55% target allocation in the asset
- **Loose Trend Filter**: Uses a 200-period EMA only to avoid extreme bear regimes
- **Wide Risk Controls**: Catastrophic stops (45% from entry, 40% trailing) allow normal volatility
- **Monthly Rebalancing**: Realizes P&L at the start of each month and re-enters

## Strategy Components

### 1. Target Allocation System

**Goal**: Maintain 55% of portfolio value in the asset at all times.

**How it works**:

- Calculates target value: `target_value = portfolio_value * 0.55`
- Calculates current value: `current_value = position_quantity * current_price`
- Calculates needed addition: `add_value = max(0, target_value - current_value)`
- Converts to position size: `position_size = add_value / current_price`

**Why 55%?**

- Contest maximum allowed position size
- Maintains significant exposure during uptrends
- Leaves 45% cash buffer for risk management

### 2. Trend Filter (200-Period EMA)

**Purpose**: Very loose filter to avoid entering in extreme bear markets.

**Logic**:

- Calculates 200-period EMA from price history
- Only avoids entry if: `current_price < 0.7 * ema_long`
- This means we only avoid entry if price is more than 30% below the long-term average

**Why so loose?**

- Strategy is designed for trend-following, not mean reversion
- Tight filters would cause frequent exits during normal volatility
- Wide filter allows strategy to stay in position during uptrends

### 3. Risk Management

#### Hard Stop Loss (45% from entry)

**Purpose**: Catastrophic protection - only triggers in extreme selloffs.

**Logic**:

- Tracks entry price for each position
- Calculates gain from entry: `gain = (current_price - entry_price) / entry_price`
- Exits if: `gain <= -0.45` (45% loss)

**Why 45%?**

- Very wide stop allows normal volatility (crypto can move 20-30% in normal conditions)
- Only triggers in true catastrophic events
- Prevents large losses while allowing normal market movements

#### Trailing Stop (40% from peak)

**Purpose**: Protects gains by exiting if price drops significantly from peak.

**Logic**:

- Tracks highest price since entry: `highest_price_since_entry`
- Calculates drop from peak: `drop = (highest_price - current_price) / highest_price`
- Exits if: `drop >= 0.40` (40% drop from peak)

**Why 40%?**

- Allows normal pullbacks during uptrends
- Protects against major reversals
- Works in conjunction with hard stop for comprehensive protection

### 4. Monthly Rebalancing

**Purpose**: Regular profit realization and position reset.

**Logic**:

- Detects first bar of each new month (day==1, hour==0)
- Performs full exit (sells entire position)
- Re-enters on next bar if trend conditions are met
- Ensures at least one trade per month

**Why monthly?**

- Regular profit realization
- Resets cost basis for risk calculations
- Ensures sufficient trade count for contest requirements
- Captures monthly trend momentum

## Trade Flow

### Entry Flow (BUY Signal)

1. **Check Trend Filter**

   - Calculate 200-period EMA
   - If EMA exists and `price < 0.7 * EMA`: Skip entry (extreme bear regime)
   - Otherwise: Proceed to allocation check

2. **Calculate Target Allocation**

   - Portfolio value = cash + (position_quantity \* current_price)
   - Target value = portfolio_value \* 0.55
   - Current value = position_quantity \* current_price
   - Add value = max(0, target_value - current_value)

3. **Check Minimum Trade Size**

   - If add_value >= $10: Generate BUY signal
   - Position size = add_value / current_price

4. **Execute Trade**
   - Buy position_size units at current_price
   - Update position tracking (entry price, size, timestamp)
   - Reset trailing peak to current_price

### Exit Flow (SELL Signal)

1. **Check Risk Exits** (if in position)

   - **Hard Stop**: If `(current_price - entry_price) / entry_price <= -0.45`: EXIT
   - **Trailing Stop**: If `(highest_price - current_price) / highest_price >= 0.40`: EXIT
   - If either triggered: Generate SELL signal for full position

2. **Check Monthly Rebalance** (if in position)

   - If first bar of new month (day==1, hour==0): EXIT
   - Generate SELL signal for full position
   - Mark rebalanced_this_month = True

3. **Execute Trade**
   - Sell entire position at current_price
   - Clear position tracking
   - Reset trailing peak

### Hold Flow

- If no entry conditions met and no exit conditions triggered: HOLD
- Continue tracking trailing peak if in position
- Wait for next bar

## Position Tracking

### Position State

The strategy maintains a single position per symbol with:

- **Entry Price**: Average entry price (weighted by size for multiple buys)
- **Size**: Total quantity held
- **Timestamp**: Last update time
- **Value**: Current position value

### Trailing Peak Tracking

- **highest_price_since_entry**: Highest price seen since position entry
- Updated on each bar if in position
- Used for trailing stop calculation
- Reset when position is closed

### Monthly State

- **current_month**: Current calendar month
- **rebalanced_this_month**: Flag to prevent multiple rebalances in same month
- Reset at start of each new month

## Example Trade Sequence

### Scenario: Strong Uptrend

1. **Day 1, Hour 0**: Strategy starts with $5,000 cash

   - Price = $40,000, EMA = $38,000
   - Trend OK (price > 0.7 \* EMA)
   - Target allocation: $5,000 \* 0.55 = $2,750
   - BUY: 0.06875 BTC @ $40,000

2. **Day 1-14**: Price rises to $45,000

   - Strategy adds incrementally to maintain 55% allocation
   - Multiple small BUY orders as portfolio value increases

3. **Day 15**: Price reaches $50,000 (peak)

   - highest_price_since_entry = $50,000
   - Position value increases, strategy maintains allocation

4. **Day 20**: Price drops to $30,000

   - Drop from peak: (50,000 - 30,000) / 50,000 = 40%
   - Trailing stop triggered: SELL entire position

5. **Day 21**: Price recovers to $42,000

   - Trend OK, target allocation: $5,000 \* 0.55 = $2,750
   - BUY: 0.06548 BTC @ $42,000

6. **Month 2, Day 1, Hour 0**: Monthly rebalance

   - SELL: Full position @ $45,000
   - Realize profit, reset position

7. **Month 2, Day 1, Hour 1**: Re-enter
   - Trend OK, BUY: New position @ $45,000

## Key Design Decisions

### Why Wide Stops?

- Crypto markets are highly volatile
- Normal movements can be 20-30%
- Tight stops would cause frequent exits
- Wide stops allow trend-following while preventing catastrophic losses

### Why Monthly Rebalancing?

- Regular profit realization
- Resets risk calculations
- Ensures sufficient trade activity
- Captures monthly momentum

### Why Constant Allocation?

- Simple and robust
- Maintains exposure during uptrends
- No complex position sizing logic
- Contest-compliant (55% maximum)

### Why Loose Trend Filter?

- Strategy is trend-following, not mean reversion
- Tight filters would cause frequent exits
- Only avoids extreme bear regimes
- Allows strategy to stay in position during uptrends

## Risk Considerations

### Drawdown Scenarios

1. **Normal Volatility**: Wide stops (45%/40%) allow normal 20-30% movements
2. **Catastrophic Events**: Hard stop (45%) prevents large losses
3. **Trend Reversals**: Trailing stop (40%) protects gains

### Position Sizing

- Always targets 55% allocation
- Incremental additions maintain target
- Never exceeds contest limit
- Cash buffer (45%) provides flexibility

### Market Conditions

- **Bull Markets**: Strategy performs well (maintains allocation, captures trends)
- **Bear Markets**: Wide stops prevent large losses, loose filter avoids entry
- **Sideways Markets**: Monthly rebalancing may cause churn, but limits losses

## Performance Characteristics

### Expected Behavior

- **High Win Rate**: Wide stops and trend-following approach
- **Moderate Returns**: Constant allocation limits upside but provides stability
- **Low Drawdown**: Wide stops and monthly rebalancing manage risk
- **Regular Trades**: Monthly rebalancing ensures activity

### Market Fit

- **Best For**: Sustained uptrends, bull markets
- **Challenging For**: High volatility sideways markets, frequent reversals
- **Risk Profile**: Moderate risk, controlled drawdowns

## Conclusion

The Adaptive Allocation Trend Strategy uses a simple but effective approach:

1. Maintain constant 55% allocation during uptrends
2. Use wide stops to allow normal volatility
3. Rebalance monthly to realize profits
4. Avoid extreme bear regimes with loose filter

This design balances return potential with risk management, making it suitable for contest requirements while maintaining robustness.
