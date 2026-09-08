#!/usr/bin/env python3
"""Prepare a separate desktop checkout against an existing machine's NixOS base."""
import argparse
import json
import os
from pathlib import Path
import pwd
import re
import shutil
import subprocess

REPO = Path(__file__).resolve().parent.parent


def nix_string(value):
    return json.dumps(str(value)).replace('${', r'\${')


def prepare(output, base, username, home):
    output = Path(output).absolute()
    base = Path(base).resolve(strict=True)
    if not base.is_file():
        raise ValueError('The base must be an existing plain NixOS configuration.nix file.')
    if not re.fullmatch(r'[a-z_][a-z0-9_-]*', username):
        raise ValueError('Use a simple Unix username (letters, digits, underscore or hyphen).')
    if not re.fullmatch(r'/[A-Za-z0-9_./-]+', home) or '..' in Path(home).parts:
        raise ValueError('Home must be an absolute path without spaces or shell metacharacters.')
    if username == 'root' or home == '/root':
        raise ValueError('Select a normal desktop user, not root.')
    if output.exists() or output.is_symlink():
        raise ValueError('Destination already exists; choose a new empty destination path.')
    resolved = output.resolve()
    if resolved == REPO or REPO in resolved.parents:
        raise ValueError('Destination must be outside the source checkout.')
    if resolved == base or resolved in base.parents:
        raise ValueError('Destination cannot contain the base configuration.')

    # Tracked source only: never export credentials, local caches or wallpapers.
    names = subprocess.check_output(['git', '-C', str(REPO), 'ls-files', '-z']).decode().split('\0')
    sources = []
    for name in filter(None, names):
        source = REPO / name
        if source.is_symlink() or not source.is_file():
            raise ValueError('Tracked source must be a regular file: ' + name)
        if name == 'hosts/nixos/hardware-configuration.nix':
            continue
        sources.append((name, source))
    output.mkdir(parents=True)
    for name, source in sources:
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        # Adapt text config paths only in the exported copy.
        try:
            original = target.read_text()
        except UnicodeDecodeError:
            continue
        updated = original.replace('/home/martin', home)
        if updated != original:
            target.write_text(updated)

    host = output / 'hosts/nixos'
    desktop = host / 'hyprland.nix'
    desktop.write_text(desktop.read_text().replace('--operator=martin', '--operator=' + username))
    # Import the destination's base in place: all its relative imports, hardware,
    # kernel, boot loader, disks, users and stateVersion keep their meaning.
    (host / 'configuration.nix').write_text('''{ config, lib, ... }:
{
  imports = [
    (builtins.toPath BASE)
    ./hyprland.nix
    ./appearance.nix
  ];
  services.displayManager.sddm.enable = lib.mkDefault true;
  services.desktopManager.plasma6.enable = lib.mkDefault true;
  assertions = [
    {
      assertion = config.users.users ? USER;
      message = "The selected desktop user must already exist in the base configuration.";
    }
    {
      assertion = (config.users.users.USER.home or "") == HOME;
      message = "The selected home must match the existing NixOS user.";
    }
  ];
}
'''.replace('BASE', nix_string(base)).replace('USER', nix_string(username)).replace('HOME', nix_string(home)))
    (output / 'home/.config/hypr/hyprland-gui.lua').write_text(
        '-- Machine-local overrides. Automatic preferred monitor modes are in hyprland.lua.\n')

    # The old installer explicitly targets the original disks. Never carry its
    # activation mode to another machine: preparation only offers a build check.
    (output / 'install.sh').write_text('''#!/usr/bin/env bash
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
if [[ "${1:-}" != --check || $# != 1 ]]; then
  echo 'Prepared checkout: use ./install.sh --check, then review PREPARED.md.' >&2
  exit 2
fi
"$repo/scripts/rebuild" build
python=$(nix-build "$repo/nix/pkgs.nix" -A python3 -o "$repo/result-python")
"$python/bin/python3" "$repo/scripts/install-user.py" --build-only
printf 'Build checks passed. Nothing installed, linked or activated.\\n'
''')
    (output / 'machine.json').write_text(json.dumps({'user': username, 'home': home, 'base': str(base)}, indent=2) + '\n')
    (output / 'PREPARED.md').write_text(f'''# Prepared desktop checkout

User: `{username}`. Home: `{home}`.
Existing NixOS base: `{base}` (imported in place, not copied).

This copy uses the existing machine's disks, boot configuration, users and
stateVersion. Its base file and relative imports must remain available.
The original machine's hardware configuration was omitted. Monitor overrides
were cleared; Hyprland uses automatic preferred modes. No system state changed.

1. Review `hosts/nixos/configuration.nix` and the desktop modules. This is an
   overlay on an existing plain NixOS installation, not a fresh OS installer.
   Resolve any conflicts with that installation; the script cannot infer GPU,
   network/audio choices or convert flakes and arbitrary custom modules.
2. Run `./install.sh --check`. It builds everything without installing anything.
3. After a successful build, as `{username}`, install user packages and preview
   links with `./result-python/bin/python3 scripts/install-user.py`
   and `./result-python/bin/python3 scripts/link-home.py`.
   Use `--apply` on link-home.py only after reviewing the preview. Existing
   destinations are backed up. Package installation also sets up Codex audio.
4. Run `~/.nix-profile/bin/desktop-theme` to apply dark user preferences.
5. When ready, `scripts/rebuild test` explicitly tests the generation;
   `scripts/rebuild switch` makes it persistent. Both require sudo. Preparation
   does not run them. Keep the base configuration and this checkout in place.

Account logins and personal data are not included. This directory has no Git
metadata; it is a separate working copy, so your source repo remains untouched.
''')
    print(f'Prepared {output}. Review PREPARED.md, then run ./install.sh --check there.')


def main():
    account = pwd.getpwuid(os.getuid())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, help='New directory outside this checkout')
    parser.add_argument('--base', default='/etc/nixos/configuration.nix', help='Existing target-machine plain NixOS configuration')
    parser.add_argument('--user', default=account.pw_name)
    parser.add_argument('--home', help='Defaults to the selected local user account home')
    args = parser.parse_args()
    try:
        home = args.home or pwd.getpwnam(args.user).pw_dir
        prepare(args.output, args.base, args.user, home)
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(1, str(exc) + '\n')


if __name__ == '__main__':
    main()
