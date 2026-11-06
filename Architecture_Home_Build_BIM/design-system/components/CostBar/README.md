# CostBar

A single 12px stacked bar of direct cost by discipline, with a legend underneath.

**Markup.** `.bar` (flex, `r-bar`, `line` frame) of `<span>` segments, each `width: <share>%` and `background: var(--c-S | --c-A | --c-P | --c-E)`, titled with the category name. `.legend` below (wrap, `t-meta` muted) uses `<i>` 14×3 colour keys.

**Rules**
- Order S, A, P, E as in the BOQ. For a non-house project the palette cycles `c-S`, `c-A`, `c-P`, `c-E`, `gantt`, `warn`.
- Always pair the bar with the table or legend that names each share; colour alone never identifies a discipline.
