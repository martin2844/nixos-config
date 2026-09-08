# Desktop controls

On-demand GTK3 layer-shell panels for this Hyprland/UWSM desktop. `desktop-controls
audio` opens output/microphone volume and mute controls backed by PipeWire's
`wpctl`. `desktop-controls bluetooth` uses BlueZ D-Bus for power and connecting
paired devices; pairing and advanced settings open the existing Blueman manager.
Advanced mixer, Bluetooth and Tailscale windows have floating Hyprland rules.

Each popup has a unique Gtk.Application D-Bus name: another invocation closes it.
Escape, the close button, or loss of focus dismisses it. It is a layer surface,
so it does not occupy a tile. It stores no credentials and runs no daemon.
Bluetooth's existing pairing agent continues to run in the graphical session.

`desktop-controls tailscale-status` emits Waybar JSON using only BackendState;
no peer list, addresses or credentials are stored. Clicking the bar icon opens
the already installed Trayscale GUI. It does not automatically connect or log in.

Build with `nix-build . -A desktop-controls`. The user installer manages the
package, while Waybar starts panels on demand through `uwsm app --`.

`desktop-controls windows` lists open Hyprland windows in a scrollable dropdown,
ordered by workspace and application. Selecting one focuses it through the typed
Lua API. Window titles are plain text and addresses are validated before dispatch.
The tray remains reserved for background apps; Steam's tray icon is hidden.

The window picker is an icon grid, with workspace numbers under icons and window
names in tooltips. Desktop-entry icons are resolved by application ID or
StartupWMClass, with a generic fallback. It deliberately stays open across focus
changes so moving from Waybar into it cannot dismiss it. Selection, Escape, X or
clicking the bar button again closes it. Selecting an icon focuses that window
and follows it to its current workspace, without moving the window.

Window icons are grouped inside one outlined frame per occupied workspace. Each
frame has a workspace heading; the current workspace has a brighter outline.
Long groups wrap and the picker scrolls when needed. Individual icons retain
window-title tooltips and focus their original window without moving it.
