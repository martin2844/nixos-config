# OpenRazer and the Razer Pro Click V2

`hosts/nixos/openrazer.nix` enables the NixOS OpenRazer module, adds `martin` to
the `openrazer` group, and installs Polychromatic. NixOS supplies the kernel
drivers, udev permissions, D-Bus registration and a user daemon that starts with
the graphical session in Plasma or Hyprland/UWSM.

The pinned nixpkgs contains OpenRazer 3.12.3 and Polychromatic 0.9.8. The
Pro Click V2 is supported over its USB receiver (`1532:00d1`) and a cable
(`1532:00d0`), as listed by [OpenRazer](https://openrazer.github.io/).
The current installation was verified with the wireless receiver on kernel
6.18.49. Bluetooth was not tested.

## Install and use

From the repository:

```sh
./scripts/rebuild build
./scripts/rebuild test
# After verifying the device:
./scripts/rebuild switch
```

For a new installation, log out and back in after activation to apply the new
group membership. Reconnect the receiver if it was already plugged in when the
driver was first installed.

Open **Polychromatic** from the launcher, or run `polychromatic-controller`.
Select **Razer Pro Click V2 (Wireless)** to adjust DPI, polling rate, brightness
or lighting effects and view the battery level. OpenRazer saves device settings
in `~/.config/openrazer/persistence.conf`; these settings and application logs
remain outside Git.

Waybar shows a mouse battery icon beside Bluetooth while OpenRazer detects the
Pro Click V2 and can read its status. Hover to see the charge percentage and
charging state; click to open Polychromatic. The icon changes color at 20% and
10%, and hides when the mouse stops responding, the receiver is removed or
OpenRazer is unavailable.
The [desktop-controls package](../packages/desktop-controls/) supplies this
read-only status query, refreshed every ten seconds.

## Verification

```sh
getent group openrazer
systemctl --user status openrazer-daemon.service
busctl --user call org.razer /org/razer razer.devices getDevices
journalctl --user -u openrazer-daemon.service -n 30
```

The service should be active and the D-Bus call should return the mouse's serial
number. Installation validation included device discovery, reading battery and
brightness, writing the current DPI and polling rate back to the device and
reading them again, and visually checking Polychromatic's device controls.

If the daemon is stopped after reconnecting the mouse, restart it with
`systemctl --user restart openrazer-daemon.service`. If it reports missing group
membership, refresh the login session before restarting it.
