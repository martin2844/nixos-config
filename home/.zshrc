# Personal Bash PATH setting, with duplicate entries removed by Zsh.
typeset -U path PATH
path=("$HOME/.local/bin" $path)
export PATH

export ZSH="$HOME/.nix-profile/share/oh-my-zsh"
ZSH_CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/oh-my-zsh"
ZSH_COMPDUMP="$ZSH_CACHE_DIR/zcompdump-$ZSH_VERSION"
ZSH_CUSTOM="${XDG_CONFIG_HOME:-$HOME/.config}/oh-my-zsh/custom"
mkdir -p "$ZSH_CACHE_DIR" "$ZSH_CUSTOM"
# Oh My Zsh is updated with the pinned Nix packages.
zstyle ':omz:update' mode disabled
ZSH_THEME="robbyrussell"
plugins=(git node npm)
source "$ZSH/oh-my-zsh.sh"

# Preserve the aliases supplied by NixOS's Bash configuration.
alias l='ls -alh'
alias ll='ls -l'
alias ls='ls --color=tty'

HISTFILE="$HOME/.zsh_history"
HISTSIZE=10000
SAVEHIST=10000
