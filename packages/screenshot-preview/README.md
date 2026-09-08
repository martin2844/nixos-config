# Screenshot preview

Packages [omarchy-screenshot-preview](https://github.com/rodrigo-sntg/omarchy-screenshot-preview)
at commit `62b5216315a989c888a4b367029465debb4ad224`, with its upstream Cargo.lock.
The installer builds and installs it in the user profile.

Print captures the desktop; Shift+Print selects a region. Both save a PNG in
`~/Pictures/Screenshots`, copy image/png to the Wayland clipboard, and show a
bottom-right thumbnail. Drag the thumbnail into an app, or click it to annotate
in Swappy. Closing Swappy copies the saved image again. A terminal can receive
the file path by drag-and-drop; image pasting depends on the program running in it.

The local patch places the thumbnail 20 pixels from the bottom and right and
gives it eight seconds before dismissal (hover pauses the timer). New previews
replace the previous application instance. It also clears expired GLib timer
IDs before cancellation, avoiding a crash when dismissing after the fade-in,
and clamps scaled image height to at least one pixel for very wide selections.

Build: `nix-build . -A screenshot-preview -o result-screenshot-preview`.
The capture/edit glue lives in `home/.config/hypr/scripts/screenshot`.
