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
| `boq.py` | Take-off from the model → BOQ → CPM plan → S-curve → payments. Run `python3 boq.py` after `make_model.py` |
| `BaanSaoYongHin_BOQ_Plan.xlsx` | สรุป (ปร.5), BOQ (ปร.4, formulas), ถอดปริมาณ (every quantity traced to a BIM element), ประตูหน้าต่าง, แผนงาน (CPM + Gantt), S-Curve, งวดงาน, ข้อสมมติ |
| `tracker/` | Construction tracker web app (`index.html` + generated `plan.js`); see below |
| `door_window_schedule.csv` | All 32 reclaimed units with their sizes, and where each one is used in the model |
| `preview_*.png` | Screenshots of the preview (SW, iso, plan) |
| `reference/` | The source sheets used: scaled site plan, door/window schedules, door/window axonometric |

## What is in the model (423 elements)

| Building | Contents |
|---|---|
| **A** – living pavilion 12.3 × 4.4 m (+ bedroom wing to 5.8 m) | Living/dining, bedroom + wardrobe, bathroom. 30° gable roof (ridge E–W) with 7.5 m span over a 1.8 m south veranda deck. Aluminium bi-fold glass front, reclaimed windows on the north side, white rendered east wall, west slat screen |
| **C** – bedroom house 8.0 × 9.2 m | 2 bedrooms, 2 bathrooms. Twin parallel gables: a tall west one (45°) running out over the entrance porch, and a wide east one (30°). Covered side walk, outdoor-tub deck |
| **D** – garage 7.9 × 10.4 m, turned 26° | 2 store rooms + corridor. Gable roof with a raised clerestory (monitor) roof, vertical slat screen to full gable height, 1.0 m gabion wall |
| **Site** | Timber pergola frames on boulder footings, diagonal deck from A towards D, walkway to C, concrete terrace, 2 existing trees |
| **Plumbing (P-)** | Water meter, HDPE main, 2,000 L tank + booster pump at the garage, PPR cold/hot pipes, 3 WC / 3 basins / 3 showers, pantry sink, outdoor tub, floor drains, PVC soil/waste pipes, 6 inspection chambers, grease trap, 3 septic tanks 1,600 L + 3 soak pits |
| **Electrical (E-)** | PEA pole + 3-phase meter, MDB in store room 2, consumer units in A and C, buried NYY feeders in HDPE, 61 light points (pendants, downlights, wall/post lamps, battens, floods, bollards), 33 sockets, 19 switches, 3 water heaters, 3 split ACs, 4 ground rods |
| **Ceilings** | Woven-bamboo sloped ceiling in A (photo 23), timber T&G ceilings in C and the garage rooms (hidden in the preview; tag `A-Ceiling`) |

Each element is an IFC 2x3 classified group (IfcWall, IfcDoor, IfcWindow, IfcColumn, IfcBeam, IfcMember,
IfcRoof, IfcSlab, IfcFooting, IfcPipeSegment, IfcLightFixture, IfcOutlet, …) with a tag (`S-*`, `A-*`, `P-*`, `E-*`, `Site`) and attributes
(`BSY_BIM` dictionary: mark, size, section, schedule reference, notes).

![MEP view (roofs and walls hidden)](preview_mep.png)

The MEP layout, cable sizes and pipe sizes are a sketch for estimating. A licensed MEP / electrical engineer
must design them (EIT standards) before construction.

## BOQ and plan (`boq.py`)

| | |
|---|---|
| Direct cost | 2,908,023 baht (structure 1.12 M, architecture 1.24 M, plumbing 0.23 M, electrical 0.32 M) |
| × Factor F 1.2846 | **3,735,647 baht** ≈ 18,977 baht/m² of building slab (196.85 m², decks extra) |
| Plan | 36 activities, 98 working days (Mon–Sat, listed public holidays off), 2 Nov 2026 → 1 Mar 2027 |
| Payments | 8 milestone payments, each valued at the cost of the activities it closes |

Every BOQ row comes from the model: volumes, areas, lengths and counts per building, listed element by
element in the `ถอดปริมาณ` sheet. Unit prices are 2026 estimates (same basis as the TYPE03 template in House
BIM Studio) and are blue input cells in the `BOQ` sheet; the summary, plan costs, S-curve and payments are
formulas, so changing a price updates everything (1,133 formulas, recalculated with no errors). Factor F and the
start date are assumptions, marked yellow. Changing geometry or the start date: edit `make_model.py` / `boq.py`
and run both again.

## Construction tracker (`tracker/index.html`)

One page for the site team: progress per activity, Gantt with % done and actual dates, planned-vs-actual S-curve,
SPI and forecast finish, a 4D model coloured by status (done / in progress / late / not started, or the planned
state on any date), daily site reports, issues and defects, payment milestones and BOQ value earned.

- On claude.ai (published artifact) the data is shared between everyone who opens it (`db`: `progress`, `logs`,
  `issues`, `payments`, `history`).
- Opened as a local file it keeps the data in that browser only. The 3D view needs three.js from the CDN, or the
  copy in `../../../web/house-bim-studio/vendor/` when offline.
- `screenshot_*_sample.png` show it with made-up sample progress, for illustration only.


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
