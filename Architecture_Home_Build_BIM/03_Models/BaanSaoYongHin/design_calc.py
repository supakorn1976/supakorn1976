# -*- coding: utf-8 -*-
"""
Baan Sao Yong Hin - preliminary design calculations from the BIM model.

Part 1  Foundations: column loads by tributary area (roof, ceilings, walls, beams sampled from the model and
        given to the nearest supporting post), RC pad footings, RC stumps, grade beams, wind uplift and the
        post-to-stump anchor, deck piers.  ACI 318-19 (SI) strength design, as adopted by EIT (วสท.).
Part 2  Electrical: connected load and demand per circuit, phase balance, breakers, cables, voltage drop,
        meter and main breaker.  EIT wiring standard (วสท. 2001) approach, values flagged as to be checked.

Writes design/design_results.json (read by make_model.py and boq.py) and design/design_report.pdf.
Run order: python3 make_model.py && python3 design_calc.py && python3 make_model.py && python3 boq.py
(or python3 run_all.py).  Every input that is an assumption is listed in ASSUME and printed in the report.

These are preliminary calculations for estimating and coordination. A licensed civil engineer (ภาคีวิศวกรโยธา
or higher) and electrical engineer must check, complete and sign the design. There is NO soil data: the
allowable bearing pressure is an assumption that a soil test or plate load test must confirm.
"""
import importlib.util
import json
import math
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'design')
_spec = importlib.util.spec_from_file_location('mm', os.path.join(HERE, 'make_model.py'))
mm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mm)
E = mm.E

# ------------------------------------------------------------------ assumptions (all in SI: kN, m, kPa, MPa)
ASSUME = {
    'qa_kPa': 100.0,          # allowable bearing at -1.20 m (no soil test - ASSUMED, typical stiff clay / sandy clay)
    'Df_m': 1.20,             # footing base level below ground
    'gamma_soil': 18.0,       # kN/m3
    'gamma_conc': 24.0,
    'fc_MPa': 23.5,           # f'c 240 ksc (cylinder)
    'fy_MPa': 392.0,          # SD40 deformed bars
    'fyt_MPa': 235.0,         # SR24 round bars (ties, stirrups)
    'cover_ftg_m': 0.075,
    'roof_sheet_kPa': 0.17,   # corrugated fibre-cement sheet + hooks, on slope
    'timber_kN_m3': 9.0,      # reclaimed hardwood (teng / rang) ~ 900 kg/m3
    'aac_wall_kN_m3': 11.7,   # 0.12 AAC + 2 x 15 mm plaster = 1.4 kPa
    'roof_LL_kPa': 0.30,      # roof live load 30 kg/m2 (Thai Ministerial Regulation)
    'deck_DL_kPa': 0.60, 'deck_LL_kPa': 3.0,   # balcony / veranda 300 kg/m2
    'slab_edge_strip_m': 0.50,  # slab-on-grade edge resting on the grade beam
    'floor_finish_kPa': 1.0, 'floor_LL_kPa': 1.5,
    'V50_m_s': 25.0,          # basic wind speed, wind zone 1 (DPT 1311-50)
    'rho_air': 1.25, 'Ce': 0.9,
    'CgCp_net_enclosed': -1.6,  # roof uplift incl. internal suction, buildings A and C
    'CgCp_net_open': -2.0,      # open garage D (large openings)
}
A_ = ASSUME
BAR = {'DB12': (12, 113.1, 0.888), 'DB16': (16, 201.1, 1.578), 'RB6': (6, 28.3, 0.222), 'RB9': (9, 63.6, 0.499)}


# ------------------------------------------------------------------ geometry helpers
def plan_pts(p):
    if p[0] == 'box':
        return [(p[1], p[3]), (p[2], p[3]), (p[2], p[4]), (p[1], p[4])]
    if p[0] == 'bar':
        return [tuple(p[1][:2]), tuple(p[2][:2])]
    return [tuple(q[:2]) for q in p[1]]


def vol(p):
    if p[0] == 'box':
        return (p[2] - p[1]) * (p[4] - p[3]) * (p[6] - p[5])
    if p[0] == 'bar':
        return math.dist(p[1], p[2]) * p[3] * p[4]
    s = [0.0, 0.0, 0.0]
    pts = p[1]
    for i, a in enumerate(pts):
        b = pts[(i + 1) % len(pts)]
        s[0] += a[1] * b[2] - a[2] * b[1]; s[1] += a[2] * b[0] - a[0] * b[2]; s[2] += a[0] * b[1] - a[1] * b[0]
    return math.sqrt(sum(v * v for v in s)) / 2 * p[3]


