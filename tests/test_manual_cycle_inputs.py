"""The serializer may bind reviewed bytes, never approve or execute the plan."""

import json
from pathlib import Path
from types import ModuleType

import pytest

PROJECT = Path(__file__).resolve().parents[1]


def load_source(path, raw):
    module = ModuleType(path.stem)
    module.__file__ = str(path)
    exec(compile(raw, str(path), "exec", dont_inherit=True), module.__dict__)
    return module


SERIALIZER = PROJECT / "operations/manual_inputs/assemble.py"
assembly = load_source(SERIALIZER, SERIALIZER.read_bytes())


def readable_json(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


@pytest.fixture
def example(tmp_path):
    root = tmp_path.resolve() / "invented-project"
    audit_id = "abcd" * 8
    sources = {}
    for name, relative in assembly.SOURCE_PATHS.items():
        if name == "source-manifest.json":
            raw = b'{"invented":true}'
        else:
            folder = "manual_cycle" if name in {"supervise.py", "paid_worker.py"} else "registration"
            raw = (PROJECT / "operations" / folder / name).read_bytes()
        sources[relative] = raw
    source_sha = {name: assembly.sha(sources[path]) for name, path in assembly.SOURCE_PATHS.items()}
    for role, relative in assembly.REVIEW_PATHS.items():
        sources[relative] = f"invented review for {role}\n".encode()
    reviews = {role: assembly.sha(sources[path]) for role, path in assembly.REVIEW_PATHS.items()}
    tools = {}
    for name in assembly.AUDIT_TOOLS:
        raw = f"# invented auditor source {name}\n".encode()
        sources[f"{assembly.AUDIT}/{name}"] = raw
        tools[name] = assembly.sha(raw)
    manifest = assembly.canonical({
        "tools": tools, "oracle_sha256": tools["independent_oracle.py"],
        "launch_sources": {name: source_sha[name] for name in ("supervise.py", "paid_worker.py")},
    })
    sources[f"{assembly.AUDIT}/{assembly.manifest_name(audit_id)}"] = manifest
    originals = {}
    for index, phase in enumerate(("revision", "admission", "suite"), 1):
        raw = readable_json({"invented_phase": phase})
        originals[phase] = {
            "submission_id": format(index, "032x"), "artifact_sha256": assembly.sha(phase.encode()),
            "request_file": {"path": str(root / f"runtime/invented-{phase}.json"), "sha256": assembly.sha(raw)},
            "request_binding": "embedded_semantics" if phase == "admission" else "retained_bytes",
            "submission_request": {"encoding": "utf8_text", "sha256": assembly.sha(raw), "bytes": len(raw)},
        }
    # These are inert invented state identities. No store is instantiated or sampled.
    directory = {"device": 1, "inode": 2, "uid": 17, "mode": 0o700}
    file = {**directory, "inode": 3, "mode": 0o600, "nlink": 1}
    state = {
        "root": directory, "objects": {**directory, "inode": 4},
        "control": {"physical": file, "schema_sha256": assembly.sha(b"schema"), "tables": {}},
        "research": {"physical": {**file, "inode": 5}, "sha256": assembly.sha(b"database")},
    }
    observed_at = "2024-11-04T07:45:00+00:00"
    planning_day = "2024-11-03"
    preflight = readable_json({
        "observed_at": observed_at, "planning_day": planning_day, "expected_state": state,
        "originals_sha256": assembly.sha(assembly.canonical(originals)), "comment": "invented only",
    })
    template = readable_json({
        "run_key": "old-key", "suite_sha256": originals["suite"]["artifact_sha256"],
        "evidence_kind": "historical_market_data", "models": assembly.MODELS,
        "failure_ids": [{"source": "submission", "id": "a" * 32}],
    })
    return {
        "root": str(root), "run_key": "new-key", "registration_attempt_id": "test-reg",
        "audit_attempt_id": "test-audit", "observed_at": observed_at, "planning_day": planning_day,
        "template": template, "template_sha256": assembly.sha(template),
        "preflight": preflight, "preflight_sha256": assembly.sha(preflight),
        "originals": originals, "expected_state": state, "audit_manifest_id": audit_id,
        "audit_manifest_sha256": assembly.sha(manifest), "source_sha256": source_sha,
        "review_sha256": reviews, "reviewed_files": sources,
    }


def test_exact_bytes_load_through_accepted_supervisor_and_registration_validator(example):
    files = assembly.assemble(**example)
    assert assembly.assemble(**example) == files
    root = Path(example["root"])
    assert not root.exists()
    inputs = root / "runtime/manual-cycle-inputs"
    inputs.mkdir(mode=0o700, parents=True)
    for relative, raw in example["reviewed_files"].items():
        path = root / relative
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        path.write_bytes(raw)
        path.chmod(0o600)
    assert set(files) == {"plan.json", "registration.json", "preflight.json", "template.json"}
    for name, raw in files.items():
        path = inputs / name
        path.write_bytes(raw)
        path.chmod(0o600)
    assert files["template.json"] == example["template"]
    assert files["preflight.json"] == example["preflight"]
    supervisor_file = root / assembly.SOURCE_PATHS["supervise.py"]
    supervisor = load_source(supervisor_file, supervisor_file.read_bytes())
    # Only the machine-specific registration manifest and loader's interpreter/root boundary
    # are adapted. Use both exact sources and the real validate_packet(packet, False).
    supervisor.REG_MANIFEST_SHA = example["source_sha256"]["source-manifest.json"]
    def load_invented_registration():
        path = supervisor.REG / "prepare_current_code.py"
        registration = load_source(path, supervisor.pinned(path, supervisor.REG_SHA))
        registration.ACTUAL_ROOT = root
        return registration
    supervisor.registration_module = load_invented_registration
    plan, _, packet = supervisor.load_plan(assembly.sha(files["plan.json"]))
    assert plan["request_template"] == json.loads(example["template"])
    assert packet["expected_state"] == example["expected_state"]
    assert packet["originals"] == example["originals"]
    assert not (root / "runtime/current-code-registration").exists()
    assert not (root / "runtime/manual-development-cycle").exists()
    # Keep all packet hashes valid but supply a request path outside the invented runtime.
    # The actual registration validator, invoked by load_plan(), must still reject it.
    example["originals"]["revision"]["request_file"]["path"] = str(root / "wrong.json")
    preflight = json.loads(example["preflight"])
    preflight["originals_sha256"] = assembly.sha(assembly.canonical(example["originals"]))
    example["preflight"] = readable_json(preflight)
    example["preflight_sha256"] = assembly.sha(example["preflight"])
    refused = assembly.assemble(**example)
    for name, raw in refused.items():
        (inputs / name).write_bytes(raw)
    with pytest.raises(Exception, match="invalid_packet") as failure:
        supervisor.load_plan(assembly.sha(refused["plan.json"]))
    assert type(failure.value).__name__ == "Refusal"


@pytest.mark.parametrize("change", [
    "review_bytes", "source_bytes", "audit_tool_bytes", "missing_review_digest",
    "missing_source", "extra_source", "audit_manifest_id", "audit_manifest_digest",
    "template_bytes", "preflight_bytes", "changed_state", "changed_originals", "utc_day",
    "naive_time", "different_suite", "reused_run_key", "duplicated_template_key",
])
def test_refuses_inconsistent_lead_inputs(example, change):
    sources = example["reviewed_files"]
    if change == "review_bytes":
        sources[assembly.REVIEW_PATHS["registration_quality"]] += b" "
    elif change == "source_bytes":
        sources[assembly.SOURCE_PATHS["supervise.py"]] += b" "
    elif change == "audit_tool_bytes":
        sources[f"{assembly.AUDIT}/trace_checks.py"] += b" "
    elif change == "missing_review_digest":
        del example["review_sha256"]["auditor_critic"]
    elif change == "missing_source":
        del sources[assembly.SOURCE_PATHS["prepare_current_code.py"]]
    elif change == "extra_source":
        sources["unreviewed/file"] = b"extra"
    elif change == "audit_manifest_id":
        example["audit_manifest_id"] = "../manifest"
    elif change == "audit_manifest_digest":
        example["audit_manifest_sha256"] = "f" * 64
    elif change == "template_bytes":
        example["template"] += b" "
    elif change == "preflight_bytes":
        example["preflight"] += b" "
    elif change == "changed_state":
        example["expected_state"]["research"]["sha256"] = "a" * 64
    elif change == "changed_originals":
        example["originals"]["revision"]["submission_id"] = "f" * 32
    elif change == "utc_day":
        example["planning_day"] = "2024-11-04"
    elif change == "naive_time":
        example["observed_at"] = "2024-11-04T07:45:00"
    elif change == "different_suite":
        template = json.loads(example["template"])
        template["suite_sha256"] = "f" * 64
        example["template"] = readable_json(template)
        example["template_sha256"] = assembly.sha(example["template"])
    elif change == "reused_run_key":
        example["run_key"] = "old-key"
    elif change == "duplicated_template_key":
        example["template"] = example["template"].replace(b"{", b'{"run_key":"ambiguous",', 1)
        example["template_sha256"] = assembly.sha(example["template"])
    with pytest.raises(ValueError):
        assembly.assemble(**example)
