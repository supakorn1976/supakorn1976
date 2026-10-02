# -*- coding: utf-8 -*-
"""
Baan Sao Yong Hin (บ้านเสายงหิน) - single-storey timber compound -> BIM data.

Source: BAAN_SAO_YONG_HIN.rar (21 images):
  * 4-1   site/floor plan with a 10 m scale bar  -> 24.6 px/m  (all plan positions below)
  * 9     door schedule  D01-D20 (reclaimed doors, real sizes)
  * 2-3   window schedule W01-W12 (reclaimed windows, real sizes)
  * 10    door & window axonometric (which unit goes to which building)
  * photos (Featured, 12, 17, 22-24, Rungkit*, DSC_*) -> heights, roof pitch, materials
  * Gemini_Generated_Image_*.png is a different flat-roof house; it is NOT part of this model.

Plan positions come from the scaled plan (+-0.2 m). Heights, roof pitches, structure sizes
and footings are ESTIMATES from photos - nothing here is a structural design.

Buildings
  A  living / dining / bedroom pavilion, gable roof (ridge E-W), south veranda + slat screen
  C  bedroom house: two parallel gables (tall C-W 45 deg, wide C-E 30 deg), 2 bathrooms, tub deck
  D  garage + 2 store rooms, turned 26 deg, gable roof with raised clerestory (monitor) roof,
     timber slat gable screen, gabion wall
  P  timber pergola frames on stone footings, diagonal timber deck, walkways

Axes (metres): X east (plan right), Y north (plan up), Z up, ground +-0.00.
Plan pixel (px, py) -> X = (px-130)/24.6, Y = (340-py)/24.6
Run:  python3 make_model.py
"""
import json, math, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE_SRC = os.path.join(HERE, '..', 'Architecture', 'SoundStudio_House_BIM.rb')

NOTE = 'Plan position from scaled plan; height/size ESTIMATED from photos - verify'
FFL = 0.45                   # floor level of A and C (polished concrete on grade)
DECK = 0.40                  # timber deck top
E = []                       # [ifc, name, mark, level, tag, parts, attrs]


def r4(v):
    return round(v, 4)


def box(x0, x1, y0, y1, z0, z1, mat):
    x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
    return ['box', r4(x0), r4(x1), r4(y0), r4(y1), r4(z0), r4(z1), mat]


def add(ifc, name, mark, level, tag, parts, **attrs):
    if parts and not isinstance(parts[0], list):
        parts = [parts]
    assert parts, name
    attrs.setdefault('Note', NOTE)
    E.append([ifc, name, mark, level, tag, parts, attrs])


class Frame:
    """Local (a, b) plan axes. Identity for A/C/pergola; turned for the garage."""

    def __init__(self, ox=0.0, oy=0.0, u=(1.0, 0.0), v=(0.0, 1.0)):
        self.o, self.u, self.v = (ox, oy), u, v
        self.ident = (ox, oy) == (0.0, 0.0) and u == (1.0, 0.0) and v == (0.0, 1.0)

    def p(self, a, b, z):
        return [r4(self.o[0] + a * self.u[0] + b * self.v[0]), r4(self.o[1] + a * self.u[1] + b * self.v[1]), r4(z)]

    def vec(self, da, db, dz):
        return [round(da * self.u[0] + db * self.v[0], 6), round(da * self.u[1] + db * self.v[1], 6), round(dz, 6)]

    def box(self, a0, a1, b0, b1, z0, z1, mat):
        if self.ident:
            return box(a0, a1, b0, b1, z0, z1, mat)
        a0, a1 = sorted((a0, a1)); b0, b1 = sorted((b0, b1)); z0, z1 = sorted((z0, z1))
        return ['poly', [self.p(a0, b0, z0), self.p(a1, b0, z0), self.p(a1, b1, z0), self.p(a0, b1, z0)], [0, 0, 1], r4(z1 - z0), mat]

    def bar(self, p1, p2, b, h, mat):
        return ['bar', self.p(*p1), self.p(*p2), b, h, mat]

    def poly(self, pts, n, t, mat):
        return ['poly', [self.p(*q) for q in pts], self.vec(*n), r4(t), mat]


I = Frame()
TH = math.radians(26.0)      # garage turned 26 deg (plan); local a along its 7.9 m side, b along 10.4 m
D_F = Frame(16.87, -0.48, (math.cos(TH), -math.sin(TH)), (-math.sin(TH), -math.cos(TH)))


def P(px, py):
    """plan pixel -> model metres"""
    return round((px - 130) / 24.6, 2), round((340 - py) / 24.6, 2)


# ------------------------------------------------------------------ walls, doors, windows
def wall(F, name, mark, axis, c, s0, s1, z0, z1, t, openings=(), mat='timber', ext=True, desc='Timber stud wall, reclaimed board cladding'):
    """axis 'a': wall runs along a at b=c ; 'b': runs along b at a=c. openings (o0,o1,zs,ze) absolute z."""
    parts = []

    def seg(p0, p1, zz0, zz1):
        if p1 - p0 < 1e-3 or zz1 - zz0 < 1e-3:
            return
        parts.append(F.box(p0, p1, c - t / 2, c + t / 2, zz0, zz1, mat) if axis == 'a' else F.box(c - t / 2, c + t / 2, p0, p1, zz0, zz1, mat))
    cur, area_open = s0, 0.0
    for o0, o1, zs, ze in sorted(openings):
        seg(cur, o0, z0, z1); seg(o0, o1, z0, zs); seg(o0, o1, ze, z1)
        cur = o1
        area_open += (o1 - o0) * (ze - zs)
    seg(cur, s1, z0, z1)
    add('IfcWall', name, mark, 'GF', 'A-Wall', parts,
        **{'Thickness_m': t, 'Height_m': round(z1 - z0, 2), 'Length_m': round(s1 - s0, 2),
           'NetArea_m2(one face)': round((s1 - s0) * (z1 - z0) - area_open, 2), 'IsExternal': ext, 'Description': desc})


SCHED = {}   # mark -> (H, W, pieces) from the reclaimed door/window schedule sheets (H x W as printed)
for m, h, w in (('D01', 1.84, .76), ('D02', 1.85, .85), ('D03', 1.82, .70), ('D04', 1.82, .86), ('D05', 1.93, .83),
                ('D06', 1.93, .86), ('D07', 1.84, .85), ('D08', 1.81, .69), ('D09', 2.46, .95), ('D10', 2.45, .86),
                ('D11', 2.50, 1.00), ('D12', 1.85, .81), ('D13', 1.90, .86), ('D14', 1.88, .86), ('D15', 1.92, .86),
                ('D16', 2.15, .86), ('D17', 1.85, .78), ('D18', 1.84, .78), ('D19', 1.87, .78), ('D20', 1.77, .66)):
    SCHED[m] = (h, w, 1)
for m, w, h, n in (('W01', 1.56, .57, 1), ('W02', 1.40, 1.38, 1), ('W03', 1.40, 1.38, 3), ('W04', 1.85, 1.38, 3),
                   ('W05', 1.32, .98, 2), ('W06', 1.37, .98, 2), ('W07', 1.29, .98, 1), ('W08', 1.07, .96, 1),
                   ('W09', 1.41, 1.33, 1), ('W10', 1.85, 1.33, 1), ('W11', 1.40, 1.33, 3), ('W12', 1.29, .89, 1)):
    SCHED[m] = (h, w, n)
LEAVES = {'W01': 2, 'W02': 2, 'W03': 3, 'W04': 4, 'W05': 2, 'W06': 2, 'W07': 2, 'W08': 2, 'W09': 2, 'W10': 4,
          'W11': 2, 'W12': 5}
WDESC = {'W01': 'louvre vent', 'W12': 'timber slat panel', 'W08': 'solid timber shutters'}
PLACED = {}


def unit(F, kind, name, mark, axis, c, o0, o1, zs, ze, desc, leaves, leaf, frame_mat, t=0.07, building=''):
    f = 0.05
    parts = []

    def b(s0, s1, zz0, zz1, mat, th):
        if s1 - s0 < 1e-3 or zz1 - zz0 < 1e-3:
            return
        parts.append(F.box(s0, s1, c - th / 2, c + th / 2, zz0, zz1, mat) if axis == 'a' else F.box(c - th / 2, c + th / 2, s0, s1, zz0, zz1, mat))
    b(o0, o1, ze - f, ze, frame_mat, t)
    b(o0, o0 + f, zs, ze - f, frame_mat, t)
    b(o1 - f, o1, zs, ze - f, frame_mat, t)
    if kind == 'window':
        b(o0 + f, o1 - f, zs, zs + f, frame_mat, t)
    z0 = zs + (f if kind == 'window' else 0)
    zt = ze - f
    # reclaimed units: glazed transom over timber leaves (as in the schedule photos)
    transom = leaf == 'timber' and (zt - z0) > 0.8
    zl = zt - 0.25 if transom else zt
    if transom:
        b(o0 + f, o1 - f, zl, zl + 0.04, frame_mat, t)
        b(o0 + f, o1 - f, zl + 0.04, zt, 'glass', 0.012)
    n = max(1, leaves)
    w = (o1 - o0 - 2 * f) / n
    for i in range(n):
        s0 = o0 + f + i * w
        b(s0 + 0.01, s0 + w - 0.01, z0, zl, leaf, 0.035 if leaf != 'glass' else 0.012)
        if i:
            b(s0 - 0.02, s0 + 0.02, z0, zl, frame_mat, t)
    ifc = 'IfcDoor' if kind == 'door' else 'IfcWindow'
    attrs = {'Size_WxH_m': '%.2fx%.2f' % (o1 - o0, ze - zs), 'Leaves': n, 'Description': desc,
             'SillFromFloor_m': round(zs - FFL, 2) if building != 'D' else round(zs - 0.12, 2)}
    if mark in SCHED:
        h, wd, pcs = SCHED[mark]
        attrs['Schedule'] = 'reclaimed %s, schedule size %.2f x %.2f m%s' % (mark, h, wd, ', %d pieces' % pcs if pcs > 1 else '')
        attrs['Note'] = 'Size from reclaimed door/window schedule; position ESTIMATED from plan/photos'
        PLACED.setdefault(mark, []).append(name)
    add(ifc, name, mark, 'GF', 'A-Door' if kind == 'door' else 'A-Window', parts, **attrs)


