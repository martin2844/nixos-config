{
  pkgs ? import ../../nix/pkgs.nix { },
}:
let
  python = pkgs.python3.withPackages (p: [ p.pygobject3 ]);
in
pkgs.stdenvNoCC.mkDerivation {
  pname = "desktop-controls";
  version = "1.0";
  src = ./.;
  nativeBuildInputs = [
    pkgs.wrapGAppsHook3
    pkgs.gobject-introspection
  ];
  buildInputs = [
    pkgs.gtk3
    pkgs.gtk-layer-shell
  ];
  dontBuild = true;
  installPhase = ''
    mkdir -p $out/bin $out/share/desktop-controls
    cp controls.py $out/share/desktop-controls/
    makeWrapper ${python}/bin/python3 $out/bin/desktop-controls \
      --add-flags $out/share/desktop-controls/controls.py \
      --prefix PATH : ${
        pkgs.lib.makeBinPath [
          pkgs.wireplumber
          pkgs.tailscale
          pkgs.pavucontrol
          pkgs.blueman
          pkgs.trayscale
          pkgs.hyprland
          pkgs.uwsm
        ]
      }
  '';
}
