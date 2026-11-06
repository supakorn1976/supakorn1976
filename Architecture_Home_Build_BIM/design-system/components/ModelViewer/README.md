# ModelViewer

Frame for the three.js model: `scene` background, `line` border, radius `r`, height `min(68vh, 640px)`, with a floating info card for the picked element and a toggle row above.

**Markup.** `.vtools` (toggle labels, gap 6px × `space-14`) above `.viewer` containing the `<canvas>` and `.info` (absolute top-right, max 340px, surface, `t-meta`) with an `h4` and a two-column `dl` (`dt` muted).

**Scene.** Background reads `--scene`. Meshes use the `mat-*` colours as vertex colours under a hemisphere light (sky #ffffff, ground #8a8f8c, 0.85) plus a directional light (#ffffff, 0.55). Edges draw in `scene-edge`; the selected element gets a `scene-select` bounding box. Glass, translucent roof and earth are transparent at their alpha.

**Consumer provides** the canvas, the picked element's IFC class, name, tag and dimensions in metres.
