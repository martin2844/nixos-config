# Calendar reminders

Click a day in the Waybar calendar to add, edit or delete a reminder. Green dots
mark days with reminders; hover lists their local times and titles. The editor
also opens from the application launcher as **Calendar reminders**. Select a row
to edit it; **New** clears the form. Delivered reminders remain visible until
deleted. Changing their scheduled time enables another notification.

Reminders are local, one-shot desktop notifications. The user timer checks every
30 seconds while the graphical session is active. Overdue reminders are delivered
at the next check after login or resume. Delivery requires a running notification
daemon (SwayNC in Hyprland, or Plasma's notification service); failed D-Bus calls
are retried. Do Not Disturb and notification-center settings still apply. A
successful delivery records the notification daemon's acceptance, not that the
user read it. Notifications request no expiry and remain in notification history.

## Storage and timezones

Data lives in `$XDG_DATA_HOME/desktop-calendar/reminders.json`, defaulting to
`~/.local/share/desktop-calendar/reminders.json`; back up this directory. Personal
reminders are never part of the Nix derivation or repository. Writes use a lock,
atomic replacement and fsync. The timer and editor share the same lock. Corrupt
or unsupported files cause an error and are never replaced by an empty calendar.

Each reminder stores an absolute Unix timestamp and an IANA timezone. The editor
defaults to the desktop timezone and keeps the reminder's timezone when editing;
the calendar and daily list display times in the current desktop timezone.
Ambiguous or nonexistent daylight-saving transition times are rejected with an
explanation. Editing notes/title keeps delivery state; changing time resets it.
A crash after the daemon accepts a notification but before the state is saved
may repeat that notification on the next check (delivery is at least once).

## CLI

```sh
calendar-reminders edit 2026-09-18
calendar-reminders add --at 2026-09-18T10:00 --timezone Europe/Madrid \
  --title 'Review quality checks' --notes 'Check errors and false positives'
calendar-reminders list
calendar-reminders delete REMINDER_ID
```

`add --id ID` updates an existing ID, useful for repeatable setup. `tick` delivers
only pending, due reminders; systemd invokes it automatically. Past dates are
allowed and notify on the next check.

## Installation and verification

`./install.sh` builds the package and Waybar, links the user units and enables the
timer. For a targeted update, build `nix-build . -A calendar-reminders -o
result-calendar-reminders` and `nix-build . -A waybar -o result-waybar`, replace
only those profile entries, link the two units listed in `links.json`, then run:

```sh
systemctl --user daemon-reload
systemctl --user enable --now calendar-reminders.timer
systemctl --user restart 'app-hypr\x2dwaybar@autostart.service'
systemctl --user list-timers calendar-reminders.timer
journalctl --user -u calendar-reminders.service
```

The package build runs `test_reminders.py`: confirmed-time conversion, DST gaps
and folds, overdue/future delivery, retries after partial failure, rescheduling,
deletion, concurrent edits/checks, and preservation after corruption/write failure.
After GTK/Waybar changes, exercise a day click and editor save on the live session,
and test a due reminder using an isolated `XDG_DATA_HOME`.
