"""Report the connected Pro Click V2 battery as Waybar JSON."""
from html import escape
import math

from gi.repository import Gio, GLib


def status():
    hidden = {"text": ""}
    try:
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)

        def call(path, interface, method):
            return bus.call_sync(
                "org.razer", path, interface, method, None, None,
                Gio.DBusCallFlags.NO_AUTO_START, 2000, None,
            ).unpack()[0]

        serials = call("/org/razer", "razer.devices", "getDevices")
    except GLib.Error:
        return hidden

    for serial in serials:
        path = "/org/razer/device/" + serial
        try:
            if tuple(call(path, "razer.device.misc", "getVidPid")) not in (
                (0x1532, 0x00D0), (0x1532, 0x00D1),
            ):
                continue
            # A receiver may remain listed while its mouse is switched off.
            # Require a valid live response instead of a timeout's zero DPI.
            dpi = call(path, "razer.device.dpi", "getDPI")
            if len(dpi) != 2 or min(dpi) <= 0:
                continue
            battery = float(call(path, "razer.device.power", "getBattery"))
            if not math.isfinite(battery) or not 0 <= battery <= 100:
                continue
            charging = call(path, "razer.device.power", "isCharging")
            name = call(path, "razer.device.misc", "getDeviceName")
        except (GLib.Error, TypeError, ValueError):
            # The mouse can disappear between discovery and a status query.
            continue

        percentage = math.floor(battery + 0.5)
        classes = ["connected"]
        if charging:
            classes.append("charging")
        elif percentage <= 10:
            classes.append("critical")
        elif percentage <= 20:
            classes.append("warning")
        return {
            "text": "󰍽",
            "percentage": percentage,
            "class": classes,
            "tooltip": escape(
                f"{name}\nBattery: {percentage}%"
                + (" · Charging" if charging else "")
                + "\nClick: mouse settings"
            ),
        }

    return hidden