def wall_units(F, name, mark, axis, c, s0, s1, z0, z1, t, units, mat='timber', ext=True, building='', desc=None):
    """units: (mark, start_along_wall, sill_z) for schedule items, or (mark, o0, o1, zs, ze, kind, desc, leaves, leaf)."""
    ops, rows = [], []
    for u in units:
        if len(u) == 3:
            m, o0, zs = u
            h, w, _ = SCHED[m]
            kind = 'door' if m.startswith('D') else 'window'
            if kind == 'window':
                w, h = SCHED[m][1], SCHED[m][0]
            o1, ze = o0 + w, zs + h
            d = ('Reclaimed timber door' if kind == 'door' else 'Reclaimed timber window, ' + WDESC.get(m, 'side-hung leaves'))
            rows.append((kind, m, o0, o1, zs, ze, d, 1 if kind == 'door' else LEAVES[m], 'timber', 'timber_dark'))
        else:
            m, o0, o1, zs, ze, kind, d, lv, leaf = u
            rows.append((kind, m, o0, o1, zs, ze, d, lv, leaf, 'frame_alu' if leaf == 'glass' else 'timber_dark'))
        ops.append((rows[-1][2], rows[-1][3], rows[-1][4], rows[-1][5]))
    kw = {} if desc is None else {'desc': desc}
    wall(F, name, mark, axis, c, s0, s1, z0, z1, t, ops, mat=mat, ext=ext, **kw)
    marks = [r[1] for r in rows]
    for i, (kind, m, o0, o1, zs, ze, d, lv, leaf, fm) in enumerate(rows):
        un = '%s/%s' % (name, m) if marks.count(m) == 1 else '%s/%s-%d' % (name, m, i + 1)
        unit(F, kind, un, m, axis, c, o0, o1, zs, ze, d, lv, leaf, fm, building=building)


# ------------------------------------------------------------------ roofs (corrugated fibre-cement sheet on timber)
class Roof:
    pass


SHEET, PURLIN_H, RAFTER_H = 0.03, 0.10, 0.15


def gable_roof(F, key, ridge, s0, s1, r0, r1, ze, pitch, gap=0.0, step=1.0, desc=''):
    """ridge along local 'a' or 'b'. s = span coordinate (eave s0 .. eave s1), r = along ridge.
    ze = sheet underside at the eaves. gap > 0 stops each slope short of the ridge (clerestory)."""
    R = Roof()
    R.s0, R.s1, R.ze, R.tn = s0, s1, ze, math.tan(math.radians(pitch))
    R.half = (s1 - s0) / 2
    R.run = R.half - gap
    R.drop = (PURLIN_H + RAFTER_H) / math.cos(math.radians(pitch))
    sm = (s0 + s1) / 2
    zr = ze + R.run * R.tn
    sn, cs = math.sin(math.radians(pitch)), math.cos(math.radians(pitch))

    def L(s, r, z):
        return (s, r, z) if ridge == 'b' else (r, s, z)

    def N(ds, dz):
        return (ds, 0, dz) if ridge == 'b' else (0, ds, dz)
    slope_len = R.run / cs
    for side, sg in (('1', 1), ('2', -1)):
        se = s0 if sg == 1 else s1
        st = se + sg * R.run
        sheet = F.poly([L(se, r0, ze), L(se, r1, ze), L(st, r1, zr), L(st, r0, zr)], N(-sg * sn, cs), SHEET, 'roof_sheet')
        add('IfcRoof', 'RF-%s-%s' % (key, side), 'RF', 'ROOF', 'A-Roof', sheet,
            **{'Pitch_deg': pitch, 'SlopeArea_m2': round(slope_len * (r1 - r0), 2), 'Description': 'Corrugated fibre-cement sheet (grey) ' + desc})
        # purlins (along ridge) every ~0.8 m up the slope
        pur = []
        k = int(slope_len / 0.8) + 1
        for i in range(k + 1):
            d = min(i * 0.8, slope_len - 0.05) * cs
            s = se + sg * d
            z = ze + d * R.tn - PURLIN_H / 2
            pur.append(F.bar(L(s, r0 + 0.05, z), L(s, r1 - 0.05, z), 0.05, PURLIN_H, 'timber'))
        add('IfcMember', 'PU-%s-%s' % (key, side), 'PU', 'ROOF', 'S-RoofTimber', pur,
            Section='50x100 timber purlin @0.80', Count=len(pur))
        # rafters
        raf = []
        n = max(2, int(round((r1 - r0 - 0.2) / step)) + 1)
        for i in range(n):
            r = r0 + 0.1 + i * (r1 - r0 - 0.2) / (n - 1)
            off = PURLIN_H + RAFTER_H / 2
            p1 = L(se - sg * 0.0, r, ze - off / cs)
            p2 = L(st, r, zr - off / cs)
            raf.append(F.bar(p1, p2, 0.05, RAFTER_H, 'timber'))
        add('IfcMember', 'RA-%s-%s' % (key, side), 'RA', 'ROOF', 'S-RoofTimber', raf,
            Section='50x150 reclaimed timber rafter @%.2f' % ((r1 - r0 - 0.2) / (n - 1)), Count=len(raf))
    zb = zr - R.drop - 0.10
    if gap <= 0:
        add('IfcBeam', 'RB-%s' % key, 'RB', 'ROOF', 'S-RoofTimber', F.bar(L(sm, r0, zb), L(sm, r1, zb), 0.10, 0.20, 'timber_dark'),
            Section='100x200 ridge beam')
    else:
        add('IfcBeam', 'RB-%s' % key, 'RB', 'ROOF', 'S-RoofTimber',
            [F.bar(L(sm - gap, r0, zb), L(sm - gap, r1, zb), 0.10, 0.20, 'timber_dark'),
             F.bar(L(sm + gap, r0, zb), L(sm + gap, r1, zb), 0.10, 0.20, 'timber_dark')],
            Section='2 x 100x200 head beams at the clerestory')
    return R


def under(R, s):
    """rafter underside at span coordinate s"""
    d = max(0.0, min(s - R.s0, R.s1 - s, R.run))
    return R.ze + d * R.tn - R.drop


def gable_infill(F, name, R, ridge, c, w0, w1, zb, t=0.08, mat='timber_v'):
    """vertical cladding between wall plate zb and the roof line, across the span w0..w1, at ridge coordinate c"""
    ss = sorted({w0, w1} | {s for s in (R.s0 + R.run, R.s1 - R.run) if w0 < s < w1})
    top = [(s, under(R, s)) for s in ss]
    if max(z for _, z in top) <= zb + 0.03:
        return
    top = [(s, max(z, zb + 0.001)) for s, z in top]
    pts2 = [(w0, zb), (w1, zb)] + [(s, z) for s, z in reversed(top)]
    if ridge == 'b':
        pts = [(s, c - t / 2, z) for s, z in pts2]; n = (0, 1, 0)
    else:
        pts = [(c - t / 2, s, z) for s, z in pts2]; n = (1, 0, 0)
    add('IfcWall', name, 'GB', 'GF', 'A-Wall', F.poly(pts, n, t, mat),
        Description='Gable infill: vertical reclaimed board cladding up to the roof', Thickness_m=t)


# ------------------------------------------------------------------ structure helpers
def post(F, name, a, b, z0, z1, size=0.15, mat='timber_dark', footing=True, stump_top=None, fnd_mat='concrete'):
    add('IfcColumn', name, 'TC', 'GF', 'S-Column', F.box(a - size / 2, a + size / 2, b - size / 2, b + size / 2, z0, z1, mat),
        Section='%dx%d reclaimed hardwood post' % (size * 1000, size * 1000), Height_m=round(z1 - z0, 2))
    if footing:
        st = z0 if stump_top is None else stump_top
        add('IfcFooting', 'F-' + name, 'F1', 'FND', 'S-Foundation', F.box(a - .4, a + .4, b - .4, b + .4, -1.20, -0.95, fnd_mat),
            Size_m='0.80x0.80x0.25', Note='Footing ASSUMED (no soil data, no structural design)')
        if st > -0.95:
            add('IfcColumn', 'ST-' + name, 'ST', 'FND', 'S-Column', F.box(a - .1, a + .1, b - .1, b + .1, -0.95, st, fnd_mat),
                Section='0.20x0.20 RC stump', Note='ASSUMED')


def beam(F, name, axis, c, s0, s1, ztop, h=0.20, w=0.10, mat='timber_dark', mark='TB', tag='S-Beam'):
    part = F.box(s0, s1, c - w / 2, c + w / 2, ztop - h, ztop, mat) if axis == 'a' else F.box(c - w / 2, c + w / 2, s0, s1, ztop - h, ztop, mat)
    add('IfcBeam', name, mark, 'GF', tag, part, Section='%dx%d timber beam' % (w * 1000, h * 1000), Length_m=round(s1 - s0, 2))


def deck(F, name, pts, z, desc, piers=True, t=0.05):
    """pts: plan polygon (a, b); boards t thick, top at z, joists implied, concrete piers ~1.5 m"""
    add('IfcSlab', name, 'DK', 'GF', 'A-Deck', F.poly([(a, b, z - t) for a, b in pts], (0, 0, 1), t, 'deck'),
        Description=desc + ' (reclaimed hardwood boards on joists)', Area_m2=round(poly_area(pts), 2))
    if piers:
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        prs = []
        nx = max(1, int((max(xs) - min(xs)) / 1.5)); ny = max(1, int((max(ys) - min(ys)) / 1.5))
        for i in range(nx + 1):
            for j in range(ny + 1):
                a = min(xs) + 0.35 + i * (max(xs) - min(xs) - 0.7) / nx
                b = min(ys) + 0.15 + j * (max(ys) - min(ys) - 0.3) / ny
                if inside((a, b), pts):
                    prs.append(F.box(a - .1, a + .1, b - .1, b + .1, 0.0, z - t - 0.10, 'concrete'))
                    prs.append(F.box(a - .3, a + .3, b - .05, b + .05, z - t - 0.10, z - t, 'timber'))
        if prs:
            add('IfcMember', name + '-SUB', 'DKJ', 'GF', 'S-Beam', prs, Description='Deck piers (0.20 RC) + 50x100 bearers, ASSUMED')


def poly_area(pts):
    return abs(sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))) / 2


def inside(p, pts):
    x, y = p
    c = False
    for i in range(len(pts)):
        (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % len(pts)]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def octagon(cx, cy, r):
    return [(cx + r * math.cos(math.pi / 8 + k * math.pi / 4), cy + r * math.sin(math.pi / 8 + k * math.pi / 4)) for k in range(8)]


# ================================================================== BUILDING A  (living / dining / bedroom)
AX0, AX1 = 0.0, 12.30          # plan x 130 .. 433
AYN, AYS = 9.85, 5.45          # north wall (py 97), south glazing line (py 205)
AYV = 3.85                     # veranda post line (py 245)
ABX = 9.43                     # living | bedroom (px 362)
ABYS = 4.07                    # bedroom block south face (py 240)
ABAX, ABAY = 2.06, 7.30        # bathroom corner (px 181, py 160)
A_PLATE = 3.10                 # top of wall plate
A_WTOP = A_PLATE - 0.20

# slab + grade beams
add('IfcSlab', 'A-SLAB', 'SL1', 'GF', 'S-Slab', [box(AX0, ABX, AYS, AYN, 0.30, FFL, 'concrete_floor'), box(ABX, AX1, ABYS, AYN, 0.30, FFL, 'concrete_floor')],
    Thickness_m=0.15, Area_m2=round((ABX - AX0) * (AYN - AYS) + (AX1 - ABX) * (AYN - ABYS), 2), Description='Polished concrete floor slab on grade, FFL +0.45')
