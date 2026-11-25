{ pkgs ? import ../../nix/pkgs.nix { } }:

pkgs.writeScriptBin "windows-vm-launcher" (
  builtins.replaceStrings
    [ "#!/usr/bin/env python3" "/run/current-system/sw/bin/xfreerdp" ]
    [ "#!${pkgs.python3}/bin/python3" "${pkgs.freerdp}/bin/xfreerdp" ]
    (builtins.readFile ./windows.py)
)
