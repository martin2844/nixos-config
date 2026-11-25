{ pkgs ? import ../../nix/pkgs.nix { }, }:
let
  python = pkgs.python3.withPackages (p: [ p.pygobject3 p.tzdata ]);
in pkgs.stdenvNoCC.mkDerivation {
  pname = "calendar-reminders";
  version = "1.0";
  src = pkgs.lib.cleanSourceWith {
    name = "calendar-reminders-source";
    src = ./.;
    filter = path: type:
      (type == "directory" && baseNameOf path != "__pycache")
      || (type == "regular" && pkgs.lib.hasSuffix ".py" path);
  };
  nativeBuildInputs = [ pkgs.wrapGAppsHook3 pkgs.gobject-introspection ];
  buildInputs = [ pkgs.gtk3 ];
  dontBuild = true;
  doCheck = true;
  checkPhase = ''
    ${python}/bin/python3 -m unittest -v test_reminders.py
  '';
  installPhase = ''
    mkdir -p $out/bin $out/share/calendar-reminders $out/share/applications
    cp reminders.py editor.py $out/share/calendar-reminders/
    makeWrapper ${python}/bin/python3 $out/bin/calendar-reminders \
      --add-flags $out/share/calendar-reminders/reminders.py
    cat > $out/share/applications/calendar-reminders.desktop <<EOF
    [Desktop Entry]
    Type=Application
    Name=Calendar reminders
    Comment=Add and manage local calendar reminders
    Exec=$out/bin/calendar-reminders edit
    Icon=appointment-soon
    Categories=Office;Calendar;
    EOF
  '';
}
