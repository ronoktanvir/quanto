"""Deterministic daily-bar research, without any order or network integration.

Prices are raw, positive prices in one currency; fractional shares are allowed.
An SMA signal formed at a completed close can fill only at the next supplied
session's open. There is no terminal liquidation or implied exit fee. Float
accounting is unrounded; consumers should compare amounts with rel_tol=1e-12,
abs_tol=1e-9, not exact decimal equality. Threshold comparisons are exact.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
import hashlib
import json
import math
from typing import Any, Sequence
from zoneinfo import ZoneInfo


class ResearchValidationError(ValueError):
    """Input is invalid or asks for unsupported financial treatment."""


class InsufficientDataError(ResearchValidationError):
    """There is no evaluation session after the required warm-up."""


def _number(name: str, value: float, *, positive: bool = False) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ResearchValidationError(f"{name} must be a finite number")
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite or (value <= 0 if positive else value < 0):
        bound = "positive" if positive else "nonnegative"
        raise ResearchValidationError(f"{name} must be finite and {bound}")


@dataclass(frozen=True)
class Bar:
    """One completed daily session; timestamp.date() is its session label.

    Supply an exchange-local session label with an aware timezone. All bars must
    share the same ZoneInfo key, equal fixed-offset timezone, or identical tzinfo
    object. ZoneInfo daylight-saving offset changes are allowed. The timestamp
    does not establish the exact availability instant of the completed bar.
    This module does not infer calendars, currencies, adjustments, or rights.
    """

    timestamp: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float

    def __post_init__(self) -> None:
        if not isinstance(self.timestamp, datetime) or self.timestamp.utcoffset() is None:
            raise ResearchValidationError("timestamp must be a timezone-aware datetime")
        if not isinstance(self.symbol, str) or not self.symbol.strip():
            raise ResearchValidationError("symbol must be nonempty")
        for name in ("open", "high", "low", "close"):
            _number(name, getattr(self, name), positive=True)
        _number("volume", self.volume)
        if self.low > min(self.open, self.close) or self.high < max(self.open, self.close):
            raise ResearchValidationError("OHLC prices are inconsistent")


@dataclass(frozen=True)
class StrategySpec:
    """Fixed SMA trend rule; strict crossings enter/exit, equality preserves state.

    Enter when close > SMA * (1 + entry_threshold); exit when close < SMA *
    (1 - exit_threshold). Thresholds are fractions, costs basis points per fill.
    Each entry invests all available cash including its fee.
    """

    lookback: int
    entry_threshold: float = 0.0
    exit_threshold: float = 0.0
    starting_cash: float = 10_000.0
    cost_bps: float = 0.0

    def __post_init__(self) -> None:
        if (
            isinstance(self.lookback, bool)
            or not isinstance(self.lookback, int)
            or self.lookback < 1
        ):
            raise ResearchValidationError("lookback must be a positive integer")
        _number("starting_cash", self.starting_cash, positive=True)
        _number("cost_bps", self.cost_bps)
        if self.cost_bps >= 10_000:
            raise ResearchValidationError("cost_bps must be below 10000")
        for name in ("entry_threshold", "exit_threshold"):
            _number(name, getattr(self, name))
            if getattr(self, name) >= 1:
                raise ResearchValidationError(f"{name} must be below 1")


@dataclass(frozen=True)
class Trade:
    """An assumed fill at a session's open, without a claimed execution instant."""

    execution_session: date
    signal_session: date | None
    side: str
    quantity: float
    price: float
    fee: float
    cash_after: float
    execution_price_point: str = "open"


@dataclass(frozen=True)
class DailyEquity:
    timestamp: datetime
    cash: float
    quantity: float
    close: float
    equity: float
    daily_return: float
    signal: str


@dataclass(frozen=True)
class Performance:
    daily_equity: tuple[DailyEquity, ...]
    trades: tuple[Trade, ...]
    total_return: float
    max_drawdown: float
    total_fees: float
    ending_equity: float