def inside(x, y, poly):
    c = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def area2(poly):
    return abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))) / 2


def samples_area(poly, step=0.25):
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    out = []
    x = min(xs) + step / 2
    while x < max(xs):
        y = min(ys) + step / 2
        while y < max(ys):
            if inside(x, y, poly):
                out.append((x, y))
            y += step
        x += step
    return out


def samples_line(p, step=0.5):
    """points along the longest plan extent of a part (walls, beams, bars)"""
    pts = plan_pts(p)
    best = max(((a, b) for a in pts for b in pts), key=lambda ab: math.dist(*ab))
    n = max(1, math.ceil(math.dist(*best) / step))
    return [(best[0][0] + (best[1][0] - best[0][0]) * (i + 0.5) / n, best[0][1] + (best[1][1] - best[0][1]) * (i + 0.5) / n) for i in range(n)]


def locate(x, y):
    if -1.3 <= x <= 13.2 and 3.0 <= y <= 12.6:
        return 'A'
    if 20.0 <= x <= 32.5 and -2.6 <= y <= 12.5:
        return 'C'
    dx, dy = x - mm.D_F.o[0], y - mm.D_F.o[1]
    a = dx * mm.D_F.u[0] + dy * mm.D_F.u[1]
    b = dx * mm.D_F.v[0] + dy * mm.D_F.v[1]
    if -1.3 <= a <= 12.5 and -1.5 <= b <= 11.5:
        return 'D'
    return 'S'


def centroid(p):
    pts = plan_pts(p)
    return sum(q[0] for q in pts) / len(pts), sum(q[1] for q in pts) / len(pts)


# ================================================================== PART 1  FOUNDATIONS
byname = {e[1]: e for e in E}
POSTS = []                                  # name, x, y, bld, top_z, bottom_z, timber volume
for e in E:
    if e[0] == 'IfcColumn' and e[2] == 'TC':
        p = e[5][0]
        x, y = centroid(p)
        if p[0] == 'box':
            z0, z1 = p[5], p[6]
        else:
            z0, z1 = p[1][0][2], p[1][0][2] + p[3]
        POSTS.append(dict(name=e[1], x=x, y=y, bld=locate(x, y), z0=z0, z1=z1, vol=vol(p), D=0.0, L=0.0, W_up=0.0,
                          src=defaultdict(float)))
by_bld = defaultdict(list)
for q in POSTS:
    by_bld[q['bld']].append(q)


def nearest(x, y, bld, roof=False):
    cand = [q for q in by_bld[bld] if not roof or q['z1'] >= 2.4]
    return min(cand, key=lambda q: (q['x'] - x) ** 2 + (q['y'] - y) ** 2)


# roofs: weight per roof key spread over its plan area, live load and wind uplift on plan
roof_keys = defaultdict(lambda: {'plan': [], 'slope_area': 0.0, 'members': 0.0, 'bld': None})
for e in E:
    nm = e[1]
    if e[0] == 'IfcRoof':
        key = nm.split('-')[1]
        poly = plan_pts(e[5][0])
        roof_keys[key]['plan'].append(poly)
        roof_keys[key]['slope_area'] += e[6]['SlopeArea_m2']
        roof_keys[key]['bld'] = locate(*centroid(e[5][0]))
    elif nm.split('-')[0] in ('PU', 'RA', 'RB') and e[4] == 'S-RoofTimber':
        roof_keys[nm.split('-')[1]]['members'] += sum(vol(p) for p in e[5]) * A_['timber_kN_m3']
