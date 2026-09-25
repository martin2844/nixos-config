#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
mounted_uuid=$(findmnt -no UUID --target /run/media/martin/Ediloco || true)
if [[ "$mounted_uuid" != 1c5b930d-5d2f-4b13-9577-661c73bc1993 ]]; then
  echo 'Conectá y montá Ediloco antes de iniciar Immich.' >&2
  exit 1
fi
docker compose up -d
