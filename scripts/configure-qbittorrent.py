"""Keep qBittorrent out of Plasma's restored login session."""
from datetime import datetime
import os
from pathlib import Path
import re
import shutil
import subprocess

home = Path.home()
config = Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config") / "ksmserverrc"
current = subprocess.check_output(
    ["kreadconfig6", "--file", str(config), "--group", "General", "--key", "excludeApps"],
    text=True,
).strip()
excluded = {entry.strip().lower() for entry in re.split("[,:]", current)}
if "qbittorrent" not in excluded:
    if config.exists():
        backup = home / ".local/state/nixos-config/backups" / datetime.now().strftime("%Y%m%d-%H%M%S-qbittorrent")
        backup.mkdir(parents=True, exist_ok=True)
        shutil.copy2(config, backup / "ksmserverrc")
    subprocess.run(
        ["kwriteconfig6", "--file", str(config), "--group", "General", "--key", "excludeApps",
         current + ("," if current else "") + "qbittorrent"],
        check=True,
    )
