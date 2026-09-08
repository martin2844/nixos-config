{
  pkgs ? import ../../nix/pkgs.nix { },
}:
pkgs.vimPlugins.blink-cmp
