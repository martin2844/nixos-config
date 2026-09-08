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
