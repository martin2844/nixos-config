"""Publish confirmed Codex idle windows for Hyprland's border animation.

Titles identify a thread, never prove completion. Read local SQLite metadata
and incremental rollout lifecycle events; do not store conversation content.
"""
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import time

SPINNERS = frozenset("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏")
LIFECYCLE = re.compile(rb'"type"\s*:\s*"(?:task_started|task_complete|turn_aborted)"')
CHUNK = 256 * 1024


class Rollout:
    def __init__(self, path):
        self.path = Path(path)
        self.offset = 0
        self.inode = None
        self.state = "unknown"
        self.turn_id = None
        self.completed_since = None

    def consume(self, line, now):
        if not LIFECYCLE.search(line):
            return False
        try:
            event = json.loads(line)
        except (ValueError, UnicodeError):
            return False
        if not isinstance(event, dict) or event.get("type") != "event_msg":
            return False
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            return False
        kind = payload.get("type")
        turn = payload.get("turn_id")
        if kind == "task_started":
            self.state, self.turn_id, self.completed_since = "busy", turn, None
        elif kind == "task_complete":
            if not isinstance(turn, str) or not turn:
                self.state, self.turn_id, self.completed_since = "unknown", None, None
                return True
            if self.turn_id is not None and turn != self.turn_id:
                return False
            self.state, self.turn_id, self.completed_since = "idle", turn, now
        elif kind == "turn_aborted":
            self.state, self.turn_id, self.completed_since = "unknown", None, None
        else:
            return False
        return True

    def update(self, now):
        try:
            with self.path.open("rb") as stream:
                stat = os.fstat(stream.fileno())
                if self.inode != stat.st_ino or stat.st_size < self.offset:
                    self.state, self.turn_id, self.completed_since = "unknown", None, None
                    self.inode = stat.st_ino
                    self.offset = stat.st_size
                    stream.seek(max(0, stat.st_size - CHUNK))
                    ending = stream.read()
                    self.offset -= len(ending.rsplit(b"\n", 1)[-1])
                    # Search backwards for the latest real lifecycle event. Bound
                    # bootstrap work for very large turns; missing evidence stays
                    # unknown until the next lifecycle event arrives.
                    end = stat.st_size
                    for _ in range(64):
                        start = max(0, end - CHUNK)
                        stream.seek(start)
                        data = stream.read(stat.st_size - start)
                        lines = data.splitlines(keepends=True)
                        if start:
                            lines = lines[1:]
                        for line in reversed(lines):
                            if line.endswith(b"\n") and self.consume(line, now):
                                return self.state
                        if not start:
                            break
                        end = start
                else:
                    stream.seek(self.offset)
                    while line := stream.readline():
                        if not line.endswith(b"\n"):
                            break
                        self.consume(line, now)
                        self.offset = stream.tell()
        except OSError:
            self.state, self.completed_since = "unknown", None
        return self.state

    def confirmed_idle(self, now, goal_status):
        # A goal may immediately start another turn after task_complete. Never
        # advertise completion while the goal remains active.
        return (self.state == "idle" and goal_status != "active"
                and self.completed_since is not None and now - self.completed_since >= 1)


def readonly(path):
    return sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=0.2)


def threads(codex_home):
    with readonly(codex_home / "state_5.sqlite") as database:
        database.row_factory = sqlite3.Row
        return [dict(row) for row in database.execute(
            "SELECT id, name, cwd, rollout_path, source FROM threads "
            "WHERE archived = 0 AND name IS NOT NULL AND name != ''")
            if not is_subagent(row["source"])]


def is_subagent(source):
    try:
        metadata = json.loads(source)
    except (ValueError, TypeError):
        return False
    return isinstance(metadata, dict) and "subagent" in metadata


def goals(codex_home):
    path = codex_home / "goals_1.sqlite"
    if not path.exists():
        return {}
    with readonly(path) as database:
        return dict(database.execute("SELECT thread_id, status FROM thread_goals"))


def normalize(value):
    return " ".join(value.split())


def title_part_matches(label, value, maximum):
    value = normalize(value)
    return label == value or (label.endswith("...") and len(label) == maximum
                              and value.startswith(label[:-3]))


def match_thread(title, candidates):
    title = normalize(title)
    if "Action Required" in title or title.startswith("●"):
        return None
    if title[:1] in SPINNERS:
        title = title[1:].lstrip()
    # A title-generation spinner may also follow the thread name.
    if " | " not in title:
        return None
    label, project = title.rsplit(" | ", 1)
    if label[-1:] in SPINNERS:
        label = label[:-1].rstrip()
    matches = [row for row in candidates
               if title_part_matches(label, row["name"], 48)
               and title_part_matches(project, Path(row["cwd"]).name, 24)]
    # Duplicate/truncated names must not select an arbitrary session.
    return matches[0] if len(matches) == 1 else None


def idle_windows(windows, candidates, goal_states, rollouts, now):
    result = []
    for window in windows:
        if window.get("class") != "com.mitchellh.ghostty":
            continue
        title = window.get("title", "")
        thread = match_thread(title, candidates)
        if thread is None:
            continue
        path = thread["rollout_path"]
        reader = rollouts.setdefault(path, Rollout(path))
        reader.update(now)
        # The spinner is useful as an additional negative signal while log
        # writes catch up, but its absence never establishes idleness.
        if title[:1] not in SPINNERS and reader.confirmed_idle(now, goal_states.get(thread["id"])):
            result.append(window["address"])
    return result


def publish(destination, addresses):
    valid = [a for a in addresses if re.fullmatch(r"0x[0-9a-fA-F]+", a)]
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(str(int(time.time())) + "\n" + "\n".join(valid) + "\n")
    temporary.replace(destination)


def main():
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    destination = Path(os.environ["XDG_RUNTIME_DIR"]) / "codex-border-state"
    hyprctl = "/run/current-system/sw/bin/hyprctl"
    rollouts = {}
    while True:
        try:
            windows = json.loads(subprocess.check_output([hyprctl, "clients", "-j"], timeout=2))
            candidates = threads(codex_home)
            addresses = idle_windows(windows, candidates, goals(codex_home), rollouts, time.monotonic())
            live_paths = {row["rollout_path"] for w in windows
                          if (row := match_thread(w.get("title", ""), candidates)) is not None}
            rollouts = {path: reader for path, reader in rollouts.items() if path in live_paths}
        except (OSError, sqlite3.Error, ValueError, subprocess.SubprocessError):
            addresses = []
        publish(destination, addresses)
        time.sleep(0.5)


if __name__ == "__main__":
    main()
