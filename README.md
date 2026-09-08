# Martin's NixOS desktop

Plain NixOS configuration, Plasma + Hyprland/UWSM, user dotfiles, and local
package overrides. No flakes or Home Manager. Created from the working machine
on 2026-09-08. The host/user name is currently `nixos` / `martin`.

## Install everything

On this machine, as `martin`:

```sh
git clone https://github.com/martin2844/nixos-config.git ~/Projects/nixos-config
cd ~/Projects/nixos-config
./install.sh --check    # build everything, without installing
./install.sh --test     # install user packages/configs and test the system
./install.sh --switch   # install everything and make the system generation persistent
```

If the checkout already exists, use it directly. `./install.sh --switch` is the
single-command full installer. Run it as your normal user; it asks for sudo only
when installation is ready. It builds the system and all custom packages, installs
the managed user-profile packages, backs up and links the dotfiles, creates the
screenshots directory, and activates NixOS. Python is supplied by pinned nixpkgs.
A failed build stops before user configuration or system activation changes.
The installation phase is not atomic across system and user configuration:
backups preserve replaced user files, and Nix retains previous generations.

This installs a desktop onto an **existing NixOS system**. It does not partition
or format disks. The configuration targets Martin's AMD desktop and checks the
configured disk UUIDs before activation. On another machine, adapt the hardware
module, username/home paths, and installer checks first.

After installing, select **Hyprland (UWSM)** in SDDM. Plasma remains available.
The `--test` system generation is temporary; user packages and dotfile links are
persistent even in test mode. Keep the checkout: live config directories link to it.

ChatGPT and other account logins are separate. ChatGPT's hash-pinned upstream
`latest` download may stop being available; see [limitations](docs/LIMITATIONS.md).

## Custom software included

- [Internet panel](packages/internet-panel/): the Nix override and Python Ethernet
  controls added to nmgui's graphical Wi-Fi window.
- [ChatGPT packaging](packages/chatgpt/): the Nix derivation and Qt startup fix;
  the proprietary app binary is fetched during the build, not committed.
- [Desktop helpers](home/.config/hypr/scripts/): clipboard history, screenshots,
  shortcut help, wallpaper selection, and the session menu.
- [Development tools](packages/nvim-tools/): GitHub CLI, Neovim language servers,
  formatters, and compiled Blink support. LazyVim configuration and its plugin
  lockfile are under `home/.config/nvim/`.

## Layout

- `hosts/nixos/`: actual `/etc/nixos` configuration and hardware module.
- `home/`: Hyprland Lua/bindings/scripts, Waybar, UWSM autostart, Ghostty,
  Rofi, notifications, GTK appearance, file associations, and LazyVim + lockfile.
- `packages/internet-panel/`: nixpkgs nmgui with the custom Ethernet section.
- `packages/chatgpt/`: Debian repackaging and the Qt plugin startup fix.
- `packages/nvim-tools/`: Nix language servers/tools and native Blink plugin.
- `packages/wallpapers/` and `packages/wallpaper-tools/`: curated image sources,
  Waypaper gallery, and the persistent Hyprpaper bridge.
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
installation builds all outputs before replacing the managed profile entries;
other profile entries are retained. Log into Hyprland UWSM to start the desktop.
For a running session, `hyprctl reload` reloads compositor configuration; restart
Waybar separately after changing its config.

Wallpaper files are tracked under `home/.config/hypr/`. The wallpaper picker
writes there through the directory symlink, so changing it produces a Git diff.
**Super+Ctrl+Space** opens the thumbnail gallery. Twelve predefined space/abstract/
Plasma images are built by Nix; add personal images to `~/Pictures/Wallpapers`.
See [wallpaper gallery](packages/wallpaper-tools/README.md) and
[image credits](packages/wallpapers/CREDITS.md).

## Version control

Public source repository: https://github.com/martin2844/nixos-config.
Browser/app profiles, credentials, Wi-Fi passwords, Tailscale state, screenshots,
logs, binaries, and caches are outside its scope. Host disk UUIDs, username, and
the current wallpaper are included. Existing setup backups remain outside Git.

See `docs/LIMITATIONS.md` before restoring onto a different machine or updating
nixpkgs. Future setup work should edit this repository rather than regenerate
files with the old `~/hyprland-setup/create-user-config.py` script.
