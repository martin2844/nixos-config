"""GTK editor opened by a day in the Waybar calendar."""
from datetime import date, datetime
from zoneinfo import ZoneInfo
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk
import reminders


class Editor(Gtk.Window):
    def __init__(self, selected_date):
        super().__init__(title='Calendar reminders')
        self.set_default_size(580, 560)
        self.set_titlebar(Gtk.HeaderBar(title='Calendar reminders', show_close_button=True))
        self.set_border_width(20)
        self.connect('destroy', Gtk.main_quit)
        self.selected_date = date.fromisoformat(selected_date).isoformat()
        self.zone = reminders.local_zone()
        self.current_id = None
        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.add(body)
        heading = Gtk.Label(label=f'Reminders · {self.selected_date}', xalign=0)
        body.pack_start(heading, False, False, 0)
        self.store = Gtk.ListStore(str, str, str)
        tree = Gtk.TreeView(model=self.store)
        for column, name in enumerate(('Time', 'Reminder'), start=1):
            tree.append_column(Gtk.TreeViewColumn(name, Gtk.CellRendererText(), text=column))
        tree.get_selection().connect('changed', self.select)
        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_height(130)
        scroll.add(tree)
        body.pack_start(scroll, True, True, 0)
        form = Gtk.Grid(column_spacing=12, row_spacing=10)
        body.pack_start(form, False, False, 0)
        self.fields = {}
        for row, (key, label) in enumerate((('title', 'Title'), ('date', 'Date (YYYY-MM-DD)'),
                                          ('time', 'Time (HH:MM)'), ('timezone', 'Timezone'))):
            form.attach(Gtk.Label(label=label, xalign=0), 0, row, 1, 1)
            entry = Gtk.Entry()
            entry.set_hexpand(True)
            form.attach(entry, 1, row, 1, 1)
            self.fields[key] = entry
        body.pack_start(Gtk.Label(label='Notes', xalign=0), False, False, 0)
        self.notes = Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD_CHAR)
        notes_scroll = Gtk.ScrolledWindow()
        notes_scroll.set_min_content_height(90)
        notes_scroll.add(self.notes)
        body.pack_start(notes_scroll, True, True, 0)
        self.status = Gtk.Label(xalign=0, wrap=True)
        body.pack_start(self.status, False, False, 0)
        buttons = Gtk.Box(spacing=8)
        body.pack_start(buttons, False, False, 0)
        for label, callback in [('New', self.new), ('Delete', self.remove), ('Save', self.save)]:
            button = Gtk.Button(label=label)
            button.connect('clicked', callback)
            buttons.pack_start(button, True, True, 0)
        self.new()
        self.reload()

    def reload(self):
        self.items = {r['id']: r for r in reminders.read()['reminders']}
        self.store.clear()
        for item in self.items.values():
            local = datetime.fromtimestamp(item['at'], ZoneInfo(self.zone))
            if local.date().isoformat() == self.selected_date:
                title = item['title'] + (' · notified' if item.get('notified_at') is not None else '')
                self.store.append([item['id'], local.strftime('%H:%M'), title])

    def new(self, *_):
        self.current_id = None
        for key, value in dict(title='', date=self.selected_date, time='10:00', timezone=self.zone).items():
            self.fields[key].set_text(value)
        self.notes.get_buffer().set_text('')
        self.status.set_text('Saved reminders notify at the selected time, or when you next log in.')
        self.fields['title'].grab_focus()

    def select(self, selection):
        model, row = selection.get_selected()
        if row is None:
            return
        item = self.items[model[row][0]]
        self.current_id = item['id']
        wall = datetime.fromtimestamp(item['at'], ZoneInfo(item['timezone']))
        for key, value in dict(title=item['title'], date=wall.date().isoformat(),
                               time=wall.strftime('%H:%M'), timezone=item['timezone']).items():
            self.fields[key].set_text(value)
        self.notes.get_buffer().set_text(item['notes'])
        self.status.set_text('Notification delivered' if item.get('notified_at') is not None else 'Notification pending')

    def save(self, *_):
        try:
            values = {key: field.get_text().strip() for key, field in self.fields.items()}
            buffer = self.notes.get_buffer()
            notes = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)
            item = reminders.save(values['title'], f"{values['date']}T{values['time']}", values['timezone'], notes, self.current_id)
            self.current_id = item['id']
            self.reload()
            self.status.set_text('Saved. You can close this window; notifications run in the background.')
        except Exception as error:
            self.status.set_text(str(error))

    def remove(self, *_):
        if self.current_id is None:
            return
        dialog = Gtk.MessageDialog(transient_for=self, modal=True, message_type=Gtk.MessageType.QUESTION,
                                   buttons=Gtk.ButtonsType.OK_CANCEL, text='Delete this reminder?')
        response = dialog.run()
        dialog.destroy()
        if response != Gtk.ResponseType.OK:
            return
        try:
            reminders.delete(self.current_id)
            self.new()
            self.reload()
            self.status.set_text('Reminder deleted')
        except Exception as error:
            self.status.set_text(str(error))


def run(selected_date):
    GLib.set_prgname('calendar-reminders')
    GLib.set_application_name('Calendar reminders')
    window = Editor(selected_date)
    window.show_all()
    Gtk.main()
