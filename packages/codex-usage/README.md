# Codex usage in Waybar

`codex-usage` emits one Waybar JSON object. It uses the installed Codex CLI's
authenticated `app-server` over stdio to call `account/rateLimits/read`.
It does not start a conversation or run a model. The CLI handles authentication;
this module does not read or copy tokens, store responses, or log account payloads.

The bar shows the lowest remaining percentage across the main `codex` bucket's
available windows. The tooltip lists the actual window lengths, local reset
times, and other model buckets separately. No five-hour window is assumed.
At 25% remaining it turns amber; at 10% it turns red. Missing data, failed
requests, and elapsed reset timestamps show `Codex —` instead of a guessed value.
Waybar polls every 15 seconds; each request times out after 15 seconds and its
child process is terminated. The tooltip includes the local time of the last
successful query, including seconds, so an old reading is visible. The allowance
comes from the server; its value can remain unchanged between queries.
Right-clicking refreshes immediately using Waybar's `exec-on-event` behavior;
left-clicking opens the installed ChatGPT desktop app.

The [Waybar package](../waybar/) includes the shared hover-tooltip fix: refreshed
JSON tooltip text no longer restarts GTK's hover timer across the bar.

The click launcher explicitly uses `uwsm app -t service`, which returns after
starting the app. Waybar's polling worker waits for click commands to exit;
UWSM's default `scope` mode can hold that worker until ChatGPT closes, freezing
the percentage regardless of the polling interval.

The `↻` counter shows available earned resets, using the authoritative
`rateLimitResetCredits.availableCount`, including zero. Missing counts show `—`.
The tooltip lists reset expiry dates when provided. Reading this counter never
consumes a reset; automatic quota renewal dates are shown separately above it.

By default the CLI is `~/.local/bin/codex`; `CODEX_USAGE_BIN` overrides its path.
It uses the CLI's normal account and configuration (including `CODEX_HOME` if set).
Sign in with `codex login` if the CLI has no account. This shows the Codex account
allowance, not a combined percentage for every ChatGPT product.

Protocol: https://learn.chatgpt.com/docs/app-server#6-rate-limits-chatgpt

```sh
node --test packages/codex-usage/usage.test.mjs
nix-build -A codex-usage -o result-codex-usage
./result-codex-usage/bin/codex-usage
```

The regular user-package installer includes this package. For a standalone install:

```sh
nix --extra-experimental-features nix-command profile add ./result-codex-usage
```

When updating an existing install, replace the `codex-usage` profile entry with
the newly built package, as `scripts/install-user.py` does. Reload Waybar after
changing its polling interval or click actions (the linked config is read at
startup):

```sh
systemctl --user kill --kill-whom=main --signal=SIGUSR2 'app-hypr\x2dwaybar@autostart.service'
```
