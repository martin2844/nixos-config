{
  pkgs ? import ../../nix/pkgs.nix { },
}:
pkgs.waybar.overrideAttrs (old: {
  patches = (old.patches or [ ]) ++ [
    ./tray-filter.patch
    ./hyprland-lua-workspaces.patch
  ];
})
