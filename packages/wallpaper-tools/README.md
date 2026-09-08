# Wallpaper gallery

The GUI is [Waypaper](https://github.com/anufrievroman/waypaper), packaged by
nixpkgs. This repository adds a dark launcher, an image collection, and a small
bridge to the existing UWSM-managed Hyprpaper service.

Use **Super+Ctrl+Space**, or launch **Wallpapers** from Rofi. Click a thumbnail to
apply it to all monitors. Escape closes the gallery. Put extra images in
`~/Pictures/Wallpapers`; reopen the gallery to load them. Press **Z** to show
Waypaper's standard controls (folders, sorting, etc.). The default is a compact
four-column gallery. Current selection is stored in `~/.local/state/waypaper/`.

The selected image is copied atomically to `~/.config/hypr/wallpaper-custom.*` and
`hyprpaper.conf` is updated. The existing graphical-session service is restarted,
so there is one wallpaper daemon and the selection survives login. Updates are
serialized with flock. No separate Waypaper daemon or restore autostart is added.

Waypaper's backend is `none`; its post-command calls `wallpaper-apply` instead of
its older Hyprpaper IPC implementation. This keeps the existing persistent config
and service lifecycle authoritative. The selection applies to all monitors;
Waypaper's backend/fill controls are not used by this bridge (cover is fixed).

The small package patch:

- Uses Python shlex.quote for post-command filenames, including spaces and shell
  metacharacters.
- Preserves configured gallery folders on first launch when no state file exists.

Image sources, licenses, and credits are in [../wallpapers/CREDITS.md](../wallpapers/CREDITS.md).
Nix downloads/builds the collection; image binaries are not added to Git.
The collection is SDR, chosen for contrast and colour, not HDR-encoded.
