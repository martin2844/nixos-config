"""Native GTK pages for desktop settings outside the compositor configuration."""

import shutil
import subprocess
import threading
from pathlib import Path

from gi.repository import Adw, GLib, Gtk
from hyprmod.ui import confirm, make_page_layout

from . import backend as service


class DesktopPage:
    def __init__(self, window):
        self.window = window
        self.busy = False
        self.pending_job = None

    def layout(self, header):
        self.toolbar, _, self.content, _ = make_page_layout(header=header)
        self.status = Gtk.Label(wrap=True, xalign=0)
        self.status.add_css_class("dim-label")
        self.content.append(self.status)
        return self.toolbar

    def group(self, title, description=""):
        group = Adw.PreferencesGroup(title=title, description=description)
        self.content.append(group)
        return group

    def button(self, group, title, subtitle, label, callback):
        row = Adw.ActionRow(title=title, subtitle=subtitle, use_markup=False)
        button = Gtk.Button(label=label, valign=Gtk.Align.CENTER)
        button.connect("clicked", lambda _: callback())
        row.add_suffix(button)
        group.add(row)
        return button

    def job(self, function, done, *, on_error=None, background=False):
        if self.busy:
            if not background:
                self.pending_job = (function, done, on_error)
            return
        self.busy = True
        if not background:
            self.content.set_sensitive(False)
            self.status.set_text("Loading…")

        def finish(value, error):
            self.busy = False
            self.content.set_sensitive(True)
            if error:
                if on_error:
                    on_error(error)
                self.status.set_text(str(error))
            else:
                self.status.set_text("")
                done(value)
            if self.pending_job:
                pending, self.pending_job = self.pending_job, None
                self.job(pending[0], pending[1], on_error=pending[2])
            return GLib.SOURCE_REMOVE

        def worker():
            try:
                value = function()
            except (
                service.SettingsError,
                OSError,
                ValueError,
                subprocess.SubprocessError,
            ) as error:
                GLib.idle_add(finish, None, error)
            else:
                GLib.idle_add(finish, value, None)

        threading.Thread(target=worker, daemon=True).start()


