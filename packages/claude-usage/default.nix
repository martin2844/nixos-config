{ pkgs ? import ../../nix/pkgs.nix { } }:
pkgs.writeShellApplication {
  name = "claude-usage";
  runtimeInputs = [ pkgs.nodejs ];
  text = ''
    exec node ${./usage.mjs} "$@"
  '';
}
