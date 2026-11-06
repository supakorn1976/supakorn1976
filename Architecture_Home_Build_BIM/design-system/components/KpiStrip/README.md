# KpiStrip

A single framed strip of project figures under the title bar: cost, duration, elements, clashes. Cells divide with `line2` hairlines instead of being separate cards.

**Markup.** `.kpis` (grid, `repeat(auto-fit, minmax(140px, 1fr))`, 1px `line` frame, radius `r`) containing `.kpi` cells, each with `.l` label (`t-small`, muted), `.v` value (`t-kpi`, mono, tabular-nums, no wrap) and `.s` sub-line (`t-small`, muted).

**Consumer provides** the label, the formatted value with its unit in the sub-line (บาท, วัน, สัปดาห์, ชิ้น), and the basis.

**Rules**
- Values are numbers only; the unit goes in `.l` or `.s`.
- Baht values use thousands separators and no decimals; percentages one decimal.
- When the spec fails to compute, show one cell: label สถานะ, value ข้อมูลแบบมีข้อผิดพลาด in `crit`.
