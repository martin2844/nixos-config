{
  pkgs ? import ../../nix/pkgs.nix { },
}:
let
  tone = pkgs.runCommand "codex-tululu.wav" { nativeBuildInputs = [ pkgs.python3 ]; } ''
    python3 ${./generate-tone.py} "$out"
  '';
in
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
    timeout 5 pw-play --volume=0.5 ${tone} >/dev/null 2>&1 || true
  '';
}
