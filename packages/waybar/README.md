# Waybar tray filtering

The pinned Waybar 0.15.0 package does not have a per-item tray filter. This
small override adds `ignored-items` and `allowed-items` arrays to each tray
module, matching exact StatusNotifierItem D-Bus object paths. Matching indicators are omitted by the tray host; the
applets and their NetworkManager password/Bluetooth pairing agents keep running.
Other tray applications remain visible. This is a local patch, not an upstream
Waybar setting. Recheck the patch when updating nixpkgs.

Build with `nix-build . -A waybar`. The user installer manages this package;
`hypr-waybar.desktop` starts its user-profile executable under UWSM.

The bar uses two tray instances: `tray#apps` excludes NetworkManager and Blueman,
while `tray#network` only accepts NetworkManager. A separator places application
icons apart from network, Bluetooth, audio, usage, notifications and settings.
The NetworkManager dropdown remains native and CPU/RAM percentages stay visible.

Application tray icons remain visible; Steam is hidden. A single windows
button opens the desktop-controls window list instead of showing every window. The second local patch updates workspace clicks
to the typed Lua dispatchers required by the pinned Hyprland 0.55.4. It must be
reviewed alongside a future Hyprland upgrade. Neither patch changes NixOS services.
