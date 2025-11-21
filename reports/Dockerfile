# Backtest Dockerfile for Adaptive Allocation Trend Strategy
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (handy for debugging / SSL / networking)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# yfinance will pull in numpy & pandas; we pin pandas explicitly.
RUN pip install --no-cache-dir \
    yfinance \
    pandas \
    requests>=2.31

# Copy base bot infrastructure
COPY base-bot-template/ /app/base-bot-template/

# Copy Adaptive Allocation Trend strategy
COPY adaptive-allocation-trend-strategy/ /app/adaptive-allocation-trend-strategy/

# Copy reports folder (backtest runner)
COPY reports/ /app/reports/

# Set working directory to reports
WORKDIR /app/reports

# Create results directory
RUN mkdir -p /app/reports/results

# Run the backtest
CMD ["python3", "backtest_runner.py"]
