# -*- coding: utf-8 -*-
"""
Modern House -> IngeTrazo build package (AI Bridge / MCP).

Reads model.js (written by make_model.py) and writes ingetrazo/:
  mcp_call.py        stdio client for ingetrazo-mcp.exe (stops at the first error)
  build_house.json   staged run_python calls: setup, FND, GF, 1F, ROOF, tag + export, screenshot
  build_house.ps1    one-click runner for Windows (checks port 4763 first)

Every box part becomes one IngeTrazo group made with extrude(), one layer per BIM tag.
The house is shifted by (OX, OY) so it does not sit on the 1.70 m "Engineer" scale figure.
Run:  python3 make_ingetrazo.py
"""
import json, os
from collections import OrderedDict, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'ingetrazo')
OX, OY = 2.0, 2.0
STAGES = [('FND', 'ฐานราก + ตอม่อ'), ('GF', 'ชั้น 1'), ('1F', 'ชั้น 2'), ('ROOF', 'หลังคา')]
# classes IngeTrazo can export (bim.IFC_CLASSES); anything else stays an untagged group
IFC_OK = {'IfcWall', 'IfcSlab', 'IfcColumn', 'IfcBeam', 'IfcFooting', 'IfcRoof', 'IfcStair', 'IfcRamp',
          'IfcDoor', 'IfcWindow', 'IfcRailing', 'IfcCovering', 'IfcPile', 'IfcMember', 'IfcSpace'}
IFC_MAP = {'IfcCurtainWall': 'IfcWindow'}
DEST = r'~\Documents\IngeTrazo_ModernHouse'
BASE = 'HOME-ARC-ALL-MODEL-R01'

with open(os.path.join(HERE, 'model.js'), encoding='utf-8') as f:
    s = f.read()
model = json.loads(s[s.index('{'):s.rindex('}') + 1])
mats = model['mats']

rows = defaultdict(list)          # level -> [name, ifc, tag, x0, x1, y0, y1, z0, z1, r, g, b, a]
for e in model['elements']:
    ifc = IFC_MAP.get(e['ifc'], e['ifc'])
    ifc = ifc if ifc in IFC_OK else ''
    lv = e['level'] if e['level'] in dict(STAGES) else 'GF'
    n = len(e['parts'])
    for i, p in enumerate(e['parts']):
        _, x0, x1, y0, y1, z0, z1, m = p
        r, g, b, a = mats[m]
        name = 'MH_' + e['name'] + ('' if n == 1 else '#%d' % (i + 1))
        rows[lv].append([name, ifc, e['tag'], round(x0 + OX, 4), round(x1 + OX, 4), round(y0 + OY, 4),
                         round(y1 + OY, 4), z0, z1, round(r / 255, 3), round(g / 255, 3), round(b / 255, 3), a])

SETUP = r'''
from core.layers import Layer
assert not any(getattr(g, 'name', '').startswith('MH_') for g in groups), 'MH_ groups already exist: undo or delete them first'
_MH = {'n0': len(groups), 'done': 0}
print('setup ok, existing groups:', _MH['n0'])
'''

STAGE = r'''
from core.layers import Layer, assign_layer
assert len(groups) == _MH['n0'] + _MH['done'], ('group count changed', len(groups), _MH['n0'] + _MH['done'])
_vol = 0.0
for _name, _ifc, _tag, x0, x1, y0, y1, z0, z1, r, g_, b, a in _rows:
    _g = extrude([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0, z1, name=_name, color=(r, g_, b, 1.0))
    if a < 1.0:
        _g.material = {"color": (r, g_, b), "opacity": a}
    _L = None
    for _l in layers:
        if getattr(_l, 'name', None) == _tag:
            _L = _l
    if _L is None:
        _L = Layer(_tag); layers.append(_L)
    assign_layer(_g, _L)
    _vol += (x1 - x0) * (y1 - y0) * (z1 - z0)
_MH['done'] += len(_rows)
assert len(groups) == _MH['n0'] + _MH['done'], ('extrude did not add one group per box', len(groups))
print('groups +%d (total %d), box volume %.3f m3' % (len(_rows), len(groups), _vol))
'''

