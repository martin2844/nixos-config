{
  pkgs ? import ../../nix/pkgs.nix { },
}:
pkgs.writeShellApplication {
  name = "desktop-theme";
  runtimeInputs = [
    pkgs.glib
    pkgs.kdePackages.plasma-workspace
  ];
  text = ''
    # Apply the repository defaults to an existing user database too.
    export GSETTINGS_SCHEMA_DIR=${pkgs.gsettings-desktop-schemas}/share/gsettings-schemas/${pkgs.gsettings-desktop-schemas.name}/glib-2.0/schemas
    export GIO_EXTRA_MODULES=${pkgs.dconf.lib}/lib/gio/modules
    gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark'
    gsettings set org.gnome.desktop.interface gtk-theme 'Breeze-Dark'
    gsettings set org.gnome.desktop.interface icon-theme 'breeze-dark'
    QT_QPA_PLATFORM=offscreen plasma-apply-colorscheme BreezeDark
  '';
}
