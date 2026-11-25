# OpenCode V2 on NixOS

OpenCode 2.0.32 is fetched from the hash-pinned official
[`@opencode/cli-linux-x64` package](https://www.npmjs.com/package/@opencode/cli-linux-x64).
This preserves V2 instead of installing the older V1 in our pinned nixpkgs.
Only the Nix expression is versioned; Nix downloads the binary during the build.

The upstream installer places a generic Linux binary in `~/.opencode/bin`.
Its `/lib64/ld-linux-x86-64.so.2` interpreter cannot run directly on NixOS.
`autoPatchelfHook` supplies the Nix loader and library paths. Stripping is disabled
to preserve Bun's embedded application. The wrapper supplies native-module
libraries, Git and ripgrep. Both `opencode` and `opencode2` launch V2.
Automatic binary updates are disabled so an upstream update cannot replace the
patched installation. Update the version and archive hash here, rebuild, and
replace the managed `opencode` profile entry to upgrade.

The regular user-package installer includes this package. To install it alone:

```sh
nix-build -A opencode -o result-opencode
nix --extra-experimental-features nix-command profile add ./result-opencode
opencode --version
opencode
```

Do not prepend `~/.opencode/bin` to PATH: the managed user profile supplies both
commands. On this machine, the original downloaded executables were backed up
under `~/.local/state/nixos-config/backups/` and their old paths replaced with
links to `~/.nix-profile/bin/` so already-open shells keep working.
Account logins, sessions and runtime state stay outside the repository.