roof_keys['DU']['members'] += sum(vol(p) for p in byname['D-MONITOR-POSTS'][5]) * A_['timber_kN_m3']
q_wind = 0.5 * A_['rho_air'] * A_['V50_m_s'] ** 2 / 1000 * A_['Ce']           # kPa
ROOFS = []
for key, r in roof_keys.items():
    plan = sum(area2(p) for p in r['plan'])
    W = r['slope_area'] * A_['roof_sheet_kPa'] + r['members']
    dl = W / plan
    up = q_wind * (A_['CgCp_net_open'] if r['bld'] == 'D' else A_['CgCp_net_enclosed'])
    ROOFS.append(dict(key=key, bld=r['bld'], plan=round(plan, 2), W=round(W, 2), dl=round(dl, 3), wind=round(up, 3)))
    step = 0.25
    for poly in r['plan']:
        for x, y in samples_area(poly, step):
            q = nearest(x, y, r['bld'], roof=True)
            a = step * step
            q['D'] += dl * a; q['L'] += A_['roof_LL_kPa'] * a; q['W_up'] += up * a
            q['src']['roof'] += dl * a

# walls, gables, screens, doors/windows, timber beams, ceilings -> nearest post of the building
DENS = {'plaster': A_['aac_wall_kN_m3'], 'glass': 25.0, 'frame_alu': 27.0}
for e in E:
    ifc, nm, mark, lvl, tag, parts, at = e
    take = (ifc in ('IfcWall', 'IfcDoor', 'IfcWindow', 'IfcCovering') and nm != 'D-GABION') or tag == 'A-Screen' or \
           (ifc == 'IfcBeam' and mark == 'TB') or (ifc == 'IfcColumn' and mark == 'TC')
    if not take:
        continue
    for p in parts:
        w = vol(p) * DENS.get(p[-1], A_['timber_kN_m3'])
        if ifc == 'IfcColumn':
            byname_post = next(q for q in POSTS if q['name'] == nm)
            byname_post['D'] += w; byname_post['src']['post'] += w
            continue
        sp = samples_line(p)
        bld = locate(*centroid(p))
        if bld not in by_bld:
            continue
        for x, y in sp:
            q = nearest(x, y, bld)
            q['D'] += w / len(sp); q['src']['walls/beams'] += w / len(sp)

# ---------------- pad footing design (ACI 318-19 SI)
fc, fy, fyt = A_['fc_MPa'], A_['fy_MPa'], A_['fyt_MPa']
sfc = math.sqrt(fc)
COL = 0.20                                   # RC stump section


def design_footing(Ps, Pu, B, h=0.25):
    d = h - A_['cover_ftg_m'] - 0.012                     # m, average for two layers
    Wf = B * B * h * A_['gamma_conc'] + COL * COL * (A_['Df_m'] - h) * A_['gamma_conc'] + \
        (B * B - COL * COL) * (A_['Df_m'] - h) * A_['gamma_soil']
    q = (Ps + Wf) / (B * B)
    qu = Pu / (B * B)                                     # net factored pressure (self weight cancels)
    bo = 4 * (COL + d)
    Vp = qu * (B * B - (COL + d) ** 2)
    phiVp = 0.75 * 0.33 * sfc * bo * d * 1000            # kN
    Lp = (B - COL) / 2
    V1 = qu * B * max(0.0, Lp - d)
    phiV1 = 0.75 * 0.17 * sfc * B * d * 1000
    Mu = qu * B * Lp ** 2 / 2                              # kN.m
    Rn = Mu / (0.9 * B * d * d * 1000)                     # MPa
    rho = 0.85 * fc / fy * (1 - math.sqrt(max(0.0, 1 - 2 * Rn / (0.85 * fc))))
    As_req = rho * B * d * 1e6
    As_min = 0.0018 * B * h * 1e6
    As = max(As_req, As_min)
    n = max(4, math.ceil(As / BAR['DB12'][1]))
    s = (B - 2 * A_['cover_ftg_m']) / (n - 1)
    if s > min(3 * h, 0.45):
        n = math.ceil((B - 2 * A_['cover_ftg_m']) / min(3 * h, 0.45)) + 1
        s = (B - 2 * A_['cover_ftg_m']) / (n - 1)
    ldh = max(fy / (23 * sfc) * 12 ** 1.5, 8 * 12, 150) / 1000          # ACI 318-19 25.4.3.1 (SI)
    avail = Lp - A_['cover_ftg_m']
    ok = q <= A_['qa_kPa'] and Vp <= phiVp and V1 <= phiV1 and ldh <= avail
    bar_len = B - 2 * A_['cover_ftg_m'] + 2 * 0.15                      # 90 deg hooks up 0.15
    kg = 2 * n * bar_len * BAR['DB12'][2]
    return dict(B=B, h=h, d=round(d, 3), q=round(q, 1), qu=round(qu, 1), Vp=round(Vp, 1), phiVp=round(phiVp, 1),
                V1=round(V1, 1), phiV1=round(phiV1, 1), Mu=round(Mu, 2), As_req=round(As_req), As_min=round(As_min),
                bars='%d-DB12 @%.2f each way, 90° hooks' % (n, s), n=n, ldh=round(ldh, 3), ld_avail=round(avail, 3),
                kg=round(kg, 1), ok=ok)


