# Immich runtime sources

Copied into `~/Projects/immich-ediloco` by `scripts/install-ediloco.py`.
The pinned Compose deployment and library initializer use local storage and a
read-only source mount. Private login information and processing state are not
part of this repository. See [Ediloco setup](../../docs/EDILOCO.md).

After starting the containers, run `ediloco-node configurar.mjs` to register the
local administrator, configure models and create/scan the external photo library.
The script preserves an existing administrator and requires the private login to
match. It never sends email or exports photographs to an external service.
