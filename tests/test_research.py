"""Synthetic accounting and time-integrity checks; no investment evidence."""

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
import json
import math
from zoneinfo import ZoneInfo

import pytest

from quanto.research import (
    Bar,
    InsufficientDataError,
    ResearchValidationError,
    StrategySpec,
    run_backtest,
)


def bars(closes, opens=None):
    opens = closes if opens is None else opens
    start = datetime(2024, 6, 1, 16, tzinfo=timezone.utc)
    return [
        Bar(
            start + timedelta(days=i),
            "FIXTURE",
            opening,
            max(opening, close),
            min(opening, close),
            close,
            1000,
        )
        for i, (opening, close) in enumerate(zip(opens, closes))
    ]


def test_round_trip_uses_next_open_and_charges_both_fills():
    supplied = bars([10, 12, 18, 6, 5], [10, 12, 20, 18, 5])
    report = run_backtest(supplied, StrategySpec(lookback=2, starting_cash=100, cost_bps=100))
    buy, sell = report.strategy.trades
    quantity = 100 / (20 * 1.01)
    expected_cash = quantity * 5 * 0.99
    assert (buy.price, sell.price) == (20, 5)
    assert buy.signal_session == supplied[1].timestamp.date()
    assert sell.signal_session == supplied[3].timestamp.date()
    assert buy.quantity == pytest.approx(quantity)
    assert report.strategy.ending_equity == pytest.approx(expected_cash)
    assert report.strategy.total_fees == pytest.approx(quantity * 20 * 0.01 + quantity * 5 * 0.01)
    assert report.strategy.total_return == pytest.approx(expected_cash / 100 - 1)
    assert report.strategy.daily_equity[0].equity == pytest.approx(quantity * 18)
    assert report.strategy.daily_equity[1].signal == "cash"
    assert report.strategy.daily_equity[1].quantity > 0  # Exit waits for the next open.
    assert report.strategy.max_drawdown == pytest.approx(1 - expected_cash / 100)


def test_benchmark_uses_identical_evaluation_window_and_fee_convention():
    supplied = bars([10, 12, 18, 6, 5], [10, 12, 20, 18, 5])
    report = run_backtest(supplied, StrategySpec(2, starting_cash=100, cost_bps=100))
    assert report.warmup_sessions == (date(2024, 6, 1), date(2024, 6, 2))
    assert report.evaluation_start == date(2024, 6, 3)
    assert report.evaluation_end == date(2024, 6, 5)
    assert [day.timestamp for day in report.strategy.daily_equity] == [
        day.timestamp for day in report.benchmark.daily_equity
    ]
    assert report.benchmark.trades[0].execution_session == supplied[2].timestamp.date()
    assert report.benchmark.trades[0].fee == pytest.approx(report.strategy.trades[0].fee)
    assert report.benchmark.ending_equity == pytest.approx((100 / (20 * 1.01)) * 5)
    assert len(report.benchmark.trades) == 1  # Mark-to-close, no invented terminal sale.
    compounded = math.prod(1 + day.daily_return for day in report.benchmark.daily_equity)
    assert compounded == pytest.approx(1 + report.benchmark.total_return)


def test_no_trade_keeps_cash_and_zero_returns():
    report = run_backtest(bars([10, 9, 8, 7]), StrategySpec(2, starting_cash=100, cost_bps=25))
    assert report.strategy.trades == ()
    assert report.strategy.ending_equity == 100
    assert (
        report.strategy.total_return
        == report.strategy.total_fees
        == report.strategy.max_drawdown
        == 0
    )
    assert all(day.daily_return == 0 and day.cash == 100 for day in report.strategy.daily_equity)


def test_last_close_signal_is_reported_without_same_close_fill():
    report = run_backtest(bars([10, 9, 12]), StrategySpec(2))
    assert report.strategy.trades == ()
    assert report.strategy.daily_equity[-1].signal == "long"
    assert report.strategy.daily_equity[-1].quantity == 0


def test_threshold_equality_preserves_cash_until_strict_entry():
    # At the warm-up close, 12 equals SMA(8,12) * 1.2; equality stays cash.
    report = run_backtest(bars([8, 12, 20, 21]), StrategySpec(2, entry_threshold=0.2))
    assert report.strategy.daily_equity[0].quantity == 0
    assert report.strategy.daily_equity[0].signal == "long"
    assert (
        report.strategy.trades[0].execution_session
        == report.strategy.daily_equity[1].timestamp.date()
    )


def test_future_perturbation_cannot_change_earlier_signals_or_fills():
    original = bars([10, 12, 18, 6, 5, 8], [10, 12, 20, 18, 5, 7])
    changed = original[:-1] + [replace(original[-1], open=100, high=120, low=1, close=1)]
    spec = StrategySpec(2, starting_cash=100, cost_bps=100)
    before, after = run_backtest(original, spec), run_backtest(changed, spec)
    assert before.strategy.daily_equity[:-1] == after.strategy.daily_equity[:-1]
    assert [
        trade
        for trade in before.strategy.trades
        if trade.execution_session < original[-1].timestamp.date()
    ] == [
        trade
        for trade in after.strategy.trades
        if trade.execution_session < original[-1].timestamp.date()
    ]
    assert before.data_sha256 != after.data_sha256


def test_repeated_runs_are_identical_and_json_serializable():
    supplied, spec = bars([10, 12, 14, 16]), StrategySpec(2)
    first = run_backtest(supplied, spec)
    assert first == run_backtest(supplied, spec)
    assert first.evidence_kind == "synthetic_fixture"
    assert (
        json.loads(json.dumps(first.to_dict(), allow_nan=False))["evaluation_start"] == "2024-06-03"
    )


