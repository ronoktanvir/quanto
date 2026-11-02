"""Storage tests use synthetic software fixtures, never investment evidence."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from quanto.ledger import (BudgetExceeded, Journal, LedgerError, StaleLease,
                           canonical_json, hash_bytes, hash_json)


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "journal.sqlite3"
        self.now = datetime(2026, 11, 2, 7, 59, 59, tzinfo=timezone.utc)
        self.journal = Journal(self.path, clock=lambda: self.now)
        self.addCleanup(self.journal.close)

    def experiment(self):
        return self.journal.register_experiment({"signal": "fixture"}, {"sha256": "data"},
                                                {"commit": "code"}, "synthetic_fixture")

    def test_canonical_identity_and_strict_json(self):
        self.assertEqual(hash_json({"a": 1, "b": [2]}), hash_json({"b": [2], "a": 1}))
        self.assertEqual(hash_bytes(b"x"), "2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881")
        for value in ({1: "bad"}, {"n": float("nan")}, [float("inf")], {"x": object()}, "x" * 1_048_577):
            with self.subTest(value=type(value)), self.assertRaises(LedgerError):
                canonical_json(value)

    def test_event_chain_triggers_tampering_and_checkpoint(self):
        self.journal.append_event("one", {"n": 1})
        head = self.journal.append_event("two", {"n": 2})
        self.assertEqual(self.journal.verify_events(head), {"count": 2, "head": head})
        for sql in ("UPDATE events SET payload='{}' WHERE id=1", "DELETE FROM events WHERE id=2"):
            with self.assertRaises(sqlite3.IntegrityError):
                self.journal.connection.execute(sql)
        # Simulate a privileged owner bypassing application protections.
        self.journal.connection.execute("DROP TRIGGER no_update_events")
        self.journal.connection.execute("UPDATE events SET payload='{}' WHERE id=1")
        with self.assertRaisesRegex(LedgerError, "damaged"):
            self.journal.verify_events()

    def test_external_checkpoint_detects_suffix_removal(self):
        self.journal.append_event("first", {})
        head = self.journal.append_event("last", {})
        self.journal.connection.execute("DROP TRIGGER no_delete_events")
        self.journal.connection.execute("DELETE FROM events WHERE id=2")
        self.assertEqual(self.journal.verify_events()["count"], 1)
        with self.assertRaisesRegex(LedgerError, "checkpoint"):
            self.journal.verify_events(head)

    def test_experiment_duplicates_attempt_history_and_foreign_keys(self):
        fingerprint = self.experiment()
        self.assertEqual(self.experiment(), fingerprint)
        statuses = ("success", "failed", "invalid", "rejected")
        for status in statuses:
            attempt = self.journal.start_attempt(fingerprint)
            self.journal.finish_attempt(attempt, status, {"artifact": "sha256:fixture"})
            with self.assertRaises(sqlite3.IntegrityError):
                self.journal.finish_attempt(attempt, "success")
        self.journal.start_attempt(fingerprint)
        overview = self.journal.overview()
        self.assertEqual(overview["experiments"], 1)
        self.assertEqual(overview["attempts"], 5)
        self.assertEqual(overview["unfinished_attempts"], 1)
        self.assertEqual(overview["attempt_statuses"], dict.fromkeys(statuses, 1))
        self.assertEqual(overview["evidence_kinds"], {"synthetic_fixture": 1})
        before = overview["events"]
        with self.assertRaises(sqlite3.IntegrityError):
            self.journal.start_attempt("missing")
        self.assertEqual(self.journal.overview()["events"], before)
        with self.assertRaises(sqlite3.IntegrityError):
            self.journal.connection.execute("UPDATE experiments SET code_identity='changed'")

    def test_changed_specification_data_code_and_assumptions_change_identity(self):
        base = ({"a": 1}, "data", "code", "synthetic_fixture", {})
        variants = (({"a": 2}, "data", "code", "synthetic_fixture", {}),
                    ({"a": 1}, "other-data", "code", "synthetic_fixture", {}),
                    ({"a": 1}, "data", "other-code", "synthetic_fixture", {}),
                    ({"a": 1}, "data", "code", "synthetic_fixture", {"cost": 1}))
        first = self.journal.register_experiment(*base)
        self.assertTrue(all(self.journal.register_experiment(*variant) != first for variant in variants))
        with self.assertRaises(LedgerError):
            self.journal.register_experiment({}, "data", "code", "paper")

    def test_reviews_require_distinct_producer_and_exact_artifact_identity(self):
        artifact = hash_bytes(b"exact reviewed revision")
        for role in ("criticism", "quality_validation", "no_drift"):
            self.journal.record_review(role, role + "-worker", "producer", artifact, "changes_required", {"objections": ["fixture"]})
        self.assertEqual(self.journal.overview()["reviews"], 3)
        with self.assertRaises(LedgerError):
            self.journal.record_review("quality", "Producer", "producer", artifact, "pass", {})
        with self.assertRaises(LedgerError):
            self.journal.record_review("quality", "qa", "producer", "branch-name", "pass", {})

    def test_atomic_parallel_budget_reservations(self):
        def reserve(index):
            with Journal(self.path, clock=lambda: self.now) as journal:
                try:
                    return journal.reserve(f"request-{index}", 1_000_000)["created"]
                except BudgetExceeded:
                    return False
        with ThreadPoolExecutor(max_workers=8) as pool:
            accepted = list(pool.map(reserve, range(40)))
        self.assertEqual(sum(accepted), 20)
        self.assertEqual(self.journal.budget_snapshot()["committed_micro_usd"], 20_000_000)
        self.assertEqual(self.journal.verify_events()["count"], 20)

    def test_concurrent_duplicate_request_creates_only_one_reservation(self):
        def reserve(_):
            with Journal(self.path, clock=lambda: self.now) as journal:
                return journal.reserve("same", 2_000_000)["created"]
        with ThreadPoolExecutor(max_workers=5) as pool:
            results = list(pool.map(reserve, range(10)))
        self.assertEqual(sum(results), 1)
        self.assertEqual(self.journal.budget_snapshot()["committed_micro_usd"], 2_000_000)
        with self.assertRaises(LedgerError):
            self.journal.reserve("same", 1)

    def test_dispatch_rejects_reservation_from_before_midnight_and_keeps_hold(self):
        self.journal.reserve("before-midnight", 2_000_000)
        self.now += timedelta(seconds=1)
        with self.assertRaisesRegex(LedgerError, "expired"):
            self.journal.authorize_dispatch("before-midnight")
        self.assertEqual(self.journal.budget_snapshot("2026-11-01")["committed_micro_usd"], 2_000_000)
        self.assertEqual(self.journal.connection.execute("SELECT COUNT(*) FROM dispatches").fetchone()[0], 0)
        self.journal.reserve("new-day-unique-id", 2_000_000)
        authorization = self.journal.authorize_dispatch("new-day-unique-id")
        self.assertEqual(authorization["day"], "2026-11-02")
        self.assertEqual(authorization["authorized_at"], "2026-11-02T08:00:00.000000+00:00")

    def test_dispatch_parallel_authorizers_have_one_winner(self):
        self.journal.reserve("dispatch-once", 2_000_000)
        def authorize(_):
            with Journal(self.path, clock=lambda: self.now) as journal:
                try:
                    return journal.authorize_dispatch("dispatch-once")
                except LedgerError:
                    return None
        with ThreadPoolExecutor(max_workers=5) as pool:
            results = list(pool.map(authorize, range(10)))
        self.assertEqual(sum(result is not None for result in results), 1)
        self.assertEqual(self.journal.connection.execute("SELECT COUNT(*) FROM dispatches").fetchone()[0], 1)
        self.assertEqual(self.journal.connection.execute("SELECT COUNT(*) FROM events WHERE kind='dispatch_authorized'").fetchone()[0], 1)
        self.assertEqual(self.journal.budget_snapshot()["committed_micro_usd"], 2_000_000)
        self.journal.verify_events()

    def test_dispatch_crash_restart_and_timeout_cannot_authorize_again(self):
        self.journal.reserve("crash-after-authorization", 2_000_000)
        with Journal(self.path, clock=lambda: self.now) as sender:
            sender.authorize_dispatch("crash-after-authorization")
            # Model a crash after authorization: no settlement and no network retry.
        with Journal(self.path, clock=lambda: self.now) as restarted:
            self.assertFalse(restarted.reserve("crash-after-authorization", 2_000_000)["created"])
            with self.assertRaisesRegex(LedgerError, "already authorized"):
                restarted.authorize_dispatch("crash-after-authorization")
            restarted.mark_uncertain("crash-after-authorization", "send result lost during restart")
            with self.assertRaises(LedgerError):
                restarted.authorize_dispatch("crash-after-authorization")
        self.assertEqual(self.journal.budget_snapshot()["committed_micro_usd"], 2_000_000)

    def test_dispatch_requires_reserved_state_and_append_only_authorization(self):
        with self.assertRaises(LedgerError):
            self.journal.authorize_dispatch("missing")
        self.journal.reserve("uncertain", 1_000_000)
        self.journal.mark_uncertain("uncertain", "unknown outcome")
        self.journal.reserve("settled", 1_000_000)
        self.journal.settle("settled", 100)
        for request_id in ("uncertain", "settled"):
            with self.subTest(request_id=request_id), self.assertRaises(LedgerError):
                self.journal.authorize_dispatch(request_id)
        self.journal.reserve("valid", 1_000_000)
        self.journal.authorize_dispatch("valid")
        for sql in ("UPDATE dispatches SET day='2000-01-01'", "DELETE FROM dispatches"):
            with self.assertRaises(sqlite3.IntegrityError):
                self.journal.connection.execute(sql)

    def test_budget_settlement_timeout_and_overage(self):
        self.journal.reserve("a", 10_000_000)
        self.journal.mark_uncertain("a", "timeout after send")
        self.assertEqual(self.journal.budget_snapshot()["committed_micro_usd"], 10_000_000)
        self.journal.reserve("b", 10_000_000)
        with self.assertRaises(BudgetExceeded):
            self.journal.reserve("c", 1)
        self.journal.settle("b", 2_000_000)
        self.journal.settle("b", 2_000_000)
        self.assertEqual(self.journal.budget_snapshot()["committed_micro_usd"], 12_000_000)
        with self.assertRaises(LedgerError):
            self.journal.settle("b", 1)
        with self.assertRaises(BudgetExceeded):
            self.journal.settle("a", 21_000_000)
        snapshot = self.journal.budget_snapshot()
        self.assertEqual(snapshot["committed_micro_usd"], 23_000_000)
        self.assertEqual(snapshot["uncertain_count"], 1)
        with self.assertRaises(BudgetExceeded):
            self.journal.reserve("blocked-after-overage", 1)
        with self.assertRaises(LedgerError):
            self.journal.settle("a", 0)
        self.assertEqual(self.journal.connection.execute("SELECT kind FROM events ORDER BY id DESC LIMIT 1").fetchone()[0], "budget_overage")

    def test_budget_validation_and_los_angeles_day(self):
        for bad in (-1, 1.5, True, "1", 0):
            with self.subTest(bad=bad), self.assertRaises(LedgerError):
                self.journal.reserve("bad", bad)
        with self.assertRaises(LedgerError):
            Journal(self.path, daily_limit_micro_usd=20_000_001)
        first = self.journal.reserve("yesterday", 20_000_000)
        self.assertEqual(first["day"], "2026-11-01")
        self.journal.mark_uncertain("yesterday", "cross-midnight timeout")
        self.now += timedelta(seconds=1)
        second = self.journal.reserve("today", 20_000_000)
        self.assertEqual(second["day"], "2026-11-02")
        self.assertFalse(self.journal.reserve("yesterday", 20_000_000)["created"])
        self.assertEqual(self.journal.budget_snapshot("2026-11-01")["uncertain_count"], 1)
        self.assertEqual(self.journal.budget_snapshot()["remaining_micro_usd"], 0)
        stored = self.journal.connection.execute("SELECT occurred_at FROM events LIMIT 1").fetchone()[0]
        self.assertTrue(stored.endswith("+00:00"))

    def test_clock_rejects_naive_datetime_and_rolls_back(self):
        self.now = datetime(2026, 1, 1)
        with self.assertRaises(LedgerError):
            self.journal.append_event("bad-clock", {})
        self.assertEqual(self.journal.verify_events()["count"], 0)

    def test_job_claim_parallel_workers_and_completion(self):
        self.journal.enqueue_job("one", {"kind": "fixture"})
        def claim(index):
            with Journal(self.path, clock=lambda: self.now) as journal:
                return journal.claim_job(f"worker-{index}")
        with ThreadPoolExecutor(max_workers=2) as pool:
            claims = list(pool.map(claim, range(2)))
        winner = next(claim for claim in claims if claim)
        self.assertEqual(sum(claim is not None for claim in claims), 1)
        self.assertEqual(winner["payload"], {"kind": "fixture"})
        with self.assertRaises(StaleLease):
            self.journal.complete_job("one", "wrong-worker", winner["fence"])
        self.journal.complete_job("one", winner["worker_id"], winner["fence"], {"result_ref": "fixture"})
        self.assertEqual(self.journal.overview()["job_states"], {"complete": 1})
        with self.assertRaises(StaleLease):
            self.journal.complete_job("one", winner["worker_id"], winner["fence"])

    def test_job_recovery_fences_old_worker_and_bounds_attempts(self):
        self.journal.enqueue_job("recover", {}, max_attempts=2)
        first = self.journal.claim_job("old", lease_seconds=1)
        self.now += timedelta(seconds=1)
        with self.assertRaises(StaleLease):
            self.journal.complete_job("recover", "old", first["fence"])
        second = self.journal.claim_job("new", lease_seconds=1)
        self.assertGreater(second["fence"], first["fence"])
        with self.assertRaises(StaleLease):
            self.journal.fail_job("recover", "old", first["fence"], "late")
        self.now += timedelta(seconds=1)
        self.assertIsNone(self.journal.claim_job("third"))
        self.assertEqual(self.journal.overview()["job_states"], {"failed": 1})
        self.assertEqual(self.journal.connection.execute("SELECT attempts FROM jobs").fetchone()[0], 2)

    def test_job_failure_retry_and_idempotent_enqueue(self):
        self.journal.enqueue_job("retry", {"x": 1}, max_attempts=2)
        self.journal.enqueue_job("retry", {"x": 1}, max_attempts=2)
        with self.assertRaises(LedgerError):
            self.journal.enqueue_job("retry", {"x": 2})
        for _ in range(2):
            claim = self.journal.claim_job("worker")
            self.journal.fail_job("retry", "worker", claim["fence"], "fixture failure", retryable=True)
        self.assertIsNone(self.journal.claim_job("worker"))
        self.assertEqual(self.journal.overview()["job_states"], {"failed": 1})
        events = [json.loads(r[0]) for r in self.journal.connection.execute("SELECT payload FROM events WHERE kind='job_failed'")]
        self.assertEqual([e["state"] for e in events], ["pending", "failed"])

    def test_persistence_across_close_and_rollback_journal(self):
        fingerprint = self.experiment()
        with Journal(self.path, clock=lambda: self.now) as reopened:
            self.assertEqual(reopened.overview()["experiments"], 1)
            self.assertEqual(reopened.connection.execute("PRAGMA journal_mode").fetchone()[0], "delete")
            attempt = reopened.start_attempt(fingerprint)
            reopened.finish_attempt(attempt, "failed", {"reason": "fixture"})
        self.assertEqual(self.journal.overview()["outcomes"], 1)


if __name__ == "__main__":
    unittest.main()
