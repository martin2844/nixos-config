# HyprMod desktop settings

Upstream: https://github.com/BlueManCZ/hyprmod

HyprMod 0.4.0 is pinned at commit
`ffd47d804d8996cf3852dbb7ca1c949c424a57fb`. The application and five Python
support libraries are hash-pinned in `default.nix`. Nix supplies the GTK4,
libadwaita, Python and service-command dependencies.

Open with **Super+,**, the **Waybar gear**, or **HyprMod** in the launcher.
The local extension adds three English pages and opens Power and sleep first.

## Power and sleep

- Select the power profiles exposed by power-profiles-daemon. The active profile
  and restrictions are read from the system, with a refresh every 15 seconds
  while this page is visible. The daemon remembers profile changes.
- Set lock and display-off timeouts. Zero means Never. Saving changes follows
  the home symlink into the repository's `home/.config/hypr/hypridle.conf`, keeps
  unrelated rules, creates a backup in `~/.local/state/nixos-config/backups`, and
  restarts hypridle. Failed activation restores the original file. Concurrent
  external changes require Reload instead of overwriting them.
- Automatic sleep, hibernation and shutdown are not enabled by the extension.
  The status checks hypridle commands and logind's idle policy and reports
  detected external changes. It does not audit arbitrary scripts or timers.
  Current defaults remain lock after 10 minutes, display off after 15 minutes,
  and no automatic sleep or shutdown.
- Presentation mode creates a temporary systemd user service holding logind
  idle/sleep inhibitors. It survives closing the settings window, turns off via
  the switch, and is stopped with the graphical session. It does not change
  saved timeout values. hypridle must respect systemd inhibitors (its default).
- Battery/UPS information and application inhibitors are shown when available.
- Manual Sleep requires confirmation and uses systemd/logind with hypridle's
  existing lock-before-sleep handler. No shutdown or hibernation action is added.

Power profile selections are stored by the system service, not in Git. The Nix
package and the linked idle policy are reproducible from this repository.

## Displays and brightness

Includes navigation to the existing Monitors page, backlight detection for
laptops and DDC/CI brightness detection for external displays. Writes happen
only on Apply and are followed by a read-back. Commands run outside GTK's main
thread with timeouts. Unsupported displays show an explanatory empty state.

On the current Corsair monitor setup there is no exposed backlight or
`/dev/i2c-*` access, so the page reports Brightness unavailable. No kernel/I2C
permission changes were activated and physical monitor control is unverified.
Brightness restoration across reconnects is not implemented; hardware controls
remain usable. The user explicitly accepted brightness being unavailable.

## More settings

Opens existing network, VPN, Bluetooth, Tailscale, audio, wallpaper,
notification, font, file-association, default-application, printer and system
information tools. KDE modules are used for standalone settings with applicable
system/XDG services, not to control KWin or PowerDevil in the Hyprland session.
Missing applications are visibly disabled. The NixOS entry opens the source
repository for services, users, language and update configuration.

These are external tools, not embedded replicas of all Plasma settings.

## Implementation and maintenance

`desktop-settings.patch` registers the pages in the upstream window and sidebar,
and selects the initial page after GTK presents a new window.
`desktop_settings/` contains the Python UI and service adapters copied into the
package during the build. The extension uses its own save/apply flow; power and
idle settings do not enter `hyprland-gui.lua` or compositor profiles/undo history.
The upstream Monitors, appearance, input and window-management pages remain
available. Ctrl+S still saves compositor settings, while idle timeouts use their
own Save button.

Build: `nix-build . -A hyprmod -o result-hyprmod`. The user-package installer
manages the package. When updating upstream, review the patch and exercise GTK
callbacks against the current Hyprland Lua API.

Boundary tests: `python3 packages/hyprmod/test_desktop_settings.py -v`.
They cover preservation of other rules, Never/re-enable, duplicate detection,
symlink preservation, rollback, external edits and unsupported service responses.
Live GTK checks exercise profile apply, the presentation inhibitor, timeout
save/restart/read-back/restore, the sleep confirmation dialog without sleeping,
and page navigation. The PC is never suspended or shut down by these tests.
