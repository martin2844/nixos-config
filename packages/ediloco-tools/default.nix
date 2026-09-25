{ pkgs ? import ../../nix/pkgs.nix { } }:
pkgs.runCommand "ediloco-tools" { nativeBuildInputs = [ pkgs.makeWrapper ]; } ''
  mkdir -p $out/bin
  makeWrapper ${pkgs.nodejs}/bin/node $out/bin/ediloco-node
  makeWrapper ${pkgs.libredwg}/bin/dwggrep $out/bin/ediloco-dwggrep
''