gb = []
for y0, y1, x0, x1 in ((AYN, AYN, AX0, AX1), (AYS, AYS, AX0, ABX), (ABYS, ABYS, ABX, AX1)):
    gb.append(box(x0 - .1, x1 + .1, y0 - .1, y0 + .1, -0.10, 0.30, 'concrete'))
for x, y0, y1 in ((AX0, AYS, AYN), (ABX, ABYS, AYN), (AX1, ABYS, AYN)):
    gb.append(box(x - .1, x + .1, y0 + .1, y1 - .1, -0.10, 0.30, 'concrete'))
add('IfcBeam', 'A-GB', 'GB1', 'FND', 'S-Beam', gb, Section='0.20x0.40 RC grade beam', Note='ASSUMED')

A_POSTS_X = [AX0, ABAX, 4.425, 6.875, ABX, AX1]
for x in A_POSTS_X:
    post(I, 'A-C-N%s' % ('%.2f' % x).replace('.', ''), x, AYN, FFL, A_PLATE)
for x in [AX0, ABAX, 4.425, 6.875, ABX]:
    post(I, 'A-C-S%s' % ('%.2f' % x).replace('.', ''), x, AYS, FFL, A_PLATE)
for x in (ABX, AX1):
    post(I, 'A-C-B%s' % ('%.2f' % x).replace('.', ''), x, ABYS, FFL, A_PLATE)
RA = gable_roof(I, 'A', 'a', 3.25, 10.75, AX0 - 1.10, AX1 + 0.60, 2.95, 30, desc='over living/bedroom pavilion + veranda')
for (x, y) in ((3.66, 9.27), (6.54, 9.27), (3.66, 5.73), (6.54, 5.73)):       # interior posts (plan) -> purlin beams
    post(I, 'A-C-I%d%d' % (round(x), round(y)), x, y, FFL, round(under(RA, y) - 0.20, 3), size=0.18)
for x in (AX0, ABAX, 4.425, 6.875):                                            # veranda posts
    post(I, 'A-C-V%s' % ('%.2f' % x).replace('.', ''), x, AYV, DECK, 2.95, size=0.18, stump_top=DECK - 0.05)

beam(I, 'A-B-N', 'a', AYN, AX0 - .1, AX1 + .1, A_PLATE)
beam(I, 'A-B-S', 'a', AYS, AX0 - .1, ABX, A_PLATE)
beam(I, 'A-B-BS', 'a', ABYS, ABX - .1, AX1 + .1, A_PLATE)
beam(I, 'A-B-V', 'a', AYV, AX0 - .2, ABX - .1, 3.05, h=0.20, w=0.12)
beam(I, 'A-B-W', 'b', AX0, AYS, AYN, A_PLATE)
beam(I, 'A-B-E', 'b', AX1, ABYS, AYN, A_PLATE)
beam(I, 'A-B-I1', 'a', 9.27, ABAX, ABX, round(under(RA, 9.27), 3), h=0.20, w=0.15)
beam(I, 'A-B-I2', 'a', 5.73, ABAX, ABX, round(under(RA, 5.73), 3), h=0.20, w=0.15)

# walls (FFL -> under plate)
z0, z1 = FFL, A_WTOP
wall_units(I, 'A-W-N1', 'WT', 'a', AYN, AX0, ABAX, z0, z1, 0.10, [('W01', 0.25, FFL + 1.55)])
wall_units(I, 'A-W-N2', 'WT', 'a', AYN, ABAX, ABX, z0, z1, 0.10,
           [('W10', 2.45, FFL + 0.55), ('W04', 4.55, FFL + 0.55), ('W11', 7.15, FFL + 0.55)])
wall_units(I, 'A-W-N3', 'WT', 'a', AYN, ABX, AX1, z0, z1, 0.10, [('W09', 10.15, FFL + 0.55)])
wall_units(I, 'A-W-S0', 'WT', 'a', AYS, AX0, ABAX, z0, z1, 0.10, [('W07', 0.40, FFL + 0.90)])
wall_units(I, 'A-W-S', 'GL', 'a', AYS, ABAX, ABX, z0, z1, 0.10,
           [('GD1', ABAX + .08, 4.425 - .08, FFL, FFL + 2.40, 'door', 'Aluminium bi-fold glass door (grey frame)', 4, 'glass'),
            ('GD1', 4.425 + .08, 6.875 - .08, FFL, FFL + 2.40, 'door', 'Aluminium bi-fold glass door (grey frame)', 4, 'glass'),
            ('GD1', 6.875 + .08, ABX - .08, FFL, FFL + 2.40, 'door', 'Aluminium bi-fold glass door (grey frame)', 4, 'glass')],
           desc='Glazed veranda front, timber framed')
wall_units(I, 'A-W-W1', 'WT', 'b', AX0, AYS, ABAY, z0, z1, 0.10, [('D07', 5.90, FFL)])
wall_units(I, 'A-W-W2', 'WP', 'b', AX0, ABAY, AYN, z0, z1, 0.12, [('W12', 7.95, FFL + 1.10)], mat='plaster',
           desc='Bathroom wall, rendered masonry, white')
wall_units(I, 'A-W-E', 'WP', 'b', AX1, ABYS, AYN, z0, z1, 0.15, [('W05', 7.20, FFL + 0.85)], mat='plaster',
           desc='East end wall, rendered masonry, white (photo 17)')
wall_units(I, 'A-W-BS', 'WT', 'a', ABYS, ABX, AX1, z0, z1, 0.10, [('W03', 10.15, FFL + 0.55)])
wall_units(I, 'A-W-BW', 'WT', 'b', ABX, ABYS, AYS, z0, z1, 0.10, [('D14', 4.35, FFL)])
wall_units(I, 'A-W-BP', 'WT', 'b', ABX, AYS, AYN, z0, z1, 0.10, [('D13', 5.75, FFL)], ext=False, desc='Partition living | bedroom')
wall_units(I, 'A-W-BE', 'WT', 'a', AYS, ABX, AX1, z0, z1, 0.10, [('D19', 11.20, FFL)], ext=False, desc='Partition bedroom | wardrobe')
wall(I, 'A-W-BA1', 'WP', 'b', ABAX, ABAY, AYN, z0, z1, 0.10, mat='plaster', ext=False, desc='Bathroom partition, rendered')
wall_units(I, 'A-W-BA2', 'WP', 'a', ABAY, AX0, ABAX, z0, z1, 0.10, [('D03', 1.10, FFL)], mat='plaster', ext=False,
           desc='Bathroom partition, rendered')

add('IfcWall', 'A-W-S-UP', 'GB', 'GF', 'A-Wall', box(AX0, ABX, AYS - .02, AYS + .02, A_PLATE, round(under(RA, AYS), 3), 'timber_v'),
    Description='Vertical board infill above the glazed front', Thickness_m=0.04)
gable_infill(I, 'A-GB-W', RA, 'a', AX0, AYS, AYN, A_PLATE)
gable_infill(I, 'A-GB-E', RA, 'a', AX1, ABYS, AYN, A_PLATE, mat='plaster')
gable_infill(I, 'A-GB-P', RA, 'a', ABX, AYS, AYN, A_PLATE)

deck(I, 'A-DK-VER', [(AX0 - 0.05, 3.65), (ABX, 3.65), (ABX, AYS - 0.05), (AX0 - 0.05, AYS - 0.05)], DECK, 'South veranda deck')
deck(I, 'A-DK-W', [(-0.95, 5.60), (AX0 - 0.05, 5.60), (AX0 - 0.05, 9.40), (-0.95, 9.40)], DECK, 'West veranda deck')
add('IfcSlab', 'A-TERRACE', 'TR', 'GF', 'Site', I.poly([(-1.0, 3.62, 0), (2.76, 3.62, 0), (2.76, 1.22, 0), (-1.0, 3.38, 0)], (0, 0, 1), 0.15, 'concrete'),
    Description='Concrete terrace (plan, SW of A)')
# west slat screen (Featured image, photo 24)
scr = [box(-1.05, -0.95, y - .05, y + .05, 0.0, 2.40, 'timber_dark') for y in (3.70, 5.60, 7.50, 9.40)]
scr += [I.bar((-1.0, 3.70, z), (-1.0, 9.40, z), 0.03, 0.09, 'timber') for z in [0.45 + 0.13 * k for k in range(15)]]
add('IfcBuildingElementProxy', 'A-SCREEN-W', 'SCR', 'GF', 'A-Screen', scr, Description='Horizontal reclaimed-timber slat screen, ~2.4 m high')
# bathroom fittings
add('IfcSanitaryTerminal', 'A-WC', 'WC', 'GF', 'P-Sanitary', box(0.30, 0.68, 9.05, 9.75, FFL, FFL + 0.40, 'sanitary'), Description='Close-coupled WC')
add('IfcSanitaryTerminal', 'A-BASIN', 'LB', 'GF', 'P-Sanitary', box(1.20, 1.85, 9.30, 9.78, FFL + 0.75, FFL + 0.88, 'sanitary'), Description='Counter basin')
add('IfcFurniture', 'A-DINING', 'FN', 'GF', 'A-Furniture', [box(3.9, 6.3, 7.1, 8.0, FFL + 0.70, FFL + 0.75, 'timber'),
    box(3.95, 4.05, 7.15, 7.95, FFL, FFL + 0.70, 'timber'), box(6.15, 6.25, 7.15, 7.95, FFL, FFL + 0.70, 'timber')],
    Description='Dining table 2.40 x 0.90 (plan / photo 23)')

# ================================================================== BUILDING C  (bedroom house, twin gables)
CX0, CXM, CXE, CXB = 21.54, 24.59, 27.56, 29.55     # px 660, 735, 808, 857
CYS, CYM, CYN = 2.03, 6.10, 9.43                    # py 290, 190, 108
CYB2 = 0.20                                         # lower bathroom south (py 335)
CXK = 20.53                                         # covered side walk (px 635)
C_PLATE = 2.95
C_WTOP = C_PLATE - 0.20

add('IfcSlab', 'C-SLAB', 'SL1', 'GF', 'S-Slab', [box(CX0, CXE, CYS, CYN, 0.30, FFL, 'concrete_floor'),
    box(CXE, CXB, CYM, CYN, 0.30, FFL, 'concrete_floor'), box(CXM, CXE, CYB2, CYS, 0.30, FFL, 'concrete_floor')],
    Thickness_m=0.15, Description='Concrete floor slab on grade, FFL +0.45')
gb = [box(CX0 - .1, CXB + .1, CYN - .1, CYN + .1, -0.10, 0.30, 'concrete'), box(CX0 - .1, CXM + .1, CYS - .1, CYS + .1, -0.10, 0.30, 'concrete'),
      box(CXM - .1, CXE + .1, CYB2 - .1, CYB2 + .1, -0.10, 0.30, 'concrete'), box(CXE - .1, CXB + .1, CYM - .1, CYM + .1, -0.10, 0.30, 'concrete'),
      box(CX0 - .1, CX0 + .1, CYS + .1, CYN - .1, -0.10, 0.30, 'concrete'), box(CXM - .1, CXM + .1, CYB2 + .1, CYS - .1, -0.10, 0.30, 'concrete'),
      box(CXE - .1, CXE + .1, CYB2 + .1, CYM - .1, -0.10, 0.30, 'concrete'), box(CXB - .1, CXB + .1, CYM + .1, CYN - .1, -0.10, 0.30, 'concrete')]
