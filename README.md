# Martin's NixOS desktop

Plain NixOS configuration, Plasma + Hyprland/UWSM, user dotfiles, and local
package overrides. No flakes or Home Manager. Created from the working machine
on 2026-09-08. The host/user name is currently `nixos` / `martin`.

## Layout

- `hosts/nixos/`: actual `/etc/nixos` configuration and hardware module.
- `home/`: Hyprland Lua/bindings/scripts, Waybar, UWSM autostart, Ghostty,
  Rofi, notifications, GTK appearance, file associations, and LazyVim + lockfile.
- `packages/internet-panel/`: nixpkgs nmgui with the custom Ethernet section.
- `packages/chatgpt/`: Debian repackaging and the Qt plugin startup fix.
- `packages/nvim-tools/`: Nix language servers/tools and native Blink plugin.
- `nix/`: hash-pinned nixpkgs channel, shared by system and package builds.
- `links.json`: explicit mapping of live user paths into this repository.
- `docs/`: captured versions, original user-profile inventory, and limitations.

## Daily editing

User config directories and package source directories are symlinks into this
checkout. Editing `~/.config/hypr/bindings.lua`, for example, changes the tracked
file immediately. `git status` / `git diff` show changes; commit them normally.
Neovim plugin updates also change the tracked lockfile. Keep this checkout in
place, or rerun the link script after moving it.

Edit system settings in `hosts/nixos/`, not `/etc/nixos`. The original root-owned
files remain untouched: a bare `sudo nixos-rebuild switch` still reads those old
files. Use the repository script to explicitly select this configuration:

```sh
./scripts/rebuild build
./scripts/rebuild test
# After checking the test generation:
./scripts/rebuild switch
```

`build` requires no sudo. `test` activates without changing the boot default;
`switch` makes it persistent. These commands preserve the Plasma/SDDM modules.
They do not install the separate user-profile packages below.

## Restore user configuration and packages

```sh
nix-shell -p python3 --run 'python3 scripts/link-home.py'         # preview
nix-shell -p python3 --run 'python3 scripts/link-home.py --apply'
nix-shell -p python3 --run 'python3 scripts/install-user.py'
```

Linking backs up existing destinations under
`~/.local/state/nixos-config/backups/<timestamp>/`. Nothing is deleted. Package
installation builds all outputs before replacing the four managed profile entries;
other profile entries are retained. Log into Hyprland UWSM to start the desktop.
For a running session, `hyprctl reload` reloads compositor configuration; restart
Waybar separately after changing its config.

Wallpaper files are tracked under `home/.config/hypr/`. The wallpaper picker
writes there through the directory symlink, so changing it produces a Git diff.
The wallpaper helper currently references a store-path kdialog; see limitations.

## Version control

This is a local repository; no remote is configured and nothing is published.
Browser/app profiles, credentials, Wi-Fi passwords, Tailscale state, screenshots,
logs, binaries, and caches are outside its scope. Host disk UUIDs, username, and
the current wallpaper are included. Existing setup backups remain outside Git.

See `docs/LIMITATIONS.md` before restoring onto a different machine or updating
nixpkgs. Future setup work should edit this repository rather than regenerate
files with the old `~/hyprland-setup/create-user-config.py` script.
