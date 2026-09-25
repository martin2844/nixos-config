#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
expected_uuid=1c5b930d-5d2f-4b13-9577-661c73bc1993
mounted_uuid=$(findmnt -no UUID --target /run/media/martin/Ediloco || true)
if [[ "$mounted_uuid" != "$expected_uuid" ]]; then
  echo 'Conectá y montá Ediloco antes de iniciar Paperless.' >&2
  exit 1
fi
case "${1:-}" in
  '') docker compose up -d ;;
  --no-recreate) docker compose up -d --no-recreate ;;
  *) echo 'Uso: iniciar.sh [--no-recreate]' >&2; exit 2 ;;
esac
