"""Serialize the lead's reviewed inputs for one manual cycle, without reading or writing state."""

from datetime import datetime
import hashlib
import json
from pathlib import PurePosixPath
import re
from zoneinfo import ZoneInfo


REG = "runtime/development-cycle-registration-v2-preparation"
LAUNCH = "runtime/development-cycle-launch-v2-preparation"
AUDIT = "runtime/development-cycle-audit-v2-preparation"
SOURCE_PATHS = {
    "prepare_current_code.py": f"{REG}/prepare_current_code.py",
    "test_registration_preparation.py": f"{REG}/test_registration_preparation.py",
    "source-manifest.json": f"{REG}/source-manifest.json",
    "supervise.py": f"{LAUNCH}/supervise.py",
    "paid_worker.py": f"{LAUNCH}/paid_worker.py",
}
REVIEW_PATHS = {
    f"{stage}_{role}": f"docs/reviews/D008-{prefix}-{role}.md"
    for stage, prefix in (
        ("registration", "current-code-registration-v2"),
        ("supervisor", "manual-cycle-launch-v2"),
        ("auditor", "next-cycle-audit-v2"),
    )
    for role in ("critic", "quality", "scope")
}
AUDIT_TOOLS = {
    "audit_cycle.py", "audit_boundary.py", "context_checks.py", "trace_checks.py",
    "cycle_evidence.py", "independent_oracle.py",
}
MODELS = {
    role: "claude-opus-5-5" if role in {"data_critic", "statistical_critic"} else "claude-haiku-5-5"
    for role in ("director", "hypothesis", "engineer", "data_critic", "statistical_critic",
                 "quality", "scope")
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False,
                      separators=(",", ":")).encode("utf-8")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def checked(raw, digest):
    require(type(raw) is bytes and len(raw) <= 2_097_152 and sha(raw) == digest,
            "supplied bytes do not match the reviewed identity or size bound")
    return raw


def document(raw):
    def unique(pairs):
        result = dict(pairs)
        require(len(result) == len(pairs), "duplicate JSON key")
        return result

    value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique)
    require(type(value) is dict, "expected a JSON object")
    canonical(value)  # Refuse non-finite numbers, including float overflow.
    return value


def manifest_name(audit_manifest_id):
    require(isinstance(audit_manifest_id, str) and re.fullmatch("[0-9a-f]{32}", audit_manifest_id),
            "invalid audit manifest ID")
    return f"source-manifest-{audit_manifest_id}.json"


def reviewed_paths(audit_manifest_id):
    """Exact repository-relative keys for the caller's independently verified byte snapshots."""
    return frozenset([*SOURCE_PATHS.values(), *REVIEW_PATHS.values(),
                      *(f"{AUDIT}/{name}" for name in AUDIT_TOOLS),
                      f"{AUDIT}/{manifest_name(audit_manifest_id)}"])


def assemble(*, root, run_key, registration_attempt_id, audit_attempt_id,
             observed_at, planning_day, template, template_sha256, preflight, preflight_sha256,
             originals, expected_state, audit_manifest_id, audit_manifest_sha256,
             source_sha256, review_sha256, reviewed_files):
    """Return the four private files as bytes. The caller chooses all approvals and identities.

    The supplied preflight JSON must contain observed_at, planning_day, expected_state, and
    originals_sha256 (SHA-256 of canonical(originals)). Additional lead evidence is preserved.
    reviewed_files maps reviewed_paths(audit_manifest_id) to bytes. source_sha256 uses the
    filenames in SOURCE_PATHS and review_sha256 uses the nine role names in REVIEW_PATHS.
    """
    require(type(root) is str and root.startswith("/") and str(PurePosixPath(root)) == root
            and ".." not in PurePosixPath(root).parts, "invalid project root")
    require(type(run_key) is str and re.fullmatch("[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}", run_key),
            "invalid run key")
    for attempt in (registration_attempt_id, audit_attempt_id):
        # The prospective auditor requires both identities to fit within 64 characters.
        require(type(attempt) is str and re.fullmatch("[a-z0-9][a-z0-9-]{0,63}", attempt),
                "invalid attempt identity")
    require(set(reviewed_files) == reviewed_paths(audit_manifest_id), "unexpected source roster")
    require(set(source_sha256) == set(SOURCE_PATHS), "incomplete source identities")
    require(set(review_sha256) == set(REVIEW_PATHS), "incomplete review identities")
    for name, path in SOURCE_PATHS.items():
        checked(reviewed_files[path], source_sha256[name])
    for role, path in REVIEW_PATHS.items():
        checked(reviewed_files[path], review_sha256[role])

    name = manifest_name(audit_manifest_id)
    manifest = document(checked(reviewed_files[f"{AUDIT}/{name}"], audit_manifest_sha256))
    require(manifest.get("launch_sources") == {k: source_sha256[k] for k in
                                               ("supervise.py", "paid_worker.py")},
            "auditor launch identities differ")
    tools = manifest.get("tools")
    require(type(tools) is dict and set(tools) == AUDIT_TOOLS
            and tools["independent_oracle.py"] == manifest.get("oracle_sha256"), "invalid audit tools")
    for tool, digest in tools.items():
        checked(reviewed_files[f"{AUDIT}/{tool}"], digest)

    evidence = document(checked(preflight, preflight_sha256))
    stamp = datetime.fromisoformat(observed_at)
    require(stamp.utcoffset() is not None and evidence.get("observed_at") == observed_at
            and stamp.astimezone(ZoneInfo("America/Los_Angeles")).date().isoformat()
            == planning_day == evidence.get("planning_day"), "preflight date mismatch")
    require(type(expected_state) is dict and set(expected_state) == {"root", "objects", "control", "research"}
            and canonical(evidence.get("expected_state")) == canonical(expected_state), "preflight state mismatch")
    require(type(originals) is dict and set(originals) == {"revision", "admission", "suite"}
            and evidence.get("originals_sha256") == sha(canonical(originals)), "preflight originals mismatch")
    prior = document(checked(template, template_sha256))
    require(set(prior) == {"run_key", "evidence_kind", "models", "suite_sha256", "failure_ids"}
            and prior["evidence_kind"] == "historical_market_data" and prior["models"] == MODELS
            and prior["run_key"] != run_key
            and prior["suite_sha256"] == originals["suite"]["artifact_sha256"], "template mismatch")

    registry = canonical({
        "version": 1, "root": root, "source_root": root, "attempt_id": registration_attempt_id,
        "manifest_sha256": source_sha256["source-manifest.json"],
        "controller_sha256": source_sha256["prepare_current_code.py"],
        "tests_sha256": source_sha256["test_registration_preparation.py"],
        "preparation_critic_sha256": review_sha256["registration_critic"],
        "preflight_evidence_sha256": preflight_sha256, "originals": originals,
        "expected_state": expected_state,
    })
    require(len(registry) <= 1_048_576, "registration packet exceeds registration file limit")
    plan = canonical({
        "schema": 1, "run_key": run_key, "audit_attempt_id": audit_attempt_id,
        "registry_packet_sha256": sha(registry), "template_sha256": template_sha256,
        "supervisor_sha256": source_sha256["supervise.py"], "worker_sha256": source_sha256["paid_worker.py"],
        "audit_manifest": {"name": name, "sha256": audit_manifest_sha256}, "reviews": review_sha256,
    })
    return {"template.json": template, "preflight.json": preflight,
            "registration.json": registry, "plan.json": plan}
