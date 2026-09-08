{ pkgs, ... }:
{
  # Defaults, not locks: applications and users can still choose another theme.
  programs.dconf.enable = true;
  programs.dconf.profiles.user.databases = [
    {
      settings."org/gnome/desktop/interface" = {
        color-scheme = "prefer-dark";
        gtk-theme = "Breeze-Dark";
        icon-theme = "breeze-dark";
      };
    }
  ];
  environment.systemPackages = [ pkgs.kdePackages.breeze-gtk ];
  environment.etc."xdg/kdeglobals".text = ''
    [General]
    ColorScheme=BreezeDark
    [KDE]
    LookAndFeelPackage=org.kde.breezedark.desktop
  '';
}
