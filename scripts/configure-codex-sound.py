#!/usr/bin/env python3
"""Enable completion audio without copying private Codex settings into Git."""
import datetime
import json
from pathlib import Path
import re
import shutil
import tomllib

config = Path.home() / '.codex/config.toml'
original = config.read_text() if config.exists() else ''
existing = tomllib.loads(original)
command = str(Path.home() / '.nix-profile/bin/codex-complete-sound')
lines = original.splitlines(keepends=True)
section = ''
result = []
has_tui = False
for line in lines:
    match = re.match(r'^\s*\[([^\[\]]+)\]', line)
    if match:
        section = match[1].strip()
    if section == '' and re.match(r'^\s*notify\s*=', line):
        if existing.get('notify') != [command]:
            raise SystemExit('Existing notify command requires manual merging.')
        continue
    if section == 'tui' and re.match(r'^\s*notifications\s*=', line):
        continue
    result.append(line)
    if match and section == 'tui':
        has_tui = True
        result.append('notifications = false\n')
updated = 'notify = ' + json.dumps([command]) + '\n' + ''.join(result)
if not has_tui:
    updated += '\n[tui]\nnotifications = false\n'
parsed = tomllib.loads(updated)
assert parsed['notify'] == [command] and parsed['tui']['notifications'] is False
if updated == original:
    print('Codex completion sound is already configured.')
    raise SystemExit(0)
if config.exists():
    backup = Path.home() / '.local/state/nixos-config/backups' / ('codex-sound-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    backup.mkdir(parents=True)
    shutil.copy2(config, backup / 'config.toml')
config.parent.mkdir(parents=True, exist_ok=True)
config.write_text(updated)
print('Codex completion sound configured. Restart/resume Codex to activate.')
