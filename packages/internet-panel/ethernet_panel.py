"""Small Ethernet section for nmgui; all connection changes require a button click."""
import os
import subprocess
import threading
from gi.repository import Gtk, GLib


def nm(*args):
    return subprocess.check_output(
        ['nmcli', *args], text=True, stderr=subprocess.STDOUT,
        timeout=20, env={**os.environ, 'LC_ALL': 'C'}).strip()


class EthernetPanel(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        heading = Gtk.Box(spacing=10)
        title = Gtk.Label(label='Ethernet', xalign=0, hexpand=True)
        title.add_css_class('heading')
        heading.append(title)
        settings = Gtk.Button(label='Connection settings')
        settings.connect('clicked', lambda _: subprocess.Popen(['nm-connection-editor']))
        heading.append(settings)
        self.append(heading)
        self.rows = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.append(self.rows)
        self.busy = False
        self.snapshot = None
        self.timer = None
        self.connect('map', self._start)
        self.connect('unmap', self._stop)

    def _start(self, *_):
        self.refresh()
        if self.timer is None:
            self.timer = GLib.timeout_add_seconds(5, self.refresh)

    def _stop(self, *_):
        if self.timer is not None:
            GLib.source_remove(self.timer)
            self.timer = None

    def refresh(self):
        if not self.busy:
            self.busy = True
            threading.Thread(target=self._read, daemon=True).start()
        return True

    def _read(self):
        try:
            devices = []
            for line in nm('-t', '-f', 'DEVICE,TYPE', 'device', 'status').splitlines():
                interface, kind = line.rsplit(':', 1)
                if kind != 'ethernet':
                    continue
                state = nm('-g', 'GENERAL.STATE', 'device', 'show', interface)
                address = nm('-g', 'IP4.ADDRESS', 'device', 'show', interface)
                devices.append((interface, state, address))
            GLib.idle_add(self._render, devices, None)
        except Exception as exc:
            GLib.idle_add(self._render, [], str(exc))

    def _render(self, devices, error):
        self.busy = False
        snapshot = (devices, error)
        if snapshot == self.snapshot:
            return False
        self.snapshot = snapshot
        while self.rows.get_first_child():
            self.rows.remove(self.rows.get_first_child())
        if not devices:
            self.rows.append(Gtk.Label(label=error or 'No Ethernet adapter detected', xalign=0, wrap=True))
        for interface, state, address in devices:
            connected = state.startswith('100 ')
            row = Gtk.Box(spacing=12)
            row.append(Gtk.Image.new_from_icon_name('network-wired-symbolic'))
            status = 'Connected' if connected else state.partition('(')[2].rstrip(')').capitalize()
            label = Gtk.Label(label=f'{status} · {interface}' + (f'\n{address}' if address else ''), xalign=0, hexpand=True)
            label.set_selectable(True)
            row.append(label)
            button = Gtk.Button(label='Disconnect' if connected else 'Connect', valign=Gtk.Align.CENTER)
            button.set_sensitive(not state.startswith(('10 ', '20 ')))
            button.connect('clicked', self._action, interface, connected)
            row.append(button)
            self.rows.append(row)
        return False

    def _action(self, button, interface, connected):
        button.set_sensitive(False)
        button.set_label('Working…')
        def worker():
            error = None
            try:
                nm('--wait', '15', 'device', 'disconnect' if connected else 'connect', interface)
            except Exception as exc:
                error = str(exc)
            GLib.idle_add(self._done, error)
        threading.Thread(target=worker, daemon=True).start()

    def _done(self, error):
        if error:
            dialog = Gtk.AlertDialog(message='Could not change Ethernet connection', detail=error)
            dialog.show(self.get_root())
        self.snapshot = None
        self.refresh()
        return False
