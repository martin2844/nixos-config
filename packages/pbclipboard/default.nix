{ pkgs ? import ../../nix/pkgs.nix { }, }:
pkgs.symlinkJoin {
  name = "pbclipboard";
  paths = [
    (pkgs.writeShellApplication {
      name = "pbcopy";
      runtimeInputs = [ pkgs.wl-clipboard ];
      text = ''
        exec wl-copy "$@"
      '';
    })
    (pkgs.writeShellApplication {
      name = "pbpaste";
      runtimeInputs = [ pkgs.wl-clipboard ];
      text = ''
        exec wl-paste --no-newline "$@"
      '';
    })
  ];
  meta.description = "pbcopy and pbpaste commands for the Wayland clipboard";
}