Wd = {}
for q in POSTS:
    P_D, P_L = q['D'], q['L']
    q['Ps'] = P_D + P_L
    q['Pu'] = max(1.2 * P_D + 1.6 * P_L, 1.4 * P_D)
    B = 0.60
    while True:
        r = design_footing(q['Ps'], q['Pu'], B)
        if r['ok'] or B > 2.0:
            break
        B = round(B + 0.10, 2)
    q['ftg'] = r
# group into a few footing types (largest required size, min 0.70 for construction)
TYPES = [0.70, 0.80, 0.90, 1.00, 1.20, 1.50]
for q in POSTS:
    B = next(t for t in TYPES if t >= q['ftg']['B'] - 1e-9)
    q['ftg'] = design_footing(q['Ps'], q['Pu'], B)
    q['ftype'] = 'F%d' % (TYPES.index(B) + 1)

# ---------------- RC stump (short tied column 0.20 x 0.20)
for q in POSTS:
    st = byname.get('ST-' + q['name'])                     # stump as modelled: top of footing (-0.95) to post base
    p = st[5][0] if st else None
    hs = (p[6] - p[5]) if p and p[0] == 'box' else (p[3] if p else 0.0)
    Ag = COL * COL * 1e6
    Ast = 4 * BAR['DB12'][1]
    phiPn = 0.8 * 0.65 * (0.85 * fc * (Ag - Ast) + fy * Ast) / 1000
    Pu_st = q['Pu'] + 1.2 * COL * COL * hs * A_['gamma_conc']
    r_g = 0.3 * COL
    lu = min(hs, 0.30 + 0.95)                            # braced by grade beams / slab-on-grade at +0.30 (non-sway)
    klr = 1.0 * lu / r_g
    ties = math.ceil(hs / 0.15) + 1
    kg = 4 * (hs + 0.30 + 0.20) * BAR['DB12'][2] + ties * (4 * 0.14 + 0.10) * BAR['RB9'][2]
    q['stump'] = dict(h=round(hs, 2), Pu=round(Pu_st, 1), phiPn=round(phiPn, 0), rho=round(Ast / Ag, 4), klr=round(klr, 1),
                      bars='4-DB12, ties RB9 @0.15 (135° hooks)', kg=round(kg, 1), lu=round(lu, 2), ok=Pu_st <= phiPn and klr <= 34)

# ---------------- wind uplift + post anchorage
for q in POSTS:
    up = -q['W_up']                                       # kN, positive upward
    resist = 0.9 * (q['D'] + q['ftg']['B'] ** 2 * q['ftg']['h'] * A_['gamma_conc'] +
                    COL * COL * q['stump']['h'] * A_['gamma_conc'] +
                    (q['ftg']['B'] ** 2 - COL * COL) * (A_['Df_m'] - q['ftg']['h']) * A_['gamma_soil'])
    net_conn = max(0.0, 1.0 * up - 0.9 * q['D'])          # tension in the post-to-stump connection
    q['uplift'] = dict(Wup=round(up, 2), resist=round(resist, 2), conn_T=round(net_conn, 2), ok=resist >= 1.0 * up)
# anchorage: 2 steel side plates 6 mm cast into the stump, 2 through-bolts M12 in double shear.
# allowable lateral load per M12 bolt, hardwood parallel to grain with steel side plates ~ 6.0 kN (to be confirmed for the species)
BOLT_ALLOW = 6.0
max_T = max(q['uplift']['conn_T'] for q in POSTS)
ANCHOR = dict(detail='2 steel plates 6x60x300 mm (cast 150 mm into stump) + 2 through-bolts M12 (galvanised)',
              capacity=2 * BOLT_ALLOW, max_T=round(max_T, 2), ok=max_T <= 2 * BOLT_ALLOW)

