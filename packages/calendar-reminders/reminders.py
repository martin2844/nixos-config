"""Local calendar storage, timezone validation and retryable desktop notifications."""
import argparse
from contextlib import contextmanager
from datetime import datetime
import fcntl
import html
import json
import os
from pathlib import Path
import tempfile
import time
import uuid
from zoneinfo import ZoneInfo


def data_path():
    return Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share')) / 'desktop-calendar/reminders.json'


def local_zone():
    zone = os.environ.get('TZ', '').removeprefix(':')
    if zone and not zone.startswith('/'):
        return zone
    resolved = str(Path('/etc/localtime').resolve())
    if '/zoneinfo/' in resolved:
        return resolved.split('/zoneinfo/', 1)[1]
    raise ValueError('Cannot detect timezone; set TZ to an IANA timezone such as Europe/Madrid')


def timestamp(value, zone):
    """Reject DST gaps/ambiguous wall times rather than silently moving a reminder."""
    wall = datetime.fromisoformat(value)
    if wall.tzinfo is not None:
        raise ValueError('Enter a local date and time without a UTC offset')
    tz = ZoneInfo(zone)
    candidates = {wall.replace(tzinfo=tz, fold=fold).timestamp() for fold in (0, 1)
                  if datetime.fromtimestamp(wall.replace(tzinfo=tz, fold=fold).timestamp(), tz).replace(tzinfo=None) == wall}
    if not candidates:
        raise ValueError('This time does not exist because the clocks change. Choose another time.')
    if len(candidates) != 1:
        raise ValueError('This time occurs twice because the clocks change. Choose another time.')
    return int(candidates.pop())


def read(path=None):
    path = path or data_path()
    if not path.exists():
        return {'version': 1, 'reminders': []}
    data = json.loads(path.read_text())
    if data.get('version') != 1 or not isinstance(data.get('reminders'), list):
        raise ValueError('Unsupported calendar data format')
    ids = set()
    for item in data['reminders']:
        if (not isinstance(item, dict) or not isinstance(item.get('id'), str)
                or item['id'] in ids or not isinstance(item.get('title'), str)
                or not isinstance(item.get('notes'), str) or not isinstance(item.get('at'), int)
                or not isinstance(item.get('timezone'), str)
                or (item.get('notified_at') is not None and not isinstance(item['notified_at'], int))):
            raise ValueError('Invalid reminder data; restore the data file before editing')
        ZoneInfo(item['timezone'])
        datetime.fromtimestamp(item['at'], ZoneInfo(item['timezone']))
        ids.add(item['id'])
    return data


def write(path, data):
    fd, name = tempfile.mkstemp(prefix='.reminders-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as output:
            json.dump(data, output, ensure_ascii=False, indent=2)
            output.write('\n')
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(name):
            os.unlink(name)


@contextmanager
def locked(path=None):
    path = path or data_path()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield path


def save(title, at, zone, notes='', reminder_id=None, path=None):
    title = title.strip()
    if not title:
        raise ValueError('A title is required')
    at = timestamp(at, zone)
    reminder_id = reminder_id or str(uuid.uuid4())
    with locked(path) as target:
        data = read(target)
        previous = next((item for item in data['reminders'] if item['id'] == reminder_id), None)
        item = dict(id=reminder_id, title=title, at=at, timezone=zone, notes=notes.strip(),
                    notified_at=previous.get('notified_at') if previous and previous['at'] == at else None)
        data['reminders'] = sorted([r for r in data['reminders'] if r['id'] != reminder_id] + [item], key=lambda r: (r['at'], r['id']))
        write(target, data)
    return item


def delete(reminder_id, path=None):
    with locked(path) as target:
        data = read(target)
        data['reminders'] = [r for r in data['reminders'] if r['id'] != reminder_id]
        write(target, data)


def notify(item):
    from gi.repository import Gio, GLib
    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    when = datetime.fromtimestamp(item['at'], ZoneInfo(item['timezone'])).strftime('%d/%m/%Y %H:%M')
    body = html.escape(f"{when} · {item['timezone']}\n{item['notes']}")
    result = bus.call_sync('org.freedesktop.Notifications', '/org/freedesktop/Notifications',
                          'org.freedesktop.Notifications', 'Notify',
                          GLib.Variant('(susssasa{sv}i)', ('Calendar', 0, 'appointment-soon',
                              item['title'], body, [], {'urgency': GLib.Variant('y', 1),
                              'desktop-entry': GLib.Variant('s', 'calendar-reminders')}, 0)),
                          GLib.VariantType.new('(u)'), Gio.DBusCallFlags.NONE, 5000, None)
    return result.unpack()[0]


def tick(path=None, clock=time.time, send=notify):
    delivered = []
    with locked(path) as target:
        data = read(target)
        for item in data['reminders']:
            if item.get('notified_at') is None and item['at'] <= clock():
                notification_id = send(item)  # failure leaves this and later reminders pending
                item['notified_at'] = int(clock())
                write(target, data)  # persist each success before attempting another notification
                delivered.append(notification_id)
    return delivered


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    add = sub.add_parser('add')
    add.add_argument('--title', required=True)
    add.add_argument('--at', required=True, help='Local ISO date and time: 2026-09-18T10:00')
    add.add_argument('--timezone', default=None)
    add.add_argument('--notes', default='')
    add.add_argument('--id')
    sub.add_parser('list')
    remove = sub.add_parser('delete')
    remove.add_argument('id')
    sub.add_parser('tick')
    editor = sub.add_parser('edit')
    editor.add_argument('date', nargs='?', default=datetime.now().date().isoformat())
    args = parser.parse_args()
    try:
        if args.command == 'add':
            print(json.dumps(save(args.title, args.at, args.timezone or local_zone(), args.notes, args.id), ensure_ascii=False))
        elif args.command == 'list':
            print(json.dumps(read(), ensure_ascii=False, indent=2))
        elif args.command == 'delete':
            delete(args.id)
        elif args.command == 'tick':
            for notification_id in tick():
                print(f'Delivered notification {notification_id}', flush=True)
        else:
            from editor import run
            run(args.date)
    except Exception as error:
        parser.exit(1, f'calendar-reminders: {error}\n')


if __name__ == '__main__':
    main()
