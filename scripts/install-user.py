#!/usr/bin/env python3
"""Build everything first; replace only the profile entries managed here."""
import json
import argparse
import subprocess
import runpy
from pathlib import Path

repo = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser()
parser.add_argument('--build-only', action='store_true', help='build without changing the user profile or home links')
args = parser.parse_args()
nix = ['nix', '--extra-experimental-features', 'nix-command']
packages = {'chatgpt-desktop': 'chatgpt', 'nmgui': 'internet-panel',
            'lazyvim-development-tools': 'nvim-tools', 'networkmanager_dmenu': 'network-menu',
            'desktop-wallpapers': 'wallpapers', 'desktop-wallpaper-tools': 'wallpaper-tools', 'waybar': 'waybar'}
packages['desktop-controls'] = 'desktop-controls'
outputs = {}
packages['hyprmod'] = 'hyprmod'
packages['omarchy-screenshot-preview'] = 'screenshot-preview'
packages['desktop-zsh'] = 'zsh'
packages['codex-complete-sound'] = 'codex-sound'
packages['codex-usage'] = 'codex-usage'
packages['desktop-theme'] = 'desktop-theme'
for name, attr in packages.items():
    outputs[name] = subprocess.check_output(
        ['nix-build', str(repo), '-A', attr, '-o', str(repo / ('result-' + attr))], text=True).strip()
blink = subprocess.check_output(
    ['nix-build', str(repo), '-A', 'nvim-blink', '-o', str(repo / 'result-nvim-blink')], text=True).strip()
if args.build_only:
    print('All user packages built; profile and home unchanged.')
    raise SystemExit(0)
for name, path in outputs.items():
    profile = json.loads(subprocess.check_output(nix + ['profile', 'list', '--json'], text=True))['elements']
    if any(path in item['storePaths'] for item in profile.values()):
        continue
    old = profile.get(name)
    if old:
        subprocess.run(nix + ['profile', 'remove', name], check=True)
    try:
        subprocess.run(nix + ['profile', 'add', path], check=True)
    except subprocess.CalledProcessError:
        if old:
            for previous in old['storePaths']:
                subprocess.run(nix + ['profile', 'add', previous], check=True)
        raise
# Create the runtime GC roots only after the entire package set has built.
(Path.home() / '.local/share').mkdir(parents=True, exist_ok=True)
for path, target in [(blink, 'nvim-blink'), (outputs['lazyvim-development-tools'], 'nvim-tools')]:
    subprocess.run(['nix-store', '--add-root', str(Path.home() / '.local/share' / target),
                    '--indirect', '-r', path], check=True)
runpy.run_path(str(repo / 'scripts/configure-codex-sound.py'), run_name='__main__')
