# Working on this desktop

This checkout is the source for Martin's NixOS and linked user desktop configs.
Keep Plasma, SDDM, the existing user, boot, networking and audio intact.
Use plain Nix; do not introduce flakes or Home Manager without a request.
Hyprland is pinned at 0.55.4 with Lua configuration and UWSM. Validate runtime
callbacks as well as syntax. User directories are linked via links.json.
Edit these sources rather than legacy hyprland-setup generators or backups.
Build with scripts/rebuild build; activation uses scripts/rebuild test/switch.
Do not add app data, secrets, downloaded binaries, build outputs, or logs to Git.
Back up existing destinations before changing links. Document custom code.
