"""Desktop service adapters. No shell evaluation of configuration or device data."""

import datetime
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


class SettingsError(RuntimeError):
    pass


def run(*args, timeout=12):
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "LC_ALL": "C"},
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SettingsError(str(exc)) from exc
    if result.returncode:
        raise SettingsError(
            result.stderr.strip() or result.stdout.strip() or f"{args[0]} unavailable"
        )
    return result.stdout.strip()


def power_state():
    listing = run("powerprofilesctl", "list")
    profiles = re.findall(
        r"^\s*\*?\s*(power-saver|balanced|performance):", listing, re.M
    )
    return profiles, run("powerprofilesctl", "get"), listing


def set_profile(profile):
    profiles, _, _ = power_state()
    if profile not in profiles:
        raise SettingsError("That profile is not available.")
    run("powerprofilesctl", "set", profile)
    return power_state()


def presentation_active():
    return (
        subprocess.run(
            [
                "systemctl",
                "--user",
                "is-active",
                "--quiet",
                "hyprmod-presentation.service",
            ],
            timeout=5,
        ).returncode
        == 0
    )


def set_presentation(enabled):
    if enabled and not presentation_active():
        run(
            "systemd-run",
            "--user",
            "--unit=hyprmod-presentation",
            "--collect",
            "--property=PartOf=graphical-session.target",
            shutil.which("systemd-inhibit"),
            "--what=idle:sleep",
            "--mode=block",
            "--who=HyprMod",
            "--why=Presentation mode",
            shutil.which("sleep"),
            "infinity",
        )
    elif not enabled:
        run("systemctl", "--user", "stop", "hyprmod-presentation.service")
    return presentation_active()


def sleep_capability():
    return run(
        "busctl",
        "call",
        "org.freedesktop.login1",
        "/org/freedesktop/login1",
        "org.freedesktop.login1.Manager",
        "CanSuspend",
    ) in ('s "yes"', 's "challenge"')


def suspend_now():
    # logind/hypridle coordinate the lock and respect application inhibitors.
    run("systemctl", "suspend")


def inhibitors():
    return run("systemd-inhibit", "--list", "--no-pager", "--no-legend")


def batteries():
    devices = run("upower", "-e").splitlines()
    summaries = []
    for device in devices:
        if "/battery_" in device or "/ups_" in device:
            fields = {}
            for line in run("upower", "-i", device).splitlines():
                if ":" in line:
                    key, value = line.strip().split(":", 1)
                    fields[key] = value.strip()
            summaries.append(
                " · ".join(
                    filter(
                        None,
                        [
                            fields.get("model"),
                            fields.get("percentage"),
                            fields.get("state"),
                        ],
                    )
                )
            )
    return "\n".join(summaries) or "No battery or UPS detected."


IDLE_PATH = Path.home() / ".config/hypr/hypridle.conf"
BLOCK = re.compile(r"^listener\s*\{\s*\n.*?^\}", re.M | re.S)
LOCK = "loginctl lock-session"
OFF = "hyprctl dispatch 'hl.dsp.dpms({ action = \"off\" })'"
ON = "hyprctl dispatch 'hl.dsp.dpms({ action = \"on\" })'"


def idle_values(text):
    values = {"lock": 0, "screen": 0}
    found = set()
    for block in BLOCK.findall(text):
        command = re.search(r"^\s*on-timeout\s*=\s*(.*?)\s*$", block, re.M)
        if not command:
            continue
        kind = {LOCK: "lock", OFF: "screen"}.get(command[1])
        if kind:
            if kind in found:
                raise SettingsError("Duplicate idle rules found. Review hypridle.conf.")
            timeout = re.search(r"^\s*timeout\s*=\s*(\d+)\s*$", block, re.M)
            if not timeout:
                raise SettingsError("Unable to read an idle timeout.")
            found.add(kind)
            values[kind] = int(timeout[1])
    return values


def render_idle(text, lock, screen):
    for value in (lock, screen):
        if not isinstance(value, int) or not 0 <= value <= 86400:
            raise SettingsError("The timeout must be between 0 and 86400 seconds.")
    idle_values(text)  # Reject ambiguous duplicate rules before changing anything.
    remaining = {"lock": lock, "screen": screen}

    def replace(match):
        block = match[0]
        command = re.search(r"^\s*on-timeout\s*=\s*(.*?)\s*$", block, re.M)
        kind = {LOCK: "lock", OFF: "screen"}.get(command[1]) if command else None
        if kind is None:
            return block
        value = remaining.pop(kind)
        if value == 0:
            return ""
        return re.sub(
            r"(^\s*timeout\s*=\s*)\d+",
            lambda m: m[1] + str(value),
            block,
            count=1,
            flags=re.M,
        )

    result = BLOCK.sub(replace, text)
    for kind, value in remaining.items():
        if value:
            command = LOCK if kind == "lock" else OFF
            result += (
                f"\nlistener {{\n    timeout = {value}\n    on-timeout = {command}\n"
            )
            if kind == "screen":
                result += f"    on-resume = {ON}\n"
            result += "}\n"
    return result


