{ pkgs ? import ../../nix/pkgs.nix { } }:
pkgs.writeShellApplication {
  name = "codex-usage";
  runtimeInputs = [ pkgs.nodejs ];
  text = ''
    exec node ${./usage.mjs} "$@"
  '';
}
