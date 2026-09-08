{
  pkgs ? import ../../nix/pkgs.nix { },
}:
with pkgs;
stdenv.mkDerivation {
  pname = "chatgpt-desktop";
  version = "26.901.51231";
  src = fetchurl {
    url = "https://persistent.oaistatic.com/codex-app-prod/linux/deb/latest/chatgpt_amd64.deb";
    sha256 = "0pn0qpmdsrk4mrdjv2nzshc2b8x888xwgdysd69klgbwv2402n32";
  };
  nativeBuildInputs = [
    dpkg
    autoPatchelfHook
    makeWrapper
  ];
  buildInputs = [
    alsa-lib
    at-spi2-atk
    at-spi2-core
    atk
    cairo
    cups
    dbus
    expat
    fontconfig
    freetype
    gdk-pixbuf
    glib
    gtk3
    libGL
    libdrm
    libgbm
    libnotify
    libpulseaudio
    libsecret
    libusb1
    libuuid
    libxcb
    libxkbcommon
    nspr
    nss
    pango
    stdenv.cc.cc
    systemd
    wayland
    libx11
    libxcomposite
    libxdamage
    libxext
    libxfixes
    libxrandr
    libxrender
    libxtst
    libxscrnsaver
    libxshmfence
    libxkbfile
    libxkbcommon
    (lib.getLib qt5.qtbase)
    (lib.getLib qt6.qtbase)
    zlib
    openssl
  ];
  dontWrapQtApps = true;
  dontUnpack = true;
  dontStrip = true;
  # Optional Alpine/musl addons are unused on this glibc system.
  autoPatchelfIgnoreMissingDeps = [ "libc.musl-x86_64.so.1" ];
  installPhase = ''
    runHook preInstall
    dpkg-deb -x $src unpacked
    mkdir -p $out
    cp -a unpacked/usr/lib unpacked/usr/share $out/
    mkdir -p $out/bin
    # Chromium's Qt 5 integration needs the platform plugins from qtbase's
    # default (bin) output, not just the Qt libraries used by autoPatchelf.
    makeWrapper $out/lib/chatgpt/ChatGPT $out/bin/chatgpt \
      --prefix QT_PLUGIN_PATH : "${qt5.qtbase}/${qt5.qtbase.qtPluginPrefix}" \
      --prefix LD_LIBRARY_PATH : ${
        lib.makeLibraryPath [
          libGL
          libgbm
          libsecret
          libnotify
          libpulseaudio
          systemd
        ]
      } \
      --prefix XDG_DATA_DIRS : "$GSETTINGS_SCHEMAS_PATH" \
      --suffix PATH : ${
        lib.makeBinPath [
          xdg-utils
          git
          xz
        ]
      }
    substituteInPlace $out/share/applications/chatgpt.desktop \
      --replace-fail 'Exec=chatgpt' "Exec=$out/bin/chatgpt"
    runHook postInstall
  '';
  meta = {
    description = "Official ChatGPT Linux desktop application, repackaged from Debian";
    platforms = [ "x86_64-linux" ];
    mainProgram = "chatgpt";
  };
}
