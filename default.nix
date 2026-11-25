let
  pkgs = import ./nix/pkgs.nix { };
in
{
  system =
    (import ((import ./nix/nixpkgs.nix) + "/nixos") {
      configuration = ./hosts/nixos/configuration.nix;
    }).system;
  ediloco-tools = import ./packages/ediloco-tools { inherit pkgs; };
  chatgpt = import ./packages/chatgpt { inherit pkgs; };
  opencode = import ./packages/opencode { inherit pkgs; };
  slack = pkgs.slack;
  proton-vpn = pkgs.proton-vpn;
  qbittorrent = import ./packages/qbittorrent { inherit pkgs; };
  sf-mono = import ./packages/sf-mono { inherit pkgs; };
  internet-panel = import ./packages/internet-panel { inherit pkgs; };
  nvim-tools = import ./packages/nvim-tools { inherit pkgs; };
  nvim-blink = import ./packages/nvim-tools/blink.nix { inherit pkgs; };
  wallpapers = import ./packages/wallpapers { inherit pkgs; };
  wallpaper-tools = import ./packages/wallpaper-tools { inherit pkgs; };
  desktop-controls = import ./packages/desktop-controls { inherit pkgs; };
  trayscale = import ./packages/trayscale { inherit pkgs; };
  waybar = import ./packages/waybar { inherit pkgs; };
  calendar-reminders = import ./packages/calendar-reminders { inherit pkgs; };
  pbclipboard = import ./packages/pbclipboard { inherit pkgs; };
  network-menu = pkgs.networkmanager_dmenu;
  hyprmod = import ./packages/hyprmod { inherit pkgs; };
  screenshot-preview = import ./packages/screenshot-preview { inherit pkgs; };
  desktop-theme = import ./packages/desktop-theme { inherit pkgs; };
  zsh = import ./packages/zsh { inherit pkgs; };
  codex-sound = import ./packages/codex-sound { inherit pkgs; };
  codex-border = import ./packages/codex-border { inherit pkgs; };
  remote-desktop = import ./packages/remote-desktop { inherit pkgs; };
  windows-vm = import ./packages/windows-vm { inherit pkgs; };
  codex-usage = import ./packages/codex-usage { inherit pkgs; };
  claude-usage = import ./packages/claude-usage { inherit pkgs; };
}