# ---------------- grade beams 0.20 x 0.40 (continuous over footings)
def phiMn(As, d, b=0.20):
    a = As * fy / (0.85 * fc * b * 1000)                # mm
    return 0.9 * As * fy * (d * 1000 - a / 2) / 1e6     # kN.m


GB = []
for gname in ('A-GB', 'C-GB'):
    e = byname[gname]
    for i, p in enumerate(e[5]):
        x0, x1, y0, y1 = p[1], p[2], p[3], p[4]
        along_x = (x1 - x0) >= (y1 - y0)
        c = (y0 + y1) / 2 if along_x else (x0 + x1) / 2
        lo, hi = (x0, x1) if along_x else (y0, y1)
        L = hi - lo
        on = sorted([(q['x'] if along_x else q['y']) for q in POSTS
                     if abs((q['y'] if along_x else q['x']) - c) < 0.15 and lo - 0.2 <= (q['x'] if along_x else q['y']) <= hi + 0.2])
        span = max([b - a for a, b in zip(on, on[1:])] or [L])
        # wall weight on this line
        ww = 0.0
        for w in E:
            if w[0] in ('IfcWall', 'IfcDoor', 'IfcWindow') and w[1] != 'D-GABION' and not w[1].startswith(('A-GB-', 'C-GB-')):
                for pp in w[5]:
                    cx, cy = centroid(pp)
                    if abs((cy if along_x else cx) - c) < 0.15 and lo - 0.1 <= (cx if along_x else cy) <= hi + 0.1:
                        ww += vol(pp) * DENS.get(pp[-1], A_['timber_kN_m3'])
        wD = ww / L + 0.2 * 0.4 * A_['gamma_conc'] + A_['slab_edge_strip_m'] * (0.15 * A_['gamma_conc'] + A_['floor_finish_kPa'])
        wL = A_['slab_edge_strip_m'] * A_['floor_LL_kPa']
        wu = 1.2 * wD + 1.6 * wL
        d = 0.40 - 0.04 - 0.009 - 0.006
        Mu = wu * span ** 2 / 10
        Vu = 1.15 * wu * span / 2
        Rn = Mu / (0.9 * 0.2 * d * d * 1000)
        rho = 0.85 * fc / fy * (1 - math.sqrt(max(0.0, 1 - 2 * Rn / (0.85 * fc))))
        As_min = max(0.25 * sfc / fy, 1.4 / fy) * 0.2 * d * 1e6
        As = max(rho * 0.2 * d * 1e6, As_min)
        n = max(2, math.ceil(As / BAR['DB12'][1]))
        phiVc = 0.75 * 0.17 * sfc * 0.2 * d * 1000
        stir = 'RB6 @0.15' if Vu <= phiVc else 'RB6 @0.10'
        kg = (2 * n) * (L + 2 * 0.30) * BAR['DB12'][2] * 1.05 + math.ceil(L / 0.15) * (2 * (0.14 + 0.34) + 0.10) * BAR['RB6'][2]
        GB.append(dict(name='%s/%d' % (gname, i), L=round(L, 2), span=round(span, 2), w_wall=round(ww / L, 2), wD=round(wD, 2), wL=round(wL, 2),
                       wu=round(wu, 2), Mu=round(Mu, 2), Vu=round(Vu, 2), phiVc=round(phiVc, 1), As=round(As), As_min=round(As_min),
                       bars='%d-DB12 top + %d-DB12 bottom, stirrups %s' % (n, n, stir), kg=round(kg, 1),
                       phiMn=round(phiMn(n * BAR['DB12'][1], d), 2), ok=Mu <= phiMn(n * BAR['DB12'][1], d) and Vu <= 2 * phiVc))

# ---------------- deck piers 0.20 x 0.20 on 0.40 x 0.40 x 0.15 pads, grid ~1.5 m
pier_trib = 1.5 * 1.5
P_pier = pier_trib * (A_['deck_DL_kPa'] + A_['deck_LL_kPa']) + 0.2 * 0.2 * 0.7 * 24 + 0.4 * 0.4 * 0.15 * 24
PIER = dict(trib=pier_trib, P=round(P_pier, 2), q=round(P_pier / 0.16, 1), ok=P_pier / 0.16 <= A_['qa_kPa'],
            note='pad 0.40 x 0.40 x 0.15 at -0.60 m; bearing q = P / 0.16 m2')

