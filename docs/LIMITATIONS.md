# Scope and restoration notes

- This is a single-host configuration, retaining disk UUIDs, username `martin`,
  and existing absolute home paths. Adjust these before installing elsewhere.
- Nixpkgs is pinned to revision c25784012c9982bca5b3e0de87e90bbdac8927d3.
  Update the release URL and unpacked hash together, then rebuild and verify
  Hyprland's Lua API before activating an updated system.
- ChatGPT's upstream download URL contains `latest`; its fixed hash protects
  integrity but does not guarantee old versions remain downloadable. Preserve
  the existing Downloads/chatgpt_amd64.deb separately or the Nix store closure.
  Installers and proprietary application binaries are not committed here.
- Neovim plugins use LazyVim's lockfile and are fetched by Lazy. The native Blink
  plugin comes from nixpkgs; Nix tools and Blink are built by install-user.py.
- Plasma's personal session state, browser profiles, keyrings, application data,
  Bluetooth pairings, NetworkManager connection secrets, and Tailscale login
  state are not tracked. The system modules enabling those services are tracked.
- The Internet panel is a locally maintained extension of nmgui, not upstream.
- /etc/nixos was copied from disk; it is not a live link. Use scripts/rebuild.
  Earlier staged setup directories may contain proposals that were never applied;
  they are intentionally not the source of truth for this repository.

An earlier unactivated proposal in ~/hyprland-setup/default-nixos added
`services.displayManager.defaultSession = "hyprland-uwsm"`,
`services.displayManager.sddm.settings.Users.RememberLastSession = false`, and
`kdePackages.kdialog` to systemPackages. These are not in the live /etc/nixos
files and have not been silently applied as part of this migration. The current
SDDM configuration matches the copied system configuration.
