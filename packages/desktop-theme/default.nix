{ pkgs ? import ../../nix/pkgs.nix { } }:
let
  fonts = pkgs.writeShellApplication {
    name = "desktop-fonts";
    runtimeInputs = [ pkgs.glib pkgs.kdePackages.kconfig pkgs.fontconfig ];
    text = ''
    export GSETTINGS_SCHEMA_DIR=${pkgs.gsettings-desktop-schemas}/share/gsettings-schemas/${pkgs.gsettings-desktop-schemas.name}/glib-2.0/schemas
    export GIO_EXTRA_MODULES=${pkgs.dconf.lib}/lib/gio/modules
    gsettings set org.gnome.desktop.interface font-name 'Inter 10'
    gsettings set org.gnome.desktop.wm.preferences titlebar-font 'Inter Bold 10'
    for key in font menuFont toolBarFont taskbarFont; do
      kwriteconfig6 --file kdeglobals --group General --key "$key" --notify 'Inter,10,-1,5,50,0,0,0,0,0'
    done
    kwriteconfig6 --file kdeglobals --group General --key smallestReadableFont --notify 'Inter,8,-1,5,50,0,0,0,0,0'
    kwriteconfig6 --file kdeglobals --group WM --key activeFont --notify 'Inter,10,-1,5,75,0,0,0,0,0'
    '';
  };
  theme = pkgs.writeShellApplication {
    name = "desktop-theme";
    runtimeInputs = [ pkgs.glib pkgs.kdePackages.plasma-workspace ];
    text = ''
    export GSETTINGS_SCHEMA_DIR=${pkgs.gsettings-desktop-schemas}/share/gsettings-schemas/${pkgs.gsettings-desktop-schemas.name}/glib-2.0/schemas
    export GIO_EXTRA_MODULES=${pkgs.dconf.lib}/lib/gio/modules
    gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark'
    gsettings set org.gnome.desktop.interface gtk-theme 'Breeze-Dark'
    gsettings set org.gnome.desktop.interface icon-theme 'breeze-dark'
    QT_QPA_PLATFORM=offscreen plasma-apply-colorscheme BreezeDark
    ${fonts}/bin/desktop-fonts
    '';
  };
in pkgs.symlinkJoin {
  name = "desktop-theme";
  paths = [ theme fonts pkgs.inter ];
}
