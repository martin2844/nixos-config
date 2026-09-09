# SF Pro desktop trial

The desktop uses SF Pro Text for GTK/Qt controls, Waybar text, Rofi and Hyprlock.
Monospaced terminal/editor fonts and Waybar icon fonts remain unchanged.
Applications with their own fonts, including web pages, may override the desktop.
Already-running applications may need reopening to discover the installed font.

`desktop-fonts` imports the three original OTF files from
`~/clasificar/clasificar-fe/public/fonts/sf-pro` into
`~/.local/share/fonts/sf-pro`, refreshes fontconfig, and applies GTK/KDE user
preferences. `SF_PRO_SOURCE` can point at another directory. Existing installed
font files are preserved. This command is included in the `desktop-theme`
package and is also called by the full installer's theme setup.

Font binaries and personal KDE settings are not committed. On another PC,
provide that source checkout or install the same fonts locally; Noto Sans is
the generic sans-serif fallback when SF Pro is absent. The home link manifest
installs the fontconfig preference. No system rebuild is needed for this trial.

The pre-trial user settings were backed up under
`~/.local/state/nixos-config/backups/sf-pro-20260909-165021` on the original PC.
