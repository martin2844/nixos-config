#!/usr/bin/env python3
"""Build everything first; replace only the profile entries managed here."""
import json
import subprocess
from pathlib import Path

repo = Path(__file__).resolve().parent.parent
nix = ['nix', '--extra-experimental-features', 'nix-command']
packages = {'chatgpt-desktop': 'chatgpt', 'nmgui': 'internet-panel',
            'lazyvim-development-tools': 'nvim-tools', 'networkmanager_dmenu': 'network-menu'}
outputs = {}
for name, attr in packages.items():
    outputs[name] = subprocess.check_output(
        ['nix-build', str(repo), '-A', attr, '-o', str(repo / ('result-' + attr))], text=True).strip()
for attr, target in [('nvim-blink', 'nvim-blink'), ('nvim-tools', 'nvim-tools')]:
    subprocess.run(['nix-build', str(repo), '-A', attr, '-o', str(Path.home() / '.local/share' / target)], check=True)
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
