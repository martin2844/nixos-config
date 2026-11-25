import importlib.util
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "remote_desktop", Path(__file__).resolve().parents[1] / "packages/remote-desktop/remote-desktop.py")
remote = importlib.util.module_from_spec(spec)
spec.loader.exec_module(remote)


class RemoteDesktopTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        root = Path(self.directory.name) / "configuration"
        for key, value in {"DIRECTORY": root, "CONFIG": root / "wayvnc.conf", "PASSWORD": root / "password"}.items():
            patcher = patch.object(remote, key, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_restart_preserves_password_and_private_file_permissions(self):
        remote.configure()
        password = remote.PASSWORD.read_text()
        remote.configure()
        self.assertEqual(remote.PASSWORD.read_text(), password)
        self.assertEqual(len(password.strip()), 8)
        for path, mode in [(remote.DIRECTORY, 0o700), (remote.CONFIG, 0o600), (remote.PASSWORD, 0o600)]:
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), mode)

    def test_server_authenticates_and_binds_only_to_loopback(self):
        remote.configure()
        config = remote.CONFIG.read_text()
        self.assertIn("address=127.0.0.1\n", config)
        self.assertIn("enable_auth=true\n", config)
        self.assertNotIn("address=0.0.0.0", config)

    def test_unmanaged_config_is_not_overwritten(self):
        remote.DIRECTORY.mkdir()
        remote.CONFIG.write_text("existing user configuration\n")
        with self.assertRaises(RuntimeError):
            remote.configure()
        self.assertEqual(remote.CONFIG.read_text(), "existing user configuration\n")

    def test_publish_does_not_replace_another_application(self):
        with patch.object(remote, "tcp_rule", return_value={"TCPForward": "127.0.0.1:9999"}), \
                patch.object(remote.subprocess, "run") as run:
            with self.assertRaises(RuntimeError):
                remote.publish()
            run.assert_not_called()

    def test_stop_does_not_remove_another_application(self):
        with patch.object(remote, "tcp_rule", return_value={"TCPForward": "127.0.0.1:9999"}), \
                patch.object(remote.subprocess, "run") as run:
            remote.unpublish()
            run.assert_not_called()

    def test_stop_removes_only_owned_tcp_port(self):
        with patch.object(remote, "tcp_rule", return_value={"TCPForward": remote.TARGET}), \
                patch.object(remote.subprocess, "run") as run:
            remote.unpublish()
            self.assertEqual(run.call_args.args[0],
                             ["tailscale", "serve", "--bg", "--yes", "--tcp=5900", "off"])


if __name__ == "__main__":
    unittest.main()