# ================================================================== PART 2  ELECTRICAL LOAD
V1P, V3P = 230.0, 400.0
fx = {}                                       # fixture element -> (count, watts each, circuit)
W_FIX = {'l_pend': 12, 'l_down': 9, 'l_wall': 7, 'l_batten': 18, 'l_flood': 30, 'l_bollard': 5}
LIGHT_CIRC = {'E-L-A-PEND': 'A-L1', 'E-L-A-DL': 'A-L1', 'E-L-A-WALL': 'A-L2', 'E-L-C': 'C-L1', 'E-L-C-WALL': 'C-L2',
              'E-L-D-BAT': 'D-L1', 'E-L-D-IN': 'D-L1', 'E-L-D-FL': 'D-L2', 'E-L-SITE': 'SITE-L', 'E-L-PG': 'SITE-L'}
circ = defaultdict(lambda: dict(kind='', va=0.0, n=0, pts=[], cu=''))
for e in E:
    nm, at = e[1], e[6]
    if nm in LIGHT_CIRC:
        c = circ[LIGHT_CIRC[nm]]
        c['kind'] = 'lighting'; c['va'] += at['Count'] * W_FIX[at['Item']] / 0.9; c['n'] += at['Count']
        c['pts'] += [centroid(p) for p in e[5]]
