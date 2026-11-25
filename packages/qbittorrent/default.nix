{ pkgs ? import ../../nix/pkgs.nix { }, }:
let
  manifest = builtins.fromJSON (builtins.readFile ./plugins.json);
  plugins = pkgs.linkFarm "qbittorrent-search-plugins" (map (plugin: {
    name = plugin.file;
    path = pkgs.fetchurl {
      inherit (plugin) url hash;
      name = plugin.file;
    };
  }) manifest);
  setup = pkgs.writeShellScriptBin "qbittorrent-setup-search" ''
    exec ${pkgs.python3}/bin/python3 ${./setup-search.py} ${plugins} "$@"
  '';
in
pkgs.symlinkJoin {
  name = "qbittorrent-desktop";
  paths = [ pkgs.qbittorrent setup ];
  nativeBuildInputs = [ pkgs.makeWrapper ];
  postBuild = ''
    # Preserve the upstream Qt/Python wrapper and desktop integration.
    wrapProgram "$out/bin/qbittorrent" \
      --run "${setup}/bin/qbittorrent-setup-search"
  '';
  meta = pkgs.qbittorrent.meta;
}
