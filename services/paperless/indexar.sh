#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
systemctl --user reset-failed documentos-indexacion.service
systemctl --user start documentos-indexacion.service
systemctl --user status documentos-indexacion.service --no-pager
