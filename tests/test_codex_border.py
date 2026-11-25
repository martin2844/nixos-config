import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    "codex_border", Path(__file__).resolve().parents[1] / "packages/codex-border/state.py")
border = importlib.util.module_from_spec(spec)
spec.loader.exec_module(border)


def event(kind, turn="one"):
    return (json.dumps({"type": "event_msg", "payload": {"type": kind, "turn_id": turn}}) + "\n").encode()


class CodexBorderTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "rollout.jsonl"
        self.thread = {"id": "parent", "name": "Long job", "cwd": "/home/user/project",
                       "rollout_path": str(self.path)}
        self.window = {"address": "0x123", "class": "com.mitchellh.ghostty",
                       "title": "Long job | project"}

    def test_long_running_turn_without_spinner_never_idle(self):
        self.path.write_bytes(event("task_started") + b'{"type":"event_msg","payload":{"type":"token_count"}}\n')
        readers = {}
        self.assertEqual(border.idle_windows([self.window], [self.thread], {}, readers, 0), [])
        self.assertEqual(border.idle_windows([self.window], [self.thread], {}, readers, 7200), [])

    def test_completion_requires_settling_then_next_start_clears(self):
        self.path.write_bytes(event("task_complete"))
        readers = {}
        self.assertEqual(border.idle_windows([self.window], [self.thread], {}, readers, 0), [])
        self.assertEqual(border.idle_windows([self.window], [self.thread], {}, readers, 1.1), ["0x123"])
        with self.path.open("ab") as stream:
            stream.write(event("task_started", "two"))
        self.assertEqual(border.idle_windows([self.window], [self.thread], {}, readers, 2), [])

    def test_active_goal_suppresses_idle_between_automatic_turns(self):
        self.path.write_bytes(event("task_complete"))
        reader = border.Rollout(self.path)
        reader.update(0)
        self.assertFalse(reader.confirmed_idle(3600, "active"))
        self.assertTrue(reader.confirmed_idle(3600, "complete"))

    def test_unrelated_completion_does_not_end_current_turn(self):
        self.path.write_bytes(event("task_started", "current"))
        reader = border.Rollout(self.path)
        reader.update(0)
        with self.path.open("ab") as stream:
            stream.write(event("task_complete", "previous"))
        self.assertEqual(reader.update(1), "busy")
        self.assertFalse(reader.confirmed_idle(10, None))

    def test_partial_line_after_bootstrap_is_not_skipped(self):
        next_start = event("task_started", "two")
        self.path.write_bytes(event("task_complete") + next_start[:35])
        reader = border.Rollout(self.path)
        self.assertEqual(reader.update(0), "idle")
        with self.path.open("ab") as stream:
            stream.write(next_start[35:])
        self.assertEqual(reader.update(1), "busy")

    def test_missing_or_truncated_log_loses_idle_evidence(self):
        self.path.write_bytes(event("task_complete"))
        reader = border.Rollout(self.path)
        reader.update(0)
        self.path.write_bytes(b'{}\n')
        self.assertEqual(reader.update(2), "unknown")
        self.path.unlink()
        self.assertEqual(reader.update(3), "unknown")

    def test_ambiguous_names_and_unrelated_windows_fail_closed(self):
        duplicate = dict(self.thread, id="other")
        self.assertIsNone(border.match_thread(self.window["title"], [self.thread, duplicate]))
        self.assertIsNone(border.match_thread("user@host:~", [self.thread]))
        self.assertIsNone(border.match_thread("[ ! ] Action Required | project", [self.thread]))

    def test_spinner_is_negative_signal_even_before_start_event_flushes(self):
        self.path.write_bytes(event("task_complete"))
        readers = {}
        border.idle_windows([self.window], [self.thread], {}, readers, 0)
        working = dict(self.window, title="⠋ Long job | project")
        self.assertEqual(border.idle_windows([working], [self.thread], {}, readers, 2), [])

    def test_other_json_records_cannot_supply_completion(self):
        self.path.write_bytes(b'{"type":"response_item","payload":{"type":"task_complete"}}\n')
        reader = border.Rollout(self.path)
        self.assertEqual(reader.update(0), "unknown")

    def test_subagent_sources_are_excluded_regardless_of_json_spacing(self):
        self.assertTrue(border.is_subagent('{ "subagent": {"thread_spawn": {}} }'))
        self.assertFalse(border.is_subagent('cli'))

    def test_incomplete_completion_schema_and_malformed_records_fail_closed(self):
        for record in [
            {"type": "event_msg", "payload": {"type": "task_complete"}},
            [{"type": "task_complete"}],
        ]:
            self.path.write_text(json.dumps(record) + '\n')
            reader = border.Rollout(self.path)
            self.assertEqual(reader.update(0), "unknown")


if __name__ == "__main__":
    unittest.main()
