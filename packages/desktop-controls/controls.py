"""Small on-demand Wayland panels. No resident daemon or saved device state."""
import json
import re
import subprocess
import sys


def run(*args):
    return subprocess.check_output(args, text=True, timeout=4).strip()


if sys.argv[1:] == ['tailscale-status']:
    try:
        state = json.loads(run('tailscale', 'status', '--json')).get('BackendState', 'Unknown')
        print(json.dumps({'text': '󰒍', 'class': 'connected' if state == 'Running' else 'disconnected',
                          'tooltip': 'Tailscale: ' + state + '\nClic: gestionar VPN'}))
    except (subprocess.SubprocessError, ValueError, OSError):
        print(json.dumps({'text': '󰒍', 'class': 'disconnected', 'tooltip': 'Tailscale no disponible'}))
    raise SystemExit(0)

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gtk, Gdk, Gio, GLib, GtkLayerShell, Pango

mode = sys.argv[1] if len(sys.argv) > 1 else 'audio'
if mode not in ('audio', 'bluetooth', 'windows'):
    raise SystemExit('Expected audio, bluetooth, windows, or tailscale-status')


class Panel(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='local.desktop.controls.' + mode)
        self.window = None
        self.refreshing = False
        self.bus = None
        self.timer = None

    def do_activate(self):
        if self.window:
            self.quit()
            return
        self.window = Gtk.ApplicationWindow(application=self)
        self.window.set_title('Desktop ' + mode)
        self.window.set_default_size(360, -1)
        self.window.set_resizable(False)
        GtkLayerShell.init_for_window(self.window)
        GtkLayerShell.set_namespace(self.window, 'desktop-controls')
        GtkLayerShell.set_layer(self.window, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_anchor(self.window, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_anchor(self.window, GtkLayerShell.Edge.RIGHT, True)
        GtkLayerShell.set_margin(self.window, GtkLayerShell.Edge.TOP, 8)
        GtkLayerShell.set_margin(self.window, GtkLayerShell.Edge.RIGHT, 12)
        GtkLayerShell.set_keyboard_mode(self.window, GtkLayerShell.KeyboardMode.ON_DEMAND)
        self.window.connect('key-press-event', self.key)
        # Follow-mouse focus can cross another surface between bar and popup.
        # Keep the window picker open until selection, Escape, X, or another click.
        if mode != 'windows':
            self.window.connect('focus-out-event', lambda *_: self.quit())
        css = Gtk.CssProvider()
        css.load_from_data(b'''window { background: #20252e; color: #e5e9ef; border: 1px solid #56677d; border-radius: 9px; }
        button { background: #303a48; color: #e5e9ef; border: 0; border-radius: 5px; padding: 7px; }
        button:hover { background: #46566a; } label { color: #e5e9ef; }
        frame.workspace-group { border: 1px solid #495362; border-radius: 7px; padding: 6px; }
        frame.workspace-group.active { border-color: #91a7bf; }
        frame.workspace-group > border { border: none; }
        frame.workspace-group label { font-weight: normal; }''')
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin=16)
        self.window.add(self.box)
        title = Gtk.Box(spacing=12)
        title.pack_start(Gtk.Label(label={'audio': 'Sonido', 'bluetooth': 'Bluetooth', 'windows': 'Ventanas abiertas'}[mode], xalign=0), True, True, 0)
        close = Gtk.Button(label='×')
        close.connect('clicked', lambda *_: self.quit())
        title.pack_end(close, False, False, 0)
        self.box.pack_start(title, False, False, 0)
        self.error = Gtk.Label(xalign=0, wrap=True)
        if mode == 'audio':
            self.audio_rows = []
            for label, node in [('Volumen', '@DEFAULT_AUDIO_SINK@'), ('Micrófono', '@DEFAULT_AUDIO_SOURCE@')]:
                self.box.pack_start(Gtk.Label(label=label, xalign=0), False, False, 0)
                row = Gtk.Box(spacing=10)
                slider = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
                slider.set_digits(0)
                slider.set_size_request(235, -1)
                slider.connect('value-changed', self.volume, node)
                mute = Gtk.ToggleButton(label='Silenciar')
                mute.connect('toggled', self.mute, node)
                row.pack_start(slider, True, True, 0)
                row.pack_end(mute, False, False, 0)
                self.box.pack_start(row, False, False, 0)
                self.audio_rows.append((node, slider, mute))
            self.refresh_audio()
            self.timer = GLib.timeout_add_seconds(2, self.refresh_audio)
            self.button('Mezclador por aplicación…', lambda: self.launch('pavucontrol'))
        elif mode == 'bluetooth':
            self.devices = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            self.box.pack_start(self.devices, False, False, 0)
            try:
                self.bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
                self.refresh_bluetooth()
                self.timer = GLib.timeout_add_seconds(3, self.refresh_bluetooth)
            except GLib.Error as exc:
                self.error.set_text(str(exc))
            self.button('Emparejar / más ajustes…', lambda: self.launch('blueman-manager'))
        else:
            self.window.set_default_size(440, -1)
            scroll = Gtk.ScrolledWindow()
            scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            scroll.set_propagate_natural_height(True)
            scroll.set_max_content_height(500)
            windows = Gtk.Grid(column_spacing=10, row_spacing=10, column_homogeneous=True)
            desktop_apps = Gio.AppInfo.get_all()
            def desktop_app(app_class):
                key = app_class.casefold()
                for app in desktop_apps:
                    if (app.get_id() or '').removesuffix('.desktop').casefold() == key:
                        return app
                    if isinstance(app, Gio.DesktopAppInfo) and (app.get_startup_wm_class() or '').casefold() == key:
                        return app
                return None
            scroll.add(windows)
            self.box.pack_start(scroll, True, True, 0)
            try:
                clients = json.loads(run('hyprctl', 'clients', '-j'))
                clients.sort(key=lambda c: (c['workspace']['id'], c.get('class', '').lower()))
                active_workspace = json.loads(run('hyprctl', 'activeworkspace', '-j'))['id']
                groups = {}
                for client in clients:
                    workspace_id = client['workspace']['id']
                    if workspace_id not in groups:
                        name = client['workspace']['name']
                        active = workspace_id == active_workspace
                        frame = Gtk.Frame(label='Workspace ' + name + (' · actual' if active else ''))
                        frame.get_style_context().add_class('workspace-group')
                        if active:
                            frame.get_style_context().add_class('active')
                        grid = Gtk.FlowBox()
                        grid.set_selection_mode(Gtk.SelectionMode.NONE)
                        grid.set_min_children_per_line(3)
                        grid.set_max_children_per_line(3)
                        grid.set_row_spacing(4)
                        grid.set_column_spacing(4)
                        frame.add(grid)
                        windows.attach(frame, len(groups) % 2, len(groups) // 2, 1, 1)
                        groups[workspace_id] = grid
                    button = Gtk.Button()
                    content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
                    app_class = client.get('class', 'Aplicación')
                    app = desktop_app(app_class)
                    workspace = client['workspace']['name']
                    icon = app.get_icon() if app else None
                    picture = (Gtk.Image.new_from_gicon(icon, Gtk.IconSize.DIALOG) if icon
                               else Gtk.Image.new_from_icon_name('application-x-executable', Gtk.IconSize.DIALOG))
                    picture.set_pixel_size(24)
                    content.pack_start(picture, False, False, 0)
                    button.set_size_request(40, 40)
                    button.add(content)
                    name = app.get_name() if app else app_class
                    button.set_tooltip_text(name + ' · Workspace ' + workspace + '\n' + client.get('title', name))
                    button.connect('clicked', lambda _, a=client['address']: self.focus_window(a))
                    groups[workspace_id].add(button)
                if not clients:
                    windows.add(Gtk.Label(label='No hay ventanas abiertas.'))
            except (subprocess.SubprocessError, ValueError, KeyError, OSError) as exc:
                self.error.set_text(str(exc))
        self.box.pack_start(self.error, False, False, 0)
        self.window.show_all()
        self.window.present()

    def focus_window(self, address):
        if not re.fullmatch(r'0x[0-9a-fA-F]+', address):
            return
        try:
            result = run('hyprctl', 'dispatch', 'hl.dsp.focus({window = "address:' + address + '"})')
            if result.strip() != 'ok':
                self.error.set_text(result)
                return
            self.quit()
        except (subprocess.SubprocessError, OSError) as exc:
            self.error.set_text(str(exc))

    def key(self, _window, event):
        if event.keyval == Gdk.KEY_Escape:
            self.quit()
            return True
        return False

    def button(self, label, callback):
        b = Gtk.Button(label=label)
        b.connect('clicked', lambda *_: callback())
        self.box.pack_start(b, False, False, 0)

    def launch(self, command):
        subprocess.Popen(['uwsm', 'app', '--', command])
        self.quit()

    def volume(self, slider, node):
        if not self.refreshing:
            self.command('wpctl', 'set-volume', node, str(round(slider.get_value())) + '%')

    def mute(self, button, node):
        if not self.refreshing:
            self.command('wpctl', 'set-mute', node, '1' if button.get_active() else '0')

    def command(self, *args):
        try:
            run(*args)
            self.error.set_text('')
        except (subprocess.SubprocessError, OSError) as exc:
            self.error.set_text(str(exc))

    def refresh_audio(self):
        self.refreshing = True
        try:
            for node, slider, mute in self.audio_rows:
                value = run('wpctl', 'get-volume', node)
                if not slider.has_focus():
                    slider.set_value(float(value.split()[1]) * 100)
                mute.set_active('[MUTED]' in value)
        except (subprocess.SubprocessError, ValueError, OSError) as exc:
            self.error.set_text(str(exc))
        finally:
            self.refreshing = False
        return True

    def bluez(self, path, interface, method, args=None):
        def done(bus, result):
            try:
                bus.call_finish(result)
                self.error.set_text('')
            except GLib.Error as exc:
                self.error.set_text(exc.message)
            self.refresh_bluetooth()
        self.bus.call('org.bluez', path, interface, method, args, None,
                      Gio.DBusCallFlags.NONE, 20000, None, done)

    def refresh_bluetooth(self):
        try:
            objects = self.bus.call_sync('org.bluez', '/', 'org.freedesktop.DBus.ObjectManager',
                'GetManagedObjects', None, GLib.VariantType.new('(a{oa{sa{sv}}})'),
                Gio.DBusCallFlags.NONE, 2000, None).unpack()[0]
            for child in self.devices.get_children():
                child.destroy()
            count = 0
            for path, interfaces in objects.items():
                adapter = interfaces.get('org.bluez.Adapter1')
                if adapter is not None:
                    powered = adapter.get('Powered', False)
                    b = Gtk.Button(label=('Desactivar' if powered else 'Activar') + ' Bluetooth')
                    b.connect('clicked', lambda _, p=path, v=not powered: self.bluez(p,
                        'org.freedesktop.DBus.Properties', 'Set', GLib.Variant('(ssv)',
                        ('org.bluez.Adapter1', 'Powered', GLib.Variant('b', v)))))
                    self.devices.pack_start(b, False, False, 0)
                device = interfaces.get('org.bluez.Device1')
                if device and (device.get('Paired') or device.get('Connected')):
                    count += 1
                    connected = device.get('Connected', False)
                    label = device.get('Alias', 'Dispositivo') + (' · Desconectar' if connected else ' · Conectar')
                    b = Gtk.Button(label=label)
                    b.connect('clicked', lambda _, p=path, m='Disconnect' if connected else 'Connect':
                              self.bluez(p, 'org.bluez.Device1', m))
                    self.devices.pack_start(b, False, False, 0)
            if not count:
                self.devices.pack_start(Gtk.Label(label='No hay dispositivos emparejados.'), False, False, 0)
            self.devices.show_all()
        except GLib.Error as exc:
            self.error.set_text(exc.message)
        return True


Panel().run([sys.argv[0]])
