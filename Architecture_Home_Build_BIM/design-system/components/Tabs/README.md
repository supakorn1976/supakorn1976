# Tabs

Underline tab bar that switches the work area between the project's stages: สรุป, ข้อมูลแบบ, โมเดล 3D, ตรวจสอบ, ปริมาณงาน, BOQ, แผนงาน, S-Curve, ส่งออก.

**Markup.** `.tabs` (surface, bottom hairline `line`, horizontal scroll when narrow) holding `<button class="tab" role="tab" aria-selected>`; the current one adds `.on` (ink, weight 600, 2px `accent` underline).

**Rules**
- The tab order follows the BIM workflow (spec → model → check → quantities → cost → schedule → progress → export); keep it.
- Inactive tabs are `muted`. Do not add icons or counts.
- The bar scrolls sideways on phones rather than wrapping.
