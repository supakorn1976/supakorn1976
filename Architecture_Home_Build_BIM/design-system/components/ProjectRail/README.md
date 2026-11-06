# ProjectRail

Left column of the app: product name, saved projects list, and the project actions.

**Markup.** `.rail` (surface, right hairline, padding `space-16`, gap `space-14`; 260px column, stacks on top below 860px). Inside: `.brand` (`b` in `t-brand`, `span` sub-line 12px muted), an `.eyebrow` section label (`t-eyebrow`, uppercase, muted), `.plist` of `<button class="pitem">` (name with ellipsis + `small` timestamp), the current one `.on` (`accent` border, `accent-soft` fill), then a `.btnrow` of Buttons and a `.note`.

**Rules**
- Timestamps are `YYYY-MM-DD HH:MM`, cut from ISO.
- The note under the actions explains where work is stored (this browser only, or shared) in one plain sentence.
