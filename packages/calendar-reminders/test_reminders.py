import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
import reminders as r


class RemindersTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'calendar/reminders.json'

    def add(self, at='2026-09-18T10:00', reminder_id='quick', title='Control rápido'):
        return r.save(title, at, 'Europe/Madrid', 'Notas <sin markup>', reminder_id, self.path)

    def test_confirmed_times(self):
        from datetime import datetime, timezone
        self.assertEqual(datetime.fromtimestamp(r.timestamp('2026-09-18T10:00', 'Europe/Madrid'), timezone.utc).isoformat(), '2026-09-18T08:00:00+00:00')
        self.assertEqual(datetime.fromtimestamp(r.timestamp('2026-09-23T14:30', 'Europe/Madrid'), timezone.utc).isoformat(), '2026-09-23T12:30:00+00:00')

    def test_dst_gap_and_duplicate_rejected(self):
        for when in ['2026-03-29T02:30', '2026-10-25T02:30']:
            with self.assertRaises(ValueError):
                r.timestamp(when, 'Europe/Madrid')
        self.assertEqual(r.timestamp('2026-10-25T03:30', 'Europe/Madrid') - r.timestamp('2026-10-25T01:30', 'Europe/Madrid'), 3 * 3600)

    def test_due_catchup_once_and_future_untouched(self):
        first = self.add()
        self.add('2026-09-23T14:30', 'weekly')
        sent = []
        now = first['at'] + 3600
        r.tick(self.path, lambda: now, lambda item: sent.append(item['id']))
        r.tick(self.path, lambda: now, lambda item: sent.append(item['id']))
        self.assertEqual(sent, ['quick'])
        data = r.read(self.path)['reminders']
        self.assertEqual(data[0]['notified_at'], now)
        self.assertIsNone(data[1]['notified_at'])

    def test_failed_delivery_retries_without_repeating_success(self):
        first = self.add()
        self.add(reminder_id='second')
        def send(item):
            if item['id'] == 'second':
                raise RuntimeError('No notification bus')
            return 10
        with self.assertRaises(RuntimeError):
            r.tick(self.path, lambda: first['at'], send)
        sent = []
        r.tick(self.path, lambda: first['at'], lambda item: sent.append(item['id']))
        self.assertEqual(sent, ['second'])

    def test_edit_does_not_duplicate_delivered_but_reschedule_rearms(self):
        first = self.add()
        r.tick(self.path, lambda: first['at'], lambda item: 1)
        edited = self.add(title='Updated')
        self.assertIsNotNone(edited['notified_at'])
        rescheduled = self.add(at='2026-09-19T11:00')
        self.assertIsNone(rescheduled['notified_at'])
        self.assertEqual(len(r.read(self.path)['reminders']), 1)

    def test_delete_prevents_notification(self):
        item = self.add()
        r.delete(item['id'], self.path)
        sent = []
        r.tick(self.path, lambda: item['at'], lambda item: sent.append(item))
        self.assertEqual(sent, [])

    def test_concurrent_edits_preserve_all_records(self):
        errors = []
        def save(index):
            try:
                self.add(reminder_id=str(index))
            except Exception as error:
                errors.append(error)
        threads = [threading.Thread(target=save, args=(index,)) for index in range(12)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(errors, [])
        self.assertEqual(len(r.read(self.path)['reminders']), 12)

    def test_bad_file_never_overwritten(self):
        self.add()
        self.path.write_text('{invalid')
        with self.assertRaises(json.JSONDecodeError):
            self.add()
        self.assertEqual(self.path.read_text(), '{invalid')

    def test_atomic_failure_preserves_old_file(self):
        self.add()
        before = self.path.read_bytes()
        with patch.object(r.os, 'replace', side_effect=OSError('Disk full')):
            with self.assertRaises(OSError):
                self.add(title='Update')
        self.assertEqual(self.path.read_bytes(), before)

    def test_concurrent_checks_only_deliver_once(self):
        item = self.add()
        sent = []
        threads = [threading.Thread(target=r.tick, args=(self.path, lambda: item['at'], lambda reminder: sent.append(reminder['id']))) for _ in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(sent, ['quick'])


if __name__ == '__main__':
    unittest.main()
