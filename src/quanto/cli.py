"""Operator entry points; every action is explicit and local unless named otherwise."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import stat
import sys

from quanto.ledger import Journal, LedgerError, canonical_json, hash_bytes


def _request_text(path: Path) -> str:
    """Read a bounded local JSON envelope; parsing follows submission recording."""
    from quanto.provenance import MAX_REQUEST_BYTES

    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_REQUEST_BYTES:
            raise ValueError("Request must be a regular file of at most 64 KiB")
        with os.fdopen(descriptor, "rb") as source:
            descriptor = None
            raw = source.read(MAX_REQUEST_BYTES + 1)
        if len(raw) > MAX_REQUEST_BYTES:
            raise ValueError("Request exceeds the 64 KiB preflight boundary")
        return raw.decode("utf-8")
    finally:
        if descriptor is not None:
            os.close(descriptor)


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
    server = sub.add_parser("serve", help="Open the local operator dashboard")
    server.add_argument("--port", type=int, default=8765)
    sub.add_parser("demo", help="Run a synthetic engineering fixture and record evidence")
    sub.add_parser("status", help="Inspect persisted research and budget records")
    review = sub.add_parser("review", help="Request one paid Opus critique under the daily cap")
    review.add_argument("--packet", type=Path, required=True, help="Sanitized review text file")
    for name, description in (
        ("acquire-bars", "Acquire private historical Alpaca bars for data inspection"),
        ("acquire-calendar", "Acquire the paper-account session calendar"),
        ("acquire-actions", "Acquire private corporate-action observations for inspection"),
        ("register-dataset", "Register exact dataset bytes and their declared scope"),
        ("admit-dataset", "Check evidence for retrospective historical development research"),
        ("register-split-review", "Record an independent review of exact split evidence"),
        ("register-policy-revision", "Preserve and validate post-acquisition policy lineage"),
        ("register-suite", "Register all three cost scenarios before calculation"),
        ("run-suite", "Execute a complete registered scenario roster once"),
        ("run-research", "Run one bounded model-role workflow under the daily cap; no trades"),
        ("explore", "Record and execute an eligible exploratory study"),
    ):
        command = sub.add_parser(name, help=description)
        command.add_argument("--request", type=Path, required=True,
                             help="Local JSON request; credentials belong only in .env")
    submissions = sub.add_parser("submissions", help="Inspect recorded work and failed submissions")
    submissions.add_argument("--kind")
    submissions.add_argument("--status", choices=("pending", "success", "invalid", "failed",
                                                  "interrupted"))
    submissions.add_argument("--limit", type=int, default=20)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    authority = None
    try:
        guarded = {"acquire-bars", "acquire-calendar", "acquire-actions", "register-dataset",
                   "admit-dataset", "register-split-review", "register-policy-revision",
                   "register-suite", "run-suite", "run-research", "explore"}
        if args.command in guarded or (args.command == "submissions" and (root / "runtime/research.sqlite").exists()):
            from quanto.evaluation_registry import Supervisor, AccessError, current_session
            try:
                current_session(root)
            except AccessError as exc:
                if exc.reason != "authority_missing":
                    raise
                authority = Supervisor(root).session()
                authority.__enter__()

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
        elif args.command == "run-research":
            from quanto.research_broker import run_workflow
            result = run_workflow(root, _request_text(args.request))
            # Exact private records remain local; the default display is lifecycle only.
            output = {key: result[key] for key in (
                "submission_id", "status", "artifact_sha256", "workflow_run_id", "error_code",
                "dispatch_counts", "all_stages_completed", "all_models_actual", "review_outcome",
                "execution_state", "operational_acceptance", "investment_validation"
            ) if key in result}
        elif args.command in {"acquire-bars", "acquire-calendar", "acquire-actions",
                              "register-dataset", "admit-dataset", "explore", "register-split-review",
                              "register-policy-revision", "register-suite", "run-suite"}:
            request = _request_text(args.request)
            if args.command in {"acquire-bars", "acquire-calendar"}:
                from quanto.alpaca_data import acquire_bars, acquire_calendar
                action = acquire_bars if args.command == "acquire-bars" else acquire_calendar
            elif args.command == "acquire-actions":
                from quanto.alpaca_actions import acquire_actions
                action = acquire_actions
            elif args.command == "admit-dataset":
                from quanto.admission import admit_dataset
                action = admit_dataset
            elif args.command == "register-split-review":
                from quanto.admission import register_split_semantic_review
                action = register_split_semantic_review
            elif args.command == "register-policy-revision":
                from quanto.policy_revision import register_revision
                action = register_revision
            elif args.command in {"register-suite", "run-suite"}:
                from quanto.study_suite import register_suite, run_suite
                action = register_suite if args.command == "register-suite" else run_suite
            else:
                from quanto.explorer import register_dataset, run_submission
                action = register_dataset if args.command == "register-dataset" else run_submission
            output = action(root, request)
        elif args.command == "submissions":
            if not (root / "runtime" / "research.sqlite").exists():
                output = {"status": "not_initialized", "submissions": []}
            else:
                from quanto.provenance import Provenance
                with Provenance(root) as store:
                    output = {"submissions": store.list_submissions(
                        kind=args.kind, status=args.status, limit=args.limit)}
        else:
            database = root / "runtime" / "research.sqlite"
            if not database.exists():
                output = {"status": "not_initialized", "message": "No research journal exists yet."}
            else:
                with Journal(database) as journal:
                    output = journal.overview()
        print(json.dumps(output, indent=2, allow_nan=False))
        return 1 if output.get("status") in {
            "invalid", "failed", "interrupted", "rejected", "pending"
        } else 0
    except (ValueError, OSError) as exc:
        print(f"Quanto: {exc}", file=sys.stderr)
        return 1
    finally:
        if authority is not None:
            authority.__exit__(None, None, None)
