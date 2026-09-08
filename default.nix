let
  pkgs = import ./nix/pkgs.nix { };
in
{
  system =
    (import ((import ./nix/nixpkgs.nix) + "/nixos") {
      configuration = ./hosts/nixos/configuration.nix;
    }).system;
  chatgpt = import ./packages/chatgpt { inherit pkgs; };
  internet-panel = import ./packages/internet-panel { inherit pkgs; };
  nvim-tools = import ./packages/nvim-tools { inherit pkgs; };
  nvim-blink = import ./packages/nvim-tools/blink.nix { inherit pkgs; };
  network-menu = pkgs.networkmanager_dmenu;
}
