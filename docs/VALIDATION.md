# Validation — 2026-09-08

- `scripts/rebuild build`: successful full NixOS build from pinned nixpkgs.
- All package outputs built and match the pre-migration installed store paths:
  ChatGPT, nmgui Internet panel, Neovim tools, Blink, networkmanager_dmenu.
- Nix files formatted with nixfmt; imports through the old linked package paths
  evaluate correctly too.
- Python/JSON/shell syntax checked; all 18 live link targets verified.
- Hyprland --verify-config succeeded, hyprctl reload returned ok, and
  hyprctl configerrors returned no errors after linking.
- Linking script rerun in preview mode is idempotent.
- Original files preserved in ~/.local/state/nixos-config/backups/
  20260908-131012-281926/ (includes the previous extra logs/backups).
- No system activation performed: sudo needs interactive authentication and
  this migration only reorganizes source files. The system build is validated;
  a test activation is a separate action using scripts/rebuild test.
- The running generation differs from the build output; /etc/nixos on disk was
  used as the system source, and no assertion of identical generations is made.

## Public repository installer — 2026-09-08

`./install.sh --check` builds the complete system and user packages without
activation. Installer tests cover successful build-only operation and stopping
after a package build failure, with no profile/home/sudo changes in either case.
The activation branch requires interactive sudo and was not executed in this
publication task. User authentication and fresh-machine activation are not
validated by a successful build.

## Full desktop sync — 2026-09-08

`./install.sh --check` successfully built the complete NixOS system and every
user package, including HyprMod, screenshot preview, completion audio, Zsh,
Waybar, desktop controls and dark-theme setup. No activation or profile changes
were performed by this check. Installer unit tests and Python/JSON/shell syntax
checks passed; Hyprland reported no runtime configuration errors.

The current wallpaper matches the Nix-packaged Plasma Subarctic image by SHA-256;
the repo stores its user-profile reference instead of a copied image. Private
Codex settings and generated wallpaper copies remain outside version control.
