# Trayscale peer presence

The pinned Trayscale 0.18.9 reads peer availability from IPN NetMap snapshots.
With the installed Tailscale 1.98.10 daemon, those snapshots can retain old
`Online` and `LastSeen` values while the live status API reports reachable peers.
This makes the window opened from Waybar mark online devices red.

This package keeps the pinned UI and network configuration, but refreshes peer
presence from the daemon's local status API before publishing each IPN snapshot
and every five seconds while idle. Requests time out after two seconds. Node
views are copied before modification, and responses for another profile are
ignored. One publisher is retained across IPN watcher reconnections.

Build and run the presence regression tests with `nix-build . -A trayscale`.
The user installer puts this package ahead of the system Trayscale in PATH.
Only the GUI needs restarting after installation; tailscaled keeps running.

The linked hicolor fallback supplies `network-transmit-receive-symbolic`, which
the Breeze theme lacks, so online peers show a connected computer rather than
the red missing-image placeholder.

Remove this override when the pinned upstream client and daemon provide accurate
peer presence together. Upgrading the GUI alone is not sufficient evidence:
verify both initial status and online/offline transitions with the installed daemon.
