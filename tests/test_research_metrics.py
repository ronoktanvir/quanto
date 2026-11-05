"""Invented event-engine fixtures and hand arithmetic, never market evidence."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_DOWN, localcontext
import json

import pytest

from quanto.event_engine import run_event_backtest
from quanto.research import Bar, StrategySpec
from quanto.research_metrics import MetricsError, summarize_trace


def trace(closes=(1, 2, 2, 4, 8), *, opens=None, days=None, cash=100, cost=0, events=()):
    start = datetime(2020, 1, 1, 16, tzinfo=timezone.utc)
    opens = closes if opens is None else opens
    days = range(len(closes)) if days is None else days
    bars = [Bar(start + timedelta(days=day), "INVENTED", opening,
                max(opening, close), min(opening, close), close, 1000)
            for opening, close, day in zip(opens, closes, days)]
    return run_event_backtest(bars, StrategySpec(2, starting_cash=cash, cost_bps=cost),
                              corporate_action_events=events)


def block(report, name, first, last):
    rows = report["strategy"]["daily_equity"]
    return {"name": name, "start": rows[first]["session"], "end": rows[last]["session"]}


def test_known_wealth_returns_and_sample_statistics():
    report = trace()
    result = summarize_trace(report, [])
    full = result["full"]
    portfolio = full["strategy"]
    assert full["observations"] == 3
    assert full["calendar_days"] == 3
    assert portfolio["boundary_equity"] == "100"
    assert portfolio["ending_equity"] == "400"
    assert portfolio["total_return"] == "3"
    assert Decimal(portfolio["mean_daily_return"]) == pytest.approx(Decimal(2) / 3)
    assert float(portfolio["sample_std_daily_return"]) == pytest.approx((1 / 3) ** 0.5)
    assert float(portfolio["daily_sharpe_zero_rate"]) == pytest.approx(2 / (3 ** 0.5))
    assert portfolio["cagr"] is None
    assert portfolio["cagr_reason"] == "fewer_than_365_calendar_days"
    assert portfolio["max_drawdown"] == "0"
    assert portfolio["mean_cash_weight"] == "0"
    assert portfolio["mean_position_weight"] == "1"
    assert portfolio["position_session_fraction"] == "1"
    assert portfolio["trade_count"] == 1
    assert portfolio["traded_notional"] == "100"
    assert full["paired_mean_daily_return_difference"] == "0"
    assert result["holdout_status"] == "unprotected_development"
    assert "p_value" not in json.dumps(result)


def test_later_block_uses_preceding_equity_not_starting_cash():
    report = trace()
    result = summarize_trace(report, [block(report, "early", 0, 1), block(report, "later", 2, 2)])
    early, later = result["blocks"]
    assert early["strategy"]["boundary_equity"] == "100"
    assert early["strategy"]["total_return"] == "1"
    assert later["strategy"]["boundary_equity"] == "200"
    assert later["strategy"]["total_return"] == "1"
    assert later["strategy"]["mean_daily_return"] == "1"
    assert later["strategy"]["sample_std_daily_return"] is None
    assert later["strategy"]["sample_std_reason"] == "fewer_than_two_observations"
    assert later["strategy"]["daily_sharpe_reason"] == "fewer_than_two_observations"
    assert later["strategy"]["trade_count"] == 0


def test_fee_notional_drawdown_and_paired_return_arithmetic():
    report = trace((90, 100, 100, 90, 80), cash=1010, cost=100)
    result = summarize_trace(report, [block(report, "exit", 2, 2)])
    strategy, benchmark = result["full"]["strategy"], result["full"]["benchmark"]
    assert Decimal(strategy["ending_equity"]) == 792
    assert Decimal(strategy["total_fees"]) == 18
    assert Decimal(strategy["traded_notional"]) == 1800
    assert strategy["buy_count"] == strategy["sell_count"] == 1
    assert Decimal(benchmark["ending_equity"]) == 800
    assert Decimal(benchmark["total_fees"]) == 10
    assert float(strategy["max_drawdown"]) == pytest.approx(218 / 1010)
    assert float(strategy["mean_cash_weight"]) == pytest.approx(1 / 3)
    assert float(strategy["mean_position_weight"]) == pytest.approx(2 / 3)
    final = result["blocks"][0]
    assert Decimal(final["strategy"]["boundary_equity"]) == 900
    assert final["strategy"]["total_return"] == "-0.12"
    assert final["strategy"]["max_drawdown"] == "0.12"
    assert Decimal(final["strategy"]["total_fees"]) == 8
    assert float(final["paired_mean_daily_return_difference"]) == pytest.approx(-0.12 + 1 / 9)


def test_split_and_claims_do_not_create_spurious_performance():
    split = {"kind": "split", "event_id": "s", "effective_date": "2020-01-04",
             "new_rate": "2", "old_rate": "1"}
    dividend = {"kind": "cash_dividend", "event_id": "d", "ex_date": "2020-01-05",
                "payable_date": "2020-01-10", "rate": "1", "currency": "USD",
                "share_basis": "ex_date_shares"}
    report = trace((90, 100, 100, 50, 49), cash=1000, events=(split, dividend))
    summary = summarize_trace(report, [block(report, "after_split", 1, 2)])
    for name in ("strategy", "benchmark"):
        metrics = summary["full"][name]
        assert metrics["total_return"] == "0"
        assert metrics["sample_std_daily_return"] == "0"
        assert metrics["daily_sharpe_zero_rate"] is None
        assert metrics["daily_sharpe_reason"] == "zero_sample_variance"
        assert float(metrics["mean_receivables_weight"]) == pytest.approx(0.02 / 3)
        assert summary["blocks"][0][name]["boundary_equity"] == "1000"
        assert summary["blocks"][0][name]["total_return"] == "0"


def test_claim_summation_retains_engine_accrual_order_not_serialized_id_order():
    events = [{"kind": "cash_dividend", "event_id": identifier,
               "ex_date": f"2020-01-0{day}", "payable_date": "2020-01-20",
               "rate": rate, "currency": "USD", "share_basis": "ex_date_shares"}
              for identifier, day, rate in (("z", 4, "1e34"), ("a", 5, "3"), ("b", 6, "3"))]
    report = trace((90, 100, 100, 100, 100, 100), cash=100, events=events)
    assert [claim["event_id"] for claim in report["strategy"]["ending_receivables"]] == ["a", "b", "z"]
    # Rounding after (big + 3) + 3 differs from rounding (3 + 3) + big.
    result = summarize_trace(report, [])
    assert result["full"]["strategy"]["ending_equity"] == report["strategy"]["ending_equity"]


@pytest.mark.parametrize("count", [1, 364, 365, 366])
def test_cagr_calendar_floor_and_inclusive_day_count(count):
    report = trace([1, 2] + [4] * count, opens=[1, 2, 2] + [4] * (count - 1))
    full = summarize_trace(report, [])["full"]
    assert full["calendar_days"] == count
    if count < 365:
        assert full["strategy"]["cagr"] is None
    else:
        assert float(full["strategy"]["cagr"]) == pytest.approx(2 ** (365.2425 / count) - 1)
        assert full["strategy"]["cagr_reason"] is None


def test_sparse_session_labels_are_not_invented_daily_observations():
    report = trace(days=[0, 1, 2, 5, 368])
    full = summarize_trace(report, [])["full"]
    assert full["observations"] == 3
    assert full["calendar_days"] == 367
    assert full["strategy"]["cagr"] is not None
    assert "not a sample-adequacy claim" in summarize_trace(report, [])["conventions"]["annualization_floor"]


def test_appended_future_rows_leave_existing_block_unchanged():
    original = trace()
    future = trace((1, 2, 2, 4, 8, 3, 2, 9))
    chosen = [block(original, "fixed", 0, 2)]
    assert summarize_trace(original, chosen)["blocks"] == summarize_trace(future, chosen)["blocks"]


def test_global_decimal_context_does_not_change_results_or_inputs():
    report = trace(cost=10)
    before = deepcopy(report)
    expected = summarize_trace(report, [])
    with localcontext() as context:
        context.prec = 6
        context.rounding = ROUND_DOWN
        assert summarize_trace(report, []) == expected
    assert report == before


@pytest.mark.parametrize("bad", ["NaN", "Infinity", "-Infinity", "1e999999", "0e999999", 1.0, True, None])
def test_invalid_decimals_refuse(bad):
    report = trace()
    report["strategy"]["daily_equity"][0]["equity"] = bad
    with pytest.raises(MetricsError):
        summarize_trace(report, [])


@pytest.mark.parametrize("mutate,reason", [
    (lambda r: r["strategy"]["daily_equity"][1].update(daily_return="0.1"), "return_continuity"),
    (lambda r: r["strategy"]["daily_equity"][1].update(cash="1"), "wealth_components"),
    (lambda r: r["strategy"]["daily_equity"][1].update(equity="0"), "nonpositive"),
    (lambda r: r["strategy"]["daily_equity"].reverse(), "return_continuity|nonmonotonic"),
    (lambda r: r["strategy"]["trades"][0].update(fee="1"), "trade_arithmetic"),
    (lambda r: r["strategy"].update(total_fees="1"), "portfolio_totals"),
    (lambda r: r["strategy"].update(ending_cash="1"), "ending_components"),
    (lambda r: r.update(evaluation_start="2020-01-01"), "evaluation_bounds"),
    (lambda r: r.update(holdout_status="protected"), "unsupported_evidence"),
    (lambda r: r["accounting_policy"].update(decimal_precision=28), "unsupported_accounting"),
])
def test_inconsistent_inputs_refuse(mutate, reason):
    report = trace()
    mutate(report)
    with pytest.raises(MetricsError, match=reason):
        summarize_trace(report, [])


def test_strategy_and_benchmark_session_alignment_is_required():
    report = trace()
    # Change only the time-of-day: each individual sequence is still monotonic.
    report["benchmark"]["daily_equity"][1]["timestamp"] = "2020-01-04T17:00:00+00:00"
    with pytest.raises(MetricsError, match="alignment"):
        summarize_trace(report, [])


@pytest.mark.parametrize("blocks", [
    [{"name": "x", "start": "2020-01-02", "end": "2020-01-04"}],
    [{"name": "x", "start": "2020-01-05", "end": "2020-01-03"}],
    [{"name": "x", "start": "2020-01-03", "end": "2020-01-04"},
     {"name": "y", "start": "2020-01-04", "end": "2020-01-05"}],
    [{"name": "full", "start": "2020-01-03", "end": "2020-01-05"}],
    [{"name": "x", "start": "2020-01-03", "end": "2020-01-03"},
     {"name": "x", "start": "2020-01-04", "end": "2020-01-05"}],
    [{"name": "x", "start": "2020-01-03", "end": "2020-01-05", "extra": 1}],
    [None] * 11,
])
def test_invalid_blocks_refuse(blocks):
    with pytest.raises(MetricsError):
        summarize_trace(trace(), blocks)


def test_row_limit_and_output_bound():
    report = trace([1, 2] + [2] * 10_000)
    blocks = [block(report, f"part_{i}", i * 1000, (i + 1) * 1000 - 1) for i in range(10)]
    result = summarize_trace(report, blocks)
    assert len(json.dumps(result).encode()) < 128 * 1024
    report["strategy"]["daily_equity"].append(deepcopy(report["strategy"]["daily_equity"][-1]))
    with pytest.raises(MetricsError, match="row_limit"):
        summarize_trace(report, [])
