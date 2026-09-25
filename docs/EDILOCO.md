# Paperless and Immich on Ediloco

Open **Super+Space**, type **Paperless** or **Immich**, and press Enter. The
launcher opens the local browser page and starts the corresponding user service
when needed. It checks the mounted disk UUID first.

Both applications stay **off at boot/login**. Opening a launcher entry performs
a cold start, waits for the local service to respond, then opens the browser.
Use **Apagar Paperless** or **Apagar Immich** in the same launcher to stop the
whole application, including its databases and workers. Closing a browser tab
does not stop the service. An unavailable disk prevents startup but never
prevents shutdown. Backups on Ediloco remain independent and keep running.

Docker restart policies are `"no"`, and neither application nor the bulk document
indexer is enabled under `default.target`. Queued work and database files survive
shutdown and continue when the corresponding application is opened again. The
separate bulk document import controller is resumed explicitly with `indexar.sh`.
Shutdown allows workers up to 120 seconds to exit before Docker terminates them.
The local Immich gateway runs under the image's `tini` so Docker stop signals
reach Node and shutdown does not wait for the full timeout.
The server depends on the machine-learning service's health, keeping that service
available until the workers have stopped as well as checking it before startup.

| Application | Address | Runtime directory |
| --- | --- | --- |
| Paperless | http://localhost:8010 | `~/Projects/documentos-ediloco` |
| Immich | http://localhost:2283 | `~/Projects/immich-ediloco` |

Both browser entry points open automatically without entering credentials.
Paperless uses its native `PAPERLESS_AUTO_LOGIN_USERNAME=martin` option. Immich
uses `acceso-local.mjs`, a local gateway that obtains normal session cookies and
renews expired sessions on reads. HTTP streaming, range downloads and WebSockets
are forwarded. Foreign Host/Origin headers are rejected. Logging out reloads
the local library because this entry point intentionally always signs in.

Immich's internal account remains necessary for document ownership and its API.
The original server is on loopback port 2284; the automatic entry point is 2283.
Each runtime directory still has private `.env` and `ACCESO.txt` files used for
service administration. These files, job state and logs must never be committed.
Automatic access is intended only for this computer; keep the loopback bindings.

## Versioned configuration

- `services/paperless/`: Compose, the Qwen compatibility Dockerfile, OCR/import
  tools, integrity verification and resumable bulk indexing controller.
- `services/immich/`: Compose 3.2.2, read-only external library setup, automatic
  local login gateway and status tool.
- `home/.local/share/applications/{paperless,immich}{,-stop}.desktop`: Rofi/Plasma
  entries for opening and stopping each application.
- `home/.local/bin/ediloco-app`: disk check, service readiness and browser launcher.
- `home/.config/systemd/user/{paperless,immich}.service`: service lifecycle.
- `packages/ediloco-tools/`: pinned Node and LibreDWG under dedicated executable
  names, without replacing the user's development Node installation.
- `scripts/install-ediloco.py`: restore public runtime files, back up changed
  destinations, preserve existing secrets/state, generate new credentials only
  when none exist, and create data directories only on the expected mounted disk.

The normal `./install.sh --test` / `--switch` includes this setup. It does not
automatically start a new import or library scan. No system activation is needed
when only these user launchers and Compose files change.

To restore just these tools on this host:

```sh
nix-build . -A ediloco-tools -o result-ediloco-tools
nix --extra-experimental-features nix-command profile add ./result-ediloco-tools
nix-build ./nix/pkgs.nix -A python3 -o result-python
result-python/bin/python3 scripts/install-ediloco.py
result-python/bin/python3 scripts/link-home.py --apply
systemctl --user daemon-reload
bash scripts/configure-ediloco-on-demand.sh
```

Keep the private `.env` files when restoring existing databases: generating new
database passwords does not change the passwords already stored in PostgreSQL.
An existing import keeps its checkpoint in the runtime `state/` directory.

## Storage and scope

Required mount: `/run/media/martin/Ediloco`, UUID
`1c5b930d-5d2f-4b13-9577-661c73bc1993`.

Service data lives under `Servicios/Paperless` and `Servicios/Immich`. Containers
do not create replacement directories when the drive is absent. Exposed ports
bind only to `127.0.0.1`.

Paperless reads the existing document inventory in
`Archivo-TheMartin/09_Documentos/00_Indice_documentos/plan-de-copia.json` and imports
independent copies. Its conversion helper uses a read-only source mount.

