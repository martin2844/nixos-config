{ pkgs, ... }:
let
  mount = "/run/media/martin/Windows-VMs";
  uuid = "e5de2bb9-d182-49a4-b24b-de175d6742c0";
in {
  environment.systemPackages = [ pkgs.freerdp ];
  fileSystems.${mount} = {
    device = "/dev/disk/by-uuid/${uuid}";
    fsType = "ext4";
    options = [ "nofail" "nosuid" "nodev" "noexec" "x-systemd.device-timeout=15s" "x-systemd.mount-timeout=30s" ];
  };
  systemd.services.windows-vm-storage-setup = {
    description = "Prepare dedicated Windows VM storage";
    wantedBy = [ "multi-user.target" ];
    unitConfig.RequiresMountsFor = mount;
    serviceConfig.Type = "oneshot";
    script = ''
      test "$(${pkgs.util-linux}/bin/findmnt -rn -o UUID --mountpoint ${mount})" = ${uuid}
      ${pkgs.util-linux}/bin/findmnt -rn --mountpoint ${mount} --options rw >/dev/null
      ${pkgs.coreutils}/bin/chown martin:users ${mount}
      ${pkgs.coreutils}/bin/chmod 0700 ${mount}
      ${pkgs.coreutils}/bin/install -d -o martin -g users -m 0700 ${mount}/Windows ${mount}/Shared
    '';
  };
}