add('IfcBeam', 'C-GB', 'GB1', 'FND', 'S-Beam', gb, Section='0.20x0.40 RC grade beam', Note='ASSUMED')
for nm, x, y in (('W-S', CX0, CYS), ('W-M', CX0, CYM), ('W-N', CX0, CYN), ('M-S', CXM, CYS), ('M-M', CXM, CYM), ('M-N', CXM, CYN),
                 ('M-B', CXM, CYB2), ('E-B', CXE, CYB2), ('E-S', CXE, CYS), ('E-M', CXE, CYM), ('E-N', CXE, CYN),
                 ('B-M', CXB, CYM), ('B-N', CXB, CYN)):
    post(I, 'C-C-' + nm, x, y, FFL, C_PLATE)
for y in (3.46, CYM, CYN):                                       # covered walk posts
    post(I, 'C-C-K%d' % round(y * 10), CXK + 0.1, y, DECK, 2.70, size=0.12, stump_top=DECK - 0.05)
for x in (CX0 + 0.1, CXM - 0.1):                                 # porch frame under the tall gable (DSC_8934)
    post(I, 'C-C-P%d' % round(x * 10), x, 0.45, DECK, 3.20, size=0.15, stump_top=DECK - 0.05)

for nm, axis, c, s0, s1 in (('C-B-N', 'a', CYN, CX0 - .1, CXB + .1), ('C-B-S', 'a', CYS, CX0 - .1, CXE + .1), ('C-B-M', 'a', CYM, CX0, CXB + .1),
                            ('C-B-B2', 'a', CYB2, CXM - .1, CXE + .1), ('C-B-W', 'b', CX0, CYS, CYN), ('C-B-X', 'b', CXM, CYB2, CYN),
                            ('C-B-E', 'b', CXE, CYB2, CYN), ('C-B-BE', 'b', CXB, CYM, CYN)):
    beam(I, nm, axis, c, s0, s1, C_PLATE)
beam(I, 'C-B-K', 'b', CXK + 0.1, 3.40, CYN + .05, 2.70, h=0.15, w=0.10)
beam(I, 'C-B-P', 'a', 0.45, CX0, CXM, 3.20, h=0.20, w=0.10)

z0, z1 = FFL, C_WTOP
wall_units(I, 'C-W-WS', 'SD', 'a', CYS, CX0, CXM, z0, z1, 0.10,
           [('SD1', 22.30, 23.90, FFL, FFL + 2.20, 'door', 'Aluminium sliding glass door (DSC_8934)', 2, 'glass')])
wall_units(I, 'C-W-W', 'WT', 'b', CX0, CYS, CYN, z0, z1, 0.10, [('D15', 3.90, FFL), ('W06', 7.20, FFL + 0.70)])
wall_units(I, 'C-W-N1', 'WT', 'a', CYN, CX0, CXM, z0, z1, 0.10, [('W02', 22.35, FFL + 0.70)])
wall_units(I, 'C-W-N2', 'WT', 'a', CYN, CXM, CXE, z0, z1, 0.10, [('W04', 25.15, FFL + 0.60)])
wall_units(I, 'C-W-N3', 'WT', 'a', CYN, CXE, CXB, z0, z1, 0.10, [('W05', 27.90, FFL + 1.20)])
wall_units(I, 'C-W-BE', 'WT', 'b', CXB, CYM, CYN, z0, z1, 0.10, [('D08', 7.00, FFL)])
wall(I, 'C-W-BS', 'WT', 'a', CYM, CXE, CXB, z0, z1, 0.10)
wall_units(I, 'C-W-E', 'WT', 'b', CXE, CYS, CYM, z0, z1, 0.10, [('W03', 3.30, FFL + 0.55)])
wall(I, 'C-W-E2', 'WT', 'b', CXE, CYB2, CYS, z0, z1, 0.10)
wall_units(I, 'C-W-B2S', 'WT', 'a', CYB2, CXM, CXE, z0, z1, 0.10, [('W08', 25.50, FFL + 1.00)])
wall(I, 'C-W-B2W', 'WT', 'b', CXM, CYB2, CYS, z0, z1, 0.10)
wall_units(I, 'C-W-P1', 'WT', 'b', CXM, CYS, CYM, z0, z1, 0.10, [('D17', 4.90, FFL)], ext=False, desc='Partition, reclaimed boards')
wall_units(I, 'C-W-P2', 'WT', 'a', CYM, CX0, CXM, z0, z1, 0.10, [('D12', 22.00, FFL)], ext=False, desc='Partition, reclaimed boards')
wall(I, 'C-W-P3', 'WT', 'a', CYM, CXM, CXE, z0, z1, 0.10, ext=False, desc='Partition, reclaimed boards')
wall_units(I, 'C-W-P4', 'WT', 'b', CXE, CYM, CYN, z0, z1, 0.10, [('D20', 6.50, FFL)], ext=False, desc='Partition bedroom | bathroom')
wall_units(I, 'C-W-P5', 'WT', 'a', CYS, CXM, CXE, z0, z1, 0.10, [('D18', 26.40, FFL)], ext=False, desc='Partition bedroom | bathroom')

RCW = gable_roof(I, 'CW', 'b', CXK - 0.25, 25.00, -0.20, CYN + 0.65, 3.00, 45, desc='tall gable over west wing, porch + side walk')
RCE = gable_roof(I, 'CE', 'b', 24.90, 30.30, CYB2 - 0.60, CYN + 0.60, 2.85, 30, desc='wide gable over east wing + bathrooms')
gable_infill(I, 'C-GB-WS', RCW, 'b', CYS, CX0, CXM, C_PLATE)
gable_infill(I, 'C-GB-WN', RCW, 'b', CYN, CX0, CXM, C_PLATE)
gable_infill(I, 'C-GB-EN', RCE, 'b', CYN, 24.95, CXB, C_PLATE)
gable_infill(I, 'C-GB-ES', RCE, 'b', CYB2, 24.95, CXE, C_PLATE)
gable_infill(I, 'C-GB-EM', RCE, 'b', CYM, CXE, CXB, C_PLATE)

deck(I, 'C-DK-WALK', [(17.30, 2.32), (CX0, 2.32), (CX0, 3.58), (17.30, 3.58)], DECK, 'Walkway deck pergola -> C (plan)')
deck(I, 'C-DK-SIDE', [(CXK, 3.58), (CX0 - .05, 3.58), (CX0 - .05, CYN), (CXK, CYN)], DECK, 'Covered side walk, west of C')
deck(I, 'C-DK-PORCH', [(CX0, 0.41), (CXM - .05, 0.41), (CXM - .05, CYS - .05), (CX0, CYS - .05)], DECK, 'Porch deck under the tall gable')
add('IfcStair', 'C-STEPS', 'STP', 'GF', 'A-Deck', [box(22.2, 23.8, 0.05, 0.41, 0.0, 0.20, 'timber'), box(22.2, 23.8, -0.31, 0.05, 0.0, 0.05, 'stone')],
    Description='Timber block step + stone pad (DSC_8934)')
deck(I, 'C-DK-TUB', [(CXB + .05, 6.20), (31.38, 6.20), (31.38, CYN + .05), (CXB + .05, CYN + .05)], DECK, 'Outdoor bath deck (plan)')
add('IfcSanitaryTerminal', 'C-TUB', 'BT', 'GF', 'P-Sanitary', I.poly([(a, b, DECK) for a, b in octagon(30.55, 8.55, 0.55)], (0, 0, 1), 0.60, 'sanitary'),
    Description='Round outdoor soaking tub, dia 1.10 (plan)')
add('IfcSanitaryTerminal', 'C-WC1', 'WC', 'GF', 'P-Sanitary', box(28.80, 29.40, 8.80, 9.18, FFL, FFL + 0.40, 'sanitary'), Description='WC')
add('IfcSanitaryTerminal', 'C-WC2', 'WC', 'GF', 'P-Sanitary', box(24.75, 25.13, 0.40, 1.00, FFL, FFL + 0.40, 'sanitary'), Description='WC')
add('IfcSanitaryTerminal', 'C-BASIN1', 'LB', 'GF', 'P-Sanitary', box(27.75, 28.30, 6.25, 6.70, FFL + 0.75, FFL + 0.88, 'sanitary'), Description='Basin')
add('IfcSanitaryTerminal', 'C-BASIN2', 'LB', 'GF', 'P-Sanitary', box(26.80, 27.40, 0.35, 0.80, FFL + 0.75, FFL + 0.88, 'sanitary'), Description='Basin')
add('IfcFurniture', 'C-BENCH-N', 'FN', 'GF', 'A-Furniture', box(22.00, 24.10, CYN + 0.12, 10.15, 0.0, 0.45, 'timber'),
    Description='Timber window-seat box, north of C (plan)')

# ================================================================== BUILDING D  (garage + store rooms, turned 26 deg)
F = D_F
DA, DB = 7.90, 10.40
add('IfcSlab', 'D-SLAB', 'SL2', 'GF', 'S-Slab', F.box(0, DA, 0, DB, 0.0, 0.12, 'concrete'),
    Thickness_m=0.12, Area_m2=round(DA * DB, 2), Description='Concrete garage slab on grade')
D_PLATE = 2.70
for i, b in enumerate((0.10, 3.40, 6.90, DB - 0.10)):
    for a, s in ((0.10, 'W'), (DA - 0.10, 'E')):
        post(F, 'D-C-%s%d' % (s, i), a, b, 0.12, D_PLATE, size=0.20, stump_top=0.0)
for a in (2.75, 3.90):
    post(F, 'D-C-M%d' % round(a * 10), a, 0.20, 0.12, D_PLATE, size=0.12, stump_top=0.0)
for nm, c in (('D-B-W', 0.10), ('D-B-E', DA - 0.10)):
    beam(F, nm, 'b', c, -0.10, DB + 0.10, D_PLATE, h=0.25, w=0.12)
for i, b in enumerate((0.10, 3.40, 6.90, DB - 0.10)):
    beam(F, 'D-B-T%d' % i, 'a', b, 0.0, DA, D_PLATE, h=0.20, w=0.10)

