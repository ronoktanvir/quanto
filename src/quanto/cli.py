"""Operator entry points; every action is explicit and local unless named otherwise."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys

from quanto.ledger import Journal, LedgerError, canonical_json, hash_bytes


def run_demo(root: Path) -> dict:
    """Exercise real calculation/persistence code on explicitly synthetic prices."""
    from quanto.research import Bar, StrategySpec, run_backtest

    runtime = root / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    spec = StrategySpec(lookback=3, starting_cash=10_000, cost_bps=10)
    prices = [100, 102, 104, 108, 107, 101, 98, 99, 103, 108, 110, 106]
    start = datetime(2024, 1, 1, 16, tzinfo=timezone.utc)
    bars = [Bar(start + timedelta(days=i), "SYNTHETIC", float(p), float(p + 2),
                float(p - 2), float(p), 1000.0) for i, p in enumerate(prices)]
    source = Path(__file__).with_name("research.py").read_bytes()
    data = [{**asdict(bar), "timestamp": bar.timestamp.isoformat()} for bar in bars]
    with Journal(runtime / "research.sqlite") as journal:
        fingerprint = journal.register_experiment(asdict(spec), {"synthetic_bars": data},
            {"research_source_sha256": hash_bytes(source)}, "synthetic_fixture",
            assumptions={"calendar": "synthetic consecutive dates, not an exchange calendar"})
        attempt = journal.start_attempt(fingerprint)
        try:
            report = run_backtest(bars, spec).to_dict()
            encoded = canonical_json(report).encode("utf-8")
            digest = hash_bytes(encoded)
            directory = root / "artifacts" / "synthetic"
            directory.mkdir(parents=True, exist_ok=True)
            path = directory / f"{digest}.json"
            if path.exists() and path.read_bytes() != encoded:
                raise LedgerError("Existing artifact does not match its content identity")
            if not path.exists():
                temporary = path.with_suffix(".tmp")
                temporary.write_bytes(encoded)
                temporary.replace(path)
            journal.finish_attempt(attempt, "success", {
                "artifact_sha256": digest, "artifact_path": str(path.relative_to(root)),
                "evidence_kind": "synthetic_fixture", "investment_evidence": False})
        except Exception as exc:
            journal.finish_attempt(attempt, "failed", {"error_type": type(exc).__name__})
            raise
        return {"attempt_id": attempt, "experiment": fingerprint,
                "evidence_kind": "synthetic_fixture", "investment_evidence": False,
                "artifact_path": str(path), "artifact_sha256": digest,
                "strategy_ending_equity": report["strategy"]["ending_equity"],
                "event_chain": journal.verify_events()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Quanto local research desk")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Project/runtime root")
    sub = parser.add_subparsers(dest="command", required=True)
    server = sub.add_parser("serve", help="Open a read-only localhost dashboard")
    server.add_argument("--port", type=int, default=8765)
    sub.add_parser("demo", help="Run a synthetic engineering fixture and record evidence")
    sub.add_parser("status", help="Inspect persisted research and budget records")
    review = sub.add_parser("review", help="Request one paid Opus critique under the daily cap")
    review.add_argument("--packet", type=Path, required=True, help="Sanitized review text file")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "serve":
            from quanto.dashboard import serve
            serve(root, port=args.port)
            return 0
        if args.command == "demo":
            output = run_demo(root)
        elif args.command == "review":
            from quanto.critic import request_review
            output = request_review(root, args.packet.read_text())
            output = {key: value for key, value in output.items() if key != "text"}
        else:
            database = root / "runtime" / "research.sqlite"
            if not database.exists():
                output = {"status": "not_initialized", "message": "No research journal exists yet."}
            else:
                with Journal(database) as journal:
                    output = journal.overview()
        print(json.dumps(output, indent=2, allow_nan=False))
        return 0
    except (ValueError, OSError) as exc:
        print(f"Quanto: {exc}", file=sys.stderr)
        return 1
