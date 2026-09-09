# Desktop fonts

The active combination is Inter for the desktop interface and JetBrainsMono
Nerd Font for Ghostty. GTK/Qt controls, Waybar text, Rofi and Hyprlock use Inter.
Existing sizes are preserved: 10 pt for GTK/KDE, 12 px for Waybar and 11 pt for
Ghostty. Waybar icons keep their Nerd Font family.

The `desktop-theme` package includes Inter from pinned nixpkgs. JetBrains Mono
Nerd Font is installed by the host configuration. The `desktop-fonts` command
applies GTK/KDE font preferences without changing colors; the full installer's
`desktop-theme` command also invokes it. Fontconfig's generic sans-serif family
prefers Inter and falls back to Noto Sans. Some apps need reopening to discover
new fonts; websites and apps with their own typography can override these defaults.

## Previous Apple font trial

SF Pro Text and SF Mono are no longer selected. Installed copies are retained
for comparison. `packages/sf-mono` remains available as an optional Nix build
(`nix-build . -A sf-mono -o result-sf-mono`), with the official Apple download
pinned by SHA-256 and its license preserved. It is not part of the default
user-package installation anymore.

SF Pro's local OTF files were imported from
`~/clasificar/clasificar-fe/public/fonts/sf-pro` into
`~/.local/share/fonts/sf-pro`. They are outside Git. The active Inter setup does
not require that checkout or the Apple fonts.

Before switching to Inter, configuration files and personal KDE preferences
were backed up under `~/.local/state/nixos-config/backups/inter-20260909-170201`
on the original PC. Earlier trials are also recorded in Git.