class EnergyPage(DesktopPage):
    labels = {
        "power-saver": "Power saver",
        "balanced": "Balanced",
        "performance": "Performance",
    }

    def build(self, header):
        toolbar = self.layout(header)
        self.profile_dirty = False
        self.loading = False
        self.profiles = []
        power = self.group(
            "Power profile",
            "Applies to the whole computer and is remembered between sessions.",
        )
        self.profile = Adw.ComboRow(
            title="Profile", model=Gtk.StringList.new(["Loading…"])
        )
        self.profile.connect("notify::selected", self.profile_changed)
        power.add(self.profile)
        self.profile_status = Adw.ActionRow(title="Active profile", use_markup=False)
        power.add(self.profile_status)
        self.button(power, "Change profile", "", "Apply profile", self.apply_profile)

        idle = self.group(
            "Lock and display",
            "0 means Never. Turning off the display keeps the computer running.",
        )
        self.lock = Adw.SpinRow.new_with_range(0, 1440, 1)
        self.lock.set_title("Lock after (minutes)")
        self.lock.set_digits(2)
        idle.add(self.lock)
        self.screen = Adw.SpinRow.new_with_range(0, 1440, 1)
        self.screen.set_title("Turn off display after (minutes)")
        self.screen.set_digits(2)
        idle.add(self.screen)
        self.idle_save = self.button(
            idle,
            "Save idle settings",
            "Changes are saved for future sessions.",
            "Save",
            self.save_idle,
        )
        self.button(idle, "Read saved idle settings", "", "Reload", self.load_idle)
        self.automatic = Adw.ActionRow(
            title="Automatic sleep and shutdown", use_markup=False
        )
        idle.add(self.automatic)
        self.load_idle()

        presentation = self.group(
            "Presentation mode",
            "Temporarily prevents automatic locking, display power-off and sleep.",
        )
        self.presentation = Adw.SwitchRow(
            title="Keep the computer awake",
            subtitle="Turns off when you log out of the desktop.",
        )
        self.presentation.connect("notify::active", self.presentation_changed)
        presentation.add(self.presentation)

        details = self.group("Device status")
        self.battery = Adw.ActionRow(title="Battery and UPS", use_markup=False)
        details.add(self.battery)
        expander = Adw.ExpanderRow(title="Applications preventing power actions")
        self.inhibitor_text = Gtk.Label(wrap=True, selectable=True, xalign=0)
        self.inhibitor_text.set_margin_start(12)
        self.inhibitor_text.set_margin_end(12)
        self.inhibitor_text.set_margin_top(12)
        self.inhibitor_text.set_margin_bottom(12)
        expander.add_row(self.inhibitor_text)
        details.add(expander)
        self.button(details, "Refresh status", "", "Refresh", self.refresh)
        manual = self.group(
            "Manual actions", "Sleep starts only when you choose it and confirm."
        )
        self.suspend_button = self.button(
            manual,
            "Sleep now",
            "Locks the session before sleeping.",
            "Sleep…",
            self.confirm_suspend,
        )
        self.suspend_button.set_sensitive(False)
        toolbar.connect("map", lambda _: self.refresh())
        toolbar.connect("map", self.start_poll)
        toolbar.connect("unmap", self.stop_poll)
        self.poll_id = None
        return toolbar

    def start_poll(self, *_):
        if self.poll_id is None:
            self.poll_id = GLib.timeout_add_seconds(15, self.poll)

    def stop_poll(self, *_):
        if self.poll_id is not None:
            GLib.source_remove(self.poll_id)
            self.poll_id = None

    def poll(self):
        self.refresh(background=True)
        return GLib.SOURCE_CONTINUE

    def profile_changed(self, *_):
        if not self.loading:
            self.profile_dirty = True

    def refresh(self, *, background=False):
        def read():
            # Independent services can fail without disabling the rest of the page.
            state = {}
            for name, function in [
                ("power", service.power_state),
                ("presentation", service.presentation_active),
                ("battery", service.batteries),
                ("inhibitors", service.inhibitors),
                ("suspend", service.sleep_capability),
                (
                    "automatic",
                    lambda: service.automatic_sleep_status(
                        service.IDLE_PATH.read_text()
                    ),
                ),
            ]:
                try:
                    state[name] = function()
                except (
                    service.SettingsError,
                    OSError,
                    subprocess.SubprocessError,
                ) as error:
                    state[name] = error
            return state

        self.job(read, self.show_state, background=background)

    def show_state(self, state):
        power = state["power"]
        self.loading = True
        if isinstance(power, Exception):
            self.profile_status.set_subtitle(str(power))
            self.profile.set_sensitive(False)
            self.profiles = []
        else:
            profiles, active, listing = power
            if not self.profile_dirty or profiles != self.profiles:
                self.profile.set_model(
                    Gtk.StringList.new([self.labels[p] for p in profiles])
                )
                self.profile.set_selected(
                    profiles.index(active) if active in profiles else 0
                )
                self.profile_dirty = False
            self.profiles = profiles
            self.profile.set_sensitive(bool(profiles))
            self.profile_status.set_subtitle(self.labels.get(active, active))
            self.profile_status.set_tooltip_text(listing)
        presentation = state["presentation"]
        self.presentation.set_sensitive(not isinstance(presentation, Exception))
        if isinstance(presentation, bool):
            self.presentation.set_active(presentation)
        self.loading = False
        self.battery.set_subtitle(str(state["battery"]))
        self.inhibitor_text.set_text(str(state["inhibitors"]) or "No applications.")
        self.automatic.set_subtitle(str(state["automatic"]))
        self.suspend_button.set_sensitive(state["suspend"] is True)

    def apply_profile(self):
        selected = self.profile.get_selected()
        if selected >= len(self.profiles):
            return

        def done(_):
            self.profile_dirty = False
            self.refresh()

        self.job(lambda: service.set_profile(self.profiles[selected]), done)

    def load_idle(self):
        try:
            original = service.IDLE_PATH.read_text()
            values = service.idle_values(original)
        except (OSError, service.SettingsError) as error:
            self.idle_save.set_sensitive(False)
            self.status.set_text(str(error))
            return
        self.original = original
        self.lock.set_value(values["lock"] / 60)
        self.screen.set_value(values["screen"] / 60)
        self.idle_save.set_sensitive(True)

    def save_idle(self):
        lock, screen = (
            round(self.lock.get_value() * 60),
            round(self.screen.get_value() * 60),
        )

        def done(updated):
            self.original = updated
            self.status.set_text("Idle settings saved.")

        self.job(lambda: service.save_idle(self.original, lock, screen), done)

    def presentation_changed(self, *_):
        if self.loading:
            return
        enabled = self.presentation.get_active()

        def failed(_):
            self.loading = True
            self.presentation.set_active(not enabled)
            self.loading = False

        self.job(
            lambda: service.set_presentation(enabled),
            lambda _: self.refresh(),
            on_error=failed,
        )

    def confirm_suspend(self):
        confirm(
            self.window,
            "Put the computer to sleep?",
            "Your session will be locked. Wake the computer using its power button or a supported input device.",
            "Sleep",
            lambda: self.job(service.suspend_now, lambda _: self.refresh()),
            cancel_label="Cancel",
        )


