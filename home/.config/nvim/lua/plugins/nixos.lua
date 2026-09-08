return {
  -- Nix supplies language servers and formatters with compatible libraries.
  { "mason-org/mason.nvim", enabled = false },
  { "mason-org/mason-lspconfig.nvim", enabled = false },
  {
    "saghen/blink.cmp",
    dir = vim.fn.expand("~/.local/share/nvim-blink"),
    version = false,
    build = false,
    opts = {
      fuzzy = { implementation = "rust", prebuilt_binaries = { download = false } },
    },
  },
}
