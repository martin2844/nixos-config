# OpenJuice desktop launcher

`home/.local/bin/openjuice` runs the native Nix package at
`~/Projects/juiced/openjuice-port/out/linux-result/bin/juiced` with original assets
in `~/Projects/juiced/game-data`. Build it in that repository with
`nix-build -j 1 --cores 8 -o out/linux-result`. Keep the result link to retain its
Nix dependencies. No Wine process or original Windows executable is involved.

`home/.local/share/applications/openjuice.desktop` exposes OpenJuice in the
Super+Space drun launcher, plus instant-race, keyboard-controls, mod-manager and
play-without-mods actions. Six mods are enabled by default; missing package files
are seeded from the port's `mods/` directory into `~/.local/share/openjuice/mods`.
Installed edits/toggles are preserved. Options → Mods changes activation after
restart. Modded saves use `~/.local/share/openjuice/ModSaves`, separate from stock
saves. Native mod details: `~/Projects/juiced/openjuice-port/docs/linux-mods.md`.
Both user destinations are managed in `links.json`. Configuration/saves/logs live
in the standard XDG directories under `openjuice`, outside this configuration repo.
Port details and limitations: `~/Projects/juiced/openjuice-port/docs/linux-port.md`.
