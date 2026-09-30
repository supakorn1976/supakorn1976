# House BIM Studio — standalone web app

Design spec (JSON) → 3D model → clash check → quantity take-off → 4-category BOQ →
CPM schedule + Gantt → weekly S-Curve with 4-week payment milestones.
Background and accuracy notes (Thai): [NOTES_th.md](NOTES_th.md).

## Run

Serve the folder with any static server and open `index.html`:

```bash
cd Architecture_Home_Build_BIM/web/house-bim-studio
npx http-server -p 8080     # or: python3 -m http.server 8080
```

Everything is local (three.js r128, OrbitControls, SheetJS 0.18.5 are in `vendor/`),
so it works offline. Only the IBM Plex fonts come from Google Fonts, with system fallbacks.

## Storage and downloads

| Where it runs | Projects saved to | Downloads |
|---|---|---|
| claude.ai artifact | artifact `db` (`projects/<id>`, owner only) | artifact `downloads` |
| Anywhere else | this browser's `localStorage` (`hbs.projects.v1`) | normal browser download |

`local-caps.js` provides the fallback with the same API the app uses on claude.ai.
localStorage is per-browser: use **ส่งออก → ไฟล์โครงการ JSON** to back up or move projects,
and **นำเข้า JSON** to load them again.

## Exports

- Excel: Summary, BOQ (with formulas), Takeoff, Openings, Schedule, S-Curve
- SketchUp Ruby script (`*_BIM.rb.txt`, run with `load` in the Ruby Console)
- Project JSON, take-off CSV (UTF-8)

## Templates

- บ้าน TYPE03 (1-storey RC house, steel gable roof)
- ท่อลอดคลองส่งน้ำ มฐ04-62 (canal culvert)

Limits: 2-storey houses and curved roofs are not supported yet; geometry is edited in the
JSON spec tab; no direct IFC export (export IFC from SketchUp Pro using the .rb script).
