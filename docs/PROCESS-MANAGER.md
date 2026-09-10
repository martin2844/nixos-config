# Process manager

Click CPU or RAM in Waybar to open KDE System Monitor. It starts on the
Processes page, where column headers sort by CPU or memory usage and the search
field filters processes. The application is provided by the existing NixOS
Plasma desktop configuration; no separate user installation is needed.

Hyprland opens `org.kde.plasma-systemmonitor` centered in a floating 1100 × 780
window. Both buttons use `uwsm app -- plasma-systemmonitor --page-name Processes`.
If System Monitor is already open, KDE reuses its window and retains its current
page. Its activation can focus the workspace containing that window.

The bindings live in `home/.config/waybar/config.jsonc`; the window rule lives in
`home/.config/hypr/hyprland.lua`.
