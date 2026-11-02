"""Exercise registered exploration without provider access or investment claims."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from quanto.explorer import register_dataset, run_submission
from quanto.provenance import Provenance


def run(root: Path) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    start = datetime(2024, 1, 1, 16, tzinfo=timezone.utc)
    prices = [100, 102, 104, 108, 107, 101, 98, 99, 103, 108, 110, 106]
    bars = [{"timestamp": (start + timedelta(days=i)).isoformat(),
             "symbol": "SYNTHETIC", "open": price, "high": price + 2,
             "low": price - 2, "close": price, "volume": 1000}
            for i, price in enumerate(prices)]
    with Provenance(root) as store:
        source = store.put_json({"evidence_kind": "synthetic_fixture", "bars": bars})
    registration = register_dataset(root, {
        "data_sha256": source, "evidence_kind": "synthetic_fixture", "price_basis": "raw",
        "market": {"instrument_id": "synthetic:common-window-example", "venue": "synthetic",
                   "currency": "USD", "session_timezone": "UTC"},
        "expected_sessions": [bar["timestamp"][:10] for bar in bars],
    })
    if registration["status"] != "success":
        return {"status": "failed", "registration": registration}
    request = {"dataset_sha256": registration["manifest_sha256"],
               "study_name": "common-window-example", "evaluation_start": "2024-01-05",
               "evaluation_end": "2024-01-12",
               "specification": {"lookback": 2, "starting_cash": 10000, "cost_bps": 10}}
    first = run_submission(root, request)
    second = run_submission(root, {**request, "specification": {
        **request["specification"], "lookback": 4,
    }})
    retry = run_submission(root, {**request, "study_name": "renamed-same-candidate"})
    invalid = run_submission(root, '{"malformed":')
    with Provenance(root) as store:
        event_chain = store.journal.verify_events()
    return {"status": "success" if all(item["status"] == "success"
                                       for item in (first, second, retry))
            and invalid["status"] == "invalid" else "failed",
            "evidence_kind": "synthetic_fixture", "investment_evidence": False,
            "evaluation_window": [request["evaluation_start"], request["evaluation_end"]],
            "registration": registration, "studies": [first, second, retry],
            "invalid_request": invalid, "event_chain": event_chain}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True,
                        help="Separate local directory for this synthetic example")
    result = run(parser.parse_args().root.resolve())
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "success" else 1)
