"""Check that build-only mode and failed builds cannot install or activate."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import sys

REPO = Path(__file__).resolve().parent.parent


class InstallerTests(unittest.TestCase):
    def run_installer(self, fail=''):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bindir = root / 'bin'
            bindir.mkdir()
            log = root / 'commands'
            # The Python interpreter is real; only Nix and sudo are mocked.
            nix_build = bindir / 'nix-build'
            nix_build.write_text('''#!/usr/bin/env bash
printf 'nix-build %s\\n' "$*" >> "$TEST_LOG"
if [[ -n "$FAIL_ATTR" && "$*" == *"-A $FAIL_ATTR "* ]]; then exit 19; fi
if [[ "$*" == *"-A python3 "* ]]; then
  printf '%s\\n' "$TEST_PYTHON_PREFIX"
else
  echo /nix/store/mock-built-output
fi
''')
            nix_build.chmod(0o755)
            for command in ['sudo', 'nix', 'nix-store']:
                stub = bindir / command
                stub.write_text('#!/usr/bin/env bash\necho FORBIDDEN >> "$TEST_LOG"\nexit 99\n')
                stub.chmod(0o755)
            env = {**os.environ, 'PATH': str(bindir) + ':' + os.environ['PATH'],
                   'HOME': str(root / 'home'), 'TEST_LOG': str(log),
                   'FAIL_ATTR': fail, 'TEST_PYTHON_PREFIX': str(Path(sys.executable).parent.parent)}
            result = subprocess.run([str(REPO / 'install.sh'), '--check'], env=env,
                                    text=True, capture_output=True)
            return result, log.read_text(), (root / 'home').exists()

    def test_check_builds_everything_without_installing(self):
        result, log, home_created = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        for attr in ['system', 'chatgpt', 'internet-panel', 'nvim-tools', 'nvim-blink', 'network-menu', 'wallpapers', 'wallpaper-tools']:
            self.assertIn('-A ' + attr + ' ', log)
        self.assertNotIn('FORBIDDEN', log)
        self.assertFalse(home_created)

    def test_failed_build_stops_before_installing(self):
        result, log, home_created = self.run_installer('internet-panel')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('FORBIDDEN', log)
        self.assertNotIn('-A nvim-blink ', log)
        self.assertFalse(home_created)


if __name__ == '__main__':
    unittest.main()
