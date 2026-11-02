"""Invented keys and mocked children only; never generate a real recovery identity."""
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import importlib.util
import io
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("configure_backup_key_test", ROOT / "scripts/configure_backup_key.py")
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
PUBLIC = b"age1" + b"a" * 58 + b"\n"
SECRET = b"SYNTHETIC-IDENTITY-NOT-A-REAL-KEY\n"
CIPHER = b"age-encryption.org/v1\nsynthetic-ciphertext"


class TestConfigureBackupKey(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.root.chmod(0o700)
        self.path = self.root / "runtime/recovery/identity.txt"
        self.calls = []
        self.recipient, self.restored = PUBLIC, helper.SYNTHETIC
        self.failure = None
        self.returncode = 0
        child = patch.object(helper.subprocess, "run", side_effect=self.fake_child)
        child.start()
        self.addCleanup(child.stop)

    def fake_child(self, argv, **kwargs):
        self.calls.append((argv, kwargs))
        self.assertEqual(kwargs["env"], {"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"})
        self.assertEqual(kwargs["stderr"], subprocess.DEVNULL)
        self.assertEqual(kwargs["timeout"], 20)
        self.assertFalse(kwargs["check"])
        if argv[0] == helper.GIT:
            self.assertEqual(argv, [helper.GIT, "check-ignore", "--quiet", "--", str(self.path)])
            self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)
            return subprocess.CompletedProcess(argv, 0)
        if argv == [helper.KEYGEN]:
            self.assertIsInstance(kwargs["stdout"], int)
            info = os.fstat(kwargs["stdout"])
            self.assertEqual(stat.S_IMODE(info.st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(self.path.parent.stat().st_mode), 0o700)
            os.write(kwargs["stdout"], SECRET)
            if self.failure is not None:
                raise self.failure
            return subprocess.CompletedProcess(argv, self.returncode)
        if argv == [helper.KEYGEN, "-y", str(self.path)]:
            self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)
            kwargs["stdout"].write(self.recipient)
        elif argv == [helper.AGE, "-r", PUBLIC.decode().strip()]:
            self.assertEqual(kwargs["input"], helper.SYNTHETIC)
            kwargs["stdout"].write(CIPHER)
        elif argv == [helper.AGE, "-d", "-i", str(self.path)]:
            self.assertEqual(kwargs["input"], CIPHER)
            kwargs["stdout"].write(self.restored)
        else:
            self.fail("Unexpected command in isolated fixture")
        return subprocess.CompletedProcess(argv, 0)

    def test_private_no_echo_roundtrip_and_public_fingerprint(self):
        output = io.StringIO()
        with patch.dict(os.environ, {"RUNPOD_API_KEY": "synthetic-credential", "ANTHROPIC_API_KEY": "synthetic-model"}), \
                redirect_stdout(output), redirect_stderr(output):
            result = helper.configure(self.root)
        self.assertEqual(output.getvalue(), "")
        self.assertEqual(self.path.read_bytes(), SECRET)
        self.assertEqual(stat.S_IMODE(self.path.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.path.parent.stat().st_mode), 0o700)
        self.assertEqual(result["recipient"], PUBLIC.decode().strip())
        self.assertEqual(result["recipient_sha256"], hashlib.sha256(PUBLIC.strip()).hexdigest())
        self.assertTrue(result["local_roundtrip_verified"])
        self.assertFalse(result["off_mac_custody_confirmed"] or result["account_recovery_confirmed"])
        self.assertEqual(len(self.calls), 5)
        self.assertNotIn(SECRET.decode(), repr(result))

    def test_main_reports_only_public_values_and_pending_custody(self):
        output = io.StringIO()
        with patch.object(helper, "__file__", str(self.root / "scripts/configure_backup_key.py")), \
                redirect_stdout(output), redirect_stderr(output):
            helper.main()
        text = output.getvalue()
        self.assertIn(PUBLIC.decode().strip(), text)
        self.assertIn("not confirmed", text)
        self.assertNotIn(SECRET.decode(), text)

    def test_existing_identity_never_replaced(self):
        helper.configure(self.root)
        self.calls.clear()
        with self.assertRaises(FileExistsError):
            helper.configure(self.root)
        self.assertEqual(self.path.read_bytes(), SECRET)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0][0][0], helper.GIT)

    def test_symlink_directory_and_fifo_destinations_refuse(self):
        self.path.parent.mkdir(parents=True, mode=0o700)
        target = self.root / "unrelated.txt"
        target.write_bytes(b"unchanged")
        for kind in ("symlink", "directory", "fifo"):
            with self.subTest(kind=kind):
                if kind == "symlink":
                    self.path.symlink_to(target)
                elif kind == "directory":
                    self.path.mkdir()
                else:
                    os.mkfifo(self.path)
                with self.assertRaises(FileExistsError):
                    helper.configure(self.root)
                self.assertEqual(target.read_bytes(), b"unchanged")
                if kind == "directory":
                    self.path.rmdir()
                else:
                    self.path.unlink()

    def test_unsafe_parent_modes_and_symlinks_refuse(self):
        runtime = self.root / "runtime"
        runtime.mkdir(mode=0o700)
        runtime.chmod(0o777)
        with self.assertRaisesRegex(helper.SetupRefused, "unsafe_directory_permissions"):
            helper.configure(self.root)
        runtime.chmod(0o700)
        self.path.parent.mkdir(mode=0o755)
        with self.assertRaisesRegex(helper.SetupRefused, "unsafe_directory_permissions"):
            helper.configure(self.root)
        self.path.parent.rmdir()
        target = self.root / "external"
        target.mkdir(mode=0o700)
        self.path.parent.symlink_to(target, target_is_directory=True)
        with self.assertRaisesRegex(helper.SetupRefused, "unsafe_directory"):
            helper.configure(self.root)
        self.assertEqual(list(target.iterdir()), [])
        self.assertFalse(self.path.exists())

    def test_root_symlink_and_wrong_owner_refuse(self):
        link = self.root / "alias"
        link.symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(helper.SetupRefused, "symlink_path_refused"):
            helper.configure(link)
        with patch.object(helper.os, "getuid", return_value=os.getuid() + 1):
            with self.assertRaisesRegex(helper.SetupRefused, "unsafe_directory"):
                helper.configure(self.root)
        self.assertEqual(self.calls, [])

    def test_nonignored_target_refuses_before_key_creation(self):
        with patch.object(helper.subprocess, "run", return_value=subprocess.CompletedProcess([], 1)):
            with self.assertRaisesRegex(helper.SetupRefused, "local_program_refused"):
                helper.configure(self.root)
        self.assertFalse((self.root / "runtime").exists())

    def test_partial_key_kept_after_child_timeout(self):
        self.failure = subprocess.TimeoutExpired([helper.KEYGEN], 20, output=SECRET, stderr=SECRET)
        with self.assertRaisesRegex(helper.SetupRefused, "local_program_failed") as caught:
            helper.configure(self.root)
        self.assertNotIn(SECRET.decode(), str(caught.exception))
        self.assertEqual(self.path.read_bytes(), SECRET)
        self.assertEqual(len(self.calls), 2)
        with self.assertRaises(FileExistsError):
            helper.configure(self.root)

    def test_child_failure_and_interruption_keep_key_without_secret_output(self):
        for failure in (KeyboardInterrupt(), OSError(SECRET.decode())):
            with self.subTest(failure=type(failure).__name__):
                self.failure = failure
                output = io.StringIO()
                with patch.object(helper, "__file__", str(self.root / "scripts/configure_backup_key.py")), \
                        redirect_stdout(output), redirect_stderr(output), self.assertRaises(SystemExit) as caught:
                    helper.main()
                self.assertNotIn(SECRET.decode(), str(caught.exception))
                self.assertEqual(output.getvalue(), "")
                self.assertEqual(self.path.read_bytes(), SECRET)
                self.path.unlink()  # Only this invented fixture is removed between cases.

    def test_nonzero_keygen_exit_retains_unaccepted_file(self):
        self.returncode = 1
        with self.assertRaisesRegex(helper.SetupRefused, "local_program_refused"):
            helper.configure(self.root)
        self.assertEqual(self.path.read_bytes(), SECRET)
        self.assertEqual(len(self.calls), 2)

    def test_recipient_shape_and_output_boundaries(self):
        for public in (SECRET, b"age1invalid\n", PUBLIC + PUBLIC, b"a" * 129):
            with self.subTest(category=public[:8]):
                self.recipient = public
                with self.assertRaises(helper.SetupRefused):
                    helper.configure(self.root)
                self.assertEqual(self.path.read_bytes(), SECRET)
                self.path.unlink()

    def test_decryption_mismatch_retains_key_without_success(self):
        self.restored = b"incorrect synthetic value"
        with self.assertRaisesRegex(helper.SetupRefused, "synthetic_roundtrip_failed"):
            helper.configure(self.root)
        self.assertEqual(self.path.read_bytes(), SECRET)

    def test_unsafe_generated_file_refuses_before_derivation(self):
        original = self.fake_child
        def changed(argv, **kwargs):
            result = original(argv, **kwargs)
            if argv == [helper.KEYGEN]:
                self.path.chmod(0o644)
            return result
        with patch.object(helper.subprocess, "run", side_effect=changed):
            with self.assertRaisesRegex(helper.SetupRefused, "generated_identity_refused"):
                helper.configure(self.root)
        self.assertEqual(len(self.calls), 2)

    def test_unapproved_program_never_launched(self):
        with self.assertRaisesRegex(helper.SetupRefused, "program_refused"):
            helper.command(["/bin/sh"], self.root)
        self.assertEqual(self.calls, [])
