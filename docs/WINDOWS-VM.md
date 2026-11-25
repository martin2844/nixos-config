# Windows on Docker/KVM

Windows 11 runs on demand for compiling CleanCut. Open **Windows** from
Super+Space. Closing the FreeRDP window starts a 30-second timer, then requests
an orderly Windows shutdown and stops its container. Reopening cancels the
pending shutdown. Keep the window open or minimized during a compilation.
The VM does not start at login or boot. The disk and installed applications
persist after shutdown; other Docker containers keep running.

## Files managed by this repository

- `hosts/nixos/windows-vm.nix`: FreeRDP and the existing ext4 storage mount.
- `home/.config/windows-vm/compose.yaml`: pinned image, localhost ports,
  16 GiB RAM, 8 vCPUs and a growable 256 GiB virtual disk.
- `home/.config/windows-vm/check-storage`: checks the mount UUID and writable
  mount before Docker starts; missing storage must not create a replacement disk.
- `home/.config/windows-vm/oem/`: initial guest timezone and readiness scripts.
- `home/.config/systemd/user/windows*`: VM, desktop and shutdown timer units.
- `packages/windows-vm/`: Python launcher packaged with its Nix interpreter.
- `home/.local/bin/windows`, desktop entry and icon: launcher integration.

`links.json` links individual files and the scripts-only `oem` directory. Linking
that whole subdirectory keeps its scripts readable inside Docker's bind mount.
The `~/.config/windows-vm` directory itself
must remain a real directory so private credentials and local notes stay outside
the checkout. Restic and Cloudflare configuration remain private and independent.

## Storage and prerequisites

This is the existing Martin desktop configuration, not a disk provisioning tool.
It never formats disks. The Windows ext4 partition has UUID
`e5de2bb9-d182-49a4-b24b-de175d6742c0` and is mounted at
`/run/media/martin/Windows-VMs`. Adapt the module, storage check and Compose paths
before using a different disk. The mount service only prepares directories after
checking the expected UUID and writable mount.

The VM lives in `Windows/`; `Shared/` is exposed inside Windows as
`\\host.lan\Data`. Neither directory is included in Git or automatically backed
up by this configuration. Keep `VGA: std`: the tested VirtIO display produced a
black desktop on this VM. Docker and Martin's Docker group membership are in the
host configuration; KVM must be available at `/dev/kvm`.

## Credentials and installation

Preserve the existing `~/.config/windows-vm/credentials.env`, mode **0600**.
On a new installation, create it privately with `USERNAME` and `PASSWORD` entries
matching the Windows account. It is required by Compose and the launcher; no
password is generated or stored by Nix. Changing this file after installation
does not change the password inside Windows. Credentials reach FreeRDP through
stdin rather than process arguments. Do not publish expanded `docker compose
config` output: it includes the private environment values.

Use the normal `./install.sh --switch` workflow to build packages, back up and
link files, and activate NixOS. Then run `systemctl --user daemon-reload` for the
new user units. None of the Windows units should be enabled at boot.

For just the launcher package:

```sh
nix-build . -A windows-vm -o result-windows-vm
nix --extra-experimental-features nix-command profile add ./result-windows-vm
```

For subsequent package updates, use `scripts/install-user.py`, which replaces
the managed profile entry. Editing the Python source requires rebuilding the
package; editing linked Compose or unit files does not.

This restores the host configuration. A new empty virtual disk needs Windows
installation and guest tools again; the existing CleanCut checkout, Git/Node,
installed tools, installers and license are guest data, not repo contents.

## Operations and verification

- Open: `windows`.
- Shut down now: `systemctl --user stop windows.service`.
- Cancel a pending shutdown for web-console maintenance:
  `systemctl --user stop windows-idle-shutdown.timer windows-idle-shutdown.service`.
- Web console: <http://127.0.0.1:8006>. RDP is bound to localhost port 3389.
- Logs: `journalctl --user -u windows-desktop.service -u windows-idle-shutdown.service -u windows.service`.

An RDP connection failure also starts the shutdown timer. Reopen within the grace
period to reconnect. The timer checks the desktop state and launcher lock before
stopping Windows. Compose allows up to 120 seconds for shutdown. This image can
return 143 after a successful SIGTERM/ACPI shutdown; the unit accepts that exit
code. Check guest shutdown logs when diagnosing an unexpected exit.

The live close/reopen/shutdown test on 2026-09-15 completed in about 64 seconds
including the grace period and released about 16.3 GiB of memory. Evidence stays
local at `~/.local/state/windows-vm/auto-shutdown-verification.json`.
