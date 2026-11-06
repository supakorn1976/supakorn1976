House BIM Studio is an engineering workbench for Thai residential and irrigation projects: a design spec becomes a 3D model, clash check, quantity take-off, 4-category BOQ, CPM schedule and weekly S-Curve. The look is a drawing sheet: cool green-grey ground, hairline rules, one engineering blue, mono figures. Build every screen from the tokens and components here.

## Content fundamentals

- **Thai first.** All interface text is Thai; keep technical acronyms as written in the trade: BOQ, S-Curve, IFC, CPM, ksc, SD40, มฐ04-62, TYPE03.
- **Short, concrete labels.** Buttons are verbs: บันทึก, ทำสำเนา, ลบ, ส่งออก JSON, ใช้วันหยุดชุดนี้. Panel headings are nouns: ต้นทุนแยกหมวด, ความก้าวหน้าสะสม, งวดงานทุก 4 สัปดาห์.
- **Units in the label, not in the value.** ระดับดินเดิม (ม.รทก.), ค่าก่อสร้างรวม (บาท), หนึ่งวันต่อบรรทัด (ปปปป-ดด-วว). Money: บาท with thousands separators, no decimals in summaries. Quantities: 2 decimals with ม³, ม², กก., ชุด. Dates: ISO `2026-11-02` in data, Thai Buddhist year (พ.ศ. 2569) only in prose.
- **Honest about estimates.** Anything derived from an undimensioned concept says so: ขนาดทั้งหมดเป็นค่าประมาณ. Structure is never presented as designed.
- **Errors say what and where.** `ใช้ไม่ได้: <reason>` followed by where to fix it: แก้ข้อมูลในแท็บ “ข้อมูลแบบ”. No apologies, no emoji.

## Visual foundations

**Color.** Neutrals carry the page: `bg` ground, `surface` for panels and bars, `sunk` for inputs and sub-rows, `ink` text, `muted` secondary text, `line` and `line2` hairlines. `accent` is the only brand hue: primary button, active tab, selected item, focus ring, the S-Curve line. Discipline colors identify BOQ categories everywhere they appear: `c-S` โครงสร้าง, `c-A` สถาปัตย์, `c-P` สุขาภิบาล, `c-E` ไฟฟ้า. Semantic `ok`, `warn`, `crit` mark state and always come with a word. `gantt` draws non-critical schedule bars; critical ones are `crit`.

**Themes.** Light and dark are both first-class. The dark accent is light, so text on it uses `accent-ink` (near-black in dark). Never hard-code white on accent.

**Contrast.** All text pairs meet 4.5:1 in both themes (`muted` on `surface` 6.1:1 light, 6.9:1 dark). `line` is 1.4:1 on `surface`, decorative only; controls rely on the 2px `accent` focus ring (6.3:1+) for state. `c-E` in light is 3.3:1: fills only, never text.

**Type.** IBM Plex Sans Thai for everything (`--font-body`), IBM Plex Mono for figures and code (`--font-mono`), both from Google Fonts with Leelawadee UI / Tahoma and Consolas fallbacks. The scale is small and dense: `t-title` 19 for the project name, `t-heading` 15 for panels, `t-body` 14, `t-control` 13 for buttons and tables, `t-label`/`t-note` 12, `t-small` 11.5, `t-eyebrow` 11 uppercase +0.08em, `t-axis` 10.5 in charts. Numbers that line up use `t-kpi` or `t-num` with tabular-nums.

**Spacing and layout.** The app is a 260px project rail plus a work area (`rail-width`), stacking to one column below 860px. The work area gutter is `space-20`; panels sit `space-16` apart; panel padding is `space-14` × `space-16`. Grids auto-fit (`panel-min` 300px, `kpi-min` 140px, `field-min` 210px) instead of fixed column counts.

**Borders, radii, shadows.** One radius, `r` (6px), on every container and control; `r-input` 4px inside tables, `r-pill` for pills. 1px hairlines separate; there are no shadows and no gradients anywhere.

**Charts.** SVG drawn from tokens so they follow the theme: `line2` gridlines, `muted` axis text, `accent` main series, `c-*` dashed discipline series, `accent-soft` value bars. See SCurve, Gantt, CostBar.

**3D.** The viewer background is `scene`; materials use the `mat-*` tokens (same in both themes), edges `scene-edge`, selection `scene-select`. Glass, translucent roof and excavated earth are drawn transparent.

**Motion.** None beyond hover border changes. Respect `prefers-reduced-motion`.

## Iconography

The app uses no icon set and no emoji. State is shown with words, pills and the 8px status dot; categories with 10×10 swatches (2px corners) and 14×3 legend keys in the discipline colors. There is no logo: the product name is set in `t-brand`.
