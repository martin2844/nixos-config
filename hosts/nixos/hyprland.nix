{ pkgs, ... }:

{
  # Keep Plasma and SDDM in configuration.nix. Select the uwsm-managed session.
  programs.hyprland = {
    enable = true;
    withUWSM = true;
    xwayland.enable = true;
  };
  programs.hyprlock.enable = true;
  # hyprlock enables the native hypridle service; scope it to this session.
  systemd.user.services.hypridle.unitConfig.ConditionEnvironment = "XDG_CURRENT_DESKTOP=Hyprland";
  security.polkit.enable = true;
  hardware.bluetooth.enable = true;
  services.blueman.enable = true;

  # Steam's module supplies its runtime and 32-bit AMD graphics support.
  programs.steam.enable = true;
  services.tailscale = {
    enable = true;
    extraSetFlags = [ "--operator=martin" ];
  };

  # Plasma already enables NetworkManager, PipeWire, UDisks and KDE/GTK portals.
  # The Hyprland module adds its portal and desktop-specific portal preferences.
  environment.systemPackages = with pkgs; [
    ghostty
    neovim
    # Vim is already installed in martin's user packages.
    discord
    vlc
    obsidian
    trayscale # Graphical Tailscale client; sign in after activation.
    kdePackages.dolphin
    kdePackages.ark
    kdePackages.kio-extras
    kdePackages.kio-fuse
    kdePackages.kio-admin
    kdePackages.kdegraphics-thumbnailers
    kdePackages.ffmpegthumbs
    rofi
    waybar
    networkmanagerapplet
    pavucontrol
    swaynotificationcenter
    hyprpolkitagent
    wl-clipboard
    cliphist
    grim
    slurp
    swappy
    hypridle
    hyprpaper
    libnotify
  ];
  fonts.packages = [ pkgs.nerd-fonts.jetbrains-mono ];

  # Override upstream applets' autostart entries, preventing duplicate instances
  # and leaving Plasma's built-in network/Bluetooth widgets in charge in KDE.
  environment.etc."xdg/autostart/nm-applet.desktop".text = ''
    [Desktop Entry]
    Type=Application
    Name=NetworkManager
    Exec=${pkgs.networkmanagerapplet}/bin/nm-applet --indicator
    OnlyShowIn=Hyprland;
  '';
  environment.etc."xdg/autostart/blueman.desktop".text = ''
    [Desktop Entry]
    Type=Application
    Name=Blueman
    Exec=${pkgs.blueman}/bin/blueman-applet
    OnlyShowIn=Hyprland;
  '';
}
