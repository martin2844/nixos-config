{
  pkgs ? import ../../nix/pkgs.nix { },
}:
pkgs.rustPlatform.buildRustPackage {
  pname = "omarchy-screenshot-preview";
  version = "0.1.1";
  src = pkgs.fetchurl {
    name = "screenshot-preview-source.tar.gz";
    url = "https://codeload.github.com/rodrigo-sntg/omarchy-screenshot-preview/tar.gz/62b5216315a989c888a4b367029465debb4ad224";
    sha256 = "0sqivb62bkz89my06yf5zxi731f2px7dh07rz9qg63xp8mnjzi2p";
  };
  cargoLock.lockFile = ./Cargo.lock;
  patches = [ ./timers.patch ];
  nativeBuildInputs = [
    pkgs.pkg-config
    pkgs.wrapGAppsHook4
  ];
  buildInputs = [
    pkgs.gtk4
    pkgs.gtk4-layer-shell
  ];
  meta = {
    description = "Draggable screenshot thumbnail for Wayland";
    homepage = "https://github.com/rodrigo-sntg/omarchy-screenshot-preview";
    license = pkgs.lib.licenses.mit;
    mainProgram = "omarchy-screenshot-preview";
    platforms = pkgs.lib.platforms.linux;
  };
}
