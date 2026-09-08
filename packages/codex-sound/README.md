# Codex completion sound

`codex-complete-sound` accepts Codex's notify JSON argument, filters for
`agent-turn-complete`, and plays an original three-note rising “tu-lu-lú” through
PipeWire at half volume. The 0.625-second WAV is synthesized during the Nix build
from `generate-tone.py`, with soft attacks and releases; no audio binary or
download is stored in Git. Playback failure never interrupts Codex.

The user installer automatically runs `scripts/configure-codex-sound.py`
after installing the packages (never in build-only mode). It can also be run
separately with Python 3.11 or later. It backs up the existing private Codex configuration,
sets the notify command and disables TUI desktop notifications. Existing
Codex sessions need to be restarted/resumed to pick up these settings.

The full Codex config and backups are kept outside Git.
See https://learn.chatgpt.com/docs/config-file/config-advanced#notifications.
