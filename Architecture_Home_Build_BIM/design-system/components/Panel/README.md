# Panel

The work area's one container: a surface block with a 1px `line` border and radius `r`, padded `space-14` × `space-16`, titled by an `h3` in `t-heading`.

**Markup.** `<div class="panel"><h3>…</h3>…</div>`. Lay two panels side by side with `.grid2` (`repeat(auto-fit, minmax(300px, 1fr))`, gap `space-16`). Stack panels in `.work` (gap `space-16`).

**States.** Empty: `<div class="empty">` (padding `space-28`, centered, muted). Error: `.err` text in `crit` (13px, pre-wrap), followed by a `.note` that says where to fix it.

**Rules**
- No shadows. Panels never nest inside panels.
- Headings name the content in Thai nouns (ต้นทุนแยกหมวด, ความก้าวหน้าสะสม, งวดงานทุก 4 สัปดาห์).
