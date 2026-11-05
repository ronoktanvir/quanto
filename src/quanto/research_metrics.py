"""Bounded descriptive reductions of continuous DEVELOPMENT event-engine traces.

This module neither runs a strategy nor admits data. It checks consumed wealth,
return and trade fields, not the trading rule or corporate-action source truth.
All arithmetic uses a private Decimal context; output numbers are decimal strings.
No p-values, confidence bounds, annualized Sharpe or investment verdict is emitted.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Context, Decimal, DecimalException, ROUND_HALF_EVEN, localcontext
import re


MAX_ROWS = 10_000
MAX_BLOCKS = 10
MAX_CLAIMS = 100_000
_NUMBER = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\Z")
_NAME = re.compile(r"[A-Za-z][A-Za-z0-9 _-]{0,63}\Z")
_ZERO = Decimal(0)
_ONE = Decimal(1)
_YEAR = Decimal("365.2425")


class MetricsError(ValueError):
    """A fixed reason for refusing an invalid or unsupported trace."""


def _need(condition: bool, reason: str) -> None:
    if not condition:
        raise MetricsError(reason)


def _number(value: object, *, nonnegative: bool = False, positive: bool = False) -> Decimal:
    _need(type(value) is str and 0 < len(value) <= 120, "invalid_decimal")
    _need(_NUMBER.fullmatch(value) is not None, "invalid_decimal")
    number = Decimal(value)
    _need(number.is_finite() and (not number or -100 <= number.adjusted() <= 100),
          "decimal_out_of_bounds")
    _need(not nonnegative or number >= 0, "negative_value")
    _need(not positive or number > 0, "nonpositive_value")
    return number


def _text(value: Decimal) -> str:
    _need(value.is_finite(), "nonfinite_result")
    return str(value) if value else "0"


def _day(value: object) -> date:
    _need(type(value) is str and len(value) == 10, "invalid_session")
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise MetricsError("invalid_session") from None
    _need(parsed.isoformat() == value, "invalid_session")
    return parsed


def _timestamp(value: object, session: date) -> datetime:
    _need(type(value) is str and len(value) <= 40, "invalid_timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        raise MetricsError("invalid_timestamp") from None
    _need(parsed.utcoffset() is not None and parsed.date() == session, "invalid_timestamp")
    return parsed


def _claims(value: object, *, remaining: int, first_seen: dict) -> tuple[Decimal, int]:
    _need(type(value) is list and len(value) <= remaining, "claims_limit_or_shape")
    amounts = []
    identifiers = set()
    added = 0
    for claim in value:
        _need(type(claim) is dict and set(claim) == {"event_id", "payable_date", "amount"},
              "invalid_claim")
        identity = claim["event_id"]
        _need(type(identity) is str and 0 < len(identity) <= 256 and identity not in identifiers,
              "invalid_claim")
        identifiers.add(identity)
        _day(claim["payable_date"])
        nominal = _number(claim["amount"], positive=True)
        if identity not in first_seen:
            first_seen[identity] = (len(first_seen), nominal, claim["payable_date"])
            added += 1
        ordinal, original, payable = first_seen[identity]
        _need(nominal == original and claim["payable_date"] == payable, "claim_changed")
        amounts.append((ordinal, nominal))
    # The engine accrues at most one action per session, sums claims in accrual
    # order, but serializes them in ID order. Restore that order before rounding.
    _need(added <= 1, "unsupported_claim_onset")
    return sum((nominal for _, nominal in sorted(amounts)), _ZERO), len(value)


def _portfolio(value: object, *, cash: Decimal, cost: Decimal) -> dict:
    _need(type(value) is dict, "invalid_portfolio")
    rows, trades = value["daily_equity"], value["trades"]
    _need(type(rows) is list and 1 <= len(rows) <= MAX_ROWS, "row_limit_or_shape")
    _need(type(trades) is list and len(trades) <= len(rows), "trade_limit_or_shape")
    _need(_number(value["starting_cash"], positive=True) == cash
          and _number(value["starting_equity"], positive=True) == cash
          and _number(value["starting_quantity"], nonnegative=True) == 0
          and value["starting_receivables"] == [], "invalid_initial_wealth")
    parsed = []
    previous, peak, drawdown = cash, cash, _ZERO
    claims_seen = 0
    claim_order = {}
    for row in rows:
        _need(type(row) is dict, "invalid_row")
        session = _day(row["session"])
        stamp = _timestamp(row["timestamp"], session)
        if parsed:
            _need(session > parsed[-1]["session"] and stamp > parsed[-1]["timestamp"],
                  "nonmonotonic_sessions")
        cash_now = _number(row["cash"], nonnegative=True)
        quantity = _number(row["quantity"], nonnegative=True)
        close = _number(row["close"], positive=True)
        receivables = _number(row["receivables_total"], nonnegative=True)
        claims, count = _claims(row["receivables"], remaining=MAX_CLAIMS - claims_seen,
                               first_seen=claim_order)
        claims_seen += count
        _need(claims == receivables, "receivables_mismatch")
        equity = _number(row["equity"], positive=True)
        _need(cash_now + quantity * close + receivables == equity, "wealth_components_mismatch")
        daily_return = _number(row["daily_return"])
        _need(daily_return == equity / previous - 1, "return_continuity_mismatch")
        _need(row["signal"] in ("long", "cash"), "invalid_signal")
        peak = max(peak, equity)
        drawdown = max(drawdown, (peak - equity) / peak)
        parsed.append({"session": session, "timestamp": stamp, "timestamp_text": row["timestamp"],
                       "cash": cash_now, "quantity": quantity, "close": close,
                       "receivables": receivables, "equity": equity, "return": daily_return})
        previous = equity
    sessions = {row["session"] for row in parsed}
    parsed_trades = []
    fees = _ZERO
    for trade in trades:
        _need(type(trade) is dict, "invalid_trade")
        session = _day(trade["execution_session"])
        _need(session in sessions and (not parsed_trades or session > parsed_trades[-1]["session"]),
              "invalid_trade_session")
        _need(trade["side"] in ("buy", "sell") and trade["execution_price_point"] == "open",
              "unsupported_trade")
        signal = trade["signal_session"]
        _need(signal is None or _day(signal) < session, "invalid_signal_session")
        quantity = _number(trade["quantity"], positive=True)
        price = _number(trade["price"], positive=True)
        gross = _number(trade["gross"], positive=True)
        fee = _number(trade["fee"], nonnegative=True)
        before = _number(trade["cash_before"], nonnegative=True)
        after = _number(trade["cash_after"], nonnegative=True)
        residual = _number(trade["rounding_residual"])
        _need(gross == quantity * price and fee == gross * cost, "trade_arithmetic_mismatch")
        if trade["side"] == "buy":
            _need(after == 0 and quantity == before / (price * (1 + cost))
                  and residual == before - (gross + fee), "trade_cash_mismatch")
        else:
            _need(after == before + gross - fee and residual == 0, "trade_cash_mismatch")
        fees += fee
        parsed_trades.append({"session": session, "side": trade["side"], "fee": fee,
                              "gross": gross})
    _need(_number(value["ending_equity"], positive=True) == previous
          and _number(value["total_return"]) == previous / cash - 1
          and _number(value["total_fees"], nonnegative=True) == fees
          and _number(value["max_drawdown"], nonnegative=True) == drawdown,
          "portfolio_totals_mismatch")
    last = parsed[-1]
    _need(_number(value["ending_cash"], nonnegative=True) == last["cash"]
          and _number(value["ending_quantity"], nonnegative=True) == last["quantity"]
          and _number(value["ending_receivables_total"], nonnegative=True) == last["receivables"]
          and value["ending_receivables"] == rows[-1]["receivables"], "ending_components_mismatch")
    return {"cash": cash, "rows": parsed, "trades": parsed_trades}


def _metrics(portfolio: dict, start: int, end: int, days: int) -> dict:
    rows = portfolio["rows"][start:end + 1]
    initial = portfolio["cash"] if start == 0 else portfolio["rows"][start - 1]["equity"]
    count = Decimal(len(rows))
    mean = sum((row["return"] for row in rows), _ZERO) / count
    standard_deviation = None
    std_reason = "fewer_than_two_observations"
    if len(rows) >= 2:
        variance = sum(((row["return"] - mean) ** 2 for row in rows), _ZERO) / (count - 1)
        standard_deviation = variance.sqrt()
        std_reason = None
    sharpe = None
    sharpe_reason = std_reason or "zero_sample_variance"
    if standard_deviation:
        sharpe = mean / standard_deviation
        sharpe_reason = None
    peak, drawdown = initial, _ZERO
    for row in rows:
        peak = max(peak, row["equity"])
        drawdown = max(drawdown, (peak - row["equity"]) / peak)
    ratio = rows[-1]["equity"] / initial
    cagr = ratio ** (_YEAR / Decimal(days)) - 1 if days >= 365 else None
    trades = [trade for trade in portfolio["trades"]
              if rows[0]["session"] <= trade["session"] <= rows[-1]["session"]]
    held = sum(row["quantity"] > 0 for row in rows)
    return {
        "boundary_equity": _text(initial), "ending_equity": _text(rows[-1]["equity"]),
        "total_return": _text(ratio - 1),
        "cagr": _text(cagr) if cagr is not None else None,
        "cagr_reason": None if cagr is not None else "fewer_than_365_calendar_days",
        "mean_daily_return": _text(mean),
        "sample_std_daily_return": _text(standard_deviation) if standard_deviation is not None else None,
        "sample_std_reason": std_reason,
        "daily_sharpe_zero_rate": _text(sharpe) if sharpe is not None else None,
        "daily_sharpe_reason": sharpe_reason,
        "max_drawdown": _text(drawdown),
        "mean_cash_weight": _text(sum((row["cash"] / row["equity"] for row in rows), _ZERO) / count),
        "mean_position_weight": _text(sum((row["quantity"] * row["close"] / row["equity"]
                                          for row in rows), _ZERO) / count),
        "mean_receivables_weight": _text(sum((row["receivables"] / row["equity"]
                                             for row in rows), _ZERO) / count),
        "held_position_sessions": held, "position_session_fraction": _text(Decimal(held) / count),
        "trade_count": len(trades), "buy_count": sum(t["side"] == "buy" for t in trades),
        "sell_count": sum(t["side"] == "sell" for t in trades),
        "total_fees": _text(sum((trade["fee"] for trade in trades), _ZERO)),
        "traded_notional": _text(sum((trade["gross"] for trade in trades), _ZERO)),
    }


def _block(name: str, start: int, end: int, strategy: dict, benchmark: dict) -> dict:
    rows = strategy["rows"][start:end + 1]
    days = (rows[-1]["session"] - rows[0]["session"]).days + 1
    paired = sum((strategy["rows"][i]["return"] - benchmark["rows"][i]["return"]
                  for i in range(start, end + 1)), _ZERO) / Decimal(len(rows))
    return {
        "name": name, "start": rows[0]["session"].isoformat(),
        "end": rows[-1]["session"].isoformat(), "observations": len(rows),
        "calendar_days": days, "strategy": _metrics(strategy, start, end, days),
        "benchmark": _metrics(benchmark, start, end, days),
        "paired_mean_daily_return_difference": _text(paired),
    }


def summarize_trace(report: dict, blocks: list[dict]) -> dict:
    """Summarize one event-engine trace without restarting its portfolios.

    Blocks are ordered, nonoverlapping, inclusive recorded-session boundaries,
    with unique bounded names. The first trace row uses starting cash; every later
    block uses the preceding row's equity, including weekend gaps. CAGR uses the
    explicitly labeled inclusive calendar-day proxy, not observed execution times.
    Undefined sample statistics carry a reason. Unknown or inconsistent input fails.
    """
    try:
        with localcontext(Context(prec=34, rounding=ROUND_HALF_EVEN)):
            _need(type(report) is dict, "invalid_report")
            _need(report["evidence_kind"] in ("synthetic_fixture", "historical_market_data")
                  and report["holdout_status"] == "unprotected_development", "unsupported_evidence")
            policy = report["accounting_policy"]
            _need(type(policy) is dict and policy["version"] == "D006-raw-events-v1"
                  and policy["decimal_precision"] == 34
                  and policy["decimal_rounding"] == "ROUND_HALF_EVEN", "unsupported_accounting")
            specification = report["specification"]
            _need(type(specification) is dict, "invalid_specification")
            cash = _number(specification["starting_cash"], positive=True)
            cost = _number(specification["cost_bps"], nonnegative=True) / Decimal(10_000)
            _need(cost < 1, "unsupported_cost")
            strategy = _portfolio(report["strategy"], cash=cash, cost=cost)
            benchmark = _portfolio(report["benchmark"], cash=cash, cost=cost)
            rows, comparison = strategy["rows"], benchmark["rows"]
            _need(len(rows) == len(comparison) and all(
                a["session"] == b["session"] and a["timestamp_text"] == b["timestamp_text"]
                and a["close"] == b["close"] for a, b in zip(rows, comparison)),
                "portfolio_alignment_mismatch")
            _need(_day(report["evaluation_start"]) == rows[0]["session"]
                  and _day(report["evaluation_end"]) == rows[-1]["session"], "evaluation_bounds_mismatch")
            _need(type(blocks) is list and len(blocks) <= MAX_BLOCKS, "block_limit_or_shape")
            index = {row["session"]: i for i, row in enumerate(rows)}
            intervals, names, previous_end = [], set(), -1
            for block in blocks:
                _need(type(block) is dict and set(block) == {"name", "start", "end"}, "invalid_block")
                name = block["name"]
                _need(type(name) is str and _NAME.fullmatch(name) is not None
                      and name not in names and name != "full", "invalid_block_name")
                first, last = _day(block["start"]), _day(block["end"])
                _need(first in index and last in index, "block_session_missing")
                left, right = index[first], index[last]
                _need(previous_end < left <= right, "block_order_or_overlap")
                names.add(name)
                intervals.append((name, left, right))
                previous_end = right
            return {
                "schema": "development_trace_metrics_v1", "evidence_kind": report["evidence_kind"],
                "holdout_status": "unprotected_development",
                "interpretation": "descriptive_development_only",
                "conventions": {
                    "arithmetic": "Decimal precision 34, ROUND_HALF_EVEN; numbers encoded as strings",
                    "cagr": "ACT/365.2425 calendar-label proxy: (end-start).days+1; no execution instants",
                    "annualization_floor": "365 inclusive calendar days; not a sample-adequacy claim",
                    "sharpe": "unannualized sample mean / sample standard deviation; zero reference rate",
                    "exposure": "equal-weight mean of closing cash, marked position and receivables / equity",
                    "boundary": "preceding recorded equity, or starting cash at first scored session",
                    "scope": "consumed scalar/accounting fields checked; not strategy replay or data admission",
                },
                "full": _block("full", 0, len(rows) - 1, strategy, benchmark),
                "blocks": [_block(name, left, right, strategy, benchmark)
                           for name, left, right in intervals],
            }
    except MetricsError:
        raise
    except (KeyError, TypeError, ValueError, DecimalException, OverflowError):
        raise MetricsError("invalid_trace") from None
