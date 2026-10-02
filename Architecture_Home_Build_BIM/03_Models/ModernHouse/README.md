# Modern House BIM (from a concept image)

A 2-storey modern house with a flat roof and a 2-car carport. It was modelled from one image
(ground- and upper-floor plans plus a front render) that has **no dimensions**.

| File | What it is |
|---|---|
| `make_model.py` | Parametric source: every dimension lives here. Edit it, then run `python3 make_model.py` |
| `ModernHouse_BIM.rb` | SketchUp Ruby script (generated): `load` it, then `ModernHouseBIM.build` |
| `model.js` + `preview.html` | Browser 3D preview (generated data, three.js from `../../web/house-bim-studio/vendor`) |
| `preview_front.png`, `preview_iso.png` | Screenshots of the preview |

## Assumed key dimensions

- Building 10.00 × 12.40 m (plan scale taken from the 2 cars, about 32 px/m)
- Floor levels: ground FFL +0.30, upper FFL +3.50, roof slab +6.80, 0.80 m front roof overhang
- RC frame: 13 columns 0.25×0.25, footings 1.00×1.00×0.30, beams 0.20×0.40/0.50, slabs 0.12–0.15
- U-shaped stair, 20 risers of 0.16 m, 0.27 m treads
- Ground floor: carport, living, laundry, guest WC, kitchen/dining
- Upper floor: master bedroom + bath + walk-in closet + balcony, 2 bedrooms, shared bath

**Everything is an estimate.** None of the structure has been designed. An architect and a
structural engineer must set the real sizes before this is used for permits, BOQ or construction.

## Commands in SketchUp (Ruby Console)

```ruby
load 'C:/path/ModernHouse_BIM.rb'
ModernHouseBIM.build            # build everything (IFC 2x3 classified groups + tags + scenes)
ModernHouseBIM.report           # quantities + door/window schedule
ModernHouseBIM.export_csv('C:/temp/mh')
ModernHouseBIM.clashes          # bounding-box clash check
```

To get IFC, use SketchUp Pro: File → Export → IFC.
