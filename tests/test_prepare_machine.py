"""Preparation exports a copy without changing or activating the source system."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('prepare_machine', REPO / 'scripts/prepare-machine.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PrepareMachineTests(unittest.TestCase):
    def test_export_adapts_only_copy_and_preserves_base(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            base = root / 'configuration.nix'
            original = '{ ... }: { users.users.alice = { isNormalUser = true; home = "/srv/alice"; }; }\n'
            base.write_text(original)
            source = REPO / 'home/.config/waybar/config.jsonc'
            before = source.read_bytes()
            out = root / 'prepared'
            module.prepare(out, base, 'alice', '/srv/alice')
            self.assertEqual(base.read_text(), original)
            self.assertEqual(source.read_bytes(), before)
            self.assertFalse((out / 'hosts/nixos/hardware-configuration.nix').exists())
            config = (out / 'hosts/nixos/configuration.nix').read_text()
            self.assertIn(str(base), config)
            self.assertNotIn('by-uuid', config)
            self.assertIn('"alice"', config)
            self.assertIn('/srv/alice', (out / 'home/.config/waybar/config.jsonc').read_text())
            self.assertNotIn('/home/martin', (out / 'home/.config/waybar/config.jsonc').read_text())
            self.assertNotIn('DP-3', (out / 'home/.config/hypr/hyprland-gui.lua').read_text())
            self.assertIn('--operator=alice', (out / 'hosts/nixos/hyprland.nix').read_text())
            self.assertFalse((out / '.git').exists())
            self.assertFalse((out / 'home/.config/hypr/wallpaper-custom.png').exists())
            result = subprocess.run(['bash', str(out / 'install.sh'), '--switch'], capture_output=True)
            self.assertEqual(result.returncode, 2)
            subprocess.run(['nix-instantiate', '--parse', str(out / 'hosts/nixos/configuration.nix')],
                           stdout=subprocess.DEVNULL, check=True)

    def test_refuses_existing_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp) / 'base.nix'; base.write_text('{}')
            with self.assertRaisesRegex(ValueError, 'already exists'):
                module.prepare(temp, base, 'alice', '/home/alice')
            self.assertEqual(base.read_text(), '{}')

    def test_refuses_source_tree_and_unsafe_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp) / 'base.nix'; base.write_text('{}')
            with self.assertRaisesRegex(ValueError, 'outside'):
                module.prepare(REPO / 'prepared-test', base, 'alice', '/home/alice')
            for user, home in [('root', '/root'), ('bad;name', '/home/alice'), ('alice', '/home/a b')]:
                with self.assertRaises(ValueError):
                    module.prepare(Path(temp) / 'out', base, user, home)


if __name__ == '__main__':
    unittest.main()
