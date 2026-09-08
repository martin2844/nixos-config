{
  pkgs ? import ../../nix/pkgs.nix { },
}:
let
  waypaper = pkgs.waypaper.overrideAttrs (old: {
    patches = (old.patches or [ ]) ++ [ ./quote-filenames.patch ];
  });
  gallery = pkgs.writeShellScriptBin "wallpaper-gallery" ''
    export GTK_THEME=Adwaita:dark
    mkdir -p "$HOME/Pictures/Wallpapers"
    exec ${waypaper}/bin/waypaper "$@"
  '';
  apply = pkgs.writeShellScriptBin "wallpaper-apply" ''
    exec ${pkgs.bash}/bin/bash "$HOME/.config/hypr/scripts/wallpaper" "$@"
  '';
  desktop = pkgs.makeDesktopItem {
    name = "wallpaper-gallery";
    desktopName = "Wallpapers";
    comment = "Browse space photography, dark abstracts and Plasma artwork";
    exec = "wallpaper-gallery";
    icon = "preferences-desktop-wallpaper";
    categories = [
      "Settings"
      "DesktopSettings"
    ];
  };
in
pkgs.symlinkJoin {
  name = "desktop-wallpaper-tools";
  paths = [
    waypaper
    gallery
    apply
    desktop
  ];
}
