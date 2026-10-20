# DataTable

Dense quantity and cost table (BOQ, QTO, payment milestones): hairline rows, sticky muted headers, mono right-aligned figures.

**Markup.** Wrap in `.scroll` (horizontal scroll). `th` gets `t-label` muted on surface, sticky. Numeric cells `td.n` / `th.n`: right-aligned, mono, tabular-nums. Row roles: `tr.cat` (category header, `accent-soft` fill, 600), `tr.sub` (sub-total, `sunk` fill, 600), `tr.tot` (grand total, 600, `line` top rule). Editable figures: `td input` (86px, `r-input`, mono 12.5px; `.w` 52px, `.t` 120px text).

**Consumer provides** rows already grouped by discipline (S, A, P, E), with a 10×10 swatch in the discipline colour before each category title, and a `.basis` cell (muted 12px, max 420px) saying where a rate came from.

**Rules**
- Money in บาท with thousands separators; quantities 2 decimals with the unit in its own column (ม³, ม², กก., ชุด).
- Do not zebra-stripe; row rules are `line2`.
