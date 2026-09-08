# Codex completion sound

`codex-complete-sound` accepts Codex's notify JSON argument, filters for
`agent-turn-complete`, and plays the freedesktop completion sound through
PipeWire at half volume. Playback failure never interrupts Codex.

The user installer automatically runs `scripts/configure-codex-sound.py`
after installing the packages (never in build-only mode). It can also be run
separately with Python 3.11 or later. It backs up the existing private Codex configuration,
sets the notify command and disables TUI desktop notifications. Existing
Codex sessions need to be restarted/resumed to pick up these settings.

The full Codex config and backups are kept outside Git.
See https://learn.chatgpt.com/docs/config-file/config-advanced#notifications.
