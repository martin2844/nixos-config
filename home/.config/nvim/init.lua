-- Include the Nix tool bundle even when launched from a desktop shortcut.
vim.env.PATH = vim.fn.expand("~/.local/share/nvim-tools/bin") .. ":" .. vim.env.PATH
require("config.lazy")
