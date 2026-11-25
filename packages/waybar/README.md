# Waybar tray filtering

The pinned Waybar 0.15.0 package does not have a per-item tray filter. This
small override adds `ignored-items` and `allowed-items` arrays to each tray
module, matching exact StatusNotifierItem D-Bus object paths. Matching indicators are omitted by the tray host; the
applets and their NetworkManager password/Bluetooth pairing agents keep running.
Other tray applications remain visible. This is a local patch, not an upstream
Waybar setting. Recheck the patch when updating nixpkgs.

Build with `nix-build . -A waybar`. The user installer manages this package;
`hypr-waybar.desktop` starts its user-profile executable under UWSM.

`hyprland-ipc-recovery.patch` makes Waybar exit with an error if its Hyprland
event socket closes. The autostart service's restart drop-in then starts a fresh
bar, restoring workspace updates. This handles a lost connection; it does not
explain why Hyprland closed it.

`dynamic-tooltips.patch` backports the tooltip-query approach from upstream
[#5212](https://github.com/Alexays/Waybar/pull/5212) and the pointer-position guard
from [#5245](https://github.com/Alexays/Waybar/pull/5245) to Waybar 0.15.0. It routes
the custom, CPU, memory, Bluetooth, audio and Hyprland window modules through
cached tooltip content. Periodic updates no longer reset GTK's hover timer for
the entire bar, and visible cards refresh without a click. The pointer check
prevents updates from a previously hovered module overwriting an adjacent
module's tooltip. Plain-text tooltips are escaped before passing to the common
markup renderer. The clock's existing calendar popup remains separate.

Validation: the pinned build passed all three Meson test suites. A temporary
250 ms JSON stream reproduced missing hover cards in the previous build and
displayed the mouse and Codex cards in the patched build. The live bar's mouse
battery and Codex tooltips were also checked without clicking. Test bars and
generated screenshots stay outside the repository.

The bar uses two tray instances: `tray#apps` excludes NetworkManager and Blueman,
while `tray#network` only accepts NetworkManager. A separator places application
icons apart from network, Bluetooth, audio, usage, notifications and settings.
The NetworkManager dropdown remains native and CPU/RAM percentages stay visible.

Application tray icons remain visible, including Steam and passive indicators. A single windows
button opens the desktop-controls window list instead of showing every window. The second local patch updates workspace clicks
to the typed Lua dispatchers required by the pinned Hyprland 0.55.4. It must be
reviewed alongside a future Hyprland upgrade. Neither patch changes NixOS services.

Apps that expose a StatusNotifierItem remain accessible even without an open
window. Only the duplicated network/Bluetooth applets are excluded from the app
area. Applications without a tray implementation cannot appear in this tray.

The clock also has a local [interactive holiday calendar](calendar/README.md):
large adaptive cells, a padded outline for today, holiday borders and per-day
hover details. `calendar-popup: true` replaces the text-only clock tooltip.
