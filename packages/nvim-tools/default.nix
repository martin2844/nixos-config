# Install/update: nix-build ~/.config/nvim-tools -o ~/.local/share/nvim-tools
# Then: nix --extra-experimental-features 'nix-command flakes' profile install ~/.local/share/nvim-tools
{
  pkgs ? import ../../nix/pkgs.nix { },
}:
pkgs.buildEnv {
  name = "lazyvim-development-tools";
  paths = with pkgs; [
    git
    nodejs
    typescript
    vtsls
    vscode-langservers-extracted
    lua-language-server
    stylua
    prettier
    tree-sitter
    gcc
    gnumake
    unzip
    curl
    wget
    ripgrep
    fd
    fzf
    lazygit
    wl-clipboard
  ];
  pathsToLink = [
    "/bin"
    "/share/man"
  ];
}
