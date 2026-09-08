#!/usr/bin/env python3
"""Back up existing targets, then link the explicitly listed user configuration."""
import argparse
import datetime
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--apply', action='store_true', help='perform links (default: preview)')
args = parser.parse_args()
repo = Path(__file__).resolve().parent.parent
home = Path.home()
backup = home / '.local/state/nixos-config/backups' / datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
links = json.loads((repo / 'links.json').read_text())
for target_name, source_name in links.items():
    source = repo / source_name
    target = home / target_name
    if not source.exists():
        raise SystemExit(f'Missing source: {source}')
    if not target.is_relative_to(home) or not source.is_relative_to(repo) or '..' in Path(target_name).parts or '..' in Path(source_name).parts:
        raise SystemExit('Only home-relative targets and repo-relative sources are supported')
for target_name, source_name in links.items():
    source = repo / source_name
    target = home / target_name
    if target.is_symlink() and target.resolve() == source.resolve():
        continue
    print(f'{target} -> {source}')
    if args.apply:
        if target.exists() or target.is_symlink():
            saved = backup / target_name
            saved.parent.mkdir(parents=True, exist_ok=True)
            target.rename(saved)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(source, target_is_directory=source.is_dir())
if args.apply:
    print(f'Existing targets preserved under {backup}')
