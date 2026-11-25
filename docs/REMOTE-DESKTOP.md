# Mac access to the NixOS desktop through Tailscale

This shares Martin's existing Hyprland session, including the open Ghostty and
Codex windows. WayVNC listens on `127.0.0.1:5900`; Tailscale Serve forwards
tailnet port 5900 to that loopback address. No router forwarding, public
Funnel, or LAN firewall opening is needed.

## Connect from the Mac

1. Connect Tailscale on `martins-macbook-air` using the same account.
2. In Finder, press Command-K and enter `vnc://100.67.11.116`, or run:

   ```sh
   open vnc://100.67.11.116
   ```

3. Authenticate with the password saved on NixOS at
   `~/.config/nixos-remote-desktop/password`. If a username is requested, use
   `martin`. Save the password in the Mac's Keychain before traveling.

The MagicDNS address `vnc://nixos.tail86dfb4.ts.net` also works. Native macOS
Screen Sharing needs no extra client installation. VNC's legacy password
authentication is enabled for that client's compatibility; Tailscale supplies
the encrypted network transport. The local password and server configuration
are mode 0600 in a mode-0700 directory, and never enter Git or the Nix store.

## Availability while away

Leave the PC powered on, connected to the internet, and logged into Hyprland.
The session can be locked: unlock its lock screen with the normal Linux login
password, separate from the VNC connection password. WayVNC acquires output
power while a client is connected, so monitor standby should not require a
person at the PC to wake it.

This service shares a logged-in session. It does not supply a remote SDDM login
or start a desktop after a reboot; someone must log into Hyprland again after
rebooting. Avoid logging out or suspending the computer while away. Other
desktop sessions, including Plasma, do not start this Hyprland service.

Try the Mac connection before leaving; testing from a phone hotspot additionally
checks access from outside the home network. The setup's local protocol check
confirmed authentication and a nonblank desktop frame through Tailscale Serve;
it cannot verify the Mac's Screen Sharing UI remotely.

## Manage the service

```sh
nixos-remote-desktop info
systemctl --user status remote-desktop.service
systemctl --user restart remote-desktop.service
journalctl --user -u remote-desktop.service
```

The unit is enabled for `graphical-session.target` and restricted to Hyprland.
It restarts after unexpected exits, including monitor disconnection, and removes only its own Tailscale port-5900 forwarding
rule when it stops. Repeated starts preserve the generated connection password.
The stream is limited to 20 FPS; client resizing is disabled to preserve the
physical desktop's monitor resolution and window layout.

To disable access:

```sh
systemctl --user disable --now remote-desktop.service
```

The user installer builds `packages/remote-desktop`, installs the
`nixos-remote-desktop` command, links the unit, and enables it. Configuration
changes require a package rebuild/profile update and service restart, not a
system activation. Existing Tailscale and firewall settings remain in charge.

Upstream references: [WayVNC authentication](https://github.com/any1/wayvnc#authentication)
and [Tailscale TCP forwarding](https://tailscale.com/docs/reference/tailscale-cli/serve#use-a-tcp-forwarder).
