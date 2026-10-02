# Baan Sao Yong Hin BIM (บ้านเสายงหิน)

A single-storey compound of reclaimed-timber buildings with corrugated-sheet gable roofs. It was modelled
from `BAAN_SAO_YONG_HIN.rar` (21 images). The archive has a site plan with a 10 m scale bar, the
reclaimed door (D01–D20) and window (W01–W12) schedules, a door and window axonometric, and photos.

![SW view](preview_sw.png)

| File | What it is |
|---|---|
| `make_model.py` | Parametric source: every dimension lives here. Edit it, then run `python3 make_model.py` |
| `BaanSaoYongHin_BIM.rb` | SketchUp Ruby script (generated): `load` it, then `BaanSaoYongHinBIM.build` |
| `model.js` + `preview.html` | Browser 3D preview (generated data, three.js from `../../web/house-bim-studio/vendor`) |
| `door_window_schedule.csv` | All 32 reclaimed units with their sizes, and where each one is used in the model |
| `preview_*.png` | Screenshots of the preview (SW, iso, plan) |
| `reference/` | The source sheets used: scaled site plan, door/window schedules, door/window axonometric |

## What is in the model (358 elements)

| Building | Contents |
|---|---|
| **A** – living pavilion 12.3 × 4.4 m (+ bedroom wing to 5.8 m) | Living/dining, bedroom + wardrobe, bathroom. 30° gable roof (ridge E–W) with 7.5 m span over a 1.8 m south veranda deck. Aluminium bi-fold glass front, reclaimed windows on the north side, white rendered east wall, west slat screen |
| **C** – bedroom house 8.0 × 9.2 m | 2 bedrooms, 2 bathrooms. Twin parallel gables: a tall west one (45°) running out over the entrance porch, and a wide east one (30°). Covered side walk, outdoor-tub deck |
| **D** – garage 7.9 × 10.4 m, turned 26° | 2 store rooms + corridor. Gable roof with a raised clerestory (monitor) roof, vertical slat screen to full gable height, 1.0 m gabion wall |
| **Site** | Timber pergola frames on boulder footings, diagonal deck from A towards D, walkway to C, concrete terrace, 2 existing trees |

Each element is an IFC 2x3 classified group (IfcWall, IfcDoor, IfcWindow, IfcColumn, IfcBeam, IfcMember,
IfcRoof, IfcSlab, IfcFooting, …) with a tag (`S-*`, `A-*`, `P-*`, `Site`) and attributes
(`BSY_BIM` dictionary: mark, size, section, schedule reference, notes).

## How sure each number is

- **Plan positions and sizes: measured.** They come from the plan with its 10 m scale bar (24.6 px/m; the
  pickup in the garage checks out at about 5.3 m). They are accurate to about ±0.2 m.
- **Door and window sizes: real.** They are taken from the reclaimed-unit schedule sheets. Where each unit
  sits is estimated from the plan, the axonometric and the photos. 25 of the 32 units are placed; the other 7
  are listed as spares. "3 PIECES" on the sheet is read as 3 units available.
- **Heights and roof pitches: estimated** from photos. Floor +0.45, wall plate +3.10 (A) / +2.95 (C) /
  +2.70 (D), pitches 30° / 45° / 25°.
- **Structure: assumed.** Timber posts 0.15–0.20, footings 0.80 × 0.80, 0.20 × 0.40 grade beams, rafters
  50×150 @ about 1.0 m, purlins 50×100 @ 0.80. None of it has been designed. An architect and a structural
  engineer must set the real sizes before this is used for permits, BOQ or construction.
- `Gemini_Generated_Image_*.png` in the archive shows a different flat-roof house, so it is not modelled.

## Commands in SketchUp (Ruby Console)

```ruby
load 'C:/path/BaanSaoYongHin_BIM.rb'
BaanSaoYongHinBIM.build            # build everything (IFC 2x3 classified groups + tags + scenes)
BaanSaoYongHinBIM.report           # quantities + door/window schedule
BaanSaoYongHinBIM.export_csv('C:/temp/bsy')
BaanSaoYongHinBIM.clashes          # bounding-box clash check
```

The clash check compares axis-aligned bounding boxes. The garage is turned 26°, so its walls, posts and
screens show up as false clash pairs. Wall-end × post pairs at corners are by design.

To get IFC, use SketchUp Pro: File → Export → IFC.