# store rooms (plan room1 a .15-2.75, room2 a 3.9-7.05, b .2-3.2) + corridor (Rungkit11)
RZ0, RZ1 = 0.12, 2.50
wall(F, 'D-R1-N', 'WT', 'a', 0.20, 0.15, 2.75, RZ0, RZ1, 0.10)
wall_units(F, 'D-R1-S', 'WT', 'a', 3.20, 0.15, 2.75, RZ0, RZ1, 0.10, [('W06', 0.65, 1.10)], building='D')
wall(F, 'D-R1-W', 'WT', 'b', 0.15, 0.20, 3.20, RZ0, RZ1, 0.10)
wall_units(F, 'D-R1-E', 'WT', 'b', 2.75, 0.20, 3.20, RZ0, RZ1, 0.10, [('D16', 0.30, 0.12)], building='D')
wall(F, 'D-R2-N', 'WT', 'a', 0.20, 3.90, 7.05, RZ0, RZ1, 0.10)
wall_units(F, 'D-R2-S', 'WT', 'a', 3.20, 3.90, 7.05, RZ0, RZ1, 0.10, [('W11', 4.85, 0.92)], building='D')
wall_units(F, 'D-R2-W', 'WT', 'b', 3.90, 0.20, 3.20, RZ0, RZ1, 0.10, [('D02', 1.20, 0.12)], building='D')
wall(F, 'D-R2-E', 'WT', 'b', 7.05, 0.20, 3.20, RZ0, RZ1, 0.10)
add('IfcCovering', 'D-CEIL', 'CL', 'GF', 'A-Ceiling', F.box(0.10, 7.10, 0.15, 3.25, RZ1, RZ1 + 0.05, 'timber'),
    Description='Timber board ceiling over store rooms + corridor (Rungkit11)')

RDL = gable_roof(F, 'D', 'b', -0.80, DA + 0.80, -0.60, DB + 0.60, 2.60, 25, gap=1.0, desc='garage, lower slopes')
RDU = gable_roof(F, 'DU', 'b', DA / 2 - 1.55, DA / 2 + 1.55, -0.60, DB + 0.60, 4.55, 25, desc='raised clerestory (monitor) roof')
mp = []
for b in (-0.4, 2.0, 4.6, 7.2, DB + 0.4):
    for a in (DA / 2 - 1.0, DA / 2 + 1.0):
        mp.append(F.bar((a, b, under(RDL, a) + 0.05), (a, b, under(RDU, a) + RDU.drop - 0.30), 0.10, 0.10, 'timber_dark'))
add('IfcMember', 'D-MONITOR-POSTS', 'MP', 'ROOF', 'S-RoofTimber', mp, Section='100x100 timber studs carrying the clerestory roof')
# gable slat screen at the south end (Featured image / Rungkit07) - full height under both roofs
sl = []
for k in range(int(DA / 0.14) + 1):
    a = 0.05 + k * 0.14
    if a > DA - 0.05:
        break
    top = under(RDL, a) if abs(a - DA / 2) > 1.0 else under(RDU, a)
    sl.append(F.bar((a, DB - 0.05, 0.12), (a, DB - 0.05, max(top, 2.5)), 0.04, 0.06, 'timber'))
sl.append(F.bar((0, DB - 0.12, 2.10), (DA, DB - 0.12, 2.10), 0.06, 0.06, 'timber_dark'))
add('IfcBuildingElementProxy', 'D-SCREEN-S', 'SCR', 'GF', 'A-Screen', sl, Description='Vertical reclaimed-timber slat screen, full gable height')
sl = []
for k in range(int((DA - 0.1) / 0.14)):
    a = 0.10 + k * 0.14
    top = under(RDL, a) if abs(a - DA / 2) > 1.0 else under(RDU, a)
    if top > RZ1 + 0.10:
        sl.append(F.bar((a, 0.10, RZ1 + 0.05), (a, 0.10, top), 0.04, 0.06, 'timber'))
add('IfcBuildingElementProxy', 'D-SCREEN-N', 'SCR', 'GF', 'A-Screen', sl, Description='Slat gable infill above the store rooms')
add('IfcWall', 'D-GABION', 'GW', 'GF', 'A-Wall', F.box(-1.00, -0.50, 0.0, DB, 0.0, 1.00, 'gabion'),
    Description='Gabion wall: river stone in steel mesh, 0.50 x 1.00 h (Rungkit01/07)', Thickness_m=0.5, Length_m=DB)
add('IfcFurniture', 'D-BENCH', 'FN', 'GF', 'A-Furniture', F.box(0.64, 3.64, 8.95, 9.25, 0.12, 0.55, 'timber_dark'),
    Description='Low timber bench / rack (plan)')
add('IfcSlab', 'D-DRIVE', 'DW', 'GF', 'Site', F.box(DA, DA + 4.0, 0.0, DB, 0.0, 0.04, 'gravel'), Description='Gravel drive / turning area (ASSUMED)')

# ================================================================== PERGOLA, DECKS, SITE
PY = [2.11, 5.81, 9.43]
PX_ROW = [0.12, 3.66, 6.54, 9.47, 12.32, 14.72, 17.11, 19.51]   # px 133 220 291 363 433 492 551 610 (py 288)
pg = [(x, PY[0]) for x in PX_ROW] + [(x, y) for x in PX_ROW[-3:] for y in PY[1:]]
for x, y in pg:
    nm = 'PG-C-%d-%d' % (round(x * 10), round(y * 10))
    add('IfcColumn', nm, 'PC', 'GF', 'S-Column', box(x - .09, x + .09, y - .09, y + .09, 0.20, 3.00, 'timber_dark'),
        Section='180x180 reclaimed hardwood post on boulder (photo 12)', Height_m=2.8)
    add('IfcFooting', 'F-' + nm, 'FS', 'FND', 'S-Foundation', I.poly([(a, b, -0.10) for a, b in octagon(x, y, 0.30)], (0, 0, 1), 0.30, 'stone'),
        Description='Natural boulder footing (photo 12)', Note='ASSUMED: check bearing / anchorage')
add('IfcBeam', 'PG-B-S', 'PB', 'GF', 'S-Beam', box(-0.30, 19.80, PY[0] - .06, PY[0] + .06, 2.75, 3.00, 'timber_dark'),
    Section='120x250 timber', Length_m=20.1)
pb = [box(x - .05, x + .05, 1.80, 9.75, 2.40, 2.60, 'timber_dark') for x in PX_ROW[-3:]]
pb += [box(14.40, 19.80, y - .05, y + .05, 2.60, 2.80, 'timber_dark') for y in PY[1:]]
add('IfcBeam', 'PG-B-G', 'PB', 'GF', 'S-Beam', pb, Section='100x200 timber, two levels (photo 12)')
deck(I, 'P-DK-DIAG', [(3.98, 3.62), (9.35, 3.62), (15.16, 0.56), (13.95, -1.68)], DECK, 'Diagonal deck A -> garage (plan, photo 17)')
add('IfcSlab', 'GROUND', 'SITE', 'GF', 'Site', box(-5.0, 35.0, -17.0, 14.0, -0.05, 0.0, 'ground'), Description='Site (extent ASSUMED)')
for nm, (x, y), h, r in (('TREE-1', (5.49, 1.63), 5.2, 2.2), ('TREE-2', (19.10, 0.20), 5.6, 2.6)):
    add('IfcBuildingElementProxy', nm, 'TREE', 'GF', 'Site',
        [box(x - .15, x + .15, y - .15, y + .15, 0.0, h + 0.3, 'trunk'),
         I.poly([(a, b, h) for a, b in octagon(x, y, r)], (0, 0, 1), 2.0, 'leaf')], Description='Existing tree (plan) - kept')

# ================================================================== CEILINGS (for take-off; hidden in the preview)
def slope_ceiling(name, R, x0, x1, ya, yb, mat, desc):
    """sloped ceiling fixed under the rafters of roof R (ridge along X), between plan lines ya -> yb"""
    za, zb = under(R, ya) - 0.02, under(R, yb) - 0.02
    sn = math.hypot(yb - ya, zb - za)
    add('IfcCovering', name, 'CL', 'GF', 'A-Ceiling', I.poly([(x0, ya, za), (x1, ya, za), (x1, yb, zb), (x0, yb, zb)],
        (0, -(zb - za) / sn, (yb - ya) / sn) if yb > ya else (0, (zb - za) / sn, (ya - yb) / sn), 0.02, mat),
        Description=desc, Area_m2=round((x1 - x0) * sn, 2), Item='ceil_bamboo' if mat == 'bamboo' else 'ceil_timber')


slope_ceiling('A-CL-N', RA, ABAX, AX1, 7.0, AYN, 'bamboo', 'Woven bamboo ceiling panels on battens, under rafters (photo 23)')
slope_ceiling('A-CL-S', RA, ABAX, ABX, AYS, 7.0, 'bamboo', 'Woven bamboo ceiling panels on battens, under rafters (photo 23)')
slope_ceiling('A-CL-SB', RA, ABX, AX1, ABYS, 7.0, 'bamboo', 'Woven bamboo ceiling panels on battens, under rafters (photo 23)')
add('IfcCovering', 'A-CL-BATH', 'CL', 'GF', 'A-Ceiling', box(AX0, ABAX, ABAY, AYN, A_WTOP - 0.02, A_WTOP, 'ceiling_wr'),
    Description='Moisture-resistant board ceiling, bathroom', Area_m2=round((ABAX - AX0) * (AYN - ABAY), 2), Item='ceil_wr')
for nm, x0, x1, y0, y1 in (('C-CL-1', CX0, CXE, CYS, CYN), ('C-CL-2', CXE, CXB, CYM, CYN), ('C-CL-3', CXM, CXE, CYB2, CYS)):
    add('IfcCovering', nm, 'CL', 'GF', 'A-Ceiling', box(x0, x1, y0, y1, C_WTOP - 0.02, C_WTOP, 'timber'),
        Description='Timber T&G board ceiling at plate level', Area_m2=round((x1 - x0) * (y1 - y0), 2), Item='ceil_timber')

# ================================================================== MEP: WATER SUPPLY / DRAINAGE (ASSUMED layout - needs MEP design)
MEP_NOTE = 'MEP layout ASSUMED for estimating - design by a licensed engineer'


def run(name, mark, tag, pts, d, mat, item, desc, level='FND', **kw):
    parts = [I.bar(pts[i], pts[i + 1], max(d, 0.03), max(d, 0.03), mat) for i in range(len(pts) - 1)]
    ln = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    add('IfcPipeSegment' if tag.startswith('P-') else 'IfcCableCarrierSegment', name, mark, level, tag, parts,
        Description=desc, Length_m=round(ln, 2), Item=item, Note=MEP_NOTE, **kw)


def things(ifc, name, mark, tag, pts, size, mat, item, desc, level='GF', **kw):
    """a group of identical small fixtures at points (x, y, z) - z is the centre"""
    sx, sy, sz = size
    parts = [box(x - sx / 2, x + sx / 2, y - sy / 2, y + sy / 2, z - sz / 2, z + sz / 2, mat) for x, y, z in pts]
    add(ifc, name, mark, level, tag, parts, Description=desc, Count=len(pts), Item=item, Note=MEP_NOTE, **kw)


def drum(ifc, name, mark, tag, x, y, r, z0, z1, mat, item, desc, level='GF', **kw):
    add(ifc, name, mark, level, tag, I.poly([(a, b, z0) for a, b in octagon(x, y, r)], (0, 0, 1), z1 - z0, mat),
        Description=desc, Count=1, Item=item, Note=MEP_NOTE, **kw)


TANK = D_F.p(8.6, 1.0, 0)[:2]                      # east of store room 2, on the drive side
PUMP = D_F.p(8.6, 2.3, 0)[:2]
UTIL = (23.5, -15.2)                               # PEA meter pole + PWA water meter at the road (ASSUMED south)
WZ, DZ, EZ = -0.45, -0.60, -0.65                    # buried depths: water, drain start, power

