# LazyVim on this NixOS desktop

Installed from the official LazyVim starter on 2026-09-08. Plugins are recorded in
`lazy-lock.json`. The existing Neovim state and history were preserved.

Enabled extras: TypeScript/JavaScript/TSX (vtsls), JSON, ESLint, and Prettier.
Default LazyVim completion, snippets, Git integration, file picker, and syntax
highlighting are included. Space is the leader key.

Open a project with `cd /path/to/project && nvim .`.

- Space Space: find files
- Space /: search project text
- gd: go to definition
- K: hover documentation
- Space c r: rename symbol
- Space c a: code actions
- Space c f: format
- Space e: file explorer
- :Lazy: plugin manager
- :LazyExtras: optional language/features

Prettier formats on save by default. Project-local Prettier and TypeScript
versions are preferred where available. ESLint uses the project's installed
ESLint dependencies and eslint.config.* (or supported legacy configuration).
Install your project's dependencies normally; editor setup does not replace them.

## NixOS integration

`~/.config/nvim-tools/default.nix` declares the command-line tools. They are
installed in the user Nix profile, and init.lua also prepends
`~/.local/share/nvim-tools/bin` for desktop-launched sessions. No system rebuild
was necessary. Mason is disabled because Nix provides compatible executables.

Blink uses Nix's compiled plugin and Rust fuzzy matcher via
`~/.local/share/nvim-blink`, with binary downloads disabled. Rebuild editor tools
against your current Nix channel with:

```
nix-build ~/.config/nvim-tools -o ~/.local/share/nvim-tools
nix-build ~/.config/nvim-tools/blink.nix -o ~/.local/share/nvim-blink
```

Restart Neovim afterward. Use `:Lazy update` for the other plugins; the lockfile
records their versions. Blink itself is updated through Nix, not Lazy.

Ghostty already uses JetBrainsMono Nerd Font 3.4.0, installed system-wide.

## Verification

13 checks passed in a real Ghostty session: TypeScript filetype, vtsls and ESLint
attachment, both diagnostic sources, symbol completion, native Rust matcher,
TypeScript parser, TSX filetype/parser/LSP, Prettier formatting, JSON LSP, picker,
and input UI. See `~/.local/state/lazyvim-setup/verification.txt` and `health.txt`.

The relevant plugin/LSP/parser health checks reported no errors. Optional shell
formatters (fish_indent/shfmt) are not installed; image/PDF/LaTeX preview features
were not enabled or validated. Health checks run from a non-code buffer can
report Prettier's filetype condition as unavailable; TypeScript formatting was
tested successfully.
