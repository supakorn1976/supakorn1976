# Field

Labelled input for project parameters, laid out in an auto-fit `.form` grid (`minmax(210px, 1fr)`, gaps 10px × `space-16`).

**Markup.** `<div class="field"><label for="q_x">…</label><input id="q_x"></div>`; inputs, selects and textareas take `sunk` fill, `line` border, radius `r`. The JSON editor is `textarea.json` (mono 12px, min-height 420px, no wrap).

**Consumer provides** a stable `id` per control, a label that names the unit in brackets (ม., ม.รทก., บาท, %), and the value.

**Rules**
- Labels sit above the control in `t-note` muted. Put the unit or format in the label, not as placeholder text: ระดับดินเดิม (ม.รทก.), หนึ่งวันต่อบรรทัด (ปปปป-ดด-วว).
- Inputs border in `line` only (1.4:1); keyboard focus draws the 2px `accent` ring, so never remove the outline.
