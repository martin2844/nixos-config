# Paperless runtime sources

Copied into `~/Projects/documentos-ediloco` by `scripts/install-ediloco.py`.
Credentials, derived documents, index state, logs, downloaded tools and data stay
outside this checkout. See [Ediloco setup](../../docs/EDILOCO.md).

The existing import is resumed by `indexar.sh`. On a fresh restoration, install
the indexing unit after preparing the runtime and mounting Ediloco:

```sh
cp ~/Projects/documentos-ediloco/documentos-indexacion.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user start documentos-indexacion.service
```

The importer and application are not enabled at login. Use the Paperless
launcher for normal access and `indexar.sh` to resume bulk importing explicitly.

The importer preserves source bytes and verifies hashes against the inventory.
Generated searchable derivatives have their own hashes. Files without readable
text and unsupported/auxiliary files are reported separately.

Run Paperless management commands with `docker compose exec --user 1000:100 -T
webserver ...` to preserve index ownership. Running index writers as root can
make the search index inaccessible to workers.

Document categories are defined in `clasificacion.mjs`. The importer applies a
provisional category and revisits it after OCR succeeds. `reclasificar.mjs --plan`
previews the full archive; `--aplicar` backs up existing metadata and replaces
managed labels without touching files or unrelated user labels. The indexing
controller runs it again after the PDF/Office OCR passes. Decisions and backups
are private files under runtime `state/`, never source control.
