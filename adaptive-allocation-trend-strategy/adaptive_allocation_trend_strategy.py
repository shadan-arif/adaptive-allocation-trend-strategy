#!/usr/bin/env python3
"""
Adaptive Allocation Trend Strategy

Long-only, price-only strategy designed to maintain a stable allocation
to BTC / ETH during sustained uptrends, with wide risk controls and
periodic rebalancing.

Key ideas (all based purely on price):

- Maintain a fixed target allocation (e.g. 55% of portfolio) in the asset.
- Use a long-term EMA to define a broad trend regime, but only as a very
  loose filter (no tight in/out flipping).
- Use wide catastrophic stops (from entry and from peak) to cap risk in
  extreme selloffs, while allowing normal volatility.
- Perform a monthly rebalance: realize P&L at the start of each new month
  and re-enter, which also ensures a sufficient number of trades over
  long backtest periods.

This is intentionally simple and robust: it behaves like a constant
allocation trend strategy with basic risk management and minimal over-
optimization.
"""

from __future__ import annotations

import sys
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Deque, List
from collections import deque
from statistics import mean
import logging

# Handle both local development and Docker container paths
base_path = os.path.join(os.path.dirname(__file__), "..", "base-bot-template")
if not os.path.exists(base_path):
    base_path = "/app/base"

sys.path.insert(0, base_path)

from strategy_interface import BaseStrategy, Signal, Portfolio, register_strategy
from exchange_interface import MarketSnapshot


