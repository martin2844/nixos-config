{
  pkgs ? import ../../nix/pkgs.nix { },
}:
pkgs.writeShellApplication {
  name = "codex-complete-sound";
  runtimeInputs = [
    pkgs.jq
    pkgs.pipewire
    pkgs.coreutils
  ];
  text = ''
    # Codex supplies an event as a single JSON argument. Never execute its text.
    if ! jq -e '.type == "agent-turn-complete"' <<< "''${1:-}" >/dev/null 2>&1; then
      exit 0
    fi
    timeout 5 pw-play --volume=0.5 ${pkgs.sound-theme-freedesktop}/share/sounds/freedesktop/stereo/complete.oga >/dev/null 2>&1 || true
  '';
}
