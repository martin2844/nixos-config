#!/usr/bin/env bash
# Migrate existing installations without interrupting an open library.
set -euo pipefail
# systemctl disable also removes unit-file symlinks into this checkout, not
# just default.target.wants. Preserve those links while removing autostart.
unit_paths=()
unit_targets=()
for unit in paperless immich documentos-indexacion; do
  unit_path="$HOME/.config/systemd/user/$unit.service"
  if [[ -L "$unit_path" ]]; then
    unit_paths+=("$unit_path")
    unit_targets+=("$(readlink -- "$unit_path")")
  fi
done
restore_units() {
  local i
  for ((i=0; i<${#unit_paths[@]}; i++)); do
    if [[ ! -e "${unit_paths[i]}" && ! -L "${unit_paths[i]}" ]]; then
      ln -s -- "${unit_targets[i]}" "${unit_paths[i]}"
    fi
  done
}
trap restore_units EXIT
systemctl --user disable paperless.service immich.service documentos-indexacion.service
restore_units
systemctl --user daemon-reload
for project in documentos-ediloco immich-ediloco; do
  container_ids=$(docker ps -aq --filter "label=com.docker.compose.project=$project")
  if [[ -n "$container_ids" ]]; then
    mapfile -t containers <<< "$container_ids"
    docker update --restart=no "${containers[@]}" >/dev/null
  fi
done