class BrightnessPage(DesktopPage):
    def build(self, header):
        toolbar = self.layout(header)
        self.button(
            self.group("Displays"),
            "Resolution, refresh rate and arrangement",
            "Open Hyprland monitor settings.",
            "Configure",
            lambda: self.window.navigate("monitors"),
        )
        self.displays = self.group(
            "Display brightness",
            "Adjust physical brightness on supported displays. Changes take effect when you select Apply.",
        )
        self.rows = []
        self.button(
            self.group("Detection"),
            "Find brightness controls",
            "Scan again after connecting a display.",
            "Detect",
            self.detect,
        )
        toolbar.connect("map", lambda _: self.detect())
        return toolbar

    def detect(self):
        self.job(service.detect_brightness, self.show_displays)

    def show_displays(self, devices):
        for row in self.rows:
            self.displays.remove(row)
        self.rows = []
        if not devices:
            row = Adw.ActionRow(
                title="Brightness unavailable",
                subtitle="No supported brightness control is available. Use the buttons on your monitor.",
                use_markup=False,
            )
            self.displays.add(row)
            self.rows.append(row)
            return
        for device in devices:
            row = Adw.ActionRow(
                title=device["name"],
                subtitle="Current brightness: " + str(device["value"]) + " %",
                use_markup=False,
            )
            scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 1, 100, 1)
            scale.set_size_request(180, -1)
            scale.set_valign(Gtk.Align.CENTER)
            scale.set_draw_value(True)
            scale.set_digits(0)
            scale.set_value(device["value"])
            row.add_suffix(scale)
            button = Gtk.Button(label="Apply", valign=Gtk.Align.CENTER)
            button.connect(
                "clicked", lambda _, d=device, s=scale, r=row: self.apply(d, s, r)
            )
            row.add_suffix(button)
            self.displays.add(row)
            self.rows.append(row)

    def apply(self, device, scale, row):
        percent = round(scale.get_value())

        def done(value):
            scale.set_value(value)
            row.set_subtitle("Current brightness: " + str(value) + " %")

        self.job(lambda: service.set_brightness(device, percent), done)


class SystemToolsPage(DesktopPage):
    def build(self, header):
        toolbar = self.layout(header)
        home = Path.home()
        categories = [
            (
                "Connections and sound",
                [
                    ("Wi-Fi and Ethernet", "Network connections", ["nmgui"]),
                    (
                        "VPN and advanced connections",
                        "NetworkManager connection editor",
                        ["nm-connection-editor"],
                    ),
                    ("Bluetooth", "Pair and manage devices", ["blueman-manager"]),
                    ("Tailscale", "Private network and devices", ["trayscale"]),
                    (
                        "Audio and microphone",
                        "Devices, volume and audio profiles",
                        ["pavucontrol"],
                    ),
                ],
            ),
            (
                "Personalization",
                [
                    ("Wallpaper", "Wallpaper gallery", ["wallpaper-gallery"]),
                    (
                        "Notifications",
                        "Notification history and Do Not Disturb",
                        ["swaync-client", "-t"],
                    ),
                    (
                        "Fonts",
                        "Install and manage fonts",
                        ["kcmshell6", "kcm_fontinst"],
                    ),
                    (
                        "Default applications",
                        "Browser and applications for opening files",
                        ["kcmshell6", "kcm_componentchooser"],
                    ),
                    (
                        "File associations",
                        "File types and applications",
                        ["kcmshell6", "kcm_filetypes"],
                    ),
                ],
            ),
            (
                "System",
                [
                    (
                        "Printers",
                        "Print queues and printer settings",
                        ["kcmshell6", "kcm_printer_manager"],
                    ),
                    ("System information", "Hardware and diagnostics", ["kinfocenter"]),
                    (
                        "NixOS configuration",
                        "Services, users, language and system updates",
                        ["dolphin", str((home / ".config/hypr").resolve().parents[2])],
                    ),
                ],
            ),
        ]
        for title, tools in categories:
            group = self.group(title, "Each tool opens in its own window.")
            for name, description, command in tools:
                available = shutil.which(command[0]) is not None
                button = self.button(
                    group,
                    name,
                    description if available else "This tool is not installed",
                    "Open",
                    lambda cmd=command: self.launch(cmd),
                )
                button.set_sensitive(available)
        return toolbar

    def launch(self, command):
        try:
            subprocess.Popen(
                ["uwsm", "app", "--", *command],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError as error:
            self.status.set_text(str(error))
