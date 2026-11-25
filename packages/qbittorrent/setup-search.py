"""Seed the default desktop profile without replacing user settings or plugins."""
import os
from pathlib import Path
import sys


def setup(bundle: Path) -> None:
    home = Path.home()
    data = Path(os.environ.get("XDG_DATA_HOME") or home / ".local/share")
    config = Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config")
    engines = data / "qBittorrent/nova3/engines"
    engines.mkdir(parents=True, exist_ok=True)
    for source in sorted(bundle.glob("*.py")):
        destination = engines / source.name
        try:
            # Exclusive creation also preserves existing symlinks and GUI updates.
            with destination.open("xb") as output:
                output.write(source.read_bytes())
        except FileExistsError:
            pass

    settings = config / "qBittorrent/qBittorrent.conf"
    settings.parent.mkdir(parents=True, exist_ok=True)
    try:
        with settings.open("x") as output:
            output.write("[Preferences]\nSearch\\SearchEnabled=true\n")
    except FileExistsError:
        pass


if __name__ == "__main__":
    setup(Path(sys.argv[1]))
