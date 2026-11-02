"""Credential setup must preserve existing settings and never expose keys."""
from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "quanto_configure_runpod_test", ROOT / "scripts/configure_runpod_s3.py"
)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class TestConfigureRunpodS3(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / ".env"

    def test_preserve_replace_private_no_echo(self):
        self.path.write_text("# existing\nOTHER=preserve\nRUNPOD_S3_ACCESS_KEY_ID=old\nRUNPOD_S3_ACCESS_KEY_ID=duplicate\n")
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(out):
            helper.save_keys(self.path, "synthetic-id", "synthetic-secret")
        self.assertEqual(out.getvalue(), "")
        self.assertEqual(self.path.read_text(), "# existing\nOTHER=preserve\nRUNPOD_S3_ACCESS_KEY_ID=synthetic-id\nRUNPOD_S3_SECRET_ACCESS_KEY=synthetic-secret\n")
        self.assertEqual(stat.S_IMODE(self.path.stat().st_mode), 0o600)
        self.assertEqual(list(self.root.glob(".env.config-*")), [])

    def test_new_file_and_invalid_values(self):
        helper.save_keys(self.path, "synthetic-id", "synthetic-secret")
        before = self.path.read_bytes()
        for bad in ("", "x" * 513, "bad\nvalue", "bad value", "bad\tvalue", "bad\x00value", "bad'value", 'bad"value'):
            for index in (0, 1):
                values = ["synthetic-id", "synthetic-secret"]
                values[index] = bad
                with self.subTest(index=index, category=repr(bad[:10])):
                    with self.assertRaises(ValueError):
                        helper.save_keys(self.path, *values)
                    self.assertEqual(self.path.read_bytes(), before)

    def test_symlink_directory_fifo_oversize_and_bad_utf8_refuse(self):
        target = self.root / "target"
        target.write_text("unchanged")
        self.path.symlink_to(target)
        with self.assertRaises(OSError):
            helper.save_keys(self.path, "id", "secret")
        self.assertEqual(target.read_text(), "unchanged")
        self.path.unlink()
        self.path.mkdir()
        with self.assertRaises((ValueError, OSError)):
            helper.save_keys(self.path, "id", "secret")
        self.path.rmdir()
        os.mkfifo(self.path)
        with self.assertRaises(ValueError):
            helper.save_keys(self.path, "id", "secret")
        self.path.unlink()
        for raw in (b"x" * 64001, b"\xff"):
            self.path.write_bytes(raw)
            with self.assertRaises(ValueError):
                helper.save_keys(self.path, "id", "secret")
            self.assertEqual(self.path.read_bytes(), raw)

    def test_replace_failure_preserves_original_and_cleans_temp(self):
        self.path.write_text("OTHER=preserve\n")
        with patch.object(helper.os, "replace", side_effect=OSError("synthetic refusal")):
            with self.assertRaises(OSError):
                helper.save_keys(self.path, "id", "secret")
        self.assertEqual(self.path.read_text(), "OTHER=preserve\n")
        self.assertEqual(list(self.root.glob(".env.config-*")), [])

    def test_main_failures_do_not_echo_or_read_actual_env(self):
        script = self.root / "scripts/configure.py"
        script.parent.mkdir()
        self.path.write_text("OTHER=preserve\n")
        for failure in (helper.GetPassWarning("synthetic secret"), EOFError(), KeyboardInterrupt()):
            output = io.StringIO()
            with patch.object(helper, "__file__", str(script)), patch.object(helper.subprocess, "run"), patch.object(helper, "getpass", side_effect=failure):
                with redirect_stdout(output), redirect_stderr(output), self.assertRaises(SystemExit) as caught:
                    helper.main()
            self.assertNotIn("synthetic secret", str(caught.exception))
            self.assertEqual(output.getvalue(), "")
            self.assertEqual(self.path.read_text(), "OTHER=preserve\n")

    def test_main_refuses_nonignored_target_before_prompt(self):
        script = self.root / "scripts/configure.py"
        script.parent.mkdir()
        with patch.object(helper, "__file__", str(script)), patch.object(helper.subprocess, "run", side_effect=helper.subprocess.CalledProcessError(1, "git")), patch.object(helper, "getpass") as prompt:
            with self.assertRaises(SystemExit):
                helper.main()
            prompt.assert_not_called()
        self.assertFalse(self.path.exists())

