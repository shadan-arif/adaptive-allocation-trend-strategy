# Adaptive Allocation Trend Strategy - Dockerfile
FROM python:3.11-slim

LABEL description="Adaptive Allocation Trend Trading Bot - Constant-Allocation Strategy"
LABEL strategies="adaptive_allocation_trend"
LABEL tier="intermediate"

# Set working directory
WORKDIR /app

# Copy base bot infrastructure
COPY base-bot-template/ /app/base/

# Copy Adaptive Allocation Trend specific files
COPY adaptive-allocation-trend-strategy/ /app/

# Install dependencies
RUN pip install --no-cache-dir -r /app/base/requirements.txt

# Make startup script executable
RUN chmod +x /app/startup.py

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Expose ports
EXPOSE 8080 3010

# Default environment
ENV BOT_EXCHANGE=paper
ENV BOT_STRATEGY=adaptive_allocation_trend
ENV BOT_SYMBOL=BTC-USD
ENV BOT_STARTING_CASH=10000.0
ENV BOT_SLEEP=3600

# Start the Adaptive Allocation Trend bot
CMD ["python", "/app/startup.py"]
