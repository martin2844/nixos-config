# Validation (2026-09-08)

- Nix collection and patched Waypaper package built successfully.
- Gallery rendered all 12 thumbnails in a floating 1100×760 Wayland window.
- Real selection used Waypaper's post-command to update the persistent image.
  A filename containing spaces, a semicolon, and a dollar sign was handled literally.
- GUI selection of Plasma Subarctic also reached the same callback. Its saved
  wallpaper copy matches the source byte-for-byte; Hyprpaper service is active.
- The existing read-only wallpaper can now be replaced atomically, and successive
  choices work. Only the managed Hyprpaper service is used; no restore daemon added.
- Hyprland config verification and reload succeeded, with no config errors.
- Installer tests cover the two new package outputs in build-only mode.
- Login persistence follows the existing hyprpaper.conf autostart configuration;
  this task did not log the user out or reboot the machine.
