# -*- coding: utf-8 -*-
"""
Modern 2-storey house (from a single concept image: 2 floor plans + front render) -> BIM data.

Writes:
  ModernHouse_BIM.rb   SketchUp Ruby script (same engine as SoundStudio_House_BIM.rb v1.1)
  model.js             element list for preview.html (three.js viewer, works from file://)

The source image has NO dimensions. Every size here is an estimate:
  * plan scale from the 2 cars in the carport (2-car carport ~5.3 m wide) -> ~32 px/m
  * heights from the front render (~85 px/m, building width 10.0 m)
All sizes are ASSUMED and need an architect/engineer to confirm before use.

Axes (metres): X = left -> right looking at the front facade (0 .. 10.0)
               Y = front facade (0) -> back (12.4)
               Z = up, ground +-0.00
Run:  python3 make_model.py
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE_SRC = os.path.join(HERE, '..', 'Architecture', 'SoundStudio_House_BIM.rb')

# ------------------------------------------------------------------ main dimensions (ASSUMED)
W, D = 10.0, 12.4            # house plot width / depth used by the building
XL = 1.4                     # house body starts here (x 0..1.4 = carport pier / side yard)
XG = 5.3                     # carport | living split
YG = 5.0                     # carport depth
GF, F1, RF = 0.30, 3.50, 6.80  # ground FFL, upper FFL, roof structural top
T_EXT, T_INT = 0.20, 0.10    # wall thickness
NOTE = 'ASSUMED from concept image (no dimensions) - verify'

E = []                       # [ifc, name, mark, level, tag, parts, attrs]


def box(x0, x1, y0, y1, z0, z1, mat):
    x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
    return ['box', round(x0, 4), round(x1, 4), round(y0, 4), round(y1, 4), round(z0, 4), round(z1, 4), mat]


def add(ifc, name, mark, level, tag, parts, **attrs):
    if not isinstance(parts[0], list):
        parts = [parts]
    attrs.setdefault('Note', NOTE)
    E.append([ifc, name, mark, level, tag, parts, attrs])


# ------------------------------------------------------------------ walls with openings
def wall(name, mark, level, axis, c, a, b, z0, z1, t, openings=(), mat='wall_white', ext=True):
    """axis 'x': wall runs along X at y=c ; axis 'y': runs along Y at x=c.
    openings: (o0, o1, zs, ze) along the wall, absolute z."""
    ops = sorted(openings)
    parts = []
    # stop under the beam when the wall sits on a grid (beam) line, else under the slab
    lines = GY.values() if axis == 'x' else GX.values()
    soffit = {'GF': F1 - 0.50, '1F': RF - 0.50}.get(level)
    if soffit and any(abs(c - g) < 0.16 for g in lines):
        z1 = min(z1, soffit)

    def seg(s0, s1, zz0, zz1):
        if s1 - s0 < 1e-3 or zz1 - zz0 < 1e-3:
            return
        if axis == 'x':
            parts.append(box(s0, s1, c - t / 2, c + t / 2, zz0, zz1, mat))
        else:
            parts.append(box(c - t / 2, c + t / 2, s0, s1, zz0, zz1, mat))
    cur = a
    area_open = 0.0
    for o0, o1, zs, ze in ops:
        seg(cur, o0, z0, z1)
        seg(o0, o1, z0, zs)          # below sill
        seg(o0, o1, ze, z1)          # above head
        cur = o1
        area_open += (o1 - o0) * (ze - zs)
    seg(cur, b, z0, z1)
    net = (b - a) * (z1 - z0) - area_open
    add('IfcWall', name, mark, level, 'A-Wall', parts,
        **{'Thickness_m': t, 'Height_m': round(z1 - z0, 2), 'NetArea_m2(one face)': round(net, 2),
           'IsExternal': ext, 'Description': 'RC frame infill: AAC block, plaster + paint'})


def opening_unit(kind, name, mark, level, axis, c, o0, o1, zs, ze, desc, leaves=1, t=0.06, leaf='glass'):
    """Door or window filling an opening: black frame + glass (or timber leaf)."""
    f = 0.05
    parts = []

    def b(s0, s1, zz0, zz1, mat, th):
        if axis == 'x':
            parts.append(box(s0, s1, c - th / 2, c + th / 2, zz0, zz1, mat))
        else:
            parts.append(box(c - th / 2, c + th / 2, s0, s1, zz0, zz1, mat))
    b(o0, o1, ze - f, ze, 'frame_black', t)             # head
    b(o0, o0 + f, zs, ze - f, 'frame_black', t)         # jambs
    b(o1 - f, o1, zs, ze - f, 'frame_black', t)
    if kind == 'window':
        b(o0 + f, o1 - f, zs, zs + f, 'frame_black', t)  # sill
    zz0 = zs + (f if kind == 'window' else 0)
    n = max(1, leaves)
    w = (o1 - o0 - 2 * f) / n
    for i in range(n):
        s0 = o0 + f + i * w
        b(s0 + 0.01, s0 + w - 0.01, zz0, ze - f, 'wood' if leaf == 'wood' else 'glass', 0.03 if leaf == 'wood' else 0.012)
        if i:
            b(s0 - 0.02, s0 + 0.02, zz0, ze - f, 'frame_black', t)
    ifc = 'IfcDoor' if kind == 'door' else 'IfcWindow'
    add(ifc, name, mark, level, 'A-Door' if kind == 'door' else 'A-Window', parts,
        **{'Size_WxH_m': '%.2fx%.2f' % (o1 - o0, ze - zs), 'Leaves': leaves, 'Description': desc,
           'SillFromFloor_m': round(zs - (GF if level == 'GF' else F1), 2)})


def wall_with_units(name, mark, level, axis, c, a, b, z0, z1, t, units, ext=True, mat='wall_white'):
    """units: (kind, uname, umark, o0, o1, zs, ze, desc, leaves, leaf)"""
    wall(name, mark, level, axis, c, a, b, z0, z1, t, [(u[3], u[4], u[5], u[6]) for u in units], mat=mat, ext=ext)
    for kind, un, um, o0, o1, zs, ze, desc, lv, leaf in units:
        opening_unit(kind, un, um, level, axis, c, o0, o1, zs, ze, desc, lv, leaf=leaf)


# ================================================================== STRUCTURE
GX = {'1': 0.15, '2': XL + 0.1, '3': XG, '4': W - 0.15}
GY = {'A': 0.15, 'B': YG, 'C': 7.3, 'D': D - 0.15}
COLS = [('1', 'A', F1), ('1', 'B', F1)] + [(x, y, RF) for x in '234' for y in 'ABCD' if (x, y) != ('2', 'A')]
for gx, gy, top in COLS:
    x, y = GX[gx], GY[gy]
    tag = gx + gy
    add('IfcFooting', 'F1-' + tag, 'F1', 'FND', 'S-Foundation', box(x - .5, x + .5, y - .5, y + .5, -1.5, -1.2, 'concrete_dark'),
        Size_m='1.00x1.00x0.30', Rebar='6-DB12 each way', Note='Footing size ASSUMED (no soil data, no structural design)')
    add('IfcColumn', 'ST-' + tag, 'ST1', 'FND', 'S-Column', box(x - .125, x + .125, y - .125, y + .125, -1.2, -0.1, 'concrete_dark'),
        Section='0.25x0.25', Note='stub column')
    add('IfcColumn', 'C1-' + tag, 'C1', 'GF', 'S-Column', box(x - .125, x + .125, y - .125, y + .125, -0.1, top - 0.5, 'concrete'),
        Section='0.25x0.25', Top_m=top, Rebar='4-DB16', Ties='RB9@0.15')

def beams(level, ztop, h, tag, mark, rows, cols, mat='concrete'):
    for gy, (ga, gb) in rows:
        y = GY[gy]
        add('IfcBeam', '%s-%s' % (mark, gy), mark, level, tag, box(GX[ga] - .1, GX[gb] + .1, y - .1, y + .1, ztop - h, ztop, mat),
            Section='0.20x%.2f' % h, Top_m=ztop)
    for gx, (ga, gb) in cols:
        x = GX[gx]
        add('IfcBeam', '%s-%s' % (mark, gx), mark, level, tag, box(x - .1, x + .1, GY[ga] + .1, GY[gb] - .1, ztop - h, ztop, mat),
            Section='0.20x%.2f' % h, Top_m=ztop)

beams('GF', GF, 0.40, 'S-Beam', 'GB1', [('A', ('3', '4')), ('B', ('2', '4')), ('C', ('2', '4')), ('D', ('2', '4'))],
      [('2', ('B', 'D')), ('3', ('A', 'D')), ('4', ('A', 'D'))])
beams('1F', F1, 0.50, 'S-Beam', 'B1', [('A', ('1', '4')), ('B', ('1', '4')), ('C', ('2', '4')), ('D', ('2', '4'))],
      [('1', ('A', 'B')), ('2', ('B', 'D')), ('3', ('A', 'D')), ('4', ('A', 'D'))])
beams('ROOF', RF, 0.50, 'S-RoofBeam', 'RB1', [('A', ('3', '4')), ('B', ('2', '4')), ('C', ('2', '4')), ('D', ('2', '4'))],
      [('2', ('B', 'D')), ('3', ('A', 'D')), ('4', ('A', 'D'))])

# slabs
add('IfcSlab', 'S1-GF-living', 'S1', 'GF', 'S-Slab', box(XG, W, 0, YG, GF - .12, GF, 'concrete'), Thickness_m=0.12, Area_m2=round((W - XG) * YG, 2))
add('IfcSlab', 'S1-GF-rear', 'S1', 'GF', 'S-Slab', box(XL, W, YG, D, GF - .12, GF, 'concrete'), Thickness_m=0.12, Area_m2=round((W - XL) * (D - YG), 2))
add('IfcSlab', 'S0-carport', 'S0', 'GF', 'S-Slab', box(0, XG, 0, YG, 0.0, 0.12, 'paving'), Thickness_m=0.12, Area_m2=round(XG * YG, 2),
    Description='Slab on grade, carport (2 cars)')
STAIR_HOLE = (6.70, W - 0.15, YG, 8.50)
add('IfcSlab', 'S2-1F-front', 'S2', '1F', 'S-Slab', [box(0, 7.20, -0.30, YG, F1 - .15, F1, 'concrete'),
    box(7.20, W, 0.05, YG, F1 - .15, F1, 'concrete')], Thickness_m=0.15,
    Area_m2=round(W * (YG + .3), 2), Description='Upper floor + balcony + carport canopy')
add('IfcSlab', 'S2-1F-rear', 'S2', '1F', 'S-Slab', [
    box(XL, STAIR_HOLE[0], YG, D, F1 - .15, F1, 'concrete'),
    box(STAIR_HOLE[0], W, STAIR_HOLE[3], D, F1 - .15, F1, 'concrete')], Thickness_m=0.15,
    Area_m2=round((STAIR_HOLE[0] - XL) * (D - YG) + (W - STAIR_HOLE[0]) * (D - STAIR_HOLE[3]), 2), Description='stair opening 3.15x3.50')
add('IfcSlab', 'S3-canopy-band', 'S3', '1F', 'S-Slab', box(0, 7.15, -0.30, 0.05, 3.00, F1 - .15, 'concrete'),
    Description='Deep white edge band of carport canopy / balcony (render)')
add('IfcSlab', 'RS-roof', 'RS', 'ROOF', 'S-Slab', box(1.10, W + 0.2, -0.80, D + 0.2, RF - .15, RF, 'concrete'), Thickness_m=0.15,
    Area_m2=round((W + .2 - 1.1) * (D + 1.0), 2), Description='Flat RC roof, 0.80 m front overhang')

# stair (U-shape, 20 risers 0.16, tread 0.27)
r, tr = (F1 - GF) / 20, 0.27
steps = []
for i in range(10):                    # flight 1: x 6.80-8.25, going +Y
    y0 = YG + i * tr
    top = GF + (i + 1) * r
    steps.append(box(6.80, 8.25, y0, y0 + tr, max(GF, top - 0.30), top, 'concrete'))
yl = YG + 9 * tr + tr                  # landing
steps.append(box(6.80, W - 0.15, yl - tr, 8.50, GF + 10 * r - 0.15, GF + 10 * r, 'concrete'))
for i in range(9):                     # flight 2: x 8.35-9.85, going -Y
    y1 = yl - tr - i * tr
    top = GF + (11 + i) * r
    steps.append(box(8.35, W - 0.15, y1 - tr, y1, top - 0.30, top, 'concrete'))
add('IfcStair', 'ST1', 'ST1', 'GF', 'S-Stair', steps, Risers=20, Riser_m=round(r, 3), Tread_m=tr,
    Description='RC U-stair 2 flights x 1.45 m, landing +%.2f' % (GF + 10 * r))

# ================================================================== ARCHITECTURE
H_GF = (GF, F1 - 0.15)
H_1F = (F1, RF - 0.15)
# --- ground floor, exterior
wall_with_units('W-GF-front-entry', 'P1', 'GF', 'x', 0.10, XG, 7.20, GF, F1 - 0.5, T_EXT, [
    ('door', 'D1', 'D1', 5.55, 6.45, GF, GF + 2.20, 'Entrance door, solid timber, black frame', 1, 'wood')])
wall('W-GF-front-low', 'P1', 'GF', 'x', 0.10, 7.20, 9.00, GF, 0.90, T_EXT)
wall('W-GF-carport-side', 'P1', 'GF', 'y', XG, 0.0, YG, GF, F1 - 0.5, T_EXT)
wall_with_units('W-GF-carport-back', 'P1', 'GF', 'x', YG, XL, XG, GF, F1 - 0.5, T_EXT, [
    ('window', 'W1-WC', 'W1', 3.60, 5.00, 1.90, 2.30, 'High strip window (WC / laundry)', 2, 'glass')])
wall('W-GF-left', 'P1', 'GF', 'y', XL + 0.1, YG, D, GF, F1 - 0.15, T_EXT)
wall_with_units('W-GF-back', 'P1', 'GF', 'x', D - 0.1, XL, W, GF, F1 - 0.15, T_EXT, [
    ('window', 'W2-DIN', 'W2', 2.20, 4.40, GF + 0.10, GF + 2.30, 'Sliding glass door to rear garden (dining)', 2, 'glass'),
    ('window', 'W3-KIT', 'W3', 6.30, 8.10, GF + 1.10, GF + 2.10, 'Kitchen window over counter', 2, 'glass')])
wall_with_units('W-GF-right', 'P1', 'GF', 'y', W - 0.1, 0.0, D, GF, F1 - 0.15, T_EXT, [
    ('window', 'W4-LIV', 'W4', 1.50, 3.50, GF + 0.90, GF + 2.30, 'Living room side window', 2, 'glass')])
# --- ground floor, interior
wall('W-GF-wc-split', 'P2', 'GF', 'y', 3.10, YG + 0.10, 7.15, GF, F1 - 0.15, T_INT, ext=False)
wall_with_units('W-GF-service', 'P2', 'GF', 'x', 7.20, XL + .2, XG, GF, F1 - 0.15, T_INT, [
    ('door', 'D3-LDY', 'D3', 1.90, 2.70, GF, GF + 2.10, 'Laundry door', 1, 'wood')], ext=False)
wall_with_units('W-GF-wc-hall', 'P2', 'GF', 'y', XG, YG, 7.20, GF, F1 - 0.15, T_INT, [
    ('door', 'D2-WC', 'D2', 5.70, 6.45, GF, GF + 2.10, 'Guest WC door', 1, 'wood')], ext=False)

# --- curtain wall + stone (front right, double height)
cw = [box(7.25, 9.00, -0.02, 0.0, 0.90, 5.65, 'glass')]
for x in (7.26, 8.13, 8.97):
    cw.append(box(x - .03, x + .03, -0.06, 0.0, 0.90, 5.65, 'frame_black'))
for z in (0.90, 2.20, 3.45, 4.55, 5.65):
    cw.append(box(7.23, 9.00, -0.06, 0.0, z - .03, z + .03, 'frame_black'))
add('IfcCurtainWall', 'CW1', 'CW1', 'GF', 'A-Window', cw, **{'Size_WxH_m': '1.80x4.75', 'Leaves': 8,
    'Description': 'Double-height aluminium curtain wall, 2x4 panels (render)', 'SillFromFloor_m': 0.6})
add('IfcCovering', 'STONE-FIN', 'ST', 'GF', 'A-Cladding', [box(9.00, W, -0.30, 0.10, 0.90, 6.90, 'stone')],
    PredefinedType='CLADDING', Description='Vertical wall fin clad in split-face stone (render)')
add('IfcCovering', 'STONE-PLANTER', 'ST', 'GF', 'A-Cladding', [box(6.70, W, -0.60, 0.10, 0.30, 0.90, 'stone')],
    PredefinedType='CLADDING', Description='Stone-clad planter band under curtain wall')

# --- upper floor, exterior
wall_with_units('W-1F-front', 'P1', '1F', 'x', 1.70, XL, 6.50, F1, RF - 0.15, T_EXT, [
    ('door', 'D4-BAL', 'D4', 3.60, 5.40, F1, F1 + 2.40, 'Sliding glass door, master bedroom to balcony', 2, 'glass')])
wall('W-1F-front-r2', 'P1', '1F', 'x', 0.10, 9.00, W - 0.20, 5.65, RF - 0.15, T_EXT)
wall('W-1F-front-top', 'P1', '1F', 'x', 0.10, 7.20, 9.00, 5.65, RF - 0.15, T_EXT)
wall_with_units('W-1F-left', 'P1', '1F', 'y', XL + 0.1, 1.70, D, F1, RF - 0.15, T_EXT, [
    ('window', 'W5-BED2', 'W5', 9.20, 10.80, F1 + 0.90, F1 + 2.20, 'Bedroom 2 side window', 2, 'glass')])
wall_with_units('W-1F-back', 'P1', '1F', 'x', D - 0.1, XL, W, F1, RF - 0.15, T_EXT, [
    ('window', 'W6-BED2', 'W6', 2.40, 4.20, F1 + 0.90, F1 + 2.20, 'Bedroom 2 window', 2, 'glass'),
    ('window', 'W7-BATH', 'W7', 5.40, 6.20, F1 + 1.60, F1 + 2.20, 'Shared bath high window', 1, 'glass'),
    ('window', 'W6-BED3', 'W6', 7.40, 9.20, F1 + 0.90, F1 + 2.20, 'Bedroom 3 window', 2, 'glass')])
wall_with_units('W-1F-right', 'P1', '1F', 'y', W - 0.1, 0.0, D, F1, RF - 0.15, T_EXT, [
    ('window', 'W7-MBATH', 'W7', 2.00, 2.80, F1 + 1.60, F1 + 2.20, 'Master bath high window', 1, 'glass')])
# --- upper floor, interior
wall_with_units('W-1F-master-bath', 'P2', '1F', 'y', 6.50, 0.2, 5.0, F1, RF - 0.15, T_INT, [
    ('door', 'D5-MB', 'D5', 2.80, 3.55, F1, F1 + 2.10, 'Master bath door', 1, 'wood'),
    ('door', 'D6-MBR', 'D6', 4.10, 4.90, F1, F1 + 2.10, 'Master bedroom door (from stair hall)', 1, 'wood')], ext=False)
wall('W-1F-mbath-back', 'P2', '1F', 'x', 4.00, 6.55, W - 0.2, F1, RF - 0.15, T_INT, ext=False)
wall_with_units('W-1F-closet', 'P2', '1F', 'x', YG, XL + .2, 6.50, F1, RF - 0.15, T_INT, [
    ('door', 'D7-WIC', 'D7', 2.40, 3.20, F1, F1 + 2.10, 'Walk-in closet door', 1, 'wood')], ext=False)
wall('W-1F-closet-hall', 'P2', '1F', 'y', 3.80, YG, 7.30, F1, RF - 0.15, T_INT, ext=False)
wall_with_units('W-1F-bed2-front', 'P2', '1F', 'x', 7.35, XL + .2, 6.70, F1, RF - 0.15, T_INT, [
    ('door', 'D6-BED2', 'D6', 4.00, 4.80, F1, F1 + 2.10, 'Bedroom 2 door', 1, 'wood')], ext=False)
wall('W-1F-bed2-bath', 'P2', '1F', 'y', 5.00, 7.40, D - 0.2, F1, RF - 0.15, T_INT, ext=False)
wall_with_units('W-1F-landing', 'P2', '1F', 'x', 8.55, 5.05, W - 0.2, F1, RF - 0.15, T_INT, [
    ('door', 'D5-BATH', 'D5', 5.40, 6.15, F1, F1 + 2.10, 'Shared bath door', 1, 'wood'),
    ('door', 'D6-BED3', 'D6', 7.00, 7.80, F1, F1 + 2.10, 'Bedroom 3 door', 1, 'wood')], ext=False)
wall('W-1F-bath-bed3', 'P2', '1F', 'y', 6.60, 8.60, D - 0.2, F1, RF - 0.15, T_INT, ext=False)

# --- facade frame, roof finishes, railing, gate
add('IfcMember', 'FRAME-L', 'FR', '1F', 'A-Trim', box(1.33, 1.95, -0.30, 1.60, F1, 5.80, 'wall_white'), Description='White box frame around balcony (render)')
add('IfcMember', 'FRAME-R', 'FR', '1F', 'A-Trim', box(6.45, 7.20, -0.30, 0.0, F1, 5.80, 'wall_white'), Description='White box frame around balcony (render)')
add('IfcMember', 'FRAME-TOP', 'FR', '1F', 'A-Trim', box(1.33, 7.20, -0.30, 0.0, 5.80, RF - 0.50, 'wall_white'), Description='Frame head; LED strip in soffit')
add('IfcCovering', 'ROOF-MEMBRANE', 'RF', 'ROOF', 'A-Roof', box(1.10, W + 0.2, -0.80, D + 0.2, RF, RF + 0.05, 'roof_dark'),
    PredefinedType='ROOFING', Description='Waterproofing membrane + insulation, slope 1%', Area_m2=round((W + .2 - 1.1) * (D + 1.0), 2))
add('IfcCovering', 'ROOF-FASCIA', 'FS', 'ROOF', 'A-Roof', box(1.10, W + 0.2, -0.85, -0.80, RF - 0.20, RF + 0.10, 'roof_dark'),
    PredefinedType='CLADDING', Description='Dark metal fascia (render)')
add('IfcCovering', 'SOFFIT-WOOD', 'SF', 'ROOF', 'A-Ceiling', box(1.10, W + 0.2, -0.80, -0.30, RF - 0.20, RF - 0.15, 'wood'),
    PredefinedType='CEILING', Description='Timber-look soffit under roof overhang (render)')
rail = [box(1.95, 6.45, -0.24, -0.22, F1, F1 + 1.05, 'glass')]
for x in (2.00, 3.10, 4.20, 5.30, 6.40):
    rail.append(box(x - .02, x + .02, -0.26, -0.20, F1, F1 + 1.05, 'rail'))
add('IfcRailing', 'RAIL-BAL', 'GR1', '1F', 'A-Railing', rail, Description='Frameless glass balustrade 12 mm, h 1.05 m, black posts')
gate = [box(0.20, 1.30, YG - 0.04, YG + 0.04, 0.12, 2.00, 'frame_black')]
add('IfcDoor', 'GATE-SIDE', 'G1', 'GF', 'A-Door', gate, **{'Size_WxH_m': '1.10x2.00', 'Leaves': 1,
    'Description': 'Black aluminium slat gate to side yard (render)', 'SillFromFloor_m': -0.3})
add('IfcWall', 'W-PIER-L', 'P1', 'GF', 'A-Wall', box(0.0, XL, -0.30, 0.30, 0.12, 3.00, 'wall_white'),
    Description='Carport left pier (render)', **{'NetArea_m2(one face)': round(XL * 3.0, 2)})
add('IfcWall', 'W-BOUNDARY-L', 'P4', 'GF', 'A-Wall', box(0.0, 0.15, 0.30, D, 0.12, 2.00, 'wall_white'),
    Description='Side boundary wall h 2.00', **{'NetArea_m2(one face)': round((D - .3) * 2.0, 2)})
leds = [box(1.8, 4.8, 1.2 + i * 1.2, 1.25 + i * 1.2, 2.98, 3.00, 'light') for i in range(3)]
leds.append(box(2.2, 6.2, 0.6, 0.65, 5.78, 5.80, 'light'))
add('IfcLightFixture', 'LED-STRIPS', 'LED', 'GF', 'E-Lighting', leds, Description='Linear LED in carport and frame soffits', Count=4)

# floors / fixtures (light)
add('IfcCovering', 'FL-GF-tile', 'F1', 'GF', 'A-Floor', [box(XG + .1, W - .2, 0.2, YG, GF, GF + 0.01, 'tile_floor'),
    box(XL + .2, W - .2, 7.25, D - .2, GF, GF + 0.01, 'tile_floor')], PredefinedType='FLOORING', Description='Porcelain tile 60x60')
add('IfcCovering', 'FL-1F-wood', 'F2', '1F', 'A-Floor', [box(XL + .2, 6.45, 1.80, 4.95, F1, F1 + 0.01, 'wood_floor'),
    box(XL + .2, 4.95, 7.40, D - .2, F1, F1 + 0.01, 'wood_floor'), box(6.65, W - .2, 8.60, D - .2, F1, F1 + 0.01, 'wood_floor')],
    PredefinedType='FLOORING', Description='Engineered wood, bedrooms')
add('IfcFurnishingElement', 'KITCHEN', 'KC1', 'GF', 'A-Casework', [box(5.6, W - .2, D - .8, D - .2, GF + .01, GF + 0.90, 'counter'),
    box(6.6, 8.6, 9.6, 10.5, GF + .01, GF + 0.90, 'counter')], Description='Kitchen counter 0.60 + island 2.00x0.90')
for nm, x, y, lv in (('WC-GF', 4.0, 6.70, 'GF'), ('WC-MBATH', 9.2, 3.4, '1F'), ('WC-BATH', 5.8, 11.6, '1F')):
    z = GF if lv == 'GF' else F1
    add('IfcSanitaryTerminal', nm, 'WC', lv, 'P-Sanitary', [box(x - .19, x + .19, y - .35, y + .35, z, z + .40, 'sanitary')], Description='Close-coupled WC')
add('IfcSanitaryTerminal', 'TUB-MBATH', 'BT', '1F', 'P-Sanitary', box(7.0, 8.7, 0.40, 1.15, F1, F1 + 0.55, 'sanitary'), Description='Freestanding bathtub 1.70x0.75')

# ================================================================== SITE
add('IfcSite', 'GROUND', 'SITE', 'GF', 'Site', box(-1.0, W + 1.0, -5.5, D + 2.0, -0.05, 0.0, 'ground'), Description='Lot (size ASSUMED)')
add('IfcSlab', 'DRIVEWAY', 'DW', 'GF', 'Site', box(0.0, XG, -3.80, 0.0, 0.0, 0.10, 'paving'), Description='Concrete driveway strips')
add('IfcSlab', 'WALK', 'WK', 'GF', 'Site', [box(XG, 6.90, -3.80, -0.90, 0.0, 0.08, 'paving'),
    box(XG, 6.90, -0.90, -0.45, 0.0, 0.15, 'paving'), box(XG, 6.90, -0.45, 0.0, 0.0, 0.30, 'paving')],
    Description='Entrance walk + 2 steps')
add('IfcSlab', 'SIDEWALK', 'SW', 'GF', 'Site', box(-1.0, W + 1.0, -5.5, -3.80, 0.0, 0.12, 'paving'), Description='Public sidewalk')

# ------------------------------------------------------------------ output
MATS = {
    'concrete': [196, 194, 188, 1.0], 'concrete_dark': [150, 148, 142, 1.0], 'wall_white': [236, 234, 228, 1.0],
    'stone': [168, 150, 128, 1.0], 'wood': [160, 108, 64, 1.0], 'glass': [159, 195, 210, 0.35], 'frame_black': [28, 28, 28, 1.0],
    'roof_dark': [48, 50, 54, 1.0], 'rail': [21, 21, 21, 1.0], 'paving': [190, 188, 182, 1.0], 'ground': [126, 160, 92, 1.0],
    'tile_floor': [216, 212, 204, 1.0], 'wood_floor': [168, 120, 74, 1.0], 'counter': [120, 116, 112, 1.0],
    'sanitary': [255, 255, 255, 1.0], 'light': [255, 230, 128, 1.0]}


def rb(v):
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, str):
        return ':' + v if v in ('box', 'poly', 'bar') else json.dumps(v, ensure_ascii=False)
    if isinstance(v, (int, float)):
        return repr(round(v, 4)) if isinstance(v, float) else str(v)
    if isinstance(v, list):
        return '[' + ','.join(rb(x) for x in v) + ']'
    if isinstance(v, dict):
        return '{' + ', '.join('%s=>%s' % (json.dumps(k, ensure_ascii=False), rb(x)) for k, x in v.items()) + '}'
    raise TypeError(v)


HEADER = '''# encoding: utf-8
# =============================================================================
#  ModernHouse_BIM.rb  -  บ้านพักอาศัย 2 ชั้น สไตล์โมเดิร์น หลังคาแบน ที่จอดรถ 2 คัน  โมเดล BIM (SketchUp Ruby)  v0.1
#  แหล่งข้อมูล: ภาพเดียว (ผังพื้นชั้นล่าง/ชั้นบน + ภาพ render ด้านหน้า) — ไม่มีมิติในแบบ
#  ขนาดทั้งหมดเป็นค่าประมาณ: สเกลผังจากรถ 2 คัน (~32 px/ม.), ความสูงจากภาพ render (~85 px/ม.)
#  ตัวอาคาร 10.00 x 12.40 ม. ; พื้นชั้นล่าง +0.30 ; พื้นชั้นบน +3.50 ; หลังพื้นหลังคา +6.80 ; ยื่นหลังคาหน้า 0.80 ม.
#  ชั้นล่าง: ที่จอดรถ 2 คัน, ห้องนั่งเล่น, ซักล้าง, ห้องน้ำแขก, ครัว+รับประทานอาหาร, บันได U
#  ชั้นบน : ห้องนอนใหญ่ + ห้องน้ำ (อ่างอาบน้ำ) + walk-in closet + ระเบียง, ห้องนอน 2 ห้อง, ห้องน้ำรวม
#  ด้านหน้า: กรอบสีขาว, ผนังกระจก 2 ชั้น, ครีบหินกาบ, ระเบียงราวกระจก, ฝ้าชายคาลายไม้, ไฟ LED เส้น
#  โครงสร้างเป็นขนาดสมมติ (ยังไม่ได้ออกแบบ) — ต้องให้สถาปนิก/วิศวกรตรวจและกำหนดขนาดจริง
#  รวม %d องค์ประกอบ  ทุกชิ้นเป็น Group: IFC 2x3 classification + attribute 'MH_BIM' + Tag
#
#  วิธีใช้ (Window > Ruby Console):
#      load 'C:/path/ModernHouse_BIM.rb'
#      ModernHouseBIM.build                        # สร้างโมเดล (ลบของเดิมที่สคริปต์นี้สร้าง)
#      ModernHouseBIM.build(only: [:structure])    # :structure / :architecture / :mep / :site
#      ModernHouseBIM.report                       # ปริมาณงาน + ตารางประตูหน้าต่าง
#      ModernHouseBIM.export_csv('C:/temp/mh')     # _qto.csv และ _schedule.csv
#      ModernHouseBIM.clashes                      # ตรวจชน (bounding box)
#      ModernHouseBIM.show(:structure)             # :structure / :architecture / :mep / :site / :all
#      ModernHouseBIM.validate                     # ตรวจข้อมูล DATA (ใช้นอก SketchUp ได้)
#      ModernHouseBIM.diag
#
#  หน่วย = เมตร ; X ซ้าย->ขวา เมื่อมองด้านหน้า (0..10.00) ; Y หน้า->หลัง (0..12.40) ; Z ขึ้น, ดิน ±0.00
#  สร้างจาก make_model.py — แก้ขนาดที่นั่นแล้วรัน python3 make_model.py ใหม่
# =============================================================================
module ModernHouseBIM
  # reload-safe: remove old constants so repeated load does not spam "already initialized constant"
  constants.each { |c| remove_const(c) }
  @ifc_ok = nil
  NAME   = 'Modern House BIM'
  SCHEMA = 'IFC 2x3'
'''


def main():
    names = [e[1] for e in E]
    dup = {n for n in names if names.count(n) > 1}
    assert not dup, dup
    engine = open(ENGINE_SRC, encoding='utf-8').read()
    tail = engine[engine.index('  # ---------------------------------------------------------------- helpers'):]
    tail = tail.replace('SSHBIM', 'ModernHouseBIM').replace("'SSH_", "'MH_").replace('"SSH_', '"MH_') \
               .replace('Sound Studio House BIM', 'Modern House BIM')
    assert 'SSH' not in tail, re.findall(r'.{20}SSH.{20}', tail)
    out = [HEADER % len(E)]
    out.append('  MATS = {\n' + ',\n'.join('    %s=>%s' % (json.dumps(k), rb(v)) for k, v in MATS.items()) + '\n  }\n')
    out.append("  STOREYS = { 'FND'=>'Foundation (below ±0.00)', 'GF'=>'Ground floor (FFL +0.30)', '1F'=>'Upper floor (FFL +3.50)', 'ROOF'=>'Roof (+6.80)' }\n")
    out.append("  DISC = { structure: /\\AS-/, architecture: /\\AA-/, mep: /\\A[PE]-/, site: /\\ASite\\z/ }\n\n")
    out.append('  # [ifc, name, mark, level, tag, parts, attrs]\n  #  part: [:box, x0,x1,y0,y1,z0,z1, mat]\n  DATA = [\n')
    out.append(',\n'.join('    ' + rb(e) for e in E) + '\n  ]\n\n')
    out.append(tail)
    with open(os.path.join(HERE, 'ModernHouse_BIM.rb'), 'w', encoding='utf-8') as f:
        f.write(''.join(out))
    with open(os.path.join(HERE, 'model.js'), 'w', encoding='utf-8') as f:
        f.write('window.MODEL = ')
        json.dump({'name': 'Modern House BIM', 'mats': MATS, 'elements': [
            {'ifc': e[0], 'name': e[1], 'mark': e[2], 'level': e[3], 'tag': e[4], 'parts': e[5], 'attrs': e[6]} for e in E]},
            f, ensure_ascii=False, separators=(',', ':'))
        f.write(';\n')
    print('elements:', len(E), ' parts:', sum(len(e[5]) for e in E))


if __name__ == '__main__':
    main()