FINAL = r'''
import os, json, collections
from pathlib import Path
from formats import igz, ifc as _ifc
from core.scene import Scene
mine = [g for g in groups if getattr(g, 'name', '').startswith('MH_')]
assert len(mine) == _MH['done'], (len(mine), _MH['done'])
CLS = {r[0]: r[1] for r in _MH_ALL}
n_tag = 0
for g in mine:
    if CLS.get(g.name):
        bim.tag_group(g, CLS[g.name], g.name[3:]); n_tag += 1
print('tagged', n_tag, 'of', len(mine))
tot = collections.defaultdict(lambda: [0, 0.0])
for o in bim.collect_objects(scene):
    t = tot[o['class']]; t[0] += 1; t[1] += o['volume'] or 0.0
for k in sorted(tot):
    print('  %%-14s %%4d  %%8.3f m3' %% (k, tot[k][0], tot[k][1]))
dest = os.path.expanduser(r'%(DEST)s')
os.makedirs(dest, exist_ok=True)
base = os.path.join(dest, '%(BASE)s')
igz.save_scene(scene, Path(base + '.igz'))
chk = Scene(); igz.load_into(chk, Path(base + '.igz'))
print('igz reload groups:', len(chk.groups) if hasattr(chk, 'groups') else '?', 'live:', len(groups))
print('ifc elements:', _ifc.save_ifc(scene, base + '.ifc', project_name='Modern House BIM'))
open(base + '_quantities.csv', 'w', encoding='utf-8-sig').write(bim.quantities_csv(scene))
dump = []
for g in mine:
    P = [v.position for v in g.mesh.vertices]
    dump.append({'name': g.name, 'ifc': CLS.get(g.name, ''), 'layer': getattr(layer_of(g), 'name', None),
                 'min': [min(p.x() for p in P), min(p.y() for p in P), min(p.z() for p in P)],
                 'max': [max(p.x() for p in P), max(p.y() for p in P), max(p.z() for p in P)]})
json.dump(dump, open(base + '_elements.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('saved to', dest)
viewport.camera.target = QVector3D(%(CX)s, %(CY)s, 3.0)
viewport.camera.distance = 32.0
viewport.camera.yaw = 0.75
viewport.camera.pitch = 0.45
viewport.update()
''' % {'DEST': DEST, 'BASE': BASE, 'CX': OX + 5.0, 'CY': OY + 6.2}

calls = [{'tool': 'query_model', 'args': {}},
         {'tool': 'run_python', 'args': {'code': SETUP}}]
all_rows = []
for lv, label in STAGES:
    code = '# Modern House stage %s: %s\n_rows = %s\n%s' % (
        lv, label, json.dumps(rows[lv], ensure_ascii=False), STAGE)
    calls.append({'tool': 'run_python', 'args': {'code': code}})
    all_rows += rows[lv]
calls.append({'tool': 'run_python', 'args': {'code': 'from core.layers import layer_of\n_MH_ALL = %s\n%s' % (
    json.dumps([[r[0], r[1]] for r in all_rows], ensure_ascii=False), FINAL)}})
calls.append({'tool': 'query_model', 'args': {}})
calls.append({'tool': 'screenshot', 'args': {'width': 1400, 'height': 900}, 'save': 'modern_house.png'})

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, 'build_house.json'), 'w', encoding='utf-8') as f:
    json.dump(calls, f, ensure_ascii=False, indent=1)

vol = sum((r[4] - r[3]) * (r[6] - r[5]) * (r[8] - r[7]) for r in all_rows)
print('parts per stage:', OrderedDict((lv, len(rows[lv])) for lv, _ in STAGES))
print('groups %d, tagged %d, box volume %.3f m3' % (len(all_rows), sum(1 for r in all_rows if r[1]), vol))