sock = {'E-S-A': ['A-S1', 'A-S2'], 'E-S-C': ['C-S1', 'C-S2'], 'E-S-D': ['D-S1']}
for nm, cs in sock.items():
    e = byname[nm]
    for i, p in enumerate(e[5]):
        c = circ[cs[i * len(cs) // len(e[5])]]
        c['kind'] = 'receptacle'; c['va'] += 180; c['n'] += 1; c['pts'].append(centroid(p))
ext = byname['E-S-EXT']
for p, cn in zip(ext[5], ('A-S2', 'SITE-S', 'C-S2')):
    c = circ[cn]; c['kind'] = 'receptacle'; c['va'] += 180; c['n'] += 1; c['pts'].append(centroid(p))
for p, cn in zip(byname['E-WH'][5], ('A-WH', 'C-WH1', 'C-WH2')):
    c = circ[cn]; c['kind'] = 'water heater'; c['va'] = 4500; c['n'] = 1; c['pts'] = [centroid(p)]
for p, cn in zip(byname['E-AC-IN'][5], ('A-AC', 'C-AC1', 'C-AC2')):
    c = circ[cn]; c['kind'] = 'air conditioner'; c['va'] = 1250; c['n'] = 1; c['pts'] = [centroid(p)]
c = circ['PUMP']; c['kind'] = 'motor'; c['va'] = 300 / 0.8 / 0.75; c['n'] = 1; c['pts'] = [centroid(byname['P-PUMP'][5][0])]
CU_POS = {'CU-A': centroid(byname['E-CU-A'][5][0]), 'CU-C': centroid(byname['E-CU-C'][5][0]), 'MDB': centroid(byname['E-MDB'][5][0])}
for k, c in circ.items():
    c['cu'] = 'CU-A' if k.startswith('A-') else 'CU-C' if k.startswith('C-') else 'MDB'

# demand: lighting 100 %; receptacles 180 VA each, first 10 kVA 100 % + 50 % of the rest (whole installation);
# water heaters and air conditioners 100 % (no diversity - conservative); motor 125 % of the largest motor
rec_total = sum(c['va'] for c in circ.values() if c['kind'] == 'receptacle')
rec_factor = (min(rec_total, 10000) + 0.5 * max(0.0, rec_total - 10000)) / rec_total if rec_total else 1
for k, c in circ.items():
    c['demand'] = c['va'] * (rec_factor if c['kind'] == 'receptacle' else 1.25 if c['kind'] == 'motor' else 1.0)

STD_CB = [10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125]
THW = [(2.5, 21), (4, 28), (6, 36), (10, 50), (16, 66), (25, 84)]                 # THW (60227 IEC 01) in conduit, 2 conductors, 40 C
NYY = [(4, 34), (6, 43), (10, 57), (16, 74), (25, 96), (35, 116), (50, 140)]      # NYY in buried conduit, 3 loaded conductors (approx)
R70 = {1.5: 14.48, 2.5: 8.87, 4: 5.52, 6: 3.69, 10: 2.19, 16: 1.38, 25: 0.870, 35: 0.627, 50: 0.463}  # ohm/km copper at 70 C
EG = [(20, 2.5), (32, 4), (63, 10), (100, 16), (200, 25)]                         # equipment grounding conductor by breaker (to check)


def pick_cb(I, min_cb=16):
    return next(s for s in STD_CB if s >= max(I, min_cb))


def pick_cable(table, I_cb, min_mm2=2.5):
    return next(mm2 for mm2, amp in table if amp >= I_cb and mm2 >= min_mm2)


def vd(I, L, mm2, three=False):
    return (math.sqrt(3) * I * L * R70[mm2] / 1000 / V3P if three else 2 * I * L * R70[mm2] / 1000 / V1P) * 100


CIRCUITS = []
for k in sorted(circ):
    c = circ[k]
    I = c['demand'] / V1P
    cont = c['kind'] in ('water heater', 'air conditioner', 'motor')
    cb = pick_cb(I * (1.25 if cont else 1.0), 16 if c['kind'] != 'water heater' else 32)
    if c['kind'] == 'lighting':
        cb = 16
    mm2 = pick_cable(THW, cb)
    if c['kind'] in ('lighting', 'receptacle') and k.startswith(('SITE', 'PUMP')):
        mm2 = max(mm2, 2.5)
    cx, cy = CU_POS[c['cu']]
    Lmax = max(abs(x - cx) + abs(y - cy) for x, y in c['pts']) * 1.15 + 3.0
    drop = vd(I, Lmax, mm2)
    rcd = c['kind'] in ('water heater', 'receptacle') or k.startswith(('SITE', 'PUMP')) or k in ('A-L2', 'C-L2', 'D-L2')
    CIRCUITS.append(dict(id=k, cu=c['cu'], kind=c['kind'], n=c['n'], va=round(c['va']), demand=round(c['demand']),
                         I=round(I, 1), cb=cb, rcd=rcd, cable='THW 2x%g + G %g mm2' % (mm2, next(g for lim, g in EG if cb <= lim)) if not k.startswith(('SITE', 'PUMP')) else 'NYY 3x%g mm2' % max(mm2, 2.5),
                         mm2=mm2, L=round(Lmax, 1), vd=round(drop, 2)))

# phase balance: CU-A is single phase (whole board on one phase); CU-C becomes 3-phase so its circuits spread;
# MDB local circuits spread. Greedy, largest first.
ph = {'L1': 0.0, 'L2': 0.0, 'L3': 0.0}
for ci in CIRCUITS:
    if ci['cu'] == 'CU-A':
        ci['phase'] = 'L1'; ph['L1'] += ci['demand']
for ci in sorted([c for c in CIRCUITS if c['cu'] != 'CU-A'], key=lambda c: -c['demand']):
    p = min(ph, key=ph.get)
    ci['phase'] = p; ph[p] += ci['demand']
IPH = {p: round(v / V1P, 1) for p, v in ph.items()}
I_max = max(IPH.values())


def feeder(name, cu, length, three):
    rows = [c for c in CIRCUITS if c['cu'] == cu]
    perph = defaultdict(float)
    for c in rows:
        perph[c['phase']] += c['demand']
    I = max(perph.values()) / V1P
    cb = pick_cb(I * 1.0, 32)
    mm2 = pick_cable(NYY, cb, 10)
    drop = vd(I, length, mm2, three)
    while drop > 2.5 and mm2 < 50:
        mm2 = next(m for m, _ in NYY if m > mm2)
        drop = vd(I, length, mm2, three)
    g = next(gg for lim, gg in EG if cb <= lim)
    return dict(name=name, to=cu, three_phase=three, demand_kVA=round(sum(perph.values()) / 1000, 2), I=round(I, 1), cb=cb,
                cable=('NYY 4x%g + G %g mm2' % (mm2, g)) if three else ('NYY 2x%g + G %g mm2' % (mm2, g)), mm2=mm2, ground=g,
                conduit='HDPE %d mm' % (50 if mm2 >= 25 else 40), L=round(length, 1), vd=round(drop, 2))


FEEDERS = [feeder('E-FD-A', 'CU-A', byname['E-FD-A'][6]['Length_m'], False),
           feeder('E-FD-C', 'CU-C', byname['E-FD-C'][6]['Length_m'], True)]
total_demand = sum(c['demand'] for c in CIRCUITS)
main_cb = pick_cb(I_max, 32)
meter = '15(45)A 3-phase 4-wire' if main_cb <= 40 else '30(100)A 3-phase 4-wire'
main_mm2 = pick_cable(NYY, main_cb, 16)
main_vd = vd(I_max, byname['E-FD-MAIN'][6]['Length_m'], main_mm2, True)
MAIN = dict(total_connected_kVA=round(sum(c['va'] for c in CIRCUITS) / 1000, 2), total_demand_kVA=round(total_demand / 1000, 2),
            receptacle_factor=round(rec_factor, 3), phase_A=IPH, I_max=I_max, main_cb='3P %dA + RCBO/RCD 100 mA (MDB)' % main_cb,
            meter=meter, cable='NYY 4x%g mm2 in HDPE 50 mm' % main_mm2, mm2=main_mm2, L=byname['E-FD-MAIN'][6]['Length_m'],
            vd=round(main_vd, 2), ground_conductor='THW 10 mm2 to ground rod (main <= 35 mm2)', imbalance=round((max(ph.values()) - min(ph.values())) / max(ph.values()) * 100, 1))
worst_total_vd = max(MAIN['vd'] + next((f['vd'] for f in FEEDERS if f['to'] == c['cu']), 0) + c['vd'] for c in CIRCUITS)
MAIN['worst_total_vd'] = round(worst_total_vd, 2)

# ================================================================== results
FOOT_TYPES = {}
for q in POSTS:
    t = q['ftype']
    f = q['ftg']
    cur = FOOT_TYPES.setdefault(t, dict(B=f['B'], h=f['h'], bars=f['bars'], count=0, maxP=0.0, kg=f['kg']))
    cur['count'] += 1
    cur['maxP'] = round(max(cur['maxP'], q['Ps']), 1)
RES = dict(
    assumptions=ASSUME,
    roofs=ROOFS,
    footings={'F-' + q['name']: dict(post=q['name'], bld=q['bld'], type=q['ftype'], P_D=round(q['D'], 1), P_L=round(q['L'], 1),
                                     Ps=round(q['Ps'], 1), Pu=round(q['Pu'], 1), **q['ftg'], stump=q['stump'], uplift=q['uplift'])
              for q in POSTS},
    footing_types=FOOT_TYPES, anchor=ANCHOR, grade_beams=GB, deck_pier=PIER,
    electrical=dict(circuits=CIRCUITS, feeders=FEEDERS, main=MAIN),
)
all_ok = all(q['ftg']['ok'] and q['stump']['ok'] and q['uplift']['ok'] for q in POSTS) and ANCHOR['ok'] and PIER['ok'] and all(g['ok'] for g in GB)
RES['all_structural_checks_ok'] = all_ok
os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, 'design_results.json'), 'w', encoding='utf-8') as f:
    json.dump(RES, f, ensure_ascii=False, indent=1, default=str)