def test_calendar_is_unverified_without_exact_explicit_schedule():
    supplied = bars([10, 12, 14, 16])
    assert run_backtest(supplied, StrategySpec(2)).calendar_coverage == "unverified"
    dates = [bar.timestamp.date() for bar in supplied]
    checked = run_backtest(supplied, StrategySpec(2), expected_session_dates=dates)
    assert checked.calendar_coverage == "caller_supplied_schedule_checked"
    with pytest.raises(ResearchValidationError, match="expected sessions"):
        run_backtest(supplied[:2] + supplied[3:], StrategySpec(2), expected_session_dates=dates)
    with pytest.raises(ResearchValidationError, match="unique and increasing"):
        run_backtest(supplied, StrategySpec(2), expected_session_dates=dates[::-1])


def test_close_labeled_bar_does_not_claim_an_open_execution_instant():
    supplied = bars([10, 12, 14])  # Input labels are 16:00; fills use session open.
    report = run_backtest(supplied, StrategySpec(2))
    trade = report.to_dict()["strategy"]["trades"][0]
    assert supplied[2].timestamp.hour == 16
    assert trade["execution_session"] == "2024-06-03"
    assert trade["execution_price_point"] == "open"
    assert trade["signal_session"] == "2024-06-02"
    assert "timestamp" not in trade and "signal_timestamp" not in trade
    assert report.timing == "session_level_open; exact_availability_unverified"
    assert report.holdout_status == "unprotected_not_implemented"


def test_mixed_fixed_offset_session_timezones_reject():
    supplied = bars([10, 12, 14])
    supplied[-1] = replace(
        supplied[-1], timestamp=supplied[-1].timestamp.replace(tzinfo=timezone(timedelta(hours=-4)))
    )
    with pytest.raises(ResearchValidationError, match="session timezone"):
        run_backtest(supplied, StrategySpec(2))


def test_named_exchange_timezone_accepts_dst_change_with_same_zone_key():
    supplied = bars([10, 12, 14])
    days = [(2024, 3, 8), (2024, 3, 11), (2024, 3, 12)]
    supplied = [
        replace(bar, timestamp=datetime(*day, 16, tzinfo=ZoneInfo.no_cache("America/New_York")))
        for bar, day in zip(supplied, days)
    ]
    assert supplied[0].timestamp.utcoffset() != supplied[1].timestamp.utcoffset()
    assert supplied[0].timestamp.tzinfo is not supplied[1].timestamp.tzinfo
    report = run_backtest(supplied, StrategySpec(2))
    assert report.strategy.trades[0].execution_session == date(2024, 3, 12)


def test_named_and_fixed_offset_timezones_do_not_silently_mix():
    supplied = bars([10, 12, 14])
    supplied[-1] = replace(
        supplied[-1], timestamp=supplied[-1].timestamp.replace(tzinfo=ZoneInfo("UTC"))
    )
    with pytest.raises(ResearchValidationError, match="session timezone"):
        run_backtest(supplied, StrategySpec(2))


@pytest.mark.parametrize(
    "field,value",
    [
        ("open", 0),
        ("close", -1),
        ("high", float("nan")),
        ("low", float("inf")),
        ("volume", -1),
        ("volume", True),
    ],
)
def test_invalid_bar_numbers_reject(field, value):
    with pytest.raises(ResearchValidationError):
        replace(bars([10])[0], **{field: value})


def test_invalid_ohlc_and_naive_timestamp_reject():
    base = bars([10])[0]
    with pytest.raises(ResearchValidationError, match="OHLC"):
        replace(base, high=9)
    with pytest.raises(ResearchValidationError, match="timezone-aware"):
        replace(base, timestamp=datetime(2024, 6, 1))


@pytest.mark.parametrize(
    "changes",
    [
        {"lookback": 0},
        {"lookback": True},
        {"lookback": 1.5},
        {"starting_cash": 0},
        {"cost_bps": -1},
        {"cost_bps": 10_000},
        {"cost_bps": float("nan")},
        {"entry_threshold": 1},
        {"exit_threshold": float("inf")},
    ],
)
def test_invalid_spec_rejects(changes):
    with pytest.raises(ResearchValidationError):
        StrategySpec(**({"lookback": 2} | changes))


def test_duplicate_nonmonotonic_and_mixed_symbols_reject():
    supplied = bars([10, 12, 14, 16])
    for invalid in (
        supplied[:2] + supplied[1:],
        supplied[::-1],
        supplied[:-1] + [replace(supplied[-1], symbol="OTHER")],
    ):
        with pytest.raises(ResearchValidationError):
            run_backtest(invalid, StrategySpec(2))


@pytest.mark.parametrize("length", [0, 1, 2])
def test_insufficient_warmup_is_not_zero_performance(length):
    with pytest.raises(InsufficientDataError):
        run_backtest(bars([10] * length), StrategySpec(2))


@pytest.mark.parametrize(
    "options",
    [
        {"price_basis": "adjusted"},
        {"price_basis": "mixed"},
        {"corporate_action_events": [{"type": "split"}]},
        {"corporate_action_events": [{"type": "dividend"}]},
        {"evidence_kind": "live_execution"},
    ],
)
def test_unsupported_financial_or_evidence_treatment_rejects(options):
    with pytest.raises(ResearchValidationError):
        run_backtest(bars([10, 12, 14]), StrategySpec(2), **options)


def test_accounting_overflow_fails_instead_of_emitting_infinity():
    with pytest.raises(ResearchValidationError, match="overflow"):
        run_backtest(bars([1, 2, 1e308], [1, 2, 1]), StrategySpec(2, starting_cash=1e308))


def test_unrepresentable_mean_fails_instead_of_inventing_zero_price():
    with pytest.raises(ResearchValidationError, match="underflow"):
        run_backtest(bars([5e-324, 5e-324, 5e-324]), StrategySpec(2))
