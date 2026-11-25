# Codex idle border state

`state.py` runs as `codex-border.service` in Hyprland. It polls local Codex
metadata and visible window identities every 500 ms, incrementally tails the
matching parent session's JSONL rollout, and atomically publishes only confirmed
idle window addresses in `$XDG_RUNTIME_DIR/codex-border-state`. The first line
is a freshness timestamp. No conversation text is written to this file.

A matching `task_complete` must settle for one second, with no later
`task_started` and no active goal. Waiting for agents, long tool calls, quiet
periods and missing spinners do not establish completion. Subagent sessions
cannot light up their parent's window. Ambiguous thread names, unsupported
metadata schemas, missing logs and watcher errors produce no idle addresses.
Lua removes the effect if the state file is older than three seconds.

Border resets explicitly restore Hyprland's configured active/inactive theme
colors. On Hyprland 0.55.4, setting a border color to `-1` installs an empty
gradient; the border shader can then reuse a preceding window's rainbow
uniforms. An empty gradient is not a valid reset even when `getprop` reports
`0deg` and the border width has returned to two pixels.

Window identity uses the default Codex `thread-name | project-name` layout,
including its optional activity prefix. It never uses that title to decide
that work has finished. Custom layouts or project labels that cannot be
uniquely associated with metadata keep the normal border.

Build with `nix-build . -A codex-border`. The installer links/enables the user
service. Run `systemctl --user restart codex-border.service` after rebuilding
and installing the package, and `hyprctl reload config-only` after Lua edits.
Run regression checks with `python3 -m unittest discover -s tests -p
'test_codex_border.py'` from the repository root.
Run `lua tests/test_codex_border.lua` for the actual Lua state callbacks and
nonempty theme-color restoration checks.
