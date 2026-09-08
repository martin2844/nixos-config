{
  pkgs ? import ../../nix/pkgs.nix { },
}:
pkgs.nmgui.overrideAttrs (old: {
  postPatch = (old.postPatch or "") + ''
    cp ${./ethernet_panel.py} app/ui/ethernet_panel.py
    substituteInPlace app/ui/main_window.py \
      --replace-fail 'from ui.network_list import NetworkListWidget' 'from ui.network_list import NetworkListWidget
    from ui.ethernet_panel import EthernetPanel' \
      --replace-fail 'self.set_title("Network Manager")' 'self.set_title("Internet")' \
      --replace-fail 'main_box.append(self._create_wifi_toggle())' 'main_box.append(EthernetPanel())
            main_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
            main_box.append(self._create_wifi_toggle())'
  '';
})