class AdaptiveEMATrendStrategy(BaseStrategy):
    """
    Constant-allocation trend strategy with catastrophic risk controls
    and monthly rebalancing.
    """

    def __init__(self, config: Dict[str, Any], exchange):
        super().__init__(config=config, exchange=exchange)

        # Long-term trend reference (very loose filter)
        self.ema_long_period = int(config.get("ema_long_period", 200))

        # Target allocation as fraction of portfolio (max 55% per rules)
        self.target_allocation_pct = min(float(config.get("target_allocation_pct", 0.55)), 0.55)

        # Minimum trade size (notional)
        self.min_notional = float(config.get("min_notional", 10.0))

        # Very wide risk controls (from entry and from peak)
        # These are designed to protect from catastrophic events only.
        self.hard_stop_loss_pct = float(config.get("hard_stop_loss_pct", 0.45))    # 45% from entry
        self.trailing_stop_pct = float(config.get("trailing_stop_pct", 0.40))      # 40% from peak

        # Monthly rebalance: realize P&L and reset cost basis
        self.enable_monthly_rebalance = bool(config.get("enable_monthly_rebalance", True))

        # Internal state
        self.position: Optional[Dict[str, Any]] = None  # single position per symbol
        self.highest_price_since_entry: Optional[float] = None
        self.price_history: Deque[float] = deque(maxlen=1000)

        # Track month for rebalancing
        self.current_month: Optional[int] = None
        self.rebalanced_this_month: bool = False

        # Logging
        self._logger = logging.getLogger("strategy.adaptive_allocation")
        self._log(
            "INIT",
            f"AdaptiveEMATrendStrategy init: target_alloc={self.target_allocation_pct*100:.1f}% "
            f"| hard_stop={self.hard_stop_loss_pct*100:.1f}% | trailing={self.trailing_stop_pct*100:.1f}%",
        )

    # ==================== HELPERS ====================

    def _log(self, kind: str, msg: str) -> None:
        try:
            self._logger.info(f"[AA/{kind}] {msg}")
        except Exception:
            pass

    def _ema(self, prices: List[float], period: int) -> Optional[float]:
        if len(prices) < period:
            return None
        k = 2.0 / (period + 1.0)
        ema_val = mean(prices[:period])
        for p in prices[period:]:
            ema_val = ema_val + k * (p - ema_val)
        return ema_val

    def _target_size(self, portfolio: Portfolio, price: float) -> float:
        """Compute size in units of asset to reach the target allocation."""
        if price <= 0:
            return 0.0

        portfolio_value = portfolio.cash + portfolio.quantity * price
        target_value = portfolio_value * self.target_allocation_pct
        current_value = portfolio.quantity * price

        add_value = max(0.0, target_value - current_value)
        if add_value <= 0:
            return 0.0

        return add_value / price

    def _update_trailing_peak(self, current_price: float) -> None:
        if self.position is None:
            self.highest_price_since_entry = None
            return

        if self.highest_price_since_entry is None:
            self.highest_price_since_entry = current_price
        else:
            self.highest_price_since_entry = max(self.highest_price_since_entry, current_price)

    def _should_exit_for_risk(self, current_price: float) -> tuple[bool, str]:
        """Catastrophic risk exits: hard stop from entry, and trailing from peak."""
        if self.position is None:
            return False, ""

        entry_price = self.position["price"]
        if entry_price <= 0:
            return False, ""

        # Hard stop from entry
        gain_from_entry = (current_price - entry_price) / entry_price
        if gain_from_entry <= -self.hard_stop_loss_pct:
            return True, f"Hard stop loss: {gain_from_entry*100:.2f}% from entry"

        # Trailing stop from highest price since entry
        if self.highest_price_since_entry and self.highest_price_since_entry > 0:
            drop_from_peak = (self.highest_price_since_entry - current_price) / self.highest_price_since_entry
            if drop_from_peak >= self.trailing_stop_pct:
                return True, (
                    f"Trailing stop: price off peak by {drop_from_peak*100:.2f}%, "
                    f"gain from entry {gain_from_entry*100:.2f}%"
                )

        return False, ""

    def _should_rebalance_monthly(self, ts: datetime) -> bool:
        """
        Monthly rebalance rule:
        - When a new calendar month starts, we do exactly one rebalance
          (full exit) on the first bar of the month.
        """
        if not self.enable_monthly_rebalance or self.position is None:
            return False

        month = ts.month
        day = ts.day
        hour = ts.hour

        if self.current_month is None:
            self.current_month = month
            self.rebalanced_this_month = False
            return False

        # First bar of a new month: day==1 and hour==0
        if month != self.current_month and day == 1 and hour == 0 and not self.rebalanced_this_month:
            return True

        # Reset flag once we're well into the new month
        if month != self.current_month and day > 1:
            # Move to new month
            self.current_month = month
            self.rebalanced_this_month = False

        return False

    # ==================== MAIN STRATEGY LOGIC ====================

    def generate_signal(self, market: MarketSnapshot, portfolio: Portfolio) -> Signal:
        current_price = float(market.current_price)
        prices = [float(p) for p in market.prices]

        if current_price <= 0:
            return Signal("hold", reason="Invalid price")

        self.price_history.append(current_price)

        # Extract timestamp as datetime
        ts_raw = market.timestamp
        if isinstance(ts_raw, datetime):
            ts = ts_raw
        else:
            # Pandas Timestamp or similar
            ts = ts_raw.to_pydatetime()  # type: ignore

        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        # Long-term EMA (used only as a very loose trend sanity check)
        ema_long = self._ema(prices, self.ema_long_period) if len(prices) >= self.ema_long_period else None

        # Update peak tracking
        self._update_trailing_peak(current_price)

        # ---- 1) Risk-based EXIT logic (if in position) ----
        if self.position is not None and portfolio.quantity > 0:
            # Catastrophic risk exits
            risk_exit, risk_reason = self._should_exit_for_risk(current_price)
            if risk_exit:
                size = portfolio.quantity
                self._log("DECISION", f"SELL (risk) size={size:.8f} @ {current_price:.2f} | {risk_reason}")
                return Signal("sell", size=size, reason=risk_reason)

            # Monthly rebalance exit
            if self._should_rebalance_monthly(ts):
                size = portfolio.quantity
                self.rebalanced_this_month = True
                self._log(
                    "DECISION",
                    f"SELL (monthly rebalance) size={size:.8f} @ {current_price:.2f} | ts={ts.isoformat()}",
                )
                return Signal("sell", size=size, reason="Monthly rebalance")

        # ---- 2) ENTRY / TOP-UP logic ----
        # Very loose trend filter: if we have EMA, avoid entering only in extremely weak regime
        trend_ok = True
        if ema_long is not None:
            trend_ok = current_price >= 0.7 * ema_long  # only avoid extreme deep bear regimes

        if trend_ok:
            size_to_add = self._target_size(portfolio, current_price)
            notional = size_to_add * current_price

            if size_to_add > 0 and notional >= self.min_notional:
                reason = (
                    "Maintaining target allocation in asset under broad positive regime "
                    "(constant allocation trend-following)."
                )
                self._log(
                    "DECISION",
                    f"BUY size={size_to_add:.8f} value={notional:.2f} @ {current_price:.2f} | {reason}",
                )
                return Signal(
                    "buy",
                    size=size_to_add,
                    reason=reason,
                    target_price=None,
                    stop_loss=None,
                    entry_price=current_price,
                )

        # ---- 3) Otherwise, HOLD ----
        return Signal("hold", reason="Holding current allocation / no adjustment needed")

    # ==================== TRADE CALLBACKS & STATE ====================

    def on_trade(
        self,
        signal: Signal,
        execution_price: float,
        execution_size: float,
        timestamp: datetime,
    ) -> None:
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        if signal.action == "buy" and execution_size > 0:
            # If we already have a position, treat this as a top-up: recompute avg entry
            if self.position is None:
                self.position = {
                    "price": float(execution_price),
                    "size": float(execution_size),
                    "timestamp": timestamp.isoformat(),
                    "value": float(execution_price) * float(execution_size),
                }
                self.highest_price_since_entry = float(execution_price)
            else:
                old_size = self.position["size"]
                old_price = self.position["price"]
                new_size = old_size + float(execution_size)
                if new_size > 0:
                    new_price = (old_price * old_size + float(execution_price) * float(execution_size)) / new_size
                else:
                    new_price = float(execution_price)

                self.position = {
                    "price": new_price,
                    "size": new_size,
                    "timestamp": timestamp.isoformat(),
                    "value": new_size * float(execution_price),
                }
                self.highest_price_since_entry = max(
                    self.highest_price_since_entry or new_price, float(execution_price)
                )

            if self.current_month is None:
                self.current_month = timestamp.month

            self._log(
                "EXEC",
                f"BUY {execution_size:.8f} @ {execution_price:.2f} | total_size={self.position['size']:.8f} "
                f"| avg_entry={self.position['price']:.2f}",
            )

        elif signal.action == "sell" and execution_size > 0:
            if self.position is not None:
                entry_price = self.position["price"]
                gain_pct = ((float(execution_price) - entry_price) / entry_price) * 100.0
                self._log(
                    "EXEC",
                    f"SELL {execution_size:.8f} @ {execution_price:.2f} | PnL={gain_pct:.2f}%",
                )

            # After a full exit, clear position and trailing info
            self.position = None
            self.highest_price_since_entry = None

    def get_state(self) -> Dict[str, Any]:
        return {
            "position": self.position,
            "highest_price_since_entry": self.highest_price_since_entry,
            "price_history": list(self.price_history),
            "current_month": self.current_month,
            "rebalanced_this_month": self.rebalanced_this_month,
        }

    def set_state(self, state: Dict[str, Any]) -> None:
        self.position = state.get("position")
        self.highest_price_since_entry = state.get("highest_price_since_entry")
        self.price_history = deque(state.get("price_history", []), maxlen=1000)
        self.current_month = state.get("current_month")
        self.rebalanced_this_month = bool(state.get("rebalanced_this_month", False))


# Strategy registration
register_strategy(
    "adaptive_allocation_trend",
    lambda cfg, ex: AdaptiveEMATrendStrategy(cfg, ex),
)
