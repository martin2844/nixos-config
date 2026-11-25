# pbcopy and pbpaste

Small Wayland wrappers around the pinned `wl-clipboard` package. Available as
executables to shells and scripts in the managed user profile.

```sh
printf 'Hello' | pbcopy
pbpaste
pbcopy < notes.txt
pbpaste > clipboard.txt
```

`pbpaste` preserves the clipboard's bytes without adding a newline. These provide
the usual stdin/stdout workflow; optional arguments are wl-copy/wl-paste options,
not macOS pasteboard options. A running Wayland session is required.

Build with `nix-build . -A pbclipboard -o result-pbclipboard`. The user installer
includes the package; no system rebuild or shell aliases are needed.