things('IfcFlowMeter', 'P-METER', 'WM', 'P-Water', [(UTIL[0] + 0.6, UTIL[1], 0.35)], (0.35, 0.25, 0.30), 'equip', 'p_meter',
       'Water meter 1/2" + gate valve + check valve in box (PWA connection)')
run('P-SUP-MAIN', 'PE', 'P-Water', [(UTIL[0] + 0.6, UTIL[1], WZ), (24.6, -8.0, WZ), (TANK[0], TANK[1], WZ), (TANK[0], TANK[1], 0.1)],
    0.032, 'pipe_water', 'pe25', 'HDPE PN10 dia 25 mm buried supply, meter -> tank')
drum('IfcTank', 'P-TANK', 'TK', 'P-Water', TANK[0], TANK[1], 0.62, 0.15, 1.75, 'tank', 'p_tank',
     'Polyethylene water tank 2,000 L on 0.15 concrete pad')
things('IfcPump', 'P-PUMP', 'PU', 'P-Water', [(PUMP[0], PUMP[1], 0.35)], (0.45, 0.35, 0.45), 'equip', 'p_pump',
       'Constant-pressure booster pump 300 W + pressure tank, roofed housing')
run('P-SUP-A', 'PPR', 'P-Water', [(PUMP[0], PUMP[1], 0.3), (PUMP[0], PUMP[1], WZ), (16.0, -2.5, WZ), (10.0, 2.8, WZ), (1.5, 2.8, WZ),
    (1.5, 8.2, WZ), (1.5, 8.2, FFL + 0.5)], 0.032, 'pipe_water', 'ppr25', 'PPR PN20 dia 25 mm cold water main pump -> A bathroom')
run('P-SUP-A2', 'PPR', 'P-Water', [(8.0, 2.8, WZ), (8.0, 9.55, WZ), (8.0, 9.55, FFL + 0.5)], 0.025, 'pipe_water', 'ppr20',
    'PPR PN20 dia 20 mm branch to pantry sink')
run('P-SUP-C', 'PPR', 'P-Water', [(PUMP[0], PUMP[1], WZ), (24.2, -1.0, WZ), (26.0, -1.0, WZ), (26.0, 0.6, WZ), (26.0, 0.6, FFL + 0.5)],
    0.032, 'pipe_water', 'ppr25', 'PPR PN20 dia 25 mm cold water main pump -> C bathroom 2')
run('P-SUP-C1', 'PPR', 'P-Water', [(26.0, -1.0, WZ), (28.8, -1.0, WZ), (28.8, 6.4, WZ), (28.8, 6.4, FFL + 0.5)], 0.032, 'pipe_water',
    'ppr25', 'PPR PN20 dia 25 mm cold water C bathroom 1 + tub deck')
run('P-HOT', 'PPR', 'P-Water', [(0.15, 8.4, FFL + 1.5), (0.15, 8.4, FFL + 2.0)], 0.025, 'pipe_hot', 'ppr20h',
    'PPR PN20 dia 20 mm hot water heater -> shower (x3 bathrooms, 3 m each)', level='GF', Count=3)
things('IfcFlowTerminal', 'P-YARD-TAPS', 'YT', 'P-Water', [(PUMP[0] + 0.4, PUMP[1], 0.6), (17.11, 5.6, 0.6), (-1.2, 6.0, 0.6)],
       (0.08, 0.08, 0.6), 'equip', 'p_yard', 'Garden tap on post (garage, pergola, A west)')
add('IfcSanitaryTerminal', 'A-SHOWER', 'SH', 'GF', 'P-Sanitary', box(0.10, 0.20, 7.80, 8.00, FFL + 1.9, FFL + 2.1, 'sanitary'),
    Description='Rain shower set + mixer', Count=1, Item='san_shower')
add('IfcSanitaryTerminal', 'C-SHOWERS', 'SH', 'GF', 'P-Sanitary', [box(29.35, 29.45, 7.4, 7.6, FFL + 1.9, FFL + 2.1, 'sanitary'),
    box(27.36, 27.46, 1.4, 1.6, FFL + 1.9, FFL + 2.1, 'sanitary')], Description='Rain shower set + mixer', Count=2, Item='san_shower')
add('IfcSanitaryTerminal', 'A-SINK', 'SK', 'GF', 'P-Sanitary', [box(7.20, 9.20, 9.20, 9.80, FFL, FFL + 0.85, 'counter'),
    box(7.80, 8.40, 9.30, 9.70, FFL + 0.70, FFL + 0.86, 'sanitary')], Description='Pantry counter 2.0 m + stainless sink', Count=1,
    Item='san_sink')
things('IfcFlowTerminal', 'P-FD', 'FD', 'P-Drain', [(1.0, 8.0, FFL + 0.01), (28.3, 8.2, FFL + 0.01), (26.0, 1.2, FFL + 0.01), (30.0, 7.0, DECK)],
       (0.12, 0.12, 0.02), 'equip', 'p_fd', 'Floor drain 4" stainless, with trap')
# drainage: WC -> septic tank -> soak pit; grey water -> chamber -> soak pit; pantry -> grease trap
run('P-DR-A-WC', 'PVC', 'P-Drain', [(0.49, 9.4, FFL), (0.49, 9.4, DZ), (0.5, 10.6, DZ - 0.03), (1.0, 11.6, DZ - 0.05)], 0.11,
    'pipe_drain', 'pvc100', 'PVC class 8.5 dia 100 mm soil pipe, slope 1:50')
run('P-DR-A-GW', 'PVC', 'P-Drain', [(1.5, 9.5, FFL), (1.5, 9.5, DZ + 0.1), (1.0, 8.0, DZ + 0.1), (1.6, 10.6, DZ), (3.5, 11.8, DZ - 0.1)],
    0.06, 'pipe_drain', 'pvc55', 'PVC class 8.5 dia 55 mm waste (basin, shower, floor drain)')
run('P-DR-A-K', 'PVC', 'P-Drain', [(8.1, 9.5, FFL), (8.1, 9.5, DZ + 0.1), (8.1, 10.9, DZ), (3.5, 11.8, DZ - 0.15)], 0.08,
    'pipe_drain', 'pvc80', 'PVC class 8.5 dia 80 mm pantry -> grease trap -> soak pit')
run('P-DR-C1', 'PVC', 'P-Drain', [(29.1, 8.99, FFL), (29.1, 8.99, DZ), (29.1, 10.6, DZ - 0.03), (29.8, 11.5, DZ - 0.05)], 0.11,
    'pipe_drain', 'pvc100', 'PVC class 8.5 dia 100 mm soil pipe, slope 1:50')
run('P-DR-C2', 'PVC', 'P-Drain', [(24.94, 0.7, FFL), (24.94, 0.7, DZ), (24.94, -0.6, DZ - 0.03), (25.5, -1.8, DZ - 0.05)], 0.11,
    'pipe_drain', 'pvc100', 'PVC class 8.5 dia 100 mm soil pipe, slope 1:50')
run('P-DR-C-GW', 'PVC', 'P-Drain', [(28.0, 6.5, DZ + 0.1), (28.3, 8.2, DZ + 0.1), (28.6, 10.6, DZ), (31.5, 11.5, DZ - 0.1)], 0.06, 'pipe_drain', 'pvc55', 'PVC dia 55 mm waste C bathroom 1 + tub deck')
run('P-DR-C2-GW', 'PVC', 'P-Drain', [(27.1, 0.55, DZ + 0.1), (26.0, 1.2, DZ + 0.1), (26.0, -0.6, DZ), (27.0, -2.0, DZ - 0.1)], 0.06,
    'pipe_drain', 'pvc55', 'PVC dia 55 mm waste C bathroom 2')
run('P-DR-EFF', 'PVC', 'P-Drain', [(1.6, 11.6, DZ - 0.3), (3.5, 11.8, DZ - 0.3)], 0.11, 'pipe_drain', 'pvc100',
    'PVC dia 100 mm septic effluent -> soak pit (x3 tanks, ~2 m each)', Count=3)
things('IfcDistributionChamberElement', 'P-IC', 'IC', 'P-Drain', [(0.5, 10.6, -0.25), (1.6, 10.6, -0.25), (29.1, 10.6, -0.25),
       (28.6, 10.6, -0.25), (24.94, -0.6, -0.25), (26.0, -0.6, -0.25)], (0.5, 0.5, 0.6), 'concrete', 'p_ic',
       'Inspection chamber 0.50 x 0.50 precast + cover', level='FND')
things('IfcInterceptor', 'P-GT', 'GT', 'P-Drain', [(8.1, 10.9, -0.2)], (0.6, 0.4, 0.5), 'tank', 'p_gt', 'Grease trap 30 L, buried with lid', level='FND')
for nm, (x, y) in (('A', (1.6, 11.6)), ('C1', (29.8, 11.5)), ('C2', (25.5, -1.8))):
    drum('IfcTank', 'P-ST-' + nm, 'ST', 'P-Drain', x, y, 0.62, -1.75, 0.05, 'tank', 'p_septic',
         'Precast septic tank 1,600 L (anaerobic + aerobic), buried', level='FND')
for nm, (x, y) in (('A', (3.5, 11.8)), ('C1', (31.5, 11.5)), ('C2', (27.0, -2.0))):
    drum('IfcTank', 'P-SP-' + nm, 'SP', 'P-Drain', x, y, 0.6, -2.0, -0.2, 'gravel', 'p_soak',
         'Soak pit dia 1.20 x 1.80, concrete rings + gravel', level='FND')

# ================================================================== MEP: ELECTRICAL (ASSUMED layout - needs electrical design)
MDB = D_F.p(6.95, 1.6, 0)[:2]                      # inside store room 2, east wall
CUA = (2.16, 8.5)                                  # living side of bathroom partition
CUC = (21.64, 5.0)                                 # C west wall, inside
add('IfcElectricDistributionPoint', 'E-POLE', 'MP', 'GF', 'E-Power', [I.bar((UTIL[0], UTIL[1], -1.0), (UTIL[0], UTIL[1], 6.0), 0.18, 0.18, 'concrete'),
    box(UTIL[0] - 0.2, UTIL[0] + 0.2, UTIL[1] - 0.15, UTIL[1] - 0.09, 1.4, 1.9, 'elec')],
    Description='Concrete pole 6.0 m + PEA kWh meter 15(45)A 3-phase 4-wire (ASSUMED supply)', Count=1, Item='e_meter', Note=MEP_NOTE)
things('IfcElectricDistributionPoint', 'E-MDB', 'MDB', 'E-Power', [(MDB[0], MDB[1], 1.5)], (0.45, 0.45, 0.6), 'elec', 'e_mdb',
       'MDB load centre 3-phase, main MCCB 3P 63A + RCBO, 12 ways')
things('IfcElectricDistributionPoint', 'E-CU-A', 'CU', 'E-Power', [(CUA[0], CUA[1], FFL + 1.5)], (0.08, 0.35, 0.45), 'elec', 'e_cu',
       'Consumer unit 1-phase main 63A + RCBO, 10 ways (building A)')