@dataclass(frozen=True)
class BacktestReport:
    evidence_kind: str
    symbol: str
    specification: StrategySpec
    data_sha256: str
    specification_sha256: str
    warmup_sessions: tuple[date, ...]
    evaluation_start: date
    evaluation_end: date
    calendar_coverage: str
    timing: str
    holdout_status: str
    strategy: Performance
    benchmark: Performance
    assumptions: tuple[str, ...]
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-compatible values, including ISO dates/timestamps."""
        return _json_values(asdict(self))


def _json_values(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_values(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_values(item) for item in value]
    return value


def _identity(value: Any) -> str:
    encoded = json.dumps(
        _json_values(value), sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    return hashlib.sha256(encoded.encode()).hexdigest()


def _checked(value: float, *, positive: bool = False) -> float:
    if not math.isfinite(value) or (value <= 0 if positive else value < 0):
        raise ResearchValidationError("accounting overflow, underflow, or invalid derived amount")
    return value


def _same_session_timezone(first: datetime, current: datetime) -> bool:
    first_zone, current_zone = first.tzinfo, current.tzinfo
    if isinstance(first_zone, ZoneInfo) and isinstance(current_zone, ZoneInfo):
        return first_zone.key == current_zone.key
    if isinstance(first_zone, timezone) and isinstance(current_zone, timezone):
        return first_zone == current_zone
    return first_zone is current_zone


def _target(bars: tuple[Bar, ...], index: int, spec: StrategySpec, holding: bool) -> bool:
    # Divide before summation to avoid overflowing an otherwise representable mean.
    mean = _checked(
        math.fsum(bar.close / spec.lookback for bar in bars[index + 1 - spec.lookback : index + 1]),
        positive=True,
    )
    entry = _checked(mean * (1 + spec.entry_threshold))
    if bars[index].close > entry:
        return True
    if bars[index].close < mean * (1 - spec.exit_threshold):
        return False
    return holding


def _simulate(bars: tuple[Bar, ...], spec: StrategySpec, *, benchmark: bool) -> Performance:
    cash = float(spec.starting_cash)
    quantity = 0.0
    previous_equity = peak = cash
    drawdown = 0.0
    fee_rate = spec.cost_bps / 10_000
    desired = True if benchmark else _target(bars, spec.lookback - 1, spec, False)
    trades: list[Trade] = []
    daily: list[DailyEquity] = []
    for index in range(spec.lookback, len(bars)):
        bar = bars[index]
        signal_session = None if benchmark else bars[index - 1].timestamp.date()
        if desired and quantity == 0:
            quantity = _checked((cash / bar.open) / (1 + fee_rate))
            if quantity == 0:
                raise ResearchValidationError("entry quantity underflow")
            fee = _checked(quantity * bar.open * fee_rate)
            cash = 0.0
            trades.append(
                Trade(bar.timestamp.date(), signal_session, "buy", quantity, bar.open, fee, cash)
            )
        elif not desired and quantity > 0:
            proceeds = _checked(quantity * bar.open)
            fee = _checked(proceeds * fee_rate)
            cash = _checked(proceeds - fee)
            trades.append(
                Trade(bar.timestamp.date(), signal_session, "sell", quantity, bar.open, fee, cash)
            )
            quantity = 0.0
        equity = _checked(cash + _checked(quantity * bar.close), positive=True)
        if previous_equity == 0:
            raise ResearchValidationError("equity underflow prevents return calculation")
        daily_return = equity / previous_equity - 1
        if not math.isfinite(daily_return):
            raise ResearchValidationError("return overflow")
        peak = max(peak, equity)
        drawdown = max(drawdown, (peak - equity) / peak)
        desired = True if benchmark else _target(bars, index, spec, quantity > 0)
        daily.append(
            DailyEquity(
                bar.timestamp,
                cash,
                quantity,
                bar.close,
                equity,
                daily_return,
                "long" if desired else "cash",
            )
        )
        previous_equity = equity
    total_return = previous_equity / spec.starting_cash - 1
    if not math.isfinite(total_return):
        raise ResearchValidationError("total return overflow")
    return Performance(
        tuple(daily),
        tuple(trades),
        total_return,
        drawdown,
        _checked(math.fsum(trade.fee for trade in trades)),
        previous_equity,
    )


def run_backtest(
    bars: Sequence[Bar],
    spec: StrategySpec,
    *,
    expected_session_dates: Sequence[date] | None = None,
    evidence_kind: str = "synthetic_fixture",
    price_basis: str = "raw",
    corporate_action_events: Sequence[Any] = (),
) -> BacktestReport:
    """Evaluate supplied daily bars; reject gaps only against an explicit schedule.

    The first ``lookback`` sessions are warm-up only. Strategy and buy-and-hold
    benchmark share the following open as their first eligible fill and the same
    final close. No annualized metrics or investment-performance claims are made.
    A supplied schedule is checked exactly, but is not independently certified as
    an exchange calendar. Missing sessions never receive substituted prices.
    """
    if not isinstance(spec, StrategySpec):
        raise ResearchValidationError("spec must be StrategySpec")
    if evidence_kind not in {"synthetic_fixture", "historical_market_data"}:
        raise ResearchValidationError(
            "backtests support synthetic_fixture or historical_market_data evidence only"
        )
    if price_basis != "raw":
        raise ResearchValidationError("adjusted or mixed price treatment is unsupported")
    if corporate_action_events:
        raise ResearchValidationError(
            "corporate actions, including dividends and splits, are unsupported"
        )
    supplied = tuple(bars)
    if any(not isinstance(bar, Bar) for bar in supplied):
        raise ResearchValidationError("bars must contain Bar instances")
    if len(supplied) <= spec.lookback:
        raise InsufficientDataError(
            "need lookback warm-up sessions plus at least one evaluation session"
        )
    symbol = supplied[0].symbol
    sessions = tuple(bar.timestamp.date() for bar in supplied)
    for index, bar in enumerate(supplied):
        if bar.symbol != symbol:
            raise ResearchValidationError("mixed symbols are unsupported")
        if not _same_session_timezone(supplied[0].timestamp, bar.timestamp):
            raise ResearchValidationError("bars must share a consistent exchange session timezone")
        if index and (
            bar.timestamp <= supplied[index - 1].timestamp or sessions[index] <= sessions[index - 1]
        ):
            raise ResearchValidationError(
                "daily bars must have unique, strictly increasing sessions and timestamps"
            )
    coverage = "unverified"
    if expected_session_dates is not None:
        expected = tuple(expected_session_dates)
        if any(type(session) is not date for session in expected):
            raise ResearchValidationError("expected sessions must be date values")
        if any(current <= previous for previous, current in zip(expected, expected[1:])):
            raise ResearchValidationError("expected sessions must be unique and increasing")
        if sessions != expected:
            raise ResearchValidationError("supplied bars do not exactly match expected sessions")
        coverage = "caller_supplied_schedule_checked"
    return BacktestReport(
        evidence_kind,
        symbol,
        spec,
        _identity([asdict(bar) for bar in supplied]),
        _identity(asdict(spec)),
        sessions[: spec.lookback],
        sessions[spec.lookback],
        sessions[-1],
        coverage,
        "session_level_open; exact_availability_unverified",
        "unprotected_not_implemented",
        _simulate(supplied, spec, benchmark=False),
        _simulate(supplied, spec, benchmark=True),
        (
            "Completed-close signals fill at the next supplied session open.",
            "Trade dates identify sessions and open prices, not exact execution instants.",
            "Fractional long/cash positions; one currency; fees per fill; no slippage model.",
            "Both portfolios use identical evaluation dates and fee rates; no terminal liquidation.",
            "Daily returns include fees and use starting cash for the first evaluation session.",
        ),
        (
            "Raw price returns exclude dividends; splits and corporate actions are unsupported.",
            "Caller must establish corporate-action absence, currency consistency, and source rights.",
            "Exchange calendar and completeness are not independently verified.",
            "Exact bar availability and execution instants are unverified at session-level timing.",
            "Holdout protection and exposure tracking are not implemented; this evaluation is unprotected.",
            "Synthetic fixtures validate software, not investment performance.",
            "No liquidity, spread, market impact, taxes, interest, or execution feasibility model.",
        ),
    )
