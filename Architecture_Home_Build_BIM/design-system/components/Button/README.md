# Button

Bordered action button; `.btn` for most actions, `.btn.pri` for the one save or run action in a group, `.btn.warn` for delete.

**Markup.** `<button class="btn">…</button>`. Variants are modifier classes: `pri` (accent fill, `accent-ink` text), `warn` (crit text on surface; destructive). `:disabled` drops to 50% opacity.

**Spacing.** Put buttons in `.btnrow` (flex, wrap, gap `space-6`).

**Rules**
- One `pri` per row. In the rail that is บันทึก (Save).
- Labels are short Thai verbs or verb + object: บันทึก, ทำสำเนา, ลบ, ส่งออก Excel, ใหม่: บ้าน TYPE03.
- Hover changes only the border to `accent`; focus shows a 2px `accent` outline offset 1px.
- Never colour a button green or red fill; destructive is `warn` text only, and asks for confirmation inside the page (no `confirm()`).
