"""Hand-derived synthetic accounting cases; not investment-performance evidence."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_DOWN, localcontext
import json

import pytest

from quanto.event_engine import policy_identity, run_event_backtest
from quanto.research import Bar, ResearchValidationError, StrategySpec, run_backtest


def bars(closes, opens=None, days=None):
    opens = closes if opens is None else opens
    start = datetime(2024, 6, 3, 16, tzinfo=timezone.utc)
    return [Bar(
        start + timedelta(days=i if days is None else days[i]), "SYNTHETIC", opening,
        max(opening, close), min(opening, close), close, 1000,
    ) for i, (opening, close) in enumerate(zip(opens, closes))]


def split(day="2024-06-06", new="2", old="1", identifier="split-1"):
    return {"kind": "split", "event_id": identifier, "effective_date": day,
            "new_rate": new, "old_rate": old}


def dividend(ex="2024-06-06", pay="2024-06-10", rate="1", identifier="div-1"):
    return {"kind": "cash_dividend", "event_id": identifier, "ex_date": ex,
            "payable_date": pay, "rate": rate, "currency": "USD",
            "share_basis": "ex_date_shares"}


def run(supplied, events=(), **spec):
    return run_event_backtest(supplied, StrategySpec(2, starting_cash=1000, **spec),
                              corporate_action_events=events)


@pytest.mark.parametrize("new,old,prices,quantity", [
    ("2", "1", [90, 100, 100, 50, 50], "20"),
    ("1", "4", [90, 100, 100, 400, 400], "2.5"),
    ("3", "2", [90, 100, 100, 80, 80], "15"),
])
def test_split_units_and_marked_wealth(new, old, prices, quantity):
    report = run(bars(prices), [split(new=new, old=old)])
    for name in ("strategy", "benchmark"):
        result = report[name]
        assert Decimal(result["ending_quantity"]) == Decimal(quantity)
        assert Decimal(result["ending_equity"]) == Decimal(quantity) * prices[-1]
        assert len(result["trades"]) == 1
        assert Decimal(result["total_fees"]) == 0
    # The 3:2 fixture includes an economic rise, rather than assuming all splits
    # mechanically conserve wealth despite a genuine raw-price move.
    assert Decimal(report["strategy"]["total_return"]) == (Decimal("0.2") if new == "3" else 0)


@pytest.mark.parametrize("warmup,expected", [([9, 1, 2], "cash"), ([1, 1, 2], "long")])
def test_nonterminating_split_rebase_exact_tie_retains_state(warmup, expected):
    # The next rolling window is exactly [2/3, 4/3, 1], whose mean is 1.
    supplied = bars(warmup + [1, 1])
    result = run_event_backtest(supplied, StrategySpec(3, starting_cash=100),
                               corporate_action_events=[split(new="3", old="2")])["strategy"]
    assert result["daily_equity"][0]["signal"] == expected
    assert len(result["trades"]) == (1 if expected == "long" else 0)


def test_split_inside_warmup_rebases_prices_without_inheriting_position():
    report = run(bars([200, 100, 100]), [split(day="2024-06-04")])
    assert report["strategy"]["initial_signal"] == "cash"  # exact 100/100 tie
    assert report["strategy"]["trades"] == []
    assert report["strategy"]["event_flows"] == []
    assert Decimal(report["benchmark"]["ending_quantity"]) == 10


def test_threshold_tie_is_exact_decimal_input_comparison():
    result = run(bars([8, 12, 20, 20]), entry_threshold=0.2)["strategy"]
    assert result["initial_signal"] == "cash"  # 12 == mean(8,12) * 1.2
    assert result["trades"][0]["execution_session"] == "2024-06-06"


def test_dividend_accrual_preserves_equity_and_sale_preserves_claim():
    report = run(bars([90, 100, 100, 99, 99]), [dividend()])
    result = report["strategy"]
    ex, after_sale = result["daily_equity"][1:]
    assert Decimal(ex["equity"]) == 1000  # 10 * 99 + 10 claim
    assert Decimal(after_sale["quantity"]) == 0
    assert Decimal(after_sale["cash"]) == 990
    assert Decimal(after_sale["receivables_total"]) == 10
    assert Decimal(result["ending_equity"]) == 1000
    assert result["ending_receivables"][0]["event_id"] == "div-1"
    assert result["ending_receivables"][0]["payable_date"] == "2024-06-10"
    assert Decimal(result["ending_receivables"][0]["amount"]) == 10
    assert result["trades"][-1]["execution_session"] == "2024-06-07"


def test_ex_date_seller_keeps_claim_and_buyer_gets_none():
    supplied = bars([90, 100, 90, 90])
    result = run(supplied, [dividend()])["strategy"]
    assert result["trades"][-1]["execution_session"] == "2024-06-06"
    assert Decimal(result["ending_receivables_total"]) == Decimal(
        "11.11111111111111111111111111111111")
    # First scored-open purchase occurs on ex-date, so neither portfolio earns it.
    buyer = run(bars([90, 100, 100]), [dividend(ex="2024-06-05")])
    assert buyer["strategy"]["ending_receivables"] == []
    assert buyer["benchmark"]["ending_receivables"] == []


def test_cash_payment_after_sale_changes_asset_form_only():
    report = run(bars([90, 100, 100, 99, 99, 99], days=[0, 1, 2, 3, 4, 7]), [dividend()])
    result = report["strategy"]
    assert Decimal(result["ending_cash"]) == 1000
    assert result["ending_receivables"] == []
    assert Decimal(result["daily_equity"][-1]["daily_return"]) == 0
    payment = result["event_flows"][-1]
    assert payment["kind"] == "dividend_payment"
    assert payment["phase"] == "session_end"


def test_later_split_does_not_scale_an_existing_claim():
    result = run(bars([90, 100, 100, 99, 49.5]),
                 [dividend(), split(day="2024-06-07")])["benchmark"]
    assert Decimal(result["ending_quantity"]) == 20
    assert Decimal(result["ending_receivables_total"]) == 10
    assert Decimal(result["ending_equity"]) == 1000


def test_ten_for_one_split_then_postsplit_penny_dividend():
    report = run(bars([90, 100, 100, 10, 9.99]),
                 [split(new="10"), dividend(ex="2024-06-07", rate="0.01")])
    assert Decimal(report["benchmark"]["ending_receivables_total"]) == 1
    assert Decimal(report["benchmark"]["ending_equity"]) == 1000
    invalid = dividend(ex="2024-06-07", rate="0.1") | {"share_basis": "pre_split_shares"}
    with pytest.raises(ResearchValidationError, match="share basis"):
        run(bars([90, 100, 100, 10, 9.99]), [split(new="10"), invalid])


@pytest.mark.parametrize("ex", ["2024-05-01", "2024-06-03", "2024-06-04"])
def test_prestart_or_warmup_dividends_never_create_inherited_claim(ex):
    report = run(bars([90, 100, 100, 100]), [dividend(ex=ex, pay="2024-06-06")])
    for name in ("strategy", "benchmark"):
        assert report[name]["ending_receivables"] == []
        assert report[name]["event_flows"] == []
        assert Decimal(report[name]["ending_cash"]) == 0


@pytest.mark.parametrize("pay,expected_quantity,ending_cash,phase", [
    ("2024-06-07", "11.25", "0", "session_end"),
    ("2024-06-08", "11.25", "0", "before_open"),
    ("2024-06-10", "10", "100", "session_end"),
])
def test_pay_date_cash_availability_and_no_automatic_benchmark_reinvestment(
    pay, expected_quantity, ending_cash, phase,
):
    # Buy 10 at 100 Wed; accrue 100 Thu and exit at 80 Thu; Fri rebound
    # targets Monday entry. A Mon payable cannot fund Mon open; Fri/Sat can.
    supplied = bars([90, 100, 90, 80, 90, 80],
                    [90, 100, 100, 80, 90, 80], days=[0, 1, 2, 3, 4, 7])
    report = run(supplied, [dividend(pay=pay, rate="10")])
    result = report["strategy"]
    assert Decimal(result["ending_quantity"]) == Decimal(expected_quantity)
    assert Decimal(result["ending_cash"]) == Decimal(ending_cash)
    assert result["ending_receivables"] == []
    assert result["event_flows"][-1]["phase"] == phase
    assert Decimal(report["benchmark"]["ending_quantity"]) == 10
    assert Decimal(report["benchmark"]["ending_cash"]) == 100
    assert len(report["benchmark"]["trades"]) == 1


def test_prior_payment_split_and_pending_entry_order_is_supported():
    supplied = bars([90, 100, 90, 80, 90, 40],
                    [90, 100, 100, 80, 90, 40], days=[0, 1, 2, 3, 4, 7])
    result = run(supplied, [dividend(pay="2024-06-08", rate="10"),
                            split(day="2024-06-10")])["strategy"]
    assert Decimal(result["trades"][-1]["quantity"]) == Decimal("22.5")
    assert result["event_flows"][-2]["kind"] == "dividend_payment"
    assert result["event_flows"][-1]["kind"] == "split"


def test_fees_cash_retention_next_open_and_terminal_mark():
    # 1010 cash buys exactly 10 at 100 plus 10 entry fee; 100 dividend is
    # retained. A later sale at 80 credits 800-8 without losing dividend cash.
    supplied = bars([90, 100, 110, 90, 80], [90, 100, 100, 100, 80])
    report = run_event_backtest(supplied, StrategySpec(2, starting_cash=1010, cost_bps=100),
                               corporate_action_events=[dividend(pay="2024-06-06", rate="10")])
    result = report["strategy"]
    assert [Decimal(t["fee"]) for t in result["trades"]] == [10, 8]
    assert Decimal(result["ending_cash"]) == 892
    assert Decimal(result["total_fees"]) == 18
    assert result["trades"][0]["signal_session"] == "2024-06-04"
    assert result["trades"][0]["execution_session"] == "2024-06-05"
    assert Decimal(report["benchmark"]["ending_equity"]) == 900
    assert Decimal(report["benchmark"]["total_fees"]) == 10
    assert len(report["benchmark"]["trades"]) == 1


def test_first_scored_split_preserves_pending_entry_in_current_units():
    report = run(bars([90, 100, 50]), [split(day="2024-06-05")])
    assert Decimal(report["strategy"]["ending_quantity"]) == 20
    assert Decimal(report["strategy"]["ending_equity"]) == 1000


def test_split_scales_pending_exit_quantity_before_sale():
    result = run(bars([90, 100, 90, 45], [90, 100, 100, 45]), [split()])["strategy"]
    assert [t["side"] for t in result["trades"]] == ["buy", "sell"]
    assert Decimal(result["trades"][-1]["quantity"]) == 20
    assert Decimal(result["ending_cash"]) == 900


def test_pay_date_before_open_and_split_preserve_existing_holdings_and_claim_value():
    # Ex Thu, pay Sat, split Mon; retained claim is released before the split.
    supplied = bars([90, 100, 100, 100, 100, 50], days=[0, 1, 2, 3, 4, 7])
    report = run(supplied, [dividend(pay="2024-06-08"), split(day="2024-06-10")])
    for name in ("strategy", "benchmark"):
        result = report[name]
        assert Decimal(result["ending_cash"]) == 10
        assert Decimal(result["ending_quantity"]) == 20
        assert Decimal(result["ending_equity"]) == 1010
        assert result["event_flows"][-2]["kind"] == "dividend_payment"
        assert result["event_flows"][-1]["kind"] == "split"


def test_future_bars_and_actions_never_rewrite_prefix():
    prefix = bars([90, 100, 100, 99, 100])
    base = run(prefix, [dividend()])
    full = run(bars([90, 100, 100, 99, 100, 10, 11]),
               [dividend(), split(day="2024-06-08", new="10")])
    future_only = run(prefix, [dividend(), split(day="2025-06-08", new="10")])
    for name in ("strategy", "benchmark"):
        assert base[name] == future_only[name]
        assert base[name]["daily_equity"] == full[name]["daily_equity"][:3]
        assert base[name]["trades"] == [t for t in full[name]["trades"]
                                        if t["execution_session"] <= "2024-06-07"]
    assert base["corporate_actions_sha256"] != future_only["corporate_actions_sha256"]


def test_decimal_context_is_local_policy_is_actual_and_report_is_json():
    supplied = bars([1, 2, 3, 4])
    report = run(supplied, cost_bps=25)
    with localcontext() as caller:
        caller.prec = 6
        caller.rounding = ROUND_DOWN
        assert run(supplied, cost_bps=25) == report
        assert caller.prec == 6
    assert policy_identity()["decimal_precision"] == 34
    assert policy_identity()["decimal_rounding"] == "ROUND_HALF_EVEN"
    assert json.loads(json.dumps(report, allow_nan=False)) == report
    assert isinstance(report["strategy"]["total_return"], str)
    assert len(Decimal(report["strategy"]["trades"][0]["quantity"]).as_tuple().digits) == 34


def test_no_action_agrees_with_legacy_within_documented_float_tolerance():
    supplied, spec = bars([10, 12, 18, 6, 5]), StrategySpec(2, cost_bps=25)
    old = run_backtest(supplied, spec)
    new = run_event_backtest(supplied, spec)
    for name in ("strategy", "benchmark"):
        assert float(new[name]["ending_equity"]) == pytest.approx(getattr(old, name).ending_equity)


@pytest.mark.parametrize("event", [
    {"kind": "spinoff"}, {"kind": "merger"}, {},
    split(new="0"), split(old="-1"), split(new=2), split(new="NaN"),
    split(new="Infinity"), split(new=" 2"), split(new="1_0"),
    split(day="20240606"), split() | {"unknown": True},
    dividend(rate="0"), dividend(rate="NaN"), dividend() | {"currency": "EUR"},
    dividend() | {"share_basis": "unknown"}, dividend(pay="2024-06-05"),
    dividend() | {"payable_date": None}, split(identifier=""),
])
def test_malformed_or_unsupported_actions_refuse(event):
    with pytest.raises(ResearchValidationError):
        run(bars([90, 100, 100, 99, 100]), [event])


@pytest.mark.parametrize("rate", ["1e999999999", "1e-999999999", "1e101", "1e-101",
                                  "1" * 101, "0." + "1" * 99])
@pytest.mark.parametrize("field", ["new_rate", "old_rate", "rate"])
def test_unbounded_event_rates_refuse_before_fraction_conversion(rate, field):
    event = dividend() if field == "rate" else split()
    event[field] = rate
    with pytest.raises(ResearchValidationError, match="event rate"):
        run(bars([90, 100, 100, 99, 100]), [event])


@pytest.mark.parametrize("events", [
    [split(), split()], [split(), split(new="3")],
    [split(), split(identifier="different")], [split(), dividend()],
    [dividend(), dividend(rate="2", identifier="different")],
])
def test_duplicate_conflicting_and_simultaneous_actions_refuse(events):
    with pytest.raises(ResearchValidationError, match="duplicate|ambiguous"):
        run(bars([90, 100, 100, 99, 100]), events)


def test_missing_session_never_silently_shifts_effective_date():
    with pytest.raises(ResearchValidationError, match="missing from supplied sessions"):
        run(bars([90, 100, 100, 99], days=[0, 1, 2, 4]), [split()])
    supplied = bars([90, 100, 100])
    dates = [b.timestamp.date() for b in supplied]
    assert run_event_backtest(supplied, StrategySpec(2), expected_session_dates=dates)[
        "calendar_coverage"] == "caller_supplied_schedule_checked"
    with pytest.raises(ResearchValidationError, match="expected sessions"):
        run_event_backtest(supplied, StrategySpec(2), expected_session_dates=dates[:-1])


@pytest.mark.parametrize("options", [
    {"price_basis": "adjusted"}, {"price_basis": "mixed"},
    {"evidence_kind": "live_execution"}, {"evidence_kind": "prospective_paper"},
])
def test_unsupported_basis_or_evidence_refuses(options):
    with pytest.raises(ResearchValidationError):
        run_event_backtest(bars([1, 2, 3]), StrategySpec(2), **options)


def test_historical_label_passes_through_without_claiming_admission():
    report = run_event_backtest(bars([1, 2, 3]), StrategySpec(2),
                                evidence_kind="historical_market_data")
    assert report["evidence_kind"] == "historical_market_data"
    assert "does not certify admission" in report["limitations"][0]


def test_input_validation_duplicate_timezone_and_symbol():
    supplied = bars([90, 100, 100])
    for invalid in [supplied[:2] + supplied[1:], supplied[::-1],
                    supplied[:-1] + [replace(supplied[-1], symbol="OTHER")],
                    supplied[:-1] + [replace(supplied[-1], timestamp=
                     supplied[-1].timestamp.replace(tzinfo=timezone(timedelta(hours=-4))))]]:
        with pytest.raises(ResearchValidationError):
            run(invalid)
