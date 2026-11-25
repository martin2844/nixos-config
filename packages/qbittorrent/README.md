# qBittorrent desktop and search

qBittorrent 5.2.2 comes from the repository's pinned nixpkgs, including Python.
The host configuration and managed user-package installer both include this
package. No daemon or Web UI is enabled.

Startup is manual: the host explicitly disables the qBittorrent service, and
the linked autostart directory contains a `Hidden=true` desktop override.
`scripts/configure-qbittorrent.py`, run by the user installer, also excludes
qBittorrent from Plasma session restore while preserving other exclusions.

`plugins.json` records 50 public search plugins from the
[unofficial plugin wiki](https://github.com/qbittorrent/search-plugins/wiki/Unofficial-search-plugins)
as checked on 2026-09-29. Each file has a SHA-256 hash; GitHub sources use commit
URLs and Snowfl uses a release URL. YTS retains its upstream branch URL with a
fixed hash, so an upstream change will fail verification until explicitly updated.
Plugin code is downloaded into the Nix store, not committed to this repository.

On launch, `qbittorrent-setup-search` copies missing plugins into
`$XDG_DATA_HOME/qBittorrent/nova3/engines` (default `~/.local/share/…`). It creates
a new default profile with the Search tab enabled. Existing settings and plugin
files are preserved, including GUI plugin updates; torrent state, logs, caches,
and downloaded content stay outside Git. qBittorrent creates its own search
runtime files when the Search tab first opens. Custom `--profile` and
`--configuration` profiles are not provisioned by this helper.

Use **View → Search Engine**, then **Search plugins…** to inspect or disable
engines. Removing a bundled plugin causes it to be restored on the next launch;
disable it to keep it inactive. Existing profiles retain their Search tab setting.

## Selection and validation

The bundle skips private trackers, adult-specific engines, wiki warning/failure
markers, duplicate implementations, and YGGtracker's extra network requirement.
The following additional omissions were found during setup:

- Cpasbien, MaxiTorrent, Mikan Project, and Torrent9 import the removed
  `helpers.headers` API and fail to load with this qBittorrent version.
- Mikanani needs an additional `requests` dependency and is not included.
- Torrenflix, UIndex, and UnionDHT have unavailable download links.
- Scare.ca's three category variants are unreachable; the listed alternatives
  for MagnetDL, ThePirateBay, and TorrentDownload are included instead.
- Nyaa.si uses the author's current `main` branch because the listed `master`
  reference is unavailable.

All 50 selected engines passed qBittorrent's actual `nova2.py --capabilities`
loading check. This verifies imports and discovery, not live availability of
every tracker; searches may still fail if a site changes or blocks requests.

## Build and install

```sh
nix-build . -A qbittorrent -o result-qbittorrent
nix --extra-experimental-features nix-command profile add ./result-qbittorrent
./result-qbittorrent/bin/qbittorrent-setup-search
./scripts/rebuild build
# Optional system-wide activation, requiring sudo:
./scripts/rebuild switch
```

The normal `./install.sh --switch` flow includes this package as well. Update
plugin URLs and hashes deliberately, then rebuild. Existing copied plugins are
preserved: to restore the pinned version of an engine, close qBittorrent, move
that engine's `.py` file to a backup outside the engines directory, and rerun
`qbittorrent-setup-search`. This also provides a way to apply new manifest pins.
