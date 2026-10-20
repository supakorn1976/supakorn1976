# StatusDot

Save-state indicator beside the project name: an 8px dot plus a sentence in `t-meta` muted.

**Markup.** `<div class="status"><span class="dot ok"></span><span>…</span></div>`. Dot modifiers: none (muted, a template not yet saved), `ok` (saved), `dirty` (warn, unsaved changes).

**Rules**
- The sentence carries the meaning; the dot only reinforces it. Say when it was saved (บันทึกแล้ว 14:32), or that there are unsaved changes.
