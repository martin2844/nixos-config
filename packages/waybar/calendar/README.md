# Interactive clock calendar

The local Waybar patch adds `clock.calendar-popup: true`. A native non-modal
GTK layer surface opens directly below the clock, without resizing the bar. Hover opens after 160 ms; a 650 ms close
delay lets the pointer cross into the calendar. Moving outside both closes it.
Click the clock to pin/unpin; the close button dismisses it. Month arrows and
Today navigate. Per-day hover shows names both in a tooltip and in a persistent
details area, so reading does not depend on a tiny tooltip.

Cells scale from 36–72 logical pixels using monitor work-area dimensions;
GTK handles HiDPI scaling. The 2560×1440 desktop uses about 70 px cells and
22 px day numbers. Today's inset pale border/background leaves space around
the number. Holiday borders nest on overlaps: orange for Catalunya/Barcelona,
light blue for Argentina and purple for USA. Today remains separately outlined.
The interface and holiday names are English, with local Barcelona names retained.

## Data and coverage

The Nix build generates an offline JSON index for 2020–2040 with the pinned
`python-holidays` package (currently 0.97). No network request occurs on hover.
The index combines Spain/CT regional holidays, Argentina national holidays and
optional non-working days, and US federal holidays including observed dates.
Optional Argentine days are explicitly labelled. US state/local holidays are
not included. Same-day entries are appended, never overwritten.

Barcelona's separately declared local dates are included only for 2026 and 2027.
These dates and Catalunya's complete 2026/2027 sets were checked against official
sources. The footer flags years without Barcelona data and future Argentine
special-date uncertainty. Other years are rule-based projections/historical
library data, not a claim that future official calendars have been published.
Outside 2020–2040 the UI explicitly reports missing holiday data. Extend the range
and verified local dates when updating the package; retain source links below.

Sources checked 2026-09-10:

- [Catalunya 2026](https://treball.gencat.cat/ca/ambits/relacions_laborals/ci/calendari_laboral/calendari-festes-2026/)
- [Catalunya 2027](https://treball.gencat.cat/ca/ambits/relacions_laborals/ci/calendari_laboral/calendari-festes-2027/)
- [Barcelona 2026 local decree](https://bcnroc.ajuntament.barcelona.cat/jspui/bitstream/11703/141067/1/GM_Festeslocals-2025.pdf): May 25, September 24.
- [Barcelona 2027](https://guia.barcelona.cat/ca/detall/festes-estatals-i-autonomiques-a-catalunya-i-locals-a-barcelona-al-2027_99400777767.html): May 17, September 24.
- [Argentina](https://www.argentina.gob.ar/feriados)
- [Argentina 2026 optional tourism days](https://www.argentina.gob.ar/normativa/nacional/norma-421799/texto)
- [US federal calendar](https://www.opm.gov/policy-data-oversight/pay-leave/federal-holidays/)
- [python-holidays](https://github.com/vacanza/holidays)

## Maintenance

`popup.hpp` is copied into the pinned Waybar source, and `calendar.patch` connects
it to Clock. The existing minute tick refreshes the today marker across midnight. Destruction disconnects anchor callbacks and pending timers. Ordinary
Waybar clock behaviour is unchanged when `calendar-popup` is disabled. Styling is
scoped to `#desktop-calendar` in the linked Waybar stylesheet.

Build with `nix-build . -A waybar -o result-waybar`. Run `test_holidays.py` using
Python with the pinned `holidays` package. Tests verify official regional dates,
Barcelona local dates, all three regions coinciding, US observed dates,
Argentine transferred and optional days, and missing future Barcelona declarations.
Also test pointer movement from clock to day, leaving/pinning/closing, month/year
navigation and today styling on the live GTK/Wayland session after patch changes.