Paperless categories use document type, extracted text, file format and specific
source context. `Documentos` groups identity documents and personal certificates;
`Planos` groups CAD records and recognizable drawing PDFs; bank statements and
transfers use `Documentos Bancarios`; immigration/residency procedures use
`Migraciones`. Other categories cover receipts, taxes, housing, health, insurance,
vehicles, study material, work, manuals and notes. Uncertain items remain
`Por clasificar`. These are conservative rules, not individual LLM judgements.
Single mentions of DNI, passport or house no longer create overlapping labels.

The importer revisits categories after successful OCR. The full indexing process
also reclassifies after PDF and Office OCR, so changes in extracted text are
included. Run `ediloco-node reclasificar.mjs --plan` in the Paperless runtime to
preview, or `--aplicar` to apply with private metadata backups. This only changes
labels and four built-in saved views; it never alters original files. Custom
labels outside the managed taxonomy and documents without archive provenance
are preserved. Regression checks: `node --test tests/paperless-clasificacion.test.mjs`.
Resuming the indexing controller starts missing containers with `--no-recreate`,
preserving running OCR/index workers. Restart `paperless.service` separately
when intentionally applying Compose configuration changes.

Immich mounts all of `Archivo-TheMartin` read-only, covering photographs inside
the equipment, phone and migration backups as well as the photo folders. It
does not move, replace or link source images. Thumbnails, models, indexes and
database files are separate. The library includes supported image formats;
videos, AppleDouble metadata, the control directory and the duplicate document
copies in `09_Documentos` are excluded. In particular `.ts` is excluded because
Immich otherwise mistakes TypeScript source for MPEG transport-stream video.
Restic repositories in `Ediloco/Backups` are backup containers, not browsable
image directories; their un-restored historical snapshots are outside this scan.

Image search uses multilingual `ViT-SO400M-16-SigLIP2-384__webli`; face recognition
uses `buffalo_l`; OCR uses Immich's `PP-OCRv5_mobile`. Face groups need names
assigned by the user. City/country lookup runs locally from GPS metadata. External
map tiles and update checks are disabled; initial image/model downloads need the
Internet. The server is limited to three CPU cores and the ML service to four;
modest job concurrency leaves resources for Paperless.
Immich ML currently uses the CPU image. The ROCm backend repeatedly blocked its
worker while compiling SigLIP2 on this Radeon and hit worker timeouts. Existing
ONNX model downloads are reused by the CPU backend; Paperless's Ollama GPU
configuration is independent and unchanged.

## Start and monitor

```sh
systemctl --user start paperless.service immich.service
cd ~/Projects/documentos-ediloco
ediloco-node estado.mjs
./indexar.sh                    # Resume the existing document batch

cd ~/Projects/immich-ediloco
ediloco-node configurar.mjs     # Create/update library and queue a scan
ediloco-node estado.mjs
docker compose logs --tail=100 immich-machine-learning
```

On an existing Paperless container, `./activar-acceso-local.sh` applies automatic
login by restarting only the supervised web process. This leaves the active OCR
worker running. The Compose setting persists the change for recreated containers.

`configurar.mjs --pausar-ia` can start metadata/thumbnail processing while model
installation is pending. Run `configurar.mjs` again without that flag when ready
to resume face detection, visual search and OCR. Video conversion stays paused
for this photo-only library.

If requests time out during the initial model download/compilation, run
`ediloco-node reintentar-ia.mjs`. It briefly pauses new AI jobs, lets active work
finish, queues only missing analyses, and resumes all three queues. It never
empties queues or forces completed analyses to be repeated.

The photo scan is a background job in Immich. Seeing an asset in the library
does not mean all thumbnail, face, OCR and semantic tasks have completed. Failed
jobs remain visible for review, including malformed images in old backups.

Before disconnecting Ediloco:

```sh
systemctl --user stop paperless.service immich.service
```

This stops the document importer and containers. Connect/mount the disk before
starting again. Back up the service databases in addition to the source media;
face names, albums and classification live in those databases.

Validation: `scripts/rebuild build`, `nix-build . -A ediloco-tools`, desktop entry
validation, `result-python/bin/python3 -m unittest discover -s tests -p 'test_ediloco.py'`
(installer preservation, warm/cold launch, stale service recovery, failed startup,
missing disk and explicit shutdown), `node --test tests/ediloco-access.test.mjs` (cookies, expired
sessions, streams, origin checks, errors and WebSockets), and fresh-browser local
API/UI checks. Upstream configuration sources:
[Paperless auto-login](https://docs.paperless-ngx.com/configuration/#PAPERLESS_AUTO_LOGIN_USERNAME),
[Immich Compose](https://docs.immich.app/install/docker-compose/),
[external libraries](https://docs.immich.app/features/libraries/),
[ROCm](https://docs.immich.app/features/ml-hardware-acceleration/).
