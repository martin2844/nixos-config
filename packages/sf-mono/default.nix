{ pkgs ? import ../../nix/pkgs.nix { } }:
pkgs.stdenvNoCC.mkDerivation {
  pname = "sf-mono";
  version = "2024-09-19";
  src = pkgs.fetchurl {
    url = "https://devimages-cdn.apple.com/design/resources/download/SF-Mono.dmg";
    sha256 = "6d4a0b78e3aacd06f913f642cead1c7db4af34ed48856d7171a2e0b55d9a7945";
  };
  nativeBuildInputs = [ pkgs._7zz ];
  dontUnpack = true;
  installPhase = ''
    runHook preInstall
    7zz x "$src" -odisk
    7zz x 'disk/SFMonoFonts/SF Mono Fonts.pkg' -opackage
    7zz x package/SFMonoFonts.pkg/Payload -opayload
    7zz x 'payload/Payload~' -ofonts
    install -Dm644 fonts/Library/Fonts/*.otf -t "$out/share/fonts/opentype"
    install -Dm644 package/Resources/English.lproj/License.rtf "$out/share/licenses/sf-mono/License.rtf"
    runHook postInstall
  '';
  meta = {
    description = "Apple SF Mono font family";
    homepage = "https://developer.apple.com/fonts/";
    license = pkgs.lib.licenses.unfree;
    platforms = pkgs.lib.platforms.all;
  };
}
