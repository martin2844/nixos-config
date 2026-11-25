{ pkgs, ... }:

{
  # Razer Pro Click V2: 1532:00d1 (receiver), 1532:00d0 (wired).
  hardware.openrazer = {
    enable = true;
    users = [ "martin" ];
  };

  environment.systemPackages = [ pkgs.polychromatic ];
}
