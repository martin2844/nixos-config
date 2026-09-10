# Notifications

SwayNotificationCenter uses the linked configuration and stylesheet in
`home/.config/swaync/`. The custom CSS extends the packaged SwayNC stylesheet,
preserving grouping, actions, inline replies and keyboard interaction.

Popups use a 460 px window, an opaque graphite surface for readability, Inter
15/14 px title/body typography, 16 px inner padding and 40 px application images.
Application icons come from the notification or its desktop entry; notifications
without usable application metadata may show a generic fallback icon. The small
overlay application badge is hidden to avoid duplicate logos. Critical notifications have a warm
border and keep their existing non-expiring timeout.

After editing, run `swaync-client -R` and `swaync-client -rs`. Restart the
`app-hypr\x2dnotifications@autostart.service` user unit when changing window size
or refreshing icon discovery after installing applications.

The notification center uses the same palette and English labels. This styling
does not add notification sounds or change the existing Codex sound hook.
