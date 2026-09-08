# ChatGPT package

Repackages the downloaded Debian application for NixOS. The launcher includes
Qt 5's platform plugin path, fixing the startup failure observed under Hyprland.
No global Qt settings are changed.

Build from the repository root: `nix-build . -A chatgpt`.
Use `scripts/install-user.py` to replace the managed user-profile package after
building. The profile uses `nix profile`, not the legacy `nix-env` interface.

The fixed source hash identifies version 26.901.51231. The upstream URL points
at `latest`, so a fresh download may eventually fail the hash check. Keep the
existing installer (`~/Downloads/chatgpt_amd64.deb`) or its Nix store source
separately; see ../../docs/LIMITATIONS.md. Do not remove or silently change the
hash to work around a changed upstream version.
