# Backtest Reports

## Quick Start

**Build:**
```bash
docker build -f reports/Dockerfile -t adaptive-allocation-backtest .
```

**Run:**
```bash
docker run --rm -v "$(pwd)/reports/results:/app/reports/results" adaptive-allocation-backtest
```

Results will be saved to `reports/results/backtest_results.json`