things('IfcElectricDistributionPoint', 'E-CU-C', 'CU', 'E-Power', [(CUC[0], CUC[1], FFL + 1.5)], (0.08, 0.35, 0.45), 'elec', 'e_cu',
       'Consumer unit 1-phase main 63A + RCBO, 12 ways (building C)')
run('E-FD-MAIN', 'UG', 'E-Power', [(UTIL[0], UTIL[1], EZ), (23.4, -8.0, EZ), (MDB[0], MDB[1], EZ), (MDB[0], MDB[1], 1.2)], 0.06, 'conduit',
    'e_fd_main', 'Main feeder NYY 4x25 mm2 in HDPE 50 mm, buried 0.65 m, sand bed + warning tape')
run('E-FD-A', 'UG', 'E-Power', [(MDB[0], MDB[1], EZ), (16.5, -2.2, EZ), (10.5, 2.5, EZ), (2.6, 2.5, EZ), (2.6, 8.5, EZ), (CUA[0], CUA[1], EZ),
    (CUA[0], CUA[1], FFL + 1.3)], 0.05, 'conduit', 'e_fd_sub16', 'Sub-feeder NYY 2x16 + G 10 mm2 in HDPE 40 mm, MDB -> CU-A')
run('E-FD-C', 'UG', 'E-Power', [(MDB[0], MDB[1], EZ), (21.0, -1.0, EZ), (21.0, 5.0, EZ), (CUC[0], CUC[1], EZ), (CUC[0], CUC[1], FFL + 1.3)],
    0.05, 'conduit', 'e_fd_sub25', 'Sub-feeder NYY 2x25 + G 16 mm2 in HDPE 40 mm, MDB -> CU-C')
run('E-FD-SITE', 'UG', 'E-Power', [(MDB[0], MDB[1], EZ), (16.0, -2.4, EZ), (13.6, -1.9, EZ), (8.4, 0.9, EZ), (4.0, 3.2, EZ),
    (17.3, 2.0, EZ), (21.0, 2.0, EZ)], 0.04, 'conduit', 'e_fd_site', 'Garden lighting NYY 3x2.5 mm2 in HDPE 25 mm')
run('E-FD-PUMP', 'UG', 'E-Power', [(MDB[0], MDB[1], EZ), (PUMP[0], PUMP[1], EZ), (PUMP[0], PUMP[1], 0.3)], 0.04, 'conduit', 'e_fd_pump',
    'Pump circuit NYY 3x2.5 mm2 in HDPE 25 mm')
things('IfcElectricDistributionPoint', 'E-EARTH', 'GR', 'E-Power', [(UTIL[0] + 0.5, UTIL[1] + 0.5, -1.4), (MDB[0], MDB[1], -1.4),
       (CUA[0] - 0.6, 11.0, -1.4), (CUC[0] - 1.3, 5.0, -1.4)], (0.02, 0.02, 2.4), 'copper', 'e_earth',
       'Ground rod copper-clad 5/8" x 2.4 m + test box', level='FND')

# lighting (points; z = fixture centre)
zA = lambda y: under(RA, y) - 0.05
things('IfcLightFixture', 'E-L-A-PEND', 'LP', 'E-Lighting', [(4.3, 7.55, FFL + 2.15), (5.1, 7.55, FFL + 2.15), (5.9, 7.55, FFL + 2.15)],
       (0.5, 0.5, 0.12), 'light', 'l_pend', 'Pendant (paper shade) LED E27 12 W, over dining (photo 23)', Circuit='A-L1')
things('IfcLightFixture', 'E-L-A-DL', 'LD', 'E-Lighting', [(x, y, zA(y)) for x in (2.8, 7.4, 8.8) for y in (6.4, 8.6)] +
       [(x, y, zA(y)) for x in (10.2, 11.5) for y in (6.6, 8.6)] + [(1.0, 8.0, A_WTOP - 0.05), (1.0, 9.2, A_WTOP - 0.05)],
       (0.12, 0.12, 0.06), 'light', 'l_down', 'LED downlight 9 W 3000K recessed in bamboo ceiling', Circuit='A-L1')
things('IfcLightFixture', 'E-L-A-WALL', 'LW', 'E-Lighting', [(x + 0.12, AYV, 2.45) for x in (AX0, ABAX, 4.425, 6.875)] +
       [(-0.05, 7.0, 2.45), (ABX - 0.08, 4.8, 2.45)], (0.1, 0.12, 0.25), 'light', 'l_wall', 'Outdoor wall/post lamp IP54 LED 7 W (photo 17)',
       Circuit='A-L2')
things('IfcLightFixture', 'E-L-C', 'LD', 'E-Lighting', [(22.8, 7.8, C_WTOP - 0.05), (25.9, 7.8, C_WTOP - 0.05), (23.0, 3.3, C_WTOP - 0.05),
       (23.0, 4.9, C_WTOP - 0.05), (26.0, 3.3, C_WTOP - 0.05), (26.0, 4.9, C_WTOP - 0.05), (28.5, 7.0, C_WTOP - 0.05), (28.5, 8.6, C_WTOP - 0.05),
       (25.5, 1.1, C_WTOP - 0.05), (26.8, 1.1, C_WTOP - 0.05)], (0.12, 0.12, 0.06), 'light', 'l_down', 'LED downlight 9 W 3000K', Circuit='C-L1')
things('IfcLightFixture', 'E-L-C-WALL', 'LW', 'E-Lighting', [(21.9, CYS - 0.1, 2.4), (24.2, CYS - 0.1, 2.4), (CXK + 0.18, 3.46, 2.3),
       (CXK + 0.18, CYM, 2.3), (CXK + 0.18, CYN, 2.3), (CXB + 0.08, 8.0, 2.3), (21.6, 8.6, FFL + 1.8), (24.5, 8.6, FFL + 1.8)],
       (0.1, 0.12, 0.25), 'light', 'l_wall', 'Wall lamp LED 7 W (porch, side walk, tub deck, bed heads)', Circuit='C-L2')
dl = lambda a, b, z: D_F.p(a, b, z)
things('IfcLightFixture', 'E-L-D-BAT', 'LB', 'E-Lighting', [dl(a, b, D_PLATE - 0.3) for a in (2.0, 5.9) for b in (4.5, 6.5, 8.5)],
       (0.15, 0.15, 0.08), 'light', 'l_batten', 'LED batten 1.2 m 18 W IP65 (garage, on cross beams)', level='GF', Circuit='D-L1')
things('IfcLightFixture', 'E-L-D-IN', 'LD', 'E-Lighting', [dl(1.45, 1.7, RZ1 - 0.05), dl(5.45, 1.7, RZ1 - 0.05), dl(3.3, 1.7, RZ1 - 0.05)],
       (0.12, 0.12, 0.06), 'light', 'l_down', 'LED downlight / linear light (store rooms, corridor - Rungkit11)', Circuit='D-L1')
things('IfcLightFixture', 'E-L-D-FL', 'LF', 'E-Lighting', [dl(7.9, 3.4, 2.4), dl(7.9, 8.0, 2.4)], (0.2, 0.15, 0.15), 'light', 'l_flood',
       'LED floodlight 30 W IP65 with photocell (drive)', Circuit='D-L2')
ux, uy = (13.95 - 3.98), (-1.68 - 3.62)
ul = math.hypot(ux, uy)
bol = [(3.98 + ux * t - uy / ul * 0.6, 3.62 + uy * t + ux / ul * 0.6, 0.35) for t in (0.1, 0.4, 0.7, 0.95)]
bol += [(18.0, 2.0, 0.35), (20.0, 2.0, 0.35), (16.2, 5.8, 0.35), (16.2, 9.2, 0.35)]
things('IfcLightFixture', 'E-L-SITE', 'LG', 'E-Lighting', bol, (0.12, 0.12, 0.7), 'light', 'l_bollard', 'Garden bollard LED 5 W IP65, 0.70 h',
       Circuit='MDB-SITE')
things('IfcLightFixture', 'E-L-PG', 'LS', 'E-Lighting', [(14.72, 5.81, 2.3), (17.11, 5.81, 2.3), (19.51, 5.81, 2.3)], (0.15, 0.15, 0.2),
       'light', 'l_wall', 'Pergola post lamp IP54 LED 7 W', Circuit='MDB-SITE')
# sockets / switches / equipment
sock = lambda pts: [(x, y, FFL + 0.35) for x, y in pts]
things('IfcOutlet', 'E-S-A', 'SO', 'E-Power', sock([(2.2, 6.0), (2.2, 7.0), (4.425, 9.75), (6.875, 9.75), (9.33, 6.2), (9.33, 8.9), (7.5, 9.7),
       (8.9, 9.7), (9.55, 9.75), (12.2, 6.0), (12.2, 8.8), (1.9, 9.75)]), (0.08, 0.08, 0.12), 'elec', 'e_sock',
       'Duplex socket 16A with earth, conduit EMT/PVC 20 mm + THW 2.5 mm2 (avg 8 m/point)', Circuit='A-S1/S2')
things('IfcOutlet', 'E-S-C', 'SO', 'E-Power', sock([(21.64, 3.0), (24.49, 4.0), (21.64, 7.6), (22.4, 9.33), (24.0, 9.33), (27.46, 7.6), (26.0, 9.33),
       (27.46, 3.0), (27.46, 5.2), (24.69, 2.6), (28.0, 6.2), (25.2, 0.3)]), (0.08, 0.08, 0.12), 'elec', 'e_sock',
       'Duplex socket 16A with earth', Circuit='C-S1/S2')
things('IfcOutlet', 'E-S-D', 'SO', 'E-Power', [dl(a, b, 0.5) for a, b in ((0.25, 4.0), (0.25, 8.0), (2.65, 1.0), (4.0, 2.4), (7.75, 5.0), (7.75, 9.0))],
       (0.08, 0.08, 0.12), 'elec', 'e_sock', 'Duplex socket 16A with earth, surface conduit', Circuit='D-S1')
things('IfcOutlet', 'E-S-EXT', 'SW', 'E-Power', [(-0.05, 9.0, FFL + 0.6), (14.72, 2.3, 0.6), (CXB + 0.08, 7.4, FFL + 0.6)], (0.1, 0.1, 0.14),
       'elec', 'e_sock_ip', 'Weatherproof socket IP55 with RCD', Circuit='A-S2/MDB-SITE/C-S2')
things('IfcSwitchingDevice', 'E-SW', 'SW', 'E-Lighting', [(2.15, 5.7, FFL + 1.2), (2.15, 7.1, FFL + 1.2), (9.33, 5.6, FFL + 1.2),
       (9.53, 6.7, FFL + 1.2), (1.9, 7.4, FFL + 1.2), (0.1, 6.9, FFL + 1.2), (9.33, 4.2, FFL + 1.2), (21.64, 4.9, FFL + 1.2), (22.9, 6.2, FFL + 1.2),
       (24.69, 5.8, FFL + 1.2), (27.46, 6.9, FFL + 1.2), (26.9, 2.13, FFL + 1.2), (22.1, 2.13, FFL + 1.2), (29.45, 7.8, FFL + 1.2),
       (21.64, 3.5, FFL + 1.2), dl(2.65, 1.4, 1.3), dl(4.0, 1.6, 1.3), dl(7.75, 3.6, 1.3), dl(0.25, 3.6, 1.3)], (0.08, 0.04, 0.12), 'elec',
       'e_switch', 'Light switch 1-2 gang, avg 6 m conduit + THW 1.5 mm2 to fixtures')
