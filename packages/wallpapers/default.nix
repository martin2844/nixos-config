{
  pkgs ? import ../../nix/pkgs.nix { },
}:
let
  space = builtins.fromJSON (builtins.readFile ./sources.json);
  download = image: pkgs.fetchurl { inherit (image) url hash; };
  gnome = pkgs.gnome-backgrounds;
  plasma = pkgs.kdePackages.plasma-workspace-wallpapers;
  breeze = pkgs.kdePackages.breeze;
in
pkgs.runCommand "desktop-wallpapers" { nativeBuildInputs = [ pkgs.imagemagick ]; } ''
  target="$out/share/wallpapers/curated"
  mkdir -p "$target" "$out/share/doc/desktop-wallpapers"
  export MAGICK_THREAD_LIMIT=2
  # Decode and resize without recolouring. Keep square artwork usable on portraits too.
  for name in fold curvy amber sheet balls; do
    magick "${gnome}/share/backgrounds/gnome/$name-d.jxl" \
      -resize '3840x3840>' -quality 94 "$target/Abstract-$name.jpg"
  done
  cp "${breeze}/share/wallpapers/Next/contents/images_dark/5120x2880.png" "$target/Plasma-Subarctic-dark.png"
  cp "${breeze}/share/wallpapers/Next/contents/images/5120x2880.png" "$target/Plasma-Subarctic.png"
  cp "${plasma}/share/wallpapers/Nexus/contents/images_dark/5120x2880.png" "$target/Plasma-Nexus-dark.png"
  cp "${plasma}/share/wallpapers/MilkyWay/contents/images/5120x2880.png" "$target/Plasma-Milky-Way.png"
  ${pkgs.lib.concatMapStringsSep "\n" (image: ''
    cp ${download image} "$target/${image.name}.jpg"
  '') space}
  cp ${./CREDITS.md} "$out/share/doc/desktop-wallpapers/CREDITS.md"
  cp ${./sources.json} "$out/share/doc/desktop-wallpapers/sources.json"
  cp "${breeze}/share/wallpapers/Next/metadata.json" "$out/share/doc/desktop-wallpapers/Plasma-Subarctic.json"
  cp "${plasma}/share/wallpapers/Nexus/metadata.json" "$out/share/doc/desktop-wallpapers/Plasma-Nexus.json"
  cp "${plasma}/share/wallpapers/MilkyWay/metadata.json" "$out/share/doc/desktop-wallpapers/Plasma-Milky-Way.json"
''
