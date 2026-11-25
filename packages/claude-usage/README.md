# Claude usage in Waybar

`claude-usage` emits one Waybar JSON object with the remaining Claude plan
allowance (Pro/Max), the same data Claude Code's `/usage` shows. It reads the
OAuth access token that Claude Code stores in `~/.claude/.credentials.json`
(or `$CLAUDE_CONFIG_DIR/.credentials.json`) and calls
`GET https://api.anthropic.com/api/oauth/usage`. It does not run a model or use
tokens from the allowance. The token is only sent to that endpoint; it is never
logged, copied or written, and neither are responses.

The module never refreshes the token: refreshing rotates the refresh token and
would sign Claude Code out. When the access token has expired (Claude Code
renews it whenever it runs) the bar shows `Claude —` and the tooltip asks you
to open `claude`. A 401 is treated the same way.

The bar shows the lowest remaining percentage across the general limits (the
5-hour session and the all-models week). Model-scoped weekly limits, the plan
and extra usage (if enabled) are listed in the tooltip. At 25% remaining it
turns amber; at 10% red. Missing data, failed requests, and elapsed reset
timestamps show `Claude —` instead of a guessed value. The structured `limits`
list is preferred; the older `five_hour`/`seven_day` fields are a fallback.

Waybar polls every 60 seconds (this is an Anthropic API, so it polls less often
than the local Codex app-server); each request times out after 15 seconds.
Right-clicking refreshes immediately (`exec-on-event`); left-clicking opens
https://claude.ai/settings/usage in the default browser via `uwsm app -t
service`, which returns immediately so Waybar's worker is not held (see the
[Codex module](../codex-usage/README.md) for why).

The endpoint is the one Claude Code itself uses and is not a documented public
API; if its shape changes the module falls back to `Claude —`.
`CLAUDE_USAGE_URL` overrides the endpoint (used by tests).

```sh
node --test packages/claude-usage/usage.test.mjs
nix-build -A claude-usage -o result-claude-usage
./result-claude-usage/bin/claude-usage
```

The regular user-package installer includes this package. Reload Waybar after
changing its config:

```sh
systemctl --user kill --kill-whom=main --signal=SIGUSR2 'app-hypr\x2dwaybar@autostart.service'
```
