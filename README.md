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

- [Codex usage indicator](packages/codex-usage/): Waybar shows the remaining
  Codex allowance and available resets, with renewal and expiry dates in the
  tooltip. Installed by the user-package installer; uses your Codex CLI login.

- [Codex completion sound](packages/codex-sound/): the installer configures a
  sound after each completed response and disables Codex's desktop toasts.
- [Screenshot preview](packages/screenshot-preview/): draggable bottom-right
  thumbnails after Print or Shift+Print; click to edit, with automatic image copying.
- [HyprMod](packages/hyprmod/): Hyprland settings with local English pages for
  power profiles, idle settings, presentation mode, optional display brightness
  and access to existing system tools. Open with Super+, or the top-bar gear.

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

## Desktop appearance and shell defaults

Breeze Dark is the GTK/KDE default. The NixOS appearance module also supplies
unlocked dconf defaults (`prefer-dark`) for portals and compatible applications.
The installer runs `desktop-theme` after linking user files, so existing user
preferences are updated as well. Run `~/.nix-profile/bin/desktop-theme` to reapply
these defaults. Applications with their own theme override may need that override
changed or a restart; website content is not forcibly recolored.

Ghostty starts the Nix-packaged Zsh login shell. `home/.zshrc` loads the pinned
Oh My Zsh package with `robbyrussell` and the git/node/npm plugins; `.zprofile`
retains the NixOS login environment. Both are linked by `links.json` and the user
installer builds `packages/zsh`. Oh My Zsh self-updates are disabled; history and
completion caches stay outside Git. The account's login shell is unchanged.

[Waybar patches](packages/waybar/) and [desktop controls](packages/desktop-controls/)
provide separate application/system areas, the icon-grid window picker, volume
and Bluetooth popups, and Tailscale status. Workspace clicks use Hyprland's Lua API.

## Additional captured desktop settings

HyprMod's `home/.config/hypr/hyprland-gui.lua` records the current DP-3 monitor
at 2560×1440/240 Hz and blur preference; the main config retains the automatic
monitor fallback. The session menu includes suspend, and idle DPMS actions use
the Hyprland Lua dispatchers. Docker is enabled in the host config with Martin
in its group for local development.

The selected Plasma Subarctic wallpaper is referenced through the Nix user
profile. The wallpaper script preserves reproducible references for curated
images; personal wallpaper copies are local and ignored by Git.

[Codex completion sound](packages/codex-sound/) is built by the user installer.
The installer runs `scripts/configure-codex-sound.py` after package installation;
it edits the private user config in place with a backup, never copies it into
this public repo, and refuses to replace an unrelated notification command.
