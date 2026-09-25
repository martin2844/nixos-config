#!/usr/bin/env bash
# Apply the Compose auto-login setting to the running web process only.
# Leave the ongoing OCR worker and its queue intact.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
docker compose exec -T --user 0 webserver sh -c '
  printf "%s\n" martin > /run/s6/container_environment/PAPERLESS_AUTO_LOGIN_USERNAME
  s6-svc -r /run/service/svc-webserver
'