if __name__ == '__main__':
    print('roofs:', [(r['key'], r['dl'], r['wind']) for r in ROOFS], ' q_wind %.3f kPa' % q_wind)
    for q in sorted(POSTS, key=lambda q: -q['Ps'])[:6]:
        print('%-12s %s D=%.1f L=%.1f Ps=%.1f Pu=%.1f %s B=%.2f q=%.1f up=%.2f res=%.1f' % (
            q['name'], q['bld'], q['D'], q['L'], q['Ps'], q['Pu'], q['ftype'], q['ftg']['B'], q['ftg']['q'], q['uplift']['Wup'], q['uplift']['resist']))
    print('footing types:', FOOT_TYPES)
    print('anchor:', ANCHOR)
    print('GB:', [(g['name'], g['span'], g['w_wall'], g['Mu'], g['bars']) for g in GB])
    print('pier:', PIER)
    print('electrical main:', MAIN)
    for f in FEEDERS:
        print('feeder:', f)
    for c in CIRCUITS:
        print('  %-7s %-5s %-15s n=%2d %5dVA I=%5.1f %s CB%dA %s L=%.0f vd=%.2f%%' % (c['id'], c['cu'], c['kind'], c['n'], c['demand'], c['I'], c['phase'], c['cb'], c['cable'], c['L'], c['vd']))
    print('ALL STRUCTURAL CHECKS OK' if all_ok else 'SOME CHECKS FAIL')
