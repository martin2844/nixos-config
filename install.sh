#!/usr/bin/env bash
# Run as the desktop user; sudo is used only for NixOS activation.
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
mode=${1:---test}
if (( $# > 1 )); then echo 'Expected at most one option.' >&2; exit 2; fi
case "$mode" in
  --help|-h)
    cat <<'HELP'
Usage: ./install.sh [--check|--test|--switch]
  --check   Build system and all user packages; do not activate or link anything.
  --test    Install/link everything and test the NixOS generation (default).
  --switch  Install/link everything and make the generation the boot default.
Run as martin, not root. This is a single-host configuration, not an OS installer.
HELP
    exit 0 ;;
  --check|--test|--switch) ;;
  *) echo 'Usage: ./install.sh [--check|--test|--switch]' >&2; exit 2 ;;
esac
[[ -f /etc/NIXOS ]] || { echo 'This installer requires an existing NixOS installation.' >&2; exit 1; }
if [[ "$mode" != --check ]]; then
  [[ $(id -un) == martin && "$HOME" == /home/martin ]] || {
    echo 'This configuration targets martin at /home/martin. Run as that user; customize the host and paths before installing elsewhere.' >&2
    exit 1
  }
  # Never activate this host's boot/filesystem configuration on unrelated disks.
  for uuid in d5f99aa5-1d42-450f-8fe2-6552b044be3b 506D-A9F9 e395cd5b-b848-48b7-bedb-3581b38c8dc9; do
    [[ -e "/dev/disk/by-uuid/$uuid" ]] || {
      echo "Missing configured disk UUID $uuid. Adapt hosts/nixos/hardware-configuration.nix and this check first." >&2
      exit 1
    }
  done
fi
# Finish all builds before any user-profile or system activation changes.
python=$(nix-build "$repo/nix/pkgs.nix" -A python3 -o "$repo/result-python")
"$repo/scripts/rebuild" build
"$python/bin/python3" "$repo/scripts/install-user.py" --build-only
if [[ "$mode" == --check ]]; then
  echo 'All builds passed. No configuration linked and no generation activated.'
  exit 0
fi
sudo -v
"$python/bin/python3" "$repo/scripts/install-user.py"
"$python/bin/python3" "$repo/scripts/link-home.py" --apply
mkdir -p "$HOME/Pictures/Screenshots"
"$repo/scripts/rebuild" "${mode#--}"
printf '\nInstallation complete. Select Hyprland (UWSM) or Plasma in SDDM.\n'
if [[ "$mode" == --test ]]; then
  echo 'System activation is temporary; run ./install.sh --switch to persist it. User config and package changes are already persistent.'
fi
