{
  pkgs ? import ../../nix/pkgs.nix { },
}:
let
  python = pkgs.python3Packages;
  hyprland-config = python.buildPythonPackage {
    pname = "hyprland-config";
    version = "0.9.16";
    pyproject = true;
    src = pkgs.fetchurl {
      url = "https://files.pythonhosted.org/packages/39/24/779fa44f2d720bf26b9675a152ede5080e56b594110b34f1ec79e7e2449e/hyprland_config-0.9.16.tar.gz";
      sha256 = "6bf861604177e7aab79aee2fbdadfbfc261150c23ff2932dfdd334f30d71b507";
    };
    build-system = [ python.hatchling ];
    dependencies = [ ];
    pythonImportsCheck = [ "hyprland_config" ];
  };
  hyprland-schema = python.buildPythonPackage {
    pname = "hyprland-schema";
    version = "0.7.1";
    pyproject = true;
    src = pkgs.fetchurl {
      url = "https://files.pythonhosted.org/packages/af/48/11d41c3740072c309fd1eb61dfbfe4f9897a2b1124c1f10cb17a18dc8172/hyprland_schema-0.7.1.tar.gz";
      sha256 = "e73d4a19aece1df602c52b2985df35f6c8bc584b0fa7058ea56e1aab9fc01233";
    };
    build-system = [ python.hatchling ];
    dependencies = [ ];
    pythonImportsCheck = [ "hyprland_schema" ];
  };
  hyprland-socket = python.buildPythonPackage {
    pname = "hyprland-socket";
    version = "0.12.2";
    pyproject = true;
    src = pkgs.fetchurl {
      url = "https://files.pythonhosted.org/packages/3d/98/f5d09c4dc2f9a4f361c9a0aa6201178feea3083475a1640586dcf15b3931/hyprland_socket-0.12.2.tar.gz";
      sha256 = "b45778940710d0667d372f227bc53452fdf123d71d1dcbd652a97677ecbfc70b";
    };
    build-system = [ python.hatchling ];
    dependencies = [ ];
    pythonImportsCheck = [ "hyprland_socket" ];
  };
  hyprland-monitors = python.buildPythonPackage {
    pname = "hyprland-monitors";
    version = "0.9.0";
    pyproject = true;
    src = pkgs.fetchurl {
      url = "https://files.pythonhosted.org/packages/d1/09/d8cff343afb02a76bf8004ca189038d65620f78cedd90cd4aa33d04b448e/hyprland_monitors-0.9.0.tar.gz";
      sha256 = "32afec5fba923283de22239d009772c50e974c0a2b3ab070e9d3ce7e67d7b99a";
    };
    build-system = [ python.hatchling ];
    dependencies = [ hyprland-socket ];
    pythonImportsCheck = [ "hyprland_monitors" ];
  };
  hyprland-state = python.buildPythonPackage {
    pname = "hyprland-state";
    version = "0.4.7";
    pyproject = true;
    src = pkgs.fetchurl {
      url = "https://files.pythonhosted.org/packages/13/1f/9acf4c2cd13535fe0a19e7656ef89196fddd6ca532052c2bd2321b16c628/hyprland_state-0.4.7.tar.gz";
      sha256 = "479a6d1d01d9a91606b92156a4a3db2f378d6cadede85836dcfbe9e057595c99";
    };
    build-system = [ python.hatchling ];
    dependencies = [
      hyprland-config
      hyprland-monitors
      hyprland-schema
      hyprland-socket
    ];
    pythonImportsCheck = [ "hyprland_state" ];
  };
in
python.buildPythonApplication {
  pname = "hyprmod";
  version = "0.4.0-2026-08-27";
  pyproject = true;
  src = pkgs.fetchurl {
    name = "hyprmod-source.tar.gz";
    url = "https://codeload.github.com/BlueManCZ/hyprmod/tar.gz/ffd47d804d8996cf3852dbb7ca1c949c424a57fb";
    sha256 = "0362r1ywpg94a9bra1k75x5s17r8wi8rkxnmx3fjcpn3cajw9hvd";
  };
  build-system = [ python.hatchling ];
  dependencies = [
    python.pygobject3
    python.pycairo
    hyprland-config
    hyprland-schema
    hyprland-state
    hyprland-monitors
    hyprland-socket
  ];
  nativeBuildInputs = [
    pkgs.glib
    pkgs.gobject-introspection
    pkgs.wrapGAppsHook4
  ];
  buildInputs = [
    pkgs.gtk4
    pkgs.libadwaita
  ];
  dontWrapGApps = true;
  preFixup = ''
    makeWrapperArgs+=("''${gappsWrapperArgs[@]}")
    makeWrapperArgs+=(--prefix PATH : ${
      pkgs.lib.makeBinPath [
        pkgs.lua5_4
        pkgs.hyprland
      ]
    })
  '';
  postInstall = ''
    install -Dm644 data/applications/io.github.bluemancz.hyprmod.desktop $out/share/applications/io.github.bluemancz.hyprmod.desktop
    mkdir -p $out/share/icons/hicolor/scalable/apps
    cp data/icons/hicolor/scalable/apps/*.svg $out/share/icons/hicolor/scalable/apps/
  '';
  meta = {
    description = "Graphical Hyprland settings with Lua support";
    homepage = "https://github.com/BlueManCZ/hyprmod";
    license = pkgs.lib.licenses.gpl3Plus;
    mainProgram = "hyprmod";
    platforms = pkgs.lib.platforms.linux;
  };
}
