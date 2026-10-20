# SCurve

Cumulative progress chart by week: a 2.5px `accent` line from 0 to 100%, weekly value as `accent-soft` bars on the lower 45%, `line2` gridlines at 0/25/50/75/100%, and a dot on the last week.

**Markup.** Inline SVG, `viewBox` width × height, padding left 44 / right 12 / top 12 / bottom 28. Axis text `t-axis` in `muted`; the x-axis is labelled สัปดาห์ and thinned to at most ten ticks. The full view adds one dashed (4 3) 1.5px line per discipline in its `c-*` colour. Payment milestones fall every 4 weeks.

**Rules**
- Every colour comes from a token, so the chart follows the theme.
- Pair the chart with the milestone table (งวด, สิ้นสัปดาห์ที่, วันที่, สะสม %, มูลค่าสะสม, มูลค่างวด).
