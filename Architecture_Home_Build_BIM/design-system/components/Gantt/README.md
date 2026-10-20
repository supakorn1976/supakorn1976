# Gantt

CPM schedule chart: one row per activity, week columns alternating `sunk`, bars in `gantt`, critical-path bars in `crit`.

**Markup.** Inline SVG; label column 290px in the app (activity id + name, cut at 34 characters with …, 11.5px `ink`), week columns 26–40px wide, row height 22px, bar height 12px with 2px corners. Week numbers on top in `t-axis` muted. Wrap in `.scroll` so long schedules scroll sideways.

**Rules**
- Critical activities are also listed with a `crit` Pill in the activity table, so the red bars are never the only signal.
- Sundays and listed holidays are non-working; durations in the table are working days.