things('IfcElectricAppliance', 'E-WH', 'WH', 'E-Power', [(0.12, 8.4, FFL + 1.6), (29.45, 8.6, FFL + 1.6), (27.46, 1.2, FFL + 1.6)],
       (0.1, 0.25, 0.4), 'equip', 'e_wh', 'Instant water heater 4,500 W + 2P 32A RCBO circuit THW 6 mm2', Circuit='A-WH/C-WH1/C-WH2')
things('IfcUnitaryEquipment', 'E-AC-IN', 'AC', 'E-Power', [(11.0, AYN - 0.15, 2.45), (23.0, CYN - 0.15, 2.4), (CXE - 0.15, 4.0, 2.4)],
       (0.8, 0.22, 0.28), 'equip', 'e_ac', 'Split AC 12,000 BTU inverter (fan coil), circuit 20A THW 4 mm2 + pipe set 4 m', Circuit='A-AC/C-AC1/C-AC2')
things('IfcUnitaryEquipment', 'E-AC-OUT', 'CDU', 'E-Power', [(11.0, AYN + 0.6, 0.4), (26.0, CYN + 0.55, 0.4), (CXE + 0.55, 4.0, 0.4)],
       (0.7, 0.3, 0.55), 'equip', 'e_ac_cdu', 'AC condensing unit on concrete pad')


# ------------------------------------------------------------------ output
MATS = {
    'timber': [150, 96, 58, 1.0], 'timber_dark': [104, 68, 42, 1.0], 'timber_v': [140, 92, 56, 1.0], 'deck': [158, 102, 62, 1.0],
    'roof_sheet': [178, 182, 184, 1.0], 'concrete': [190, 188, 182, 1.0], 'concrete_floor': [206, 202, 194, 1.0],
    'plaster': [232, 228, 218, 1.0], 'glass': [159, 195, 210, 0.35], 'frame_alu': [150, 152, 150, 1.0],
    'gabion': [132, 122, 108, 1.0], 'stone': [150, 140, 126, 1.0], 'gravel': [196, 190, 176, 1.0], 'ground': [126, 160, 92, 1.0],
    'sanitary': [250, 250, 250, 1.0], 'trunk': [96, 78, 60, 1.0], 'leaf': [96, 146, 74, 0.55],
    'pipe_water': [40, 110, 200, 1.0], 'pipe_hot': [200, 60, 50, 1.0], 'pipe_drain': [140, 140, 150, 1.0], 'conduit': [235, 125, 35, 1.0],
    'elec': [210, 210, 205, 1.0], 'light': [255, 214, 90, 1.0], 'equip': [236, 236, 236, 1.0], 'tank': [40, 80, 140, 1.0],
    'copper': [184, 115, 51, 1.0], 'bamboo': [196, 170, 120, 1.0], 'ceiling_wr': [240, 240, 236, 1.0], 'counter': [120, 116, 112, 1.0]}


def rb(v):
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, str):
        return ':' + v if v in ('box', 'poly', 'bar') else json.dumps(v, ensure_ascii=False)
    if isinstance(v, (int, float)):
        return repr(round(v, 4)) if isinstance(v, float) else str(v)
    if isinstance(v, (list, tuple)):
        return '[' + ','.join(rb(x) for x in v) + ']'
    if isinstance(v, dict):
        return '{' + ', '.join('%s=>%s' % (json.dumps(k, ensure_ascii=False), rb(x)) for k, x in v.items()) + '}'
    raise TypeError(v)


HEADER = '''# encoding: utf-8
# =============================================================================
#  BaanSaoYongHin_BIM.rb  -  บ้านเสายงหิน (กลุ่มอาคารไม้ชั้นเดียว)  โมเดล BIM (SketchUp Ruby)  v0.1
#  แหล่งข้อมูล: BAAN_SAO_YONG_HIN.rar — ผังบริเวณมีสเกล 10 ม. (24.6 px/ม.), ตารางประตู D01-D20,
#               ตารางหน้าต่าง W01-W12 (ไม้เก่า ขนาดจริง), ภาพ axonometric ประตู-หน้าต่าง, ภาพถ่ายอาคารจริง
#  ตำแหน่งในผังวัดจากแบบที่มีสเกล (±0.2 ม.) ; ความสูง/ความชันหลังคา/ขนาดโครงสร้าง ประมาณจากภาพถ่าย
#  อาคาร A : ห้องนั่งเล่น-รับประทานอาหาร + ห้องนอน + ห้องน้ำ, หลังคาจั่ว 30°, ระเบียงไม้ด้านใต้, ระแนงไม้
#  อาคาร C : ห้องนอน 2 ห้อง + ห้องน้ำ 2 ห้อง, หลังคาจั่วคู่ (45° / 30°), ชานอ่างอาบน้ำกลางแจ้ง
#  อาคาร D : โรงจอดรถ + ห้องเก็บของ 2 ห้อง (หมุน 26°), หลังคาจั่วยกระดับ (ช่องแสง), ระแนงไม้สูงเต็มจั่ว, กำแพงกาเบียน
#  P       : ซุ้มเสาไม้บนฐานหิน, ชานไม้แนวทแยง, ทางเดินไม้
#  วัสดุ: ไม้เก่า (reclaimed), หลังคาลอนกระเบื้องไฟเบอร์ซีเมนต์สีเทา, พื้นปูนขัดมัน, ผนังฉาบขาวบางส่วน
#  โครงสร้าง/ฐานรากเป็นขนาดสมมติ (ยังไม่ได้ออกแบบ) — ต้องให้สถาปนิก/วิศวกรตรวจและกำหนดขนาดจริง
#  รวม %d องค์ประกอบ  ทุกชิ้นเป็น Group: IFC 2x3 classification + attribute 'BSY_BIM' + Tag
#
#  วิธีใช้ (Window > Ruby Console):
#      load 'C:/path/BaanSaoYongHin_BIM.rb'
#      BaanSaoYongHinBIM.build                        # สร้างโมเดล (ลบของเดิมที่สคริปต์นี้สร้าง)
#      BaanSaoYongHinBIM.build(only: [:structure])    # :structure / :architecture / :mep / :site
#      BaanSaoYongHinBIM.report                       # ปริมาณงาน + ตารางประตูหน้าต่าง
#      BaanSaoYongHinBIM.export_csv('C:/temp/bsy')    # _qto.csv และ _schedule.csv
#      BaanSaoYongHinBIM.clashes                      # ตรวจชน (bounding box)
#      BaanSaoYongHinBIM.show(:structure)             # :structure / :architecture / :mep / :site / :all
#      BaanSaoYongHinBIM.validate                     # ตรวจข้อมูล DATA (ใช้นอก SketchUp ได้)
#      BaanSaoYongHinBIM.diag
#
#  หน่วย = เมตร ; X ตะวันออก (ขวาของผัง) ; Y เหนือ (บนของผัง) ; Z ขึ้น, ดิน ±0.00 ; พื้นอาคาร A/C +0.45
#  สร้างจาก make_model.py — แก้ขนาดที่นั่นแล้วรัน python3 make_model.py ใหม่
# =============================================================================
module BaanSaoYongHinBIM
  # reload-safe: remove old constants so repeated load does not spam "already initialized constant"
  constants.each { |c| remove_const(c) }
  @ifc_ok = nil
  NAME   = 'Baan Sao Yong Hin BIM'
  SCHEMA = 'IFC 2x3'
'''


def main():
    names = [e[1] for e in E]
    dup = {n for n in names if names.count(n) > 1}
    assert not dup, dup
    engine = open(ENGINE_SRC, encoding='utf-8').read()
    tail = engine[engine.index('  # ---------------------------------------------------------------- helpers'):]
    tail = tail.replace('SSHBIM', 'BaanSaoYongHinBIM').replace("'SSH_", "'BSY_").replace('"SSH_', '"BSY_') \
               .replace('Sound Studio House BIM', 'Baan Sao Yong Hin BIM')
    assert 'SSH' not in tail, re.findall(r'.{20}SSH.{20}', tail)
    out = [HEADER % len(E)]
    out.append('  MATS = {\n' + ',\n'.join('    %s=>%s' % (json.dumps(k), rb(v)) for k, v in MATS.items()) + '\n  }\n')
    out.append("  STOREYS = { 'FND'=>'Foundation (below ±0.00)', 'GF'=>'Ground floor (FFL +0.45, garage +0.12)', 'ROOF'=>'Roof' }\n")
    out.append("  NON_RC_MATS = %w[timber timber_dark timber_v stone].freeze   # timber posts/beams/rafters, boulder footings: not RC\n")
    out.append("  DISC = { structure: /\\AS-/, architecture: /\\AA-/, mep: /\\A[PE]-/, site: /\\ASite\\z/ }\n\n")
    out.append('  # [ifc, name, mark, level, tag, parts, attrs]\n'
               '  #  part: [:box, x0,x1,y0,y1,z0,z1, mat] | [:poly, [[x,y,z]..], [nx,ny,nz], thick, mat] | [:bar, p1, p2, b, h, mat]\n  DATA = [\n')
    out.append(',\n'.join('    ' + rb(e) for e in E) + '\n  ]\n\n')
    out.append(tail)
    with open(os.path.join(HERE, 'BaanSaoYongHin_BIM.rb'), 'w', encoding='utf-8') as f:
        f.write(''.join(out))
    with open(os.path.join(HERE, 'model.js'), 'w', encoding='utf-8') as f:
        f.write('window.MODEL = ')
        json.dump({'name': 'Baan Sao Yong Hin BIM', 'mats': MATS, 'elements': [
            {'ifc': e[0], 'name': e[1], 'mark': e[2], 'level': e[3], 'tag': e[4], 'parts': e[5], 'attrs': e[6]} for e in E]},
            f, ensure_ascii=False, separators=(',', ':'))
        f.write(';\n')
    # reclaimed door / window catalogue: every schedule item + where it is used in the model
    with open(os.path.join(HERE, 'door_window_schedule.csv'), 'w', encoding='utf-8') as f:
        f.write('Mark,Type,Width_m,Height_m,Pieces,PlacedIn\n')
        for m in sorted(SCHED):
            h, w, n = SCHED[m]
            f.write('%s,%s,%.2f,%.2f,%d,%s\n' % (m, 'Door' if m[0] == 'D' else 'Window', w, h, n, ' '.join(PLACED.get(m, [])) or '(spare - not placed)'))
    print('elements:', len(E), ' parts:', sum(len(e[5]) for e in E), ' schedule items placed:', len(PLACED), '/', len(SCHED))


if __name__ == '__main__':
    main()
