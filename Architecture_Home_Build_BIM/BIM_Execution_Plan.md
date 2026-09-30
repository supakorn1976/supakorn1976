# BIM Execution Plan (template)

## Project info
- Project name:
- Location / plot:
- Client:
- Target budget / area (m²):

## Roles
| Role | Name | Responsibility |
|---|---|---|
| BIM Manager | | Standards, model integrity |
| Architect | | Architecture model |
| Structural Engineer | | Structure model |
| MEP Engineer | | MEP model |
| Contractor | | 4D/5D, as-built |

## Software and formats
- Authoring: (Revit / ArchiCAD / SketchUp / other)
- Exchange: IFC 4, BCF for issues
- Coordinate system / origin:
- Units: metres

## File naming
`<Project>-<Discipline>-<Level>-<Type>-<Rev>` e.g. `HOME-ARC-GF-MODEL-R01.ifc`
Discipline codes: ARC, STR, MEP, SITE

## Level of Development
| Stage | LOD | Output |
|---|---|---|
| Concept | 100 | Massing |
| Schematic | 200 | Generic elements |
| Design development | 300 | Accurate geometry, permit drawings |
| Construction | 350–400 | Coordination, fabrication |
| As-built | 500 | Verified handover model |

## Coordination
- Clash detection cadence: weekly
- Issue tracking: BCF
- Tolerance: 25 mm hard clash

## Model checklist
- [ ] Levels and grids set
- [ ] All elements classified
- [ ] Rooms/areas named
- [ ] Quantities verified against BOQ
