# Ghostty shell

`desktop-zsh` bundles Zsh and Oh My Zsh from the pinned Nixpkgs revision and is
installed by `scripts/install-user.py`. Ghostty starts `zsh -l` for new terminals.
The account login shell remains managed separately by NixOS.

`home/.zshrc` and `home/.zprofile` are linked through `links.json`. They preserve
the personal Bash PATH addition (`~/.local/bin`), NixOS login environment, and
the system's `l`, `ll`, and `ls` aliases. Bash's own files remain usable.
Oh My Zsh uses the robbyrussell theme and git, node, and npm plugins. Its cache
and custom plugin directory are writable user directories; framework updates
come through Nix rather than its Git updater.

Build with `nix-build . -A zsh -o result-zsh`. User history is not part of Git.
