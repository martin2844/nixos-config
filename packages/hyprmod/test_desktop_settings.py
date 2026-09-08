"""Boundary tests for editing linked idle configuration and desktop services."""

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "desktop_backend", Path(__file__).parent / "desktop_settings/backend.py"
)
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

SAMPLE = f"""# preserve this comment
general {{
    before_sleep_cmd = {b.LOCK}
}}
listener {{
    timeout = 600
    on-timeout = {b.LOCK}
}}
listener {{
    timeout = 900
    on-timeout = {b.OFF}
    on-resume = {b.ON}
}}
listener {{
    timeout = 300
    on-timeout = custom-idle-action
}}
"""


class DesktopSettingsTests(unittest.TestCase):
    def test_edit_preserves_other_rules_and_resume(self):
        edited = b.render_idle(SAMPLE, 1200, 1800)
        self.assertEqual(b.idle_values(edited), {"lock": 1200, "screen": 1800})
        self.assertIn("on-resume = " + b.ON, edited)
        self.assertIn("on-timeout = custom-idle-action", edited)
        self.assertIn("# preserve this comment", edited)
        self.assertNotIn("systemctl suspend", edited)

    def test_never_and_reenable(self):
        disabled = b.render_idle(SAMPLE, 0, 0)
        self.assertEqual(b.idle_values(disabled), {"lock": 0, "screen": 0})
        restored = b.render_idle(disabled, 600, 900)
        self.assertEqual(b.idle_values(restored), {"lock": 600, "screen": 900})
        self.assertIn("on-resume = " + b.ON, restored)

    def test_duplicate_rules_rejected(self):
        duplicate = (
            SAMPLE + f"\nlistener {{\n    timeout = 60\n    on-timeout = {b.LOCK}\n}}\n"
        )
        with self.assertRaises(b.SettingsError):
            b.render_idle(duplicate, 300, 900)

    def test_atomic_write_keeps_home_symlink(self):
        with tempfile.TemporaryDirectory() as root:
            source = Path(root) / "source"
            source.write_text(SAMPLE)
            link = Path(root) / "link"
            link.symlink_to(source)
            b.atomic_write(link, "updated")
            self.assertTrue(link.is_symlink())
            self.assertEqual(source.read_text(), "updated")

    def test_failed_service_restart_rolls_back(self):
        with tempfile.TemporaryDirectory() as root:
            source = Path(root) / "hypridle.conf"
            source.write_text(SAMPLE)
            with (
                patch.object(Path, "home", return_value=Path(root)),
                patch.object(
                    b, "run", side_effect=[b.SettingsError("failed"), ""]
                ) as run,
            ):
                with self.assertRaises(b.SettingsError):
                    b.save_idle(SAMPLE, 1200, 1800, source)
                self.assertEqual(run.call_count, 2)
            self.assertEqual(source.read_text(), SAMPLE)
            self.assertEqual(
                len(
                    list(
                        Path(root).glob(
                            ".local/state/nixos-config/backups/*/hypridle.conf"
                        )
                    )
                ),
                1,
            )

    def test_external_edit_not_overwritten(self):
        with tempfile.TemporaryDirectory() as root:
            source = Path(root) / "hypridle.conf"
            source.write_text("external edit")
            with self.assertRaises(b.SettingsError):
                b.save_idle(SAMPLE, 1200, 1800, source)
            self.assertEqual(source.read_text(), "external edit")

    def test_vcp_rejects_unsupported_values(self):
        self.assertEqual(b.parse_vcp("VCP 10 C 35 100"), (35, 100))
        for value in ["VCP 10 ERR", "VCP 10 C 0 0", "garbage"]:
            with self.assertRaises(b.SettingsError):
                b.parse_vcp(value)

    def test_rejects_unavailable_profile(self):
        with (
            patch.object(b, "power_state", return_value=(["balanced"], "balanced", "")),
            patch.object(b, "run") as run,
        ):
            with self.assertRaises(b.SettingsError):
                b.set_profile("performance")
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
