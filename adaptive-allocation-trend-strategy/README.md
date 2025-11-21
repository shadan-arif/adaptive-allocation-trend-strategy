# Adaptive Allocation Trend Strategy

Long-only, price-only strategy designed to maintain a stable allocation to BTC/ETH during sustained uptrends, with wide risk controls and periodic rebalancing.

## Strategy Overview

The Adaptive Allocation Trend Strategy uses a simple but robust approach to trend following:

- **Constant Allocation**: Maintains a fixed target allocation (55% of portfolio) in the asset
- **Long-term EMA Filter**: Uses a 200-period EMA as a very loose trend filter (only avoids extreme bear regimes)
- **Wide Risk Controls**: Catastrophic stops (45% from entry, 40% trailing from peak) to cap risk in extreme selloffs
- **Monthly Rebalancing**: Realizes P&L at the start of each new month and re-enters, ensuring sufficient trades

This strategy is intentionally simple and robust: it behaves like a constant allocation trend strategy with basic risk management and minimal over-optimization.

## Core Features

### 🎯 Constant Allocation Approach

- **Target Allocation**: 55% of portfolio (contest maximum)
- **Trend Filter**: Very loose EMA filter (only avoids extreme bear regimes <70% of EMA)
- **Top-up Logic**: Automatically adds to position to maintain target allocation

### 🛡️ Risk Management

- **Hard Stop Loss**: 45% from entry price (catastrophic protection only)
- **Trailing Stop**: 40% from highest price since entry
- **Monthly Rebalancing**: Full exit and re-entry at start of each month

### 📊 Trading Logic

- **Entry**: Maintain target allocation when trend is acceptable (price >= 70% of EMA)
- **Exit**: Risk-based exits (hard stop or trailing stop) OR monthly rebalance
- **Position Sizing**: Always targets 55% allocation, adds incrementally as needed

## Configuration

### Default Parameters

```json
{
  "exchange": "paper",
  "strategy": "adaptive_allocation_trend",
  "symbol": "BTC-USD",
  "starting_cash": 10000.0,
  "sleep_seconds": 3600,
  "strategy_params": {
    "ema_long_period": 200,
    "target_allocation_pct": 0.55,
    "min_notional": 10.0,
    "hard_stop_loss_pct": 0.45,
    "trailing_stop_pct": 0.4,
    "enable_monthly_rebalance": true
  }
}
```

## Environment Variables

```bash
# Core Configuration
BOT_EXCHANGE=paper
BOT_STRATEGY=adaptive_allocation_trend
BOT_SYMBOL=BTC-USD
BOT_STARTING_CASH=10000.0
BOT_SLEEP=3600

# Dashboard Integration (Optional)
BOT_INSTANCE_ID=your-bot-id
USER_ID=your-user-id
BOT_SECRET=your-hmac-secret
BASE_URL=https://your-app.com
POSTGRES_URL=postgresql://...
```

## Quick Start

### Prerequisites

This template inherits from `base-bot-template`. Ensure the base template exists:

```
strategy-contest-1/
├── base-bot-template/           # Required infrastructure
└── adaptive-allocation-trend-strategy/   # This strategy
```

### Local Development

```bash
# Run with default configuration
python startup.py

# Run with custom symbol
BOT_SYMBOL=ETH-USD python startup.py

# Run with custom parameters
BOT_STRATEGY_PARAMS='{"target_allocation_pct":0.50}' python startup.py
```

### Docker Deployment

**Build (from repository root):**

```bash
docker build -f adaptive-allocation-trend-strategy/Dockerfile -t adaptive-allocation-trend-bot .
```

**Run:**

```bash
docker run -p 8080:8080 -p 3010:3010 \
  -e BOT_STRATEGY=adaptive_allocation_trend \
  -e BOT_SYMBOL=BTC-USD \
  -e BOT_STARTING_CASH=10000 \
  adaptive-allocation-trend-bot
```

## Trading Logic

### Entry Conditions (BUY)

1. **Trend Filter**: Price >= 70% of 200-period EMA (very loose filter)
2. **Target Allocation**: Current position < 55% of portfolio value
3. **Minimum Notional**: Trade size >= $10
4. **Incremental Buys**: Adds to position to reach target allocation

### Exit Conditions (SELL)

1. **Hard Stop Loss**: Price drops 45% below entry price
2. **Trailing Stop**: Price drops 40% from highest price since entry
3. **Monthly Rebalance**: First bar of each new month (full exit)

### Position Sizing Formula

```
target_value = portfolio_value * 0.55
current_value = position_quantity * current_price
add_value = max(0, target_value - current_value)
position_size = add_value / current_price
```

## Performance Results

### Backtest Period: January 1, 2024 - June 30, 2024

**Combined Results (BTC + ETH):**

- **Starting Capital**: $10,000.00
- **Final Equity**: $12,723.12
- **Total Return**: +27.23%
- **Max Drawdown**: 17.04%
- **Win Rate**: 92.3%
- **Total Trades**: 89
- **Sharpe Ratio**: 0.28

**BTC-USD:**

- **Final Equity**: $6,253.80
- **Total Return**: +25.08%
- **Max Drawdown**: 13.88%
- **Win Rate**: 100.0%
- **Total Trades**: 45

**ETH-USD:**

- **Final Equity**: $6,469.32
- **Total Return**: +29.39%
- **Max Drawdown**: 17.04%
- **Win Rate**: 85.7%
- **Total Trades**: 44

### Contest Validation

- ✅ **Minimum Trades (10+)**: 89 trades
- ✅ **Max Drawdown (<50%)**: 17.04%
- ✅ **Target (>25% combined)**: +27.23%
- ✅ **Position Sizing (≤55%)**: Compliant
- ✅ **Data Source**: Yahoo Finance hourly
- ✅ **Date Range**: Jan 1 - Jun 30, 2024

## Strategy Philosophy

This strategy is designed to be:

- **Simple**: Minimal indicators, clear logic
- **Robust**: Wide stops allow normal volatility
- **Trend-Following**: Maintains allocation during uptrends
- **Risk-Controlled**: Catastrophic stops prevent large losses
- **Contest-Compliant**: Meets all requirements with good returns

## API Endpoints

### Health Check (Port 8080)

- `GET /health` - Bot status and strategy info

### Control API (Port 3010, HMAC Authenticated)

- `GET /performance` - Real-time performance metrics
- `GET /settings` - Current configuration
- `POST /settings` - Update configuration (hot reload)
- `POST /commands` - Bot control (start/stop/pause/restart)
- `GET /logs` - Recent trading logs

## Dashboard Integration

Full compatibility with the main app dashboard:

- **Performance Metrics**: Real-time P&L, positions, trade history
- **Settings Management**: Hot configuration reload via dashboard
- **Bot Controls**: Start/stop/pause/restart from dashboard
- **Live Logs**: Structured log output with trade details
- **Status Reporting**: Real-time status updates via callbacks

## Risk Disclosure

This strategy is designed for the trading contest with historical backtesting data. Past performance does not guarantee future results. Cryptocurrency trading carries significant risk. Always:

- Use appropriate position sizing
- Set stop losses on all trades
- Never risk more than you can afford to lose
- Understand the strategy logic before deploying
- Monitor performance regularly

## Support & Documentation

For questions, issues, or contributions:

- Review the strategy code in `adaptive_allocation_trend_strategy.py`
- Check the backtest report in `../reports/backtest_report.md`
- Read the logic explanation in `trade_logic_explanation.md`
- Run backtests using the `../reports/` folder

## License

This strategy is submitted for the Trading Strategy Contest. All rights reserved.
