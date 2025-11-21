# Backtest Reports

## Quick Start

**Build:**
```bash
docker build -f reports/Dockerfile -t adaptive-allocation-backtest .
```

**Run:**
```bash
docker run --rm -v "$(pwd)/reports:/app/reports" adaptive-allocation-backtest
```

Results will be saved to `reports/backtest_results.json`
