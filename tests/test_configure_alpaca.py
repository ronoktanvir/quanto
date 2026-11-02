"""Credential setup tests use only fabricated values in temporary directories."""
import os
from pathlib import Path
import runpy

import pytest

save_keys = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "scripts" / "configure_alpaca.py")
)["save_keys"]


def test_preserves_other_settings_and_replaces_keys_privately(tmp_path):
    path = tmp_path / ".env"
    path.write_text("ANTHROPIC_API_KEY=synthetic-example\nAPCA_API_KEY_ID=old\n")
    save_keys(path, "synthetic-paper-id", "synthetic-paper-secret")
    assert path.read_text() == ("ANTHROPIC_API_KEY=synthetic-example\n"
                               "APCA_API_KEY_ID=synthetic-paper-id\n"
                               "APCA_API_SECRET_KEY=synthetic-paper-secret\n")
    assert path.stat().st_mode & 0o777 == 0o600
    assert list(tmp_path.glob(".env.config-*")) == []


@pytest.mark.parametrize("kind", ["symlink", "fifo", "oversized"])
def test_refuses_unsafe_existing_config(tmp_path, kind):
    path = tmp_path / ".env"
    target = tmp_path / "target"
    target.write_text("unchanged")
    if kind == "symlink":
        path.symlink_to(target)
    elif kind == "fifo":
        os.mkfifo(path)
    else:
        path.write_bytes(b"x" * 64_001)
    with pytest.raises((OSError, ValueError)):
        save_keys(path, "synthetic-paper-id", "synthetic-paper-secret")
    assert target.read_text() == "unchanged"


def test_refuses_multiline_value_before_touching_file(tmp_path):
    path = tmp_path / ".env"
    path.write_text("unchanged")
    with pytest.raises(ValueError):
        save_keys(path, "synthetic-id\nINJECT=value", "synthetic-secret")
    assert path.read_text() == "unchanged"
