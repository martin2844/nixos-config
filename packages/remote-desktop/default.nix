{ pkgs ? import ../../nix/pkgs.nix { } }:
pkgs.writeShellApplication {
  name = "nixos-remote-desktop";
  runtimeInputs = [ pkgs.python3 pkgs.wayvnc pkgs.tailscale ];
  text = ''
    exec python3 ${./remote-desktop.py} "$@"
  '';
}
