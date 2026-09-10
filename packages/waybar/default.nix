{
  pkgs ? import ../../nix/pkgs.nix { },
}:
let
  calendarPython = pkgs.python3.withPackages (ps: [ ps.holidays ]);
  calendarData = pkgs.runCommand "desktop-calendar-holidays.json" { } ''
    cp ${./calendar/generate.py} generate.py
    cp ${./calendar/test_holidays.py} test_holidays.py
    ${calendarPython}/bin/python3 test_holidays.py
    ${calendarPython}/bin/python3 generate.py > "$out"
  '';
in pkgs.waybar.overrideAttrs (old: {
  patches = (old.patches or [ ]) ++ [
    ./tray-filter.patch
    ./hyprland-lua-workspaces.patch
    ./calendar.patch
  ];
  postPatch = (old.postPatch or "") + ''
    cp ${./calendar/popup.hpp} include/modules/desktop_calendar.hpp
    substituteInPlace src/modules/clock.cpp --replace-fail '@calendar-data@' '${calendarData}'
  '';
})