def atomic_write(path, text):
    # Resolve home symlinks so changes remain in the source repository.
    path = path.resolve(strict=True)
    mode = path.stat().st_mode & 0o777
    fd, temp = tempfile.mkstemp(prefix="." + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, "w") as output:
            output.write(text)
        os.chmod(temp, mode)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def save_idle(original, lock, screen, path=IDLE_PATH):
    path = path.resolve(strict=True)
    if path.read_text() != original:
        raise SettingsError(
            "The configuration changed outside this window. Select Reload."
        )
    updated = render_idle(original, lock, screen)
    if updated == original:
        return updated
    backup = (
        Path.home()
        / ".local/state/nixos-config/backups"
        / ("hypridle-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
    )
    backup.mkdir(parents=True)
    shutil.copy2(path, backup / path.name)
    atomic_write(path, updated)
    try:
        run("systemctl", "--user", "restart", "hypridle.service")
        run("systemctl", "--user", "is-active", "--quiet", "hypridle.service")
    except SettingsError:
        atomic_write(path, original)
        run("systemctl", "--user", "restart", "hypridle.service")
        raise
    return updated


def automatic_sleep_status(text):
    # Report external policy changes rather than claiming 'Never' unconditionally.
    commands = re.findall(r"^\s*on-timeout\s*=\s*(.*)$", text, re.M)
    if any(
        re.search(r"\b(suspend|hibernate|hybrid-sleep|poweroff|shutdown|reboot)\b", c)
        for c in commands
    ):
        return "An automatic power action exists in hypridle.conf. Review the configuration."
    action = run(
        "busctl",
        "get-property",
        "org.freedesktop.login1",
        "/org/freedesktop/login1",
        "org.freedesktop.login1.Manager",
        "IdleAction",
    )
    if action != 's "ignore"':
        return "logind has an automatic power action: " + action
    return "Never · no idle suspend, hibernation or shutdown"


def detect_brightness():
    devices = []
    for device in Path("/sys/class/backlight").glob("*"):
        maximum = int((device / "max_brightness").read_text())
        if maximum > 0:
            current = int((device / "brightness").read_text())
            devices.append(
                {
                    "kind": "backlight",
                    "id": device.name,
                    "name": device.name,
                    "value": round(current * 100 / maximum),
                }
            )
    if list(Path("/dev").glob("i2c-*")):
        detected = run("ddcutil", "detect", "--brief", timeout=20)
        for number in re.findall(r"^Display\s+(\d+)\s*$", detected, re.M):
            try:
                value = run("ddcutil", "--display", number, "getvcp", "10", "--terse")
                current, maximum = parse_vcp(value)
                devices.append(
                    {
                        "kind": "ddc",
                        "id": number,
                        "name": "External display " + number,
                        "value": round(current * 100 / maximum),
                    }
                )
            except SettingsError:
                continue
    return devices


def parse_vcp(value):
    match = re.search(r"\bVCP\s+10\s+C\s+(\d+)\s+(\d+)\b", value)
    if not match or int(match[2]) <= 0:
        raise SettingsError(
            "The monitor does not report a supported brightness control."
        )
    return int(match[1]), int(match[2])


def set_brightness(device, percent):
    if not isinstance(percent, int) or not 1 <= percent <= 100:
        raise SettingsError("Brightness must be between 1 and 100%.")
    if device["kind"] == "backlight":
        run("brightnessctl", "--device", device["id"], "set", str(percent) + "%")
        root = Path("/sys/class/backlight") / device["id"]
        return round(
            int((root / "brightness").read_text())
            * 100
            / int((root / "max_brightness").read_text())
        )
    _, maximum = parse_vcp(
        run("ddcutil", "--display", device["id"], "getvcp", "10", "--terse")
    )
    run(
        "ddcutil",
        "--display",
        device["id"],
        "setvcp",
        "10",
        str(round(percent * maximum / 100)),
    )
    current, maximum = parse_vcp(
        run("ddcutil", "--display", device["id"], "getvcp", "10", "--terse")
    )
    return round(current * 100 / maximum)
