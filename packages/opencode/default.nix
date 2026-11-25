{
  pkgs ? import ../../nix/pkgs.nix { },
}:
pkgs.stdenvNoCC.mkDerivation (finalAttrs: {
  pname = "opencode";
  version = "2.0.32";

  # Same native release used by the upstream V2 installer; no npm install step.
  src = pkgs.fetchurl {
    url = "https://registry.npmjs.org/@opencode/cli-linux-x64/-/cli-linux-x64-${finalAttrs.version}.tgz";
    hash = "sha512-Q50ofBQ3gdwjD6ZQhrVR8fVlm8D2xPMshy4dynY6l6b+qLdKgBSJ9WpoaDyrQX1YWmf2s7IN4RbXmoXXdJitDA==";
  };

  nativeBuildInputs = [
    pkgs.autoPatchelfHook
    pkgs.makeWrapper
  ];
  buildInputs = [ pkgs.glibc ];

  # Bun embeds the application and native modules in the ELF executable.
  dontStrip = true;
  dontConfigure = true;
  dontBuild = true;

  installPhase = ''
    runHook preInstall
    install -Dm755 bin/opencode "$out/bin/opencode"
    runHook postInstall
  '';

  postFixup = ''
    wrapProgram "$out/bin/opencode" \
      --set OPENCODE_DISABLE_AUTOUPDATE 1 \
      --prefix LD_LIBRARY_PATH : ${pkgs.lib.makeLibraryPath [
        pkgs.stdenv.cc.cc.lib
        pkgs.openssl
        pkgs.zlib
      ]} \
      --prefix PATH : ${pkgs.lib.makeBinPath [ pkgs.git pkgs.ripgrep ]}
    ln -s opencode "$out/bin/opencode2"
  '';

  doInstallCheck = true;
  installCheckPhase = ''
    runHook preInstallCheck
    export HOME="$TMPDIR/check-home"
    mkdir -p "$HOME"
    test "$("$out/bin/opencode" --version)" = "opencode v${finalAttrs.version}"
    test "$("$out/bin/opencode2" --version)" = "opencode v${finalAttrs.version}"
    "$out/bin/opencode" --help >/dev/null
    runHook postInstallCheck
  '';

  meta = {
    description = "OpenCode V2 CLI, patched for NixOS";
    homepage = "https://opencode.ai/v2/";
    license = pkgs.lib.licenses.mit;
    sourceProvenance = [ pkgs.lib.sourceTypes.binaryNativeCode ];
    platforms = [ "x86_64-linux" ];
    mainProgram = "opencode";
  };
})
