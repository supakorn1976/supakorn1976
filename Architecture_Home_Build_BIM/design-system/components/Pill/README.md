# Pill

Outline pill for a short status word in a table cell or check list: `.pill` neutral, `.pill.ok`, `.pill.warn`, `.pill.crit`.

**Markup.** `<span class="pill ok">ผ่าน</span>`. Text and border share the semantic token; there is no fill.

**Rules**
- Always a word, never an empty coloured dot: ผ่าน, เตือน, ไม่ผ่าน, วิกฤต.
- `crit` marks critical-path activities and failed checks only.
