# HyprMod: graphical Hyprland settings

Upstream: https://github.com/BlueManCZ/hyprmod

Installed HyprMod 0.4.0 at commit
`ffd47d804d8996cf3852dbb7ca1c949c424a57fb` (2026-08-27). The application
and five Python support libraries are hash-pinned in `default.nix`.
GTK4/libadwaita, Cairo, and a Lua interpreter are supplied by Nix.
The upstream application is used without UI patches.

Open it with **Super+,**, the top-bar gear, or **HyprMod** in the launcher.
Use **Monitors** for resolution, refresh rate, scale, and arrangement;
the other sidebar pages cover appearance, input, and window management.
Changes can be previewed live. Review pending changes and save with **Ctrl+S**.

The application writes `home/.config/hypr/hyprland-gui.lua`, loaded last by
`hyprland.lua`. These overrides take precedence over the desktop defaults
and can be versioned with the rest of this checkout.

Build: `nix-build . -A hyprmod -o result-hyprmod` from the repository root.
The normal user-package installer also includes HyprMod.

## Power settings

HyprMod does not yet implement its planned hypridle/hyprlock pages.
**Super+Escape → Suspend** uses systemd, with the running hypridle service
handling locking before sleep. No suspend or hibernate was triggered during
installation. Hibernation has not been validated or added to the menu.

Idle timeouts remain in `home/.config/hypr/hypridle.conf`: lock at 10 minutes,
display off at 15 minutes, no automatic suspend. The DPMS callbacks now use
the Lua dispatch syntax required by this Hyprland version.

## Validation

- Nix package build and Python dependency imports passed.
- GUI launched with working GTK/Cairo and sidebar controls.
- Lua config detection, managed include, save, compositor reload, and read-back
  passed against the running compositor. The temporary rounding change was
  restored after testing.
- Hyprland reload reports no configuration errors; the shortcut and bar entry
  are present. Hypridle starts with both configured idle rules.
- Existing user-installation tests and the system build are checked separately.

Pre-install desktop files were backed up under
`~/.local/state/before-hyprmod-SSnpnV/` on the original PC.
