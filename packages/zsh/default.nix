{
  pkgs ? import ../../nix/pkgs.nix { },
}:
pkgs.symlinkJoin {
  name = "desktop-zsh";
  paths = [
    pkgs.zsh
    pkgs.oh-my-zsh
  ];
  meta.description = "Zsh and Oh My Zsh for Ghostty";
}
