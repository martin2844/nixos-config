#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ "$(systemctl --user show --property=LoadState --value documentos-indexacion.service)" == loaded ]]; then
  systemctl --user stop documentos-indexacion.service
fi
docker compose stop --timeout 120
