"""Share the logged-in Hyprland desktop through Tailscale Serve only."""
import argparse
import json
import os
from pathlib import Path
import secrets
import string
import subprocess

PORT = "5900"
TARGET = "127.0.0.1:5900"
DIRECTORY = Path.home() / ".config/nixos-remote-desktop"
CONFIG = DIRECTORY / "wayvnc.conf"
PASSWORD = DIRECTORY / "password"
HEADER = "# Managed by nixos-remote-desktop; credentials stay outside Git.\n"


def configure():
    DIRECTORY.mkdir(parents=True, exist_ok=True, mode=0o700)
    DIRECTORY.chmod(0o700)
    if CONFIG.exists() and not CONFIG.read_text().startswith(HEADER):
        raise RuntimeError(f"Refusing to overwrite unmanaged configuration: {CONFIG}")
    if not PASSWORD.exists():
        # Native macOS VNC authentication uses exactly eight password bytes.
        password = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
        descriptor = os.open(PASSWORD, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w") as stream:
            stream.write(password + "\n")
    password = PASSWORD.read_text().strip()
    if len(password) != 8 or not password.isascii() or not password.isalnum():
        raise RuntimeError(f"Expected an eight-character ASCII password in {PASSWORD}")
    PASSWORD.chmod(0o600)
    content = HEADER + (
        "address=127.0.0.1\nport=5900\nenable_auth=true\nusername=martin\n"
        "relax_encryption=true\nallow_broken_crypto=true\n"
        f"password={password}\nxkb_layout=us\n"
    )
    temporary = CONFIG.with_suffix(".tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        stream.write(content)
    temporary.chmod(0o600)
    temporary.replace(CONFIG)


def tcp_rule():
    status = json.loads(subprocess.check_output(["tailscale", "serve", "status", "--json"], timeout=10))
    return status.get("TCP", {}).get(PORT)


def publish():
    rule = tcp_rule()
    if rule and rule.get("TCPForward") != TARGET:
        raise RuntimeError("Tailscale port 5900 already serves another application")
    subprocess.run(["tailscale", "serve", "--bg", "--yes", "--tcp=" + PORT,
                    "tcp://" + TARGET], check=True, timeout=30)


def unpublish():
    rule = tcp_rule()
    if rule and rule.get("TCPForward") == TARGET:
        subprocess.run(["tailscale", "serve", "--bg", "--yes", "--tcp=" + PORT,
                        "off"], check=True, timeout=10)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["configure", "run", "unpublish", "info"])
    action = parser.parse_args().action
    if action == "configure":
        configure()
        print(f"Remote desktop credentials prepared in {DIRECTORY}; password unchanged on subsequent runs.")
    elif action == "run":
        if not os.environ.get("WAYLAND_DISPLAY"):
            raise RuntimeError("Start this service inside the logged-in Hyprland session")
        configure()
        publish()
        os.execvp("wayvnc", ["wayvnc", "--config=" + str(CONFIG), "--max-fps=20",
                            "--render-cursor", "--disable-resizing", "--name=NixOS Desktop"])
    elif action == "unpublish":
        unpublish()
    else:
        address = subprocess.check_output(["tailscale", "ip", "-4"], text=True).strip()
        print(f"Mac Screen Sharing: vnc://{address}\nPassword file: {PASSWORD}")
        subprocess.run(["systemctl", "--user", "is-active", "remote-desktop.service"], check=False)


if __name__ == "__main__":
    main()
