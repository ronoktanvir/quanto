"""Run a hand-checkable split/dividend fixture without credentials or network.

The invented security enters at 100, splits two-for-one and pays 0.50 per
post-split share. With 1,000 initial cash and zero fees, both portfolios end
with 20 shares at 50 plus 10 cash: equity 1,010. This is software evidence.
"""
from datetime import datetime
import json
from zoneinfo import ZoneInfo

from quanto.event_engine import run_event_backtest
from quanto.research import Bar, StrategySpec


def main() -> None:
    values = [
        ("2024-01-02", 80), ("2024-01-03", 90), ("2024-01-04", 100),
        ("2024-01-05", 50), ("2024-01-08", 50), ("2024-01-09", 50),
    ]
    bars = [Bar(datetime.fromisoformat(day).replace(tzinfo=ZoneInfo("America/New_York")),
                "SYNTHETIC", price, price, price, price, 1000)
            for day, price in values]
    events = [
        {"kind": "split", "event_id": "fixture-split", "effective_date": "2024-01-05",
         "new_rate": "2", "old_rate": "1"},
        {"kind": "cash_dividend", "event_id": "fixture-dividend", "ex_date": "2024-01-08",
         "payable_date": "2024-01-09", "rate": "0.50", "currency": "USD",
         "share_basis": "ex_date_shares"},
    ]
    report = run_event_backtest(
        bars, StrategySpec(lookback=2, starting_cash=1000, cost_bps=0),
        corporate_action_events=events,
        expected_session_dates=[bar.timestamp.date() for bar in bars],
    )
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
