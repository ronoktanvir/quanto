"""Pure D006 raw-price accounting; admission and source judgment live elsewhere.

Signals use exact rationals of the normalized inputs. Portfolio operations use
the local Decimal policy returned by policy_identity(), never caller context.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import date
from decimal import (
    Context, Decimal, DecimalException, DivisionByZero, InvalidOperation,
    Overflow, ROUND_HALF_EVEN, Underflow, localcontext,
)
from fractions import Fraction
import re
from typing import Any, Sequence

from .research import (
    Bar, InsufficientDataError, ResearchValidationError, StrategySpec,
    _identity, _same_session_timezone,
)


def policy_identity() -> dict[str, Any]:
    """Actual numerical and ordering policy, suitable for code/spec identity."""
    context = _context()
    return {
        "version": "D006-raw-events-v1",
        "signal_arithmetic": "Fraction(str(validated_normalized_price)); exact split ratios",
        "signal_rule": "current close in rolling SMA; strict levels; equality retains holding",
        "price_normalization": "Bar int/float inputs; source precision already may be lost",
        "decimal_precision": context.prec,
        "decimal_rounding": context.rounding,
        "decimal_Emin": context.Emin,
        "decimal_Emax": context.Emax,
        "decimal_clamp": context.clamp,
        "decimal_traps": sorted(trap.__name__ for trap, active in context.traps.items() if active),
        "event_rate_max_characters": 100,
        "event_rate_max_absolute_adjusted_exponent": 100,
        "session_order": [
            "release claims payable before session", "apply effective split",
            "accrue ex-date claims on pretrade shares", "fill prior completed-session target",
            "release claims payable this session at modeled end",
            "mark raw close plus cash plus nominal claims", "form next target",
        ],
        "buy_quantity": "cash / (raw_open * (1 + cost_bps / 10000))",
        "buy_cash": "all cash allocated; signed Decimal rounding residual disclosed per trade",
        "sale_cash": "existing cash + quantity * raw_open - fee",
        "split_quantity": "quantity * new_rate / old_rate (left to right Decimal operations)",
        "dividend_claim": "pretrade quantity * USD rate per ex_date_shares",
        "warmup": "exactly first lookback sessions; no inherited position or claims",
        "benchmark": "buy once at first scored open; cash dividends never redeployed",
        "terminal": "mark final close including unpaid nominal claims; no liquidation or fee",
        "simultaneous_actions": "reject multiple effective/ex-date actions on same supplied session",
        "fractional_shares": "retained; no cash-in-lieu or broker rounding",
        "settlement": "sale proceeds immediately available; no cash-account compliance claim",
    }


def _context() -> Context:
    return Context(
        prec=34, rounding=ROUND_HALF_EVEN, Emin=-999999, Emax=999999,
        capitals=1, clamp=0, flags=[],
        traps=[InvalidOperation, DivisionByZero, Overflow, Underflow],
    )


def _decimal(value: int | float | str) -> Decimal:
    return Decimal(str(value))


def _text(value: Decimal) -> str:
    if not value.is_finite():
        raise ResearchValidationError("nonfinite derived accounting amount")
    return str(value) if value else "0"


def _date(value: Any) -> date:
    if not isinstance(value, str):
        raise ResearchValidationError("event dates must be ISO date strings")
    try:
        result = date.fromisoformat(value)
    except ValueError as exc:
        raise ResearchValidationError("event dates must be ISO date strings") from exc
    if result.isoformat() != value:
        raise ResearchValidationError("event dates must be ISO date strings")
    return result


def _rate(value: Any) -> Decimal:
    if not isinstance(value, str) or len(value) > 100 or not re.fullmatch(
        r"[+]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?", value
    ):
        raise ResearchValidationError("event rates must be positive decimal strings")
    number = Decimal(value)
    if not number.is_finite() or number <= 0:
        raise ResearchValidationError("event rates must be positive decimal strings")
    if abs(number.adjusted()) > 100:
        raise ResearchValidationError("event rate outside supported numerical range")
    return number


def _events(
    supplied: Sequence[dict[str, Any]], sessions: tuple[date, ...],
) -> tuple[dict[str, Any], ...]:
    events, identifiers, economic_terms = [], set(), set()
    selected_dates: dict[date, set[str]] = {}
    for event in supplied:
        if not isinstance(event, dict):
            raise ResearchValidationError("corporate actions must be canonical dictionaries")
        kind = event.get("kind")
        if kind == "split":
            keys = {"kind", "event_id", "effective_date", "new_rate", "old_rate"}
            if set(event) != keys:
                raise ResearchValidationError("malformed split event")
            effective = _date(event["effective_date"])
            new, old = _rate(event["new_rate"]), _rate(event["old_rate"])
            terms = (kind, effective, Fraction(new) / Fraction(old))
        elif kind == "cash_dividend":
            keys = {"kind", "event_id", "ex_date", "payable_date", "rate",
                    "currency", "share_basis"}
            if set(event) != keys:
                raise ResearchValidationError("malformed cash dividend event")
            effective, payable = _date(event["ex_date"]), _date(event["payable_date"])
            rate = _rate(event["rate"])
            if event["currency"] != "USD" or event["share_basis"] != "ex_date_shares":
                raise ResearchValidationError("dividend currency or share basis unsupported")
            if payable < effective:
                raise ResearchValidationError("pay-before-ex or due-bill dividends unsupported")
            terms = (kind, effective, payable, rate)
        else:
            raise ResearchValidationError("unsupported corporate action kind")
        identifier = event["event_id"]
        if not isinstance(identifier, str) or not identifier.strip():
            raise ResearchValidationError("event_id must be a nonempty string")
        if identifier in identifiers or terms in economic_terms:
            raise ResearchValidationError("duplicate or ambiguous corporate action")
        identifiers.add(identifier)
        economic_terms.add(terms)
        if sessions[0] <= effective <= sessions[-1]:
            if effective not in sessions:
                raise ResearchValidationError("effective or ex-date missing from supplied sessions")
            kinds = selected_dates.setdefault(effective, set())
            if kinds:
                # Multiple independently identified distributions require a wider
                # contract; never guess whether they describe the same event.
                raise ResearchValidationError("ambiguous simultaneous corporate actions")
            kinds.add(kind)
        events.append(dict(event))
    return tuple(sorted(events, key=lambda e: (
        e.get("effective_date", e.get("ex_date")), e["event_id"]
    )))


def _target(prices: list[Fraction], spec: StrategySpec, holding: bool) -> bool:
    mean = sum(prices, Fraction()) / spec.lookback
    if prices[-1] > mean * (1 + Fraction(str(spec.entry_threshold))):
        return True
    if prices[-1] < mean * (1 - Fraction(str(spec.exit_threshold))):
        return False
    return holding


def _simulate(
    bars: tuple[Bar, ...], spec: StrategySpec, actions: tuple[dict[str, Any], ...],
    *, benchmark: bool,
) -> dict[str, Any]:
    cash, quantity = _decimal(spec.starting_cash), Decimal(0)
    previous_equity = peak = cash
    drawdown = fees = Decimal(0)
    fee_rate = _decimal(spec.cost_bps) / Decimal(10000)
    claims: dict[str, dict[str, Any]] = {}
    flows, trades, daily = [], [], []
    prices: list[Fraction] = []
    desired = benchmark
    initial_signal = None
    by_date = {e.get("effective_date", e.get("ex_date")): e for e in actions}

    def claim_values() -> list[dict[str, str]]:
        return [
            {"event_id": identifier, "payable_date": claim["payable_date"],
             "amount": _text(claim["amount"])}
            for identifier, claim in sorted(claims.items())
        ]

    def release(session: str, *, at_end: bool) -> None:
        nonlocal cash
        for identifier, claim in list(claims.items()):
            due = claim["payable_date"]
            if (due == session) if at_end else (due < session):
                cash += claim["amount"]
                flows.append({
                    "session": session, "event_id": identifier, "kind": "dividend_payment",
                    "phase": "session_end" if at_end else "before_open",
                    "payable_date": due, "amount": _text(claim["amount"]),
                    "cash_after": _text(cash),
                })
                del claims[identifier]

    for index, bar in enumerate(bars):
        session = bar.timestamp.date().isoformat()
        action = by_date.get(session)
        scoring = index >= spec.lookback
        if scoring:
            release(session, at_end=False)
        if action and action["kind"] == "split":
            new, old = _decimal(action["new_rate"]), _decimal(action["old_rate"])
            ratio = Fraction(new) / Fraction(old)
            prices = [price / ratio for price in prices]
            if scoring:
                before = quantity
                quantity = quantity * new / old
                if before > 0 and quantity <= 0:
                    raise ResearchValidationError("split quantity underflow")
                flows.append({
                    "session": session, "event_id": action["event_id"], "kind": "split",
                    "quantity_before": _text(before), "quantity_after": _text(quantity),
                    "new_rate": action["new_rate"], "old_rate": action["old_rate"],
                })
        if scoring and action and action["kind"] == "cash_dividend":
            amount = quantity * _decimal(action["rate"])
            if amount:
                claims[action["event_id"]] = {
                    "payable_date": action["payable_date"], "amount": amount,
                }
            flows.append({
                "session": session, "event_id": action["event_id"],
                "kind": "dividend_accrual", "entitled_quantity": _text(quantity),
                "rate": action["rate"], "amount": _text(amount),
                "payable_date": action["payable_date"], "share_basis": "ex_date_shares",
            })
        if scoring:
            price = _decimal(bar.open)
            if desired and not quantity and (not benchmark or index == spec.lookback):
                if cash <= 0:
                    raise ResearchValidationError("entry requires positive cash")
                cash_before = cash
                quantity = cash / (price * (1 + fee_rate))
                if quantity <= 0:
                    raise ResearchValidationError("entry quantity underflow")
                gross = quantity * price
                fee = gross * fee_rate
                residual = cash - (gross + fee)
                cash = Decimal(0)
                trades.append({
                    "execution_session": session, "signal_session": None if benchmark else
                    bars[index - 1].timestamp.date().isoformat(), "side": "buy",
                    "quantity": _text(quantity), "price": _text(price), "fee": _text(fee),
                    "gross": _text(gross), "cash_before": _text(cash_before),
                    "cash_after": "0", "rounding_residual": _text(residual),
                    "execution_price_point": "open",
                })
                fees += fee
            elif not desired and quantity:
                gross = quantity * price
                fee = gross * fee_rate
                cash_before = cash
                cash += gross - fee
                trades.append({
                    "execution_session": session, "signal_session":
                    bars[index - 1].timestamp.date().isoformat(), "side": "sell",
                    "quantity": _text(quantity), "price": _text(price), "fee": _text(fee),
                    "gross": _text(gross), "cash_before": _text(cash_before),
                    "cash_after": _text(cash), "rounding_residual": "0",
                    "execution_price_point": "open",
                })
                quantity = Decimal(0)
                fees += fee
            release(session, at_end=True)
            receivables = sum((claim["amount"] for claim in claims.values()), Decimal(0))
            equity = cash + quantity * _decimal(bar.close) + receivables
            if equity <= 0:
                raise ResearchValidationError("nonpositive equity prevents return calculation")
            daily_return = equity / previous_equity - 1
            peak = max(peak, equity)
            drawdown = max(drawdown, (peak - equity) / peak)
        prices.append(Fraction(str(bar.close)))
        prices = prices[-spec.lookback:]
        if len(prices) == spec.lookback:
            desired = benchmark or _target(prices, spec, bool(quantity))
            if not scoring:
                initial_signal = "long" if desired else "cash"
        if scoring:
            daily.append({
                "timestamp": bar.timestamp.isoformat(), "session": session,
                "cash": _text(cash), "quantity": _text(quantity), "close": str(bar.close),
                "receivables": claim_values(), "receivables_total": _text(receivables),
                "equity": _text(equity), "daily_return": _text(daily_return),
                "signal": "long" if desired else "cash",
            })
            previous_equity = equity
    return {
        "starting_equity": str(spec.starting_cash), "starting_cash": str(spec.starting_cash),
        "starting_quantity": "0", "starting_receivables": [],
        "initial_signal": initial_signal, "daily_equity": daily, "trades": trades,
        "event_flows": flows, "total_return": _text(previous_equity / _decimal(
            spec.starting_cash) - 1), "max_drawdown": _text(drawdown),
        "total_fees": _text(fees), "ending_equity": _text(previous_equity),
        "ending_cash": _text(cash), "ending_quantity": _text(quantity),
        "ending_receivables": claim_values(), "ending_receivables_total": _text(receivables),
    }


def run_event_backtest(
    bars: Sequence[Bar], spec: StrategySpec, *,
    corporate_action_events: Sequence[dict[str, Any]] = (),
    expected_session_dates: Sequence[date] | None = None,
    evidence_kind: str = "synthetic_fixture", price_basis: str = "raw",
) -> dict[str, Any]:
    """Calculate supplied inputs; this pure function does not grant admission.

    First lookback bars warm up signals only. The registered study must supply
    the exact chosen warmup/evaluation slice and independently checked calendar.
    """
    if not isinstance(spec, StrategySpec):
        raise ResearchValidationError("spec must be StrategySpec")
    spec.__post_init__()
    if evidence_kind not in {"synthetic_fixture", "historical_market_data"}:
        raise ResearchValidationError("unsupported backtest evidence kind")
    if price_basis != "raw":
        raise ResearchValidationError("adjusted or mixed price treatment is unsupported")
    supplied = tuple(bars)
    if any(not isinstance(bar, Bar) for bar in supplied):
        raise ResearchValidationError("bars must contain Bar instances")
    if len(supplied) <= spec.lookback:
        raise InsufficientDataError("need lookback warmup plus evaluation sessions")
    sessions = tuple(bar.timestamp.date() for bar in supplied)
    for index, bar in enumerate(supplied):
        bar.__post_init__()
        if bar.symbol != supplied[0].symbol:
            raise ResearchValidationError("mixed symbols are unsupported")
        if not _same_session_timezone(supplied[0].timestamp, bar.timestamp):
            raise ResearchValidationError("inconsistent exchange session timezone")
        if index and (bar.timestamp <= supplied[index - 1].timestamp
                      or sessions[index] <= sessions[index - 1]):
            raise ResearchValidationError("sessions and timestamps must be unique and increasing")
    if expected_session_dates is not None:
        expected = tuple(expected_session_dates)
        if any(type(session) is not date for session in expected) or expected != sessions:
            raise ResearchValidationError("supplied bars do not exactly match expected sessions")
    try:
        with localcontext(_context()):
            actions = _events(corporate_action_events, sessions)
            strategy = _simulate(supplied, spec, actions, benchmark=False)
            benchmark = _simulate(supplied, spec, actions, benchmark=True)
    except DecimalException as exc:
        raise ResearchValidationError("unsupported numerical range in event accounting") from exc
    return {
        "evidence_kind": evidence_kind, "symbol": supplied[0].symbol,
        "specification": {key: value if key == "lookback" else str(value)
                          for key, value in asdict(spec).items()},
        "data_sha256": _identity([asdict(bar) for bar in supplied]),
        "specification_sha256": _identity(asdict(spec)),
        "corporate_actions_sha256": _identity(actions),
        "accounting_policy": policy_identity(), "accounting_policy_sha256": _identity(
            policy_identity()), "warmup_sessions": [s.isoformat() for s in sessions[:spec.lookback]],
        "evaluation_start": sessions[spec.lookback].isoformat(),
        "evaluation_end": sessions[-1].isoformat(),
        "calendar_coverage": "caller_supplied_schedule_checked" if expected_session_dates is not None
        else "unverified", "timing": "session_level_open; exact_availability_unverified",
        "holdout_status": "unprotected_development", "strategy": strategy, "benchmark": benchmark,
        "assumptions": [
            "Raw next-open fills; fixed per-fill fee scenario, no terminal liquidation.",
            "Ordinary USD claims use ex-date shares and nominal value until modeled payment.",
            "Dividends remain cash while held; benchmark never redeploys dividend cash.",
            "Fractional shares; no cash-in-lieu; sale proceeds immediately available.",
        ],
        "limitations": [
            "Pure calculation does not certify admission, source rights or action completeness.",
            "Normalized int/float prices may already have lost source decimal precision.",
            "No broker credit, liquidity, spread, impact, tax, interest or execution guarantee.",
            "Synthetic fixtures validate software; historical calculations do not establish an edge.",
        ],
    }
