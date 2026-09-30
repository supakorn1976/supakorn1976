# Architecture_Home_Build_BIM

BIM project scaffold for designing and building a single-family home.

## Structure
| Folder | Purpose |
|---|---|
| 01_Brief | Client brief, program, budget, requirements |
| 02_Site | Survey, DEM/GIS, climate, regulations (setbacks, FAR, OSR) |
| 03_Models | Discipline models (Architecture / Structure / MEP), IFC exports |
| 04_Drawings | Plans, sections, elevations, details (PDF/DWG) |
| 05_Specifications | Material and finish specifications |
| 06_BOQ_Cost | Quantity take-off and cost estimates |
| 07_Coordination | Clash detection reports, issue log, meeting minutes |
| 08_Construction | 4D schedule, site instructions, RFIs, progress photos |
| 09_Handover | As-built models, O&M manuals, warranties |

## Workflow
1. Brief and site analysis
2. Concept → schematic model (LOD 100–200)
3. Design development (LOD 300), structure + MEP models
4. Coordination and clash detection
5. Drawings, specs, BOQ extracted from the model
6. Construction: 4D sequencing, RFIs
7. As-built handover (LOD 500)

See `BIM_Execution_Plan.md` for roles, naming and LOD conventions.
