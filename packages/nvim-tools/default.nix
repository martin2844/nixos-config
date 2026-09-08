# Development tools shared by the terminal and Neovim.
# Install/update from the repository root with scripts/install-user.py.
{
  pkgs ? import ../../nix/pkgs.nix { },
}:
pkgs.buildEnv {
  name = "lazyvim-development-tools";
  paths = with pkgs; [
    git
    gh
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
