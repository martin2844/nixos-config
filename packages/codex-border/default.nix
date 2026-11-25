{ pkgs ? import ../../nix/pkgs.nix { } }:
pkgs.writeShellApplication {
  name = "codex-border-state";
  runtimeInputs = [ pkgs.python3 ];
  text = ''
    exec python3 ${./state.py}
  '';
}
