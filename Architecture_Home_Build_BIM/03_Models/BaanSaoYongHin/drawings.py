# -*- coding: utf-8 -*-
"""
Baan Sao Yong Hin - 2D drawing set (A3 landscape, vector PDF) drawn from the BIM model and design results.

  S-01  แปลนฐานราก (foundation plan, 1:150)
  S-02  แบบขยายฐานราก F1 / ตอม่อ / คานคอดิน / รอยต่อเสาไม้-ตอม่อ (1:20, 1:10)
  S-03  รูปตัดโครงหลังคาไม้ + ตารางชิ้นส่วน (1:50)
  E-01  แผนผังวงจรไฟฟ้า (single line diagram)
  E-02  ตารางโหลดตู้ MDB / CU-A / CU-C
  E-03  แปลนไฟฟ้า: ดวงโคม เต้ารับ สวิตช์ ตู้ไฟ และหมายเลขวงจร (1:150)

Output: design/BaanSaoYongHin_Drawings.pdf.  Run after design_calc.py / make_model.py (run_all.py does it).
Preliminary drawings for estimating and coordination - NOT FOR CONSTRUCTION until checked and signed.
"""
import datetime as dt
import importlib.util
import json
import math
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('mmod', os.path.join(HERE, 'make_model.py'))
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)
R = json.load(open(os.path.join(HERE, 'design', 'design_results.json'), encoding='utf-8'))
BY = {e[1]: e for e in M.E}

FB = '/usr/share/fonts/truetype/tlwg/'
pdfmetrics.registerFont(TTFont('TH', FB + 'Laksaman.ttf'))
pdfmetrics.registerFont(TTFont('TH-B', FB + 'Laksaman-Bold.ttf'))
pdfmetrics.registerFont(TTFont('SYM', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
PW, PH = landscape(A3)
INK = colors.HexColor('#1e2925'); GRID = colors.HexColor('#7d8f88'); CONC = colors.HexColor('#9aa39f'); RED = colors.HexColor('#b33a2e')
WOOD = colors.HexColor('#8a5a2b'); BLUE = colors.HexColor('#2e6a8e'); LIGHT = colors.HexColor('#e8ece9'); WALL = colors.HexColor('#b7c0bb')
TODAY = dt.date.today().strftime('%d/%m/%Y')
SHEETS = []


# ------------------------------------------------------------------ sheet frame + title block
def lines_of(text, width, font, size):
    out, line = [], ''
    for w in str(text).split(' '):
        t = (line + ' ' + w).strip()
        if pdfmetrics.stringWidth(t, font, size) > width and line:
            out.append(line); line = w
        else:
            line = t
    return out + ([line] if line else [])


def frame(c, no, title, scale, note=''):
    c.setStrokeColor(INK); c.setLineWidth(0.8)
    c.rect(10 * mm, 10 * mm, PW - 20 * mm, PH - 20 * mm)
    tb_x = PW - 10 * mm - 95 * mm
    c.rect(tb_x, 10 * mm, 95 * mm, PH - 20 * mm)
    y = PH - 10 * mm
    rows = [('โครงการ', 'บ้านเสายงหิน (Baan Sao Yong Hin)', 13, True), ('', 'กลุ่มอาคารไม้ชั้นเดียว 3 หลัง + งานภายนอก', 9, False),
            ('แผ่นที่', no, 16, True), ('ชื่อแบบ', title, 11, True), ('มาตราส่วน', scale, 9.5, False), ('วันที่', TODAY, 9.5, False),
            ('ที่มา', 'สร้างจากโมเดล BIM (make_model.py) และรายการคำนวณ (design_calc.py)', 8, False)]
    for lab, val, sz, bold in rows:
        f = 'TH-B' if bold else 'TH'
        ls = lines_of(val, 70 * mm, f, sz)
        h = len(ls) * sz * 1.3 + 3 * mm
        c.setFont('TH', 8); c.setFillColor(GRID); c.drawString(tb_x + 3 * mm, y - 4.5 * mm, lab)
        c.setFont(f, sz); c.setFillColor(INK)
        for i, l in enumerate(ls):
            c.drawString(tb_x + 22 * mm, y - 1.5 * mm - sz * 1.05 - i * sz * 1.3, l)
        y -= h
        c.setStrokeColor(LIGHT); c.setLineWidth(0.5); c.line(tb_x, y, tb_x + 95 * mm, y)
    y -= 28 * mm
    c.setStrokeColor(RED); c.setFillColor(RED); c.setLineWidth(1.2)
    c.roundRect(tb_x + 6 * mm, y, 83 * mm, 24 * mm, 3 * mm)
    c.setFont('TH-B', 15); c.drawCentredString(tb_x + 47.5 * mm, y + 14 * mm, 'แบบร่างเบื้องต้น — ห้ามใช้ก่อสร้าง')
    c.setFont('TH', 9); c.drawCentredString(tb_x + 47.5 * mm, y + 6 * mm, 'จนกว่าวิศวกร/สถาปนิกผู้มีใบอนุญาตตรวจและลงนาม')
    c.setFillColor(INK); c.setStrokeColor(INK); c.setLineWidth(0.5)
    for i, who in enumerate(('สถาปนิกผู้ออกแบบ', 'วิศวกรโยธา (ภาคี/สามัญ)', 'วิศวกรไฟฟ้า (ภาคี/สามัญ)')):
        yy = 16 * mm + i * 15 * mm
        c.line(tb_x + 8 * mm, yy + 6 * mm, tb_x + 87 * mm, yy + 6 * mm)
        c.setFont('TH', 8.5); c.drawString(tb_x + 8 * mm, yy + 1.5 * mm, who + '   เลขทะเบียน ........................')
    if note:
        top, bottom = y - 6 * mm, 16 * mm + 3 * 15 * mm + 2 * mm
        size = 9.0
        while True:
            ls = lines_of('หมายเหตุ: ' + note, 87 * mm, 'TH', size)
            if len(ls) * size * 1.35 <= top - bottom or size <= 6.5:
                break
            size -= 0.5
        c.setFont('TH', size); c.setFillColor(INK)
        for i, l in enumerate(ls):
            c.drawString(tb_x + 4 * mm, top - size - i * size * 1.35, l)
    SHEETS.append((no, title))


def wrap(c, text, x, y, width, size, lead=None, font=None):
    """draws text wrapped by width (Thai has no spaces between words: split on spaces and long runs)"""
    lead = lead or size * 1.25
    fn = font or c._fontname
    words = str(text).split(' ')
    line = ''
    yy = y
    for w in words:
        t = (line + ' ' + w).strip()
        if pdfmetrics.stringWidth(t, fn, size) > width and line:
            c.drawString(x, yy, line); yy -= lead; line = w
        else:
            line = t
    if line:
        c.drawString(x, yy, line)
    return yy


def txt(c, x, y, s, size=8, bold=False, color=INK, anchor='l', font=None):
    c.setFillColor(color)
    f = font or ('TH-B' if bold else 'TH')
    c.setFont(f, size)
    parts = []
    for ch in str(s):                                  # symbols Laksaman lacks
        sym = ch in 'φ→∅⏚≤≥'
        if parts and parts[-1][0] == sym:
            parts[-1][1] += ch
        else:
            parts.append([sym, ch])
    w = sum(pdfmetrics.stringWidth(p, 'SYM' if s_ else f, size) for s_, p in parts)
    x0 = x - (w if anchor == 'r' else w / 2 if anchor == 'c' else 0)
    for s_, p in parts:
        c.setFont('SYM' if s_ else f, size if not s_ else size * 0.85)
        c.drawString(x0, y, p)
        x0 += pdfmetrics.stringWidth(p, 'SYM' if s_ else f, size if not s_ else size * 0.85)


# ------------------------------------------------------------------ plan helpers
class View:
    def __init__(self, x0, y0, xmin, ymin, scale):
        self.x0, self.y0, self.xmin, self.ymin, self.k = x0, y0, xmin, ymin, 1000 * mm / scale

    def p(self, x, y):
        return self.x0 + (x - self.xmin) * self.k, self.y0 + (y - self.ymin) * self.k


def plan_poly(part):
    if part[0] == 'box':
        return [(part[1], part[3]), (part[2], part[3]), (part[2], part[4]), (part[1], part[4])]
    if part[0] == 'poly':
        return [tuple(q[:2]) for q in part[1]]
    return [tuple(part[1][:2]), tuple(part[2][:2])]


def draw_poly(c, V, pts, stroke=INK, fill=None, lw=0.5, dash=None):
    path = c.beginPath()
    for i, (x, y) in enumerate(pts):
        px, py = V.p(x, y)
        (path.moveTo if i == 0 else path.lineTo)(px, py)
    path.close()
    c.setStrokeColor(stroke); c.setLineWidth(lw)
    c.setDash(*(dash or ()))
    if fill is not None:
        c.setFillColor(fill)
    c.drawPath(path, stroke=1, fill=1 if fill is not None else 0)
    c.setDash()


def outline_walls(c, V, color=WALL):
    for e in M.E:
        if e[0] in ('IfcWall',) and e[1] != 'D-GABION' and e[2] != 'GB':
            for p in e[5]:
                draw_poly(c, V, plan_poly(p), stroke=color, fill=None, lw=0.35)


def slab_outlines(c, V):
    for nm in ('A-SLAB', 'C-SLAB', 'D-SLAB'):
        for p in BY[nm][5]:
            draw_poly(c, V, plan_poly(p), stroke=GRID, lw=0.4, dash=(3, 2))


def centroid(p):
    pts = plan_poly(p)
    return sum(q[0] for q in pts) / len(pts), sum(q[1] for q in pts) / len(pts)


def dim(c, V, a, b, off, horiz=True, label=None):
    """dimension line between model coords a and b (scalars along x or y) at offset coordinate off"""
    if horiz:
        (x1, y1), (x2, y2) = V.p(a, off), V.p(b, off)
    else:
        (x1, y1), (x2, y2) = V.p(off, a), V.p(off, b)
    c.setStrokeColor(GRID); c.setLineWidth(0.3)
    c.line(x1, y1, x2, y2)
    for x, y in ((x1, y1), (x2, y2)):
        c.line(x - 1.2 * mm, y - 1.2 * mm, x + 1.2 * mm, y + 1.2 * mm)
    lab = label or '%.2f' % abs(b - a)
    if horiz:
        txt(c, (x1 + x2) / 2, y1 + 1.2 * mm, lab, 6.5, anchor='c', color=GRID)
    else:
        c.saveState(); c.translate(x1 - 1.2 * mm, (y1 + y2) / 2); c.rotate(90)
        txt(c, 0, 0, lab, 6.5, anchor='c', color=GRID); c.restoreState()


# ================================================================== S-01 foundation plan
def sheet_s01(c):
    frame(c, 'S-01', 'แปลนฐานราก ตอม่อ และคานคอดิน', '1 : 125',
          'ฐานรากทุกต้นแบบ F1 0.70x0.70x0.25 ม. ท้องฐานที่ระดับ -1.20 ม. จากผิวดินเดิม ; ตอม่อ 0.20x0.20 ม. ; '
          'คานคอดิน GB 0.20x0.40 ม. ; ตอม่อชาน 0.20x0.20 บนฐาน 0.40x0.40x0.15 ม. ; ฐานหินซุ้มเสา = ก้อนหินธรรมชาติ ; '
          'กำลังรับน้ำหนักดิน qa = 100 kN/ตร.ม. เป็นค่าสมมติ ต้องเจาะสำรวจดินก่อนก่อสร้าง ; ดูแบบขยายแผ่น S-02')
    V = View(24 * mm, 26 * mm, -3.0, -16.5, 125)
    slab_outlines(c, V)
    # grade beams
    for nm in ('A-GB', 'C-GB'):
        for p in BY[nm][5]:
            draw_poly(c, V, plan_poly(p), stroke=INK, fill=LIGHT, lw=0.5)
    # footings + stumps + labels
    for e in M.E:
        if e[0] == 'IfcFooting':
            for p in e[5]:
                stone = p[-1] == 'stone'
                draw_poly(c, V, plan_poly(p), stroke=INK if not stone else GRID, fill=None if not stone else LIGHT, lw=0.6 if not stone else 0.4,
                          dash=None if stone else (2, 1.2))
        if e[0] == 'IfcColumn' and e[2] == 'ST':
            for p in e[5]:
                draw_poly(c, V, plan_poly(p), stroke=INK, fill=INK, lw=0.3)
        if e[2] == 'TC' or e[2] == 'PC':
            x, y = centroid(e[5][0])
            px, py = V.p(x, y)
            if e[2] == 'TC':
                txt(c, px + 2.6 * mm, py + 2.2 * mm, 'F1', 5.5, color=INK)
        if e[1].endswith('-SUB'):
            for p in e[5]:
                if p[-1] == 'concrete':
                    draw_poly(c, V, plan_poly(p), stroke=GRID, fill=GRID, lw=0.2)
    # building labels + key dimensions
    for lab, (x, y) in (('อาคาร A', (5.5, 11.6)), ('อาคาร C', (25.3, 11.0)), ('อาคาร D (โรงจอดรถ หมุน 26°)', (19.5, -8.5)), ('ซุ้มเสา + ชานไม้', (14.5, 4.5))):
        px, py = V.p(x, y); txt(c, px, py, lab, 9, bold=True, anchor='c')
    xs = sorted(set(round(x, 3) for x in M.A_POSTS_X))
    for a, b in zip(xs, xs[1:]):
        dim(c, V, a, b, 12.9)
    dim(c, V, M.AYS, M.AYN, -1.9, horiz=False); dim(c, V, M.ABYS, M.AYS, -1.9, horiz=False)
    for a, b in ((M.CX0, M.CXM), (M.CXM, M.CXE), (M.CXE, M.CXB)):
        dim(c, V, a, b, 12.3)
    for a, b in ((M.CYB2, M.CYS), (M.CYS, M.CYM), (M.CYM, M.CYN)):
        dim(c, V, a, b, 32.2, horiz=False)
    # north arrow + scale bar
    nx, ny = V.p(-2.0, -14.0)
    c.setStrokeColor(INK); c.setFillColor(INK); c.line(nx, ny, nx, ny + 14 * mm)
    path = c.beginPath(); path.moveTo(nx, ny + 16 * mm); path.lineTo(nx - 2.5 * mm, ny + 10 * mm); path.lineTo(nx + 2.5 * mm, ny + 10 * mm); path.close()
    c.drawPath(path, fill=1, stroke=0); txt(c, nx, ny + 17.5 * mm, 'N', 9, bold=True, anchor='c')
    sx, sy = V.p(0.0, -15.6)
    for i in range(5):
        c.setFillColor(INK if i % 2 == 0 else colors.white); c.rect(sx + i * V.k * 2, sy, V.k * 2, 1.5 * mm, fill=1, stroke=1)
        txt(c, sx + i * V.k * 2, sy - 3.5 * mm, '%d' % (i * 2), 6.5, anchor='c')
    txt(c, sx + 10 * V.k, sy - 3.5 * mm, '10 ม.', 6.5, anchor='c')
    # legend
    lx, ly = 30 * mm, PH - 22 * mm
    items = [('ฐานราก F1 0.70x0.70', None, INK, (2, 1.2)), ('ตอม่อ 0.20x0.20', INK, INK, None), ('คานคอดิน GB 0.20x0.40', LIGHT, INK, None),
             ('ฐานหินซุ้มเสา', LIGHT, GRID, None), ('ขอบพื้นคอนกรีต', None, GRID, (3, 2))]
    for i, (t, fill, st, dash) in enumerate(items):
        x = lx + i * 52 * mm
        c.setStrokeColor(st); c.setDash(*(dash or ())); c.setFillColor(fill or colors.white)
        c.rect(x, ly, 6 * mm, 4 * mm, fill=1 if fill else 0, stroke=1); c.setDash()
        txt(c, x + 8 * mm, ly + 1 * mm, t, 8)


# ================================================================== S-02 details
def bar_row(c, x, y, n, span, r=1.2 * mm):
    for i in range(n):
        c.circle(x + i * span / max(1, n - 1), y, r, fill=1, stroke=0)


def sheet_s02(c):
    f = next(iter(R['footings'].values()))
    B, h = f['B'], f['h']
    frame(c, 'S-02', 'แบบขยายฐานราก F1 ตอม่อ คานคอดิน และรอยต่อเสาไม้-ตอม่อ', 'ตามระบุ (1:20 , 1:10)',
          "วัสดุ: คอนกรีต fc' 240 กก./ตร.ซม. (ทรงกระบอก) ; เหล็กข้ออ้อย SD40 ; เหล็กกลม SR24 ; ระยะหุ้ม ฐานราก 75 มม. ตอม่อ/คาน 40 มม. ; "
          'ทาบเหล็ก 40 เท่าของเส้นผ่านศูนย์กลาง ; รองพื้นทรายหยาบ 50 มม. + คอนกรีตหยาบ 50 มม. ; ถมดินคืนบดอัดเป็นชั้น ชั้นละไม่เกิน 200 มม.')
    k20 = 1000 * mm / 20
    # --- F1 plan (1:20)
    ox, oy = 40 * mm, 170 * mm
    txt(c, ox, oy + B * k20 + 12 * mm, 'แปลนฐานราก F1  มาตราส่วน 1:20', 10, bold=True)
    c.setStrokeColor(INK); c.setLineWidth(0.8); c.rect(ox, oy, B * k20, B * k20)
    c.setFillColor(LIGHT); c.rect(ox + (B - 0.2) / 2 * k20, oy + (B - 0.2) / 2 * k20, 0.2 * k20, 0.2 * k20, fill=1)
    n = f['n']; cov = 0.075 * k20
    c.setStrokeColor(RED); c.setLineWidth(0.6)
    for i in range(n):
        t = cov + i * (B * k20 - 2 * cov) / (n - 1)
        c.line(ox + cov, oy + t, ox + B * k20 - cov, oy + t); c.line(ox + t, oy + cov, ox + t, oy + B * k20 - cov)
    txt(c, ox + B * k20 + 4 * mm, oy + B * k20 / 2, f['bars'].replace(' each way, 90° hooks', ' ทั้งสองทาง'), 8.5, color=RED)
    txt(c, ox + B * k20 / 2, oy - 6 * mm, '%.2f' % B, 8, anchor='c'); txt(c, ox - 3 * mm, oy + B * k20 / 2, '%.2f' % B, 8, anchor='r')
    # --- F1 section (1:20) with stump
    sx, sy = 40 * mm, 45 * mm
    txt(c, sx, sy + 90 * mm, 'รูปตัดฐานราก F1 และตอม่อ  มาตราส่วน 1:20', 10, bold=True)
    gl = sy + 1.20 * k20                          # ground level line
    c.setStrokeColor(INK); c.setLineWidth(0.8)
    c.rect(sx, sy, B * k20, h * k20)                                    # footing
    c.rect(sx + (B - 0.2) / 2 * k20, sy + h * k20, 0.2 * k20, (1.20 - h + 0.30) * k20)   # stump to +0.30
    c.setFillColor(LIGHT); c.rect(sx - 0.10 * k20, sy - 0.10 * k20, (B + 0.2) * k20, 0.10 * k20, fill=1)   # sand + lean
    c.setStrokeColor(GRID); c.setDash(4, 2); c.line(sx - 25 * mm, gl, sx + B * k20 + 25 * mm, gl); c.setDash()
    txt(c, sx + B * k20 + 26 * mm, gl - 1 * mm, '±0.00 ผิวดินเดิม', 8)
    txt(c, sx + B * k20 + 26 * mm, sy - 1 * mm, '-1.20 ท้องฐานราก', 8)
    txt(c, sx + B * k20 + 26 * mm, sy + 1.50 * k20 - 1 * mm, '+0.30 หลังคานคอดิน / ใต้พื้น', 8)
    c.setStrokeColor(RED); c.setLineWidth(0.7)
    yb = sy + cov
    c.line(sx + cov, yb, sx + B * k20 - cov, yb)
    c.line(sx + cov, yb, sx + cov, yb + 0.15 * k20); c.line(sx + B * k20 - cov, yb, sx + B * k20 - cov, yb + 0.15 * k20)
    for xx in (sx + (B - 0.2) / 2 * k20 + 0.04 * k20, sx + (B + 0.2) / 2 * k20 - 0.04 * k20):
        c.line(xx, yb + 1 * mm, xx, sy + 1.45 * k20); c.line(xx, yb + 1 * mm, xx + (-1 if xx < sx + B * k20 / 2 else 1) * 0.25 * k20, yb + 1 * mm)
    for i in range(int((1.20 - h + 0.25) / 0.15)):
        yy = sy + h * k20 + (0.05 + i * 0.15) * k20
        c.line(sx + (B - 0.2) / 2 * k20 + 0.03 * k20, yy, sx + (B + 0.2) / 2 * k20 - 0.03 * k20, yy)
    txt(c, sx - 3 * mm, sy + h * k20 / 2, '%.2f' % h, 8, anchor='r')
    txt(c, sx + B * k20 / 2 + 0.15 * k20, sy + 0.8 * k20, 'ตอม่อ 0.20x0.20 : 4-DB12 , ปลอก RB9 @0.15', 8, color=RED)
    txt(c, sx + B * k20 / 2 + 0.15 * k20, sy + 0.70 * k20, 'เหล็กยืนงอเข้าฐาน 0.25 ม.', 8, color=RED)
    txt(c, sx, sy - 0.10 * k20 - 5 * mm, 'ทรายหยาบ 50 มม. + คอนกรีตหยาบ 50 มม.', 8)
    # --- grade beam section (1:10)
    k10 = 1000 * mm / 10
    gx, gy = 185 * mm, 175 * mm
    txt(c, gx, gy + 0.40 * k10 + 10 * mm, 'รูปตัดคานคอดิน GB 0.20x0.40  มาตราส่วน 1:10', 10, bold=True)
    c.setStrokeColor(INK); c.setLineWidth(0.8); c.rect(gx, gy, 0.20 * k10, 0.40 * k10)
    c.setStrokeColor(RED); c.rect(gx + 0.04 * k10, gy + 0.04 * k10, 0.12 * k10, 0.32 * k10)
    c.setFillColor(RED)
    gb = R['grade_beams'][0]['bars']
    nb = int(gb.split('-')[0])
    bar_row(c, gx + 0.05 * k10, gy + 0.05 * k10, nb, 0.10 * k10); bar_row(c, gx + 0.05 * k10, gy + 0.35 * k10, nb, 0.10 * k10)
    txt(c, gx + 0.20 * k10 + 5 * mm, gy + 0.35 * k10, 'บน %d-DB12' % nb, 8.5, color=RED)
    txt(c, gx + 0.20 * k10 + 5 * mm, gy + 0.05 * k10, 'ล่าง %d-DB12' % nb, 8.5, color=RED)
    txt(c, gx + 0.20 * k10 + 5 * mm, gy + 0.20 * k10, 'ปลอก RB6 @0.15', 8.5, color=RED)
    txt(c, gx + 0.10 * k10, gy - 6 * mm, '0.20', 8, anchor='c'); txt(c, gx - 3 * mm, gy + 0.2 * k10, '0.40', 8, anchor='r')
    # --- post-to-stump connection (1:10)
    px, py = 185 * mm, 50 * mm
    txt(c, px, py + 0.80 * k10 + 12 * mm, 'รอยต่อเสาไม้-ตอม่อ  มาตราส่วน 1:10', 10, bold=True)
    c.setStrokeColor(INK); c.setLineWidth(0.8)
    c.rect(px, py, 0.20 * k10, 0.30 * k10)                     # stump top
    c.setFillColor(colors.HexColor('#d9c3a5')); c.rect(px + 0.025 * k10, py + 0.32 * k10, 0.15 * k10, 0.50 * k10, fill=1)   # post
    c.setFillColor(INK)
    for xx in (px + 0.015 * k10, px + 0.175 * k10):
        c.rect(xx, py + 0.15 * k10, 0.006 * k10, 0.45 * k10, fill=1)          # steel plates
    for yy in (py + 0.42 * k10, py + 0.52 * k10):
        c.setStrokeColor(RED); c.line(px - 0.02 * k10, yy, px + 0.22 * k10, yy)
    c.setFillColor(LIGHT); c.rect(px + 0.02 * k10, py + 0.30 * k10, 0.16 * k10, 0.02 * k10, fill=1)
    notes = ['แผ่นเหล็ก 6x60x300 มม. 2 แผ่น ฝังในตอม่อ 150 มม.', 'สลักเกลียวชุบสังกะสี M12 2 ตัว ทะลุเสา', 'แผ่นรองกันชื้น (DPC) ใต้โคนเสา ไม่ให้ไม้สัมผัสคอนกรีต',
             'รับแรงยกจากลม %.1f kN ≥ แรงดึงสูงสุด %.2f kN' % (R['anchor']['capacity'], R['anchor']['max_T'])]
    for i, t in enumerate(notes):
        txt(c, px + 0.30 * k10, py + (0.62 - i * 0.07) * k10, '• ' + t, 8)
    # --- footing schedule table
    tx, ty = 40 * mm, 18 * mm
    ft = R['footing_types']
    cols = [('แบบ', 14), ('ขนาด (ม.)', 30), ('เหล็กเสริม', 62), ('จำนวน', 16), ('Ps สูงสุด (kN)', 24), ('แรงดันดินสูงสุด (kN/ตร.ม.)', 36)]
    qmax = max(v['q'] for v in R['footings'].values())
    row = [[k, '%.2fx%.2fx%.2f' % (v['B'], v['B'], v['h']), v['bars'].replace(' each way, 90° hooks', ' ทั้งสองทาง ปลายงอ 90°'), str(v['count']),
            '%.1f' % v['maxP'], '%.1f' % qmax] for k, v in ft.items()]
    table(c, tx, ty, cols, row)


def table(c, x, y, cols, rows, size=8, rh=6 * mm, head=INK):
    """table with top-left at (x, y + (len(rows)+1)*rh)"""
    W = sum(w for _, w in cols) * mm
    top = y + (len(rows) + 1) * rh
    c.setFillColor(head); c.rect(x, top - rh, W, rh, fill=1, stroke=0)
    xx = x
    for t, w in cols:
        txt(c, xx + 1.5 * mm, top - rh + 1.8 * mm, t, size, bold=True, color=colors.white)
        xx += w * mm
    for i, r in enumerate(rows):
        yy = top - (i + 2) * rh
        if i % 2:
            c.setFillColor(LIGHT); c.rect(x, yy, W, rh, fill=1, stroke=0)
        xx = x
        for (t, w), v in zip(cols, r):
            txt(c, xx + 1.5 * mm, yy + 1.8 * mm, v, size)
            xx += w * mm
    c.setStrokeColor(GRID); c.setLineWidth(0.3); c.rect(x, y, W, top - y)
    return top


# ================================================================== S-03 roof framing sections
def truss_section(c, ox, oy, k, Rf, s_a, s_b, z_plate, z_floor, title, extra=None):
    """elevation of a king-post truss across the span (model span coordinates s)"""
    s0, s1, sm = Rf.s0, Rf.s1, Rf.sm
    X = lambda s: ox + (s - s0) * k
    Y = lambda z: oy + (z - z_floor) * k
    c.setStrokeColor(INK); c.setLineWidth(1.0)
    c.line(X(s0), Y(Rf.ze), X(sm), Y(Rf.ze + Rf.run * Rf.tn)); c.line(X(sm), Y(Rf.ze + Rf.run * Rf.tn), X(s1), Y(Rf.ze))   # roof line
    c.setStrokeColor(WOOD); c.setLineWidth(2.2)
    for s in (s_a, s_b):
        c.line(X(s), Y(z_floor), X(s), Y(z_plate))                     # posts
    th = M.TS['tie'][1]
    c.line(X(s_a - 0.05), Y(z_plate + th / 2), X(s_b + 0.05), Y(z_plate + th / 2))     # tie
    if Rf.gap <= 0:
        c.line(X(sm), Y(z_plate + th), X(sm), Y(Rf.zb))                # king post
        c.setLineWidth(1.2)
        for se in (s_a, s_b):
            sx = (sm + se) / 2
            c.line(X(sm), Y(z_plate + th + 0.10), X(sx), Y(M.under(Rf, sx)))
    c.setLineWidth(1.4)
    c.line(X(s0), Y(Rf.ze - Rf.drop), X(sm), Y(Rf.ze + Rf.run * Rf.tn - Rf.drop))    # rafters (underside)
    c.line(X(sm), Y(Rf.ze + Rf.run * Rf.tn - Rf.drop), X(s1), Y(Rf.ze - Rf.drop))
    if extra:
        extra(X, Y)
    c.setStrokeColor(GRID); c.setLineWidth(0.4); c.line(X(s0) - 5 * mm, Y(z_floor), X(s1) + 5 * mm, Y(z_floor))
    txt(c, X(s0), Y(Rf.ze + Rf.run * Rf.tn) + 8 * mm, title, 9.5, bold=True)
    txt(c, X(sm) + 2 * mm, Y(Rf.zb) - 3 * mm, 'อกไก่', 7, color=WOOD)
    txt(c, X((s_a + sm) / 2), Y(z_plate + th) + 1.5 * mm, 'ขื่อ', 7, color=WOOD)
    txt(c, X(s_b) + 1.5 * mm, Y((z_floor + z_plate) / 2), 'เสา', 7, color=WOOD)
    txt(c, X(s1) - 2 * mm, Y(Rf.ze) - 4 * mm, '+%.2f' % Rf.ze, 6.5, anchor='r', color=GRID)


def sheet_s03(c):
    T = R['timber']
    frame(c, 'S-03', 'รูปตัดโครงหลังคาไม้ (ขื่อ-ดั้ง-ตะเกียบ) และตารางชิ้นส่วน', '1 : 50 , 1 : 75',
          'ไม้เนื้อแข็งเก่า (เต็ง/รัง) ไสตกแต่ง อาบน้ำยากันปลวก-เชื้อรา ; ความชื้นไม่เกิน 19% ก่อนประกอบ ; รอยต่อหลักใช้สลักเกลียวชุบสังกะสี M12 + แหวนรอง ; '
          'ยึดจันทันกับอะเสด้วยเหล็กรัดกันลมยกทุกตัว ; ค้ำยันทแยงในผนัง 50x100 แนวละ 2 ตัว ; ขนาดชิ้นส่วนจากรายการคำนวณ (design_report.pdf หัวข้อ 9)')
    k = 1000 * mm / 50
    k2 = 1000 * mm / 75
    truss_section(c, 25 * mm, 168 * mm, k, M.RA, M.AYS, M.AYN, M.A_PLATE, M.FFL, 'อาคาร A — รูปตัดขวาง 1:50 (แนวเสา X = 2.06 – 6.88)')
    truss_section(c, 195 * mm, 168 * mm, k, M.RCW, M.CX0, M.CXM, M.C_PLATE, M.FFL, 'อาคาร C ตะวันตก 1:50 (หลังคา 45°)')

    def d_extra(X, Y):
        c.setStrokeColor(WOOD); c.setLineWidth(2.0)
        for a in (M.DA / 2 - 1.0, M.DA / 2 + 1.0):
            c.line(X(a), Y(M.D_PLATE), X(a), Y(M.under(M.RDU, a) + M.RDU.drop - 0.30))
        c.line(X(M.DA / 2), Y(0.12), X(M.DA / 2), Y(M.D_PLATE - 0.20))
        c.line(X(M.DA / 2), Y(M.D_PLATE), X(M.DA / 2), Y(M.RDU.zb))
        Ru = M.RDU
        c.setStrokeColor(INK); c.setLineWidth(1.0)
        c.line(X(Ru.s0), Y(Ru.ze), X(Ru.sm), Y(Ru.ze + Ru.run * Ru.tn)); c.line(X(Ru.sm), Y(Ru.ze + Ru.run * Ru.tn), X(Ru.s1), Y(Ru.ze))
        c.setStrokeColor(WOOD); c.setLineWidth(1.2)
        for a, d in ((0.10, 1), (M.DA - 0.10, -1)):
            c.line(X(a), Y(M.D_PLATE - 0.95), X(a + d * 0.75), Y(M.D_PLATE - 0.20))
        txt(c, X(M.DA / 2) + 2 * mm, Y(1.2), 'เสากลาง 200x200', 7, color=WOOD)
        txt(c, X(0.10 + 0.4), Y(M.D_PLATE - 0.7), 'ค้ำยัน', 7, color=WOOD)
    truss_section(c, 25 * mm, 30 * mm, k2, M.RDL, 0.10, M.DA - 0.10, M.D_PLATE - 0.20, 0.12, 'อาคาร D — รูปตัดโรงจอดรถ 1:75 (หลังคายกช่องแสง)', d_extra)
    truss_section(c, 160 * mm, 30 * mm, k2, M.RCE, M.CXM, M.CXB, M.C_PLATE, M.FFL, 'อาคาร C ตะวันออก 1:75 (หลังคา 30°)')
    # member schedule
    GRP = [('purlin', 'แป', '@0.80 ม.'), ('rafter', 'จันทัน', '@1.00 ม.'), ('ridge', 'อกไก่ / คานรับหลังคายก', 'พาดระหว่างดั้ง'),
           ('tie', 'ขื่อ (ไม้คู่ประกบเสา)', 'ทุกแนวเสา'), ('kingpost', 'ดั้ง / เสาหลังคายก', 'บนขื่อ'), ('strut', 'ตะเกียบ', 'ดั้ง → จันทัน'),
           ('brace', 'ค้ำยันเสา', '45° ยาว 0.75 ม.')]
    rows = [[t, '%dx%d' % (T['sections'][g][0] * 1000, T['sections'][g][1] * 1000), n] for g, t, n in GRP]
    rows += [['อะเส / คานบนเสา', '100x200 , 120x250', 'ตามโมเดล'], ['เสา', '150 / 180 / 200', 'A,C / ระเบียง / D']]
    txt(c, 245 * mm, 125 * mm, 'ตารางชิ้นส่วนไม้', 9.5, bold=True)
    table(c, 243 * mm, 64 * mm, [('ชิ้นส่วน', 26), ('หน้าตัด (มม.)', 22), ('หมายเหตุ', 22)], [[r[0], r[1], r[2]] for r in rows], size=6.8, rh=5.6 * mm)


# ================================================================== E-01 single line diagram
def breaker(c, x, y, label, rcd=False):
    c.setStrokeColor(INK); c.setLineWidth(0.8)
    c.line(x, y, x, y - 3 * mm); c.line(x, y - 3 * mm, x + 2.5 * mm, y - 6 * mm); c.line(x, y - 7 * mm, x, y - 10 * mm)
    c.circle(x, y - 3 * mm, 0.6 * mm, fill=1)
    if rcd:
        c.ellipse(x - 2 * mm, y - 8.5 * mm, x + 4 * mm, y - 6.2 * mm)
    txt(c, x + 3.5 * mm, y - 4 * mm, label, 7)


def sheet_e01(c):
    E_ = R['electrical']; m = E_['main']
    frame(c, 'E-01', 'แผนผังวงจรไฟฟ้า (Single Line Diagram)', 'ไม่มีมาตราส่วน',
          'ระบบ 3 เฟส 4 สาย 230/400 V 50 Hz จาก กฟภ. ; สายวงจรย่อยขนาดเล็กสุด 2.5 ตร.มม. ; RCD = เครื่องตัดไฟรั่ว 30 mA ; '
          'ต่อลงดินที่ MDB ด้วยสาย THW 10 ตร.มม. หลักดินทองแดง 5/8"x2.4 ม. ; ต่อประสานสายดินและสายนิวทรัลที่ MDB จุดเดียว ; '
          'ขนาดสาย/เบรกเกอร์ตามรายการคำนวณ design_report.pdf หัวข้อ 10 — ต้องตรวจกับมาตรฐาน วสท. ฉบับปัจจุบัน')
    x0, ytop = 30 * mm, PH - 30 * mm
    txt(c, x0, ytop, 'การไฟฟ้าส่วนภูมิภาค (กฟภ.) 3 เฟส 4 สาย 400/230 V', 9, bold=True)
    c.setStrokeColor(INK); c.setLineWidth(1.2)
    c.line(x0 + 10 * mm, ytop - 3 * mm, x0 + 10 * mm, ytop - 12 * mm)
    c.rect(x0 + 4 * mm, ytop - 22 * mm, 12 * mm, 10 * mm)
    txt(c, x0 + 10 * mm, ytop - 18.5 * mm, 'kWh', 8, anchor='c')
    txt(c, x0 + 19 * mm, ytop - 18 * mm, 'มิเตอร์ ' + m['meter'].replace('3-phase 4-wire', '3 เฟส 4 สาย'), 8)
    c.line(x0 + 10 * mm, ytop - 22 * mm, x0 + 10 * mm, ytop - 30 * mm)
    txt(c, x0 + 13 * mm, ytop - 27 * mm, m['cable'].replace('mm2', 'ตร.มม.').replace(' in ', ' ใน ').replace(' mm', ' มม.') + ' ฝังดิน %.0f ม.' % m['L'], 8)
    breaker(c, x0 + 10 * mm, ytop - 30 * mm, 'MAIN ' + m['main_cb'].split(' +')[0] + ' + RCD 100 mA', rcd=True)
    busy = ytop - 46 * mm
    c.setLineWidth(3); c.line(x0, busy, PW - 120 * mm, busy)
    txt(c, x0, busy + 2 * mm, 'MDB (ห้องเก็บของ 2 อาคาร D)  3 เฟส 4 สาย', 9, bold=True)
    # ground
    gx = x0 + 2 * mm
    c.setLineWidth(0.8); c.line(gx, busy, gx, busy - 12 * mm)
    for i, w in enumerate((6, 4, 2)):
        c.line(gx - w / 2 * mm, busy - 12 * mm - i * 1.2 * mm, gx + w / 2 * mm, busy - 12 * mm - i * 1.2 * mm)
    txt(c, gx + 2 * mm, busy - 10 * mm, 'THW 10 ตร.มม. → หลักดิน', 7)
    circ = E_['circuits']; feeders = {f['to']: f for f in E_['feeders']}
    mdb_items = [('CU-A', feeders['CU-A'])] + [('CU-C', feeders['CU-C'])] + [(cc['id'], cc) for cc in circ if cc['cu'] == 'MDB']
    step = (PW - 160 * mm) / len(mdb_items)
    for i, (nm, it) in enumerate(mdb_items):
        x = x0 + 25 * mm + i * step
        c.setLineWidth(0.8); c.line(x, busy, x, busy - 3 * mm)
        if nm.startswith('CU'):
            breaker(c, x, busy - 3 * mm, '%s%dA' % ('3P ' if it['three_phase'] else '', it['cb']))
            txt(c, x + 1 * mm, busy - 20 * mm, it['cable'].replace('mm2', 'ตร.มม.'), 6.5)
            txt(c, x + 1 * mm, busy - 24 * mm, '%s %.0f ม. Vd %.2f%%' % (it['conduit'].replace(' mm', ' มม.'), it['L'], it['vd']), 6.5)
            txt(c, x + 1 * mm, busy - 28 * mm, '→ %s' % nm, 8, bold=True)
        else:
            breaker(c, x, busy - 3 * mm, '%dA' % it['cb'], rcd=it['rcd'])
            txt(c, x + 1 * mm, busy - 20 * mm, it['id'] + ' ' + it['phase'], 7, bold=True)
            txt(c, x + 1 * mm, busy - 24 * mm, it['cable'].replace('mm2', 'ตร.มม.'), 6.2)
            txt(c, x + 1 * mm, busy - 28 * mm, '%d VA' % it['demand'], 6.5)
    # sub boards
    for j, (cu, title) in enumerate((('CU-A', 'CU-A อาคาร A  1 เฟส (L1)'), ('CU-C', 'CU-C อาคาร C  3 เฟส 4 สาย'))):
        by = busy - 60 * mm - j * 52 * mm
        rows = [cc for cc in circ if cc['cu'] == cu]
        c.setLineWidth(3); c.setStrokeColor(INK); c.line(x0, by, x0 + 30 * mm + len(rows) * 30 * mm, by)
        f = feeders[cu]
        txt(c, x0, by + 2 * mm, '%s — เมน %s%dA + RCD 30 mA ; จาก MDB' % (title, '3P ' if f['three_phase'] else '', f['cb']), 9, bold=True)
        for i, cc in enumerate(rows):
            x = x0 + 25 * mm + i * 30 * mm
            c.setLineWidth(0.8); c.line(x, by, x, by - 3 * mm)
            breaker(c, x, by - 3 * mm, '%dA' % cc['cb'], rcd=cc['rcd'])
            txt(c, x + 1 * mm, by - 19 * mm, '%s %s' % (cc['id'], cc['phase']), 7, bold=True)
            txt(c, x + 1 * mm, by - 23 * mm, cc['cable'].replace('mm2', 'ตร.มม.').replace(' + G ', '+G'), 6)
            txt(c, x + 1 * mm, by - 27 * mm, '%s %d VA' % ({'lighting': 'แสงสว่าง', 'receptacle': 'เต้ารับ', 'water heater': 'น้ำอุ่น',
                                                           'air conditioner': 'แอร์', 'motor': 'ปั๊ม'}[cc['kind']], cc['demand']), 6.5)
    # summary box
    sx, sy = 30 * mm, 18 * mm
    lines = ['โหลดติดตั้ง %.2f kVA ; ดีมานด์ %.2f kVA' % (m['total_connected_kVA'], m['total_demand_kVA']),
             'กระแสดีมานด์ต่อเฟส L1 %.1f A , L2 %.1f A , L3 %.1f A (ไม่สมดุล %.1f%%)' % (m['phase_A']['L1'], m['phase_A']['L2'], m['phase_A']['L3'], m['imbalance']),
             'แรงดันตกรวมสูงสุด %.2f%% (เกณฑ์ ≤ 5%%)' % m['worst_total_vd']]
    for i, t in enumerate(lines):
        txt(c, sx, sy + (2 - i) * 5 * mm, t, 9, bold=(i == 0))


# ================================================================== E-02 panel schedules
def sheet_e02(c):
    E_ = R['electrical']
    frame(c, 'E-02', 'ตารางโหลดตู้ไฟฟ้า (Load Schedule) MDB / CU-A / CU-C', 'ไม่มีมาตราส่วน',
          'เต้ารับคิด 180 VA/จุด ; แสงสว่างตามวัตต์ดวงโคม PF 0.9 ; เครื่องทำน้ำอุ่น 4,500 W และแอร์ 1,250 VA คิดเต็ม 100% ; มอเตอร์ปั๊มคิด 125% ; '
          'RCD 30 mA ทุกวงจรเต้ารับ ห้องน้ำ และนอกอาคาร')
    KIND = {'lighting': 'แสงสว่าง', 'receptacle': 'เต้ารับ', 'water heater': 'เครื่องทำน้ำอุ่น', 'air conditioner': 'เครื่องปรับอากาศ', 'motor': 'ปั๊มน้ำ'}
    cols = [('วงจร', 18), ('รายการ', 34), ('จุด', 10), ('L1 (VA)', 18), ('L2 (VA)', 18), ('L3 (VA)', 18), ('เบรกเกอร์', 20), ('สาย', 46), ('Vd %', 13)]
    y = PH - 25 * mm
    for cu, title in (('MDB', 'ตู้ MDB (อาคาร D) — วงจรย่อยภายในตู้ + สายป้อน'), ('CU-A', 'ตู้ CU-A อาคาร A (1 เฟส)'), ('CU-C', 'ตู้ CU-C อาคาร C (3 เฟส 4 สาย)')):
        rows = [cc for cc in E_['circuits'] if cc['cu'] == cu]
        data = []
        tot = {'L1': 0, 'L2': 0, 'L3': 0}
        for cc in rows:
            v = {p: (str(cc['demand']) if cc['phase'] == p else '') for p in tot}
            tot[cc['phase']] += cc['demand']
            data.append([cc['id'], KIND[cc['kind']], str(cc['n']), v['L1'], v['L2'], v['L3'], '%dA%s' % (cc['cb'], ' RCD' if cc['rcd'] else ''),
                         cc['cable'].replace('mm2', 'ตร.มม.'), '%.2f' % cc['vd']])
        if cu == 'MDB':
            for f in E_['feeders']:
                sub = [cc for cc in E_['circuits'] if cc['cu'] == f['to']]
                ph = {p: sum(cc['demand'] for cc in sub if cc['phase'] == p) for p in tot}
                for p in tot:
                    tot[p] += ph[p]
                data.append([f['name'].replace('E-FD-', 'FD-'), 'สายป้อน → ' + f['to'], '', *(str(ph[p]) if ph[p] else '' for p in ('L1', 'L2', 'L3')),
                             '%s%dA' % ('3P ' if f['three_phase'] else '', f['cb']), f['cable'].replace('mm2', 'ตร.มม.'), '%.2f' % f['vd']])
        data.append(['รวม', '', '', *('%d' % tot[p] for p in ('L1', 'L2', 'L3')), '', 'A/เฟส: ' + ' / '.join('%.1f' % (tot[p] / 230) for p in ('L1', 'L2', 'L3')), ''])
        txt(c, 25 * mm, y, title, 10, bold=True)
        h = (len(data) + 1) * 5.6 * mm
        table(c, 25 * mm, y - 3 * mm - h, cols, data, size=7.5, rh=5.6 * mm)
        y -= h + 14 * mm


# ================================================================== E-03 electrical layout
def legend_e(c, x, y):
    c.setLineWidth(0.5); c.setStrokeColor(INK)
    items = [('ดวงโคม', 'L'), ('เต้ารับ', 'S'), ('สวิตช์', 'SW'), ('ตู้ไฟ', 'DB'), ('เครื่องทำน้ำอุ่น', 'WH'), ('เครื่องปรับอากาศ', 'AC'), ('สายป้อนใต้ดิน', 'UG')]
    for i, (t, k) in enumerate(items):
        px, py = x + i * 38 * mm, y
        c.setFillColor(colors.white)
        if k == 'L':
            c.circle(px, py, 1.3 * mm, fill=1); c.line(px - 0.9 * mm, py - 0.9 * mm, px + 0.9 * mm, py + 0.9 * mm)
        elif k == 'S':
            path = c.beginPath(); path.moveTo(px, py + 1.3 * mm); path.lineTo(px - 1.2 * mm, py - 0.9 * mm); path.lineTo(px + 1.2 * mm, py - 0.9 * mm); path.close()
            c.setFillColor(INK); c.drawPath(path, fill=1, stroke=0)
        elif k == 'SW':
            c.setFillColor(INK); c.rect(px - 0.8 * mm, py - 0.8 * mm, 1.6 * mm, 1.6 * mm, fill=1, stroke=0)
        elif k == 'DB':
            c.setFillColor(INK); c.rect(px - 2.2 * mm, py - 1.2 * mm, 4.4 * mm, 2.4 * mm, fill=1, stroke=0)
        elif k == 'UG':
            c.setStrokeColor(colors.HexColor('#d9822b')); c.setDash(3, 1.5); c.setLineWidth(0.9); c.line(px - 3 * mm, py, px + 3 * mm, py); c.setDash()
            c.setStrokeColor(INK); c.setLineWidth(0.5)
        else:
            txt(c, px, py - 1 * mm, k, 6, bold=True, anchor='c', color=RED)
        txt(c, px + 4 * mm, py - 1.2 * mm, t, 8)


SYMBOL = {'IfcLightFixture': 'L', 'IfcOutlet': 'S', 'IfcSwitchingDevice': 'SW', 'IfcElectricAppliance': 'WH', 'IfcUnitaryEquipment': 'AC'}


def sheet_e03(c):
    frame(c, 'E-03', 'แปลนไฟฟ้า: ดวงโคม เต้ารับ สวิตช์ ตู้ไฟ และแนวสายป้อนใต้ดิน', '1 : 125',
          'ดูคำอธิบายสัญลักษณ์ที่มุมบนซ้ายของแบบ ; เลขวงจรกำกับดวงโคม (สีน้ำเงิน) ตรงกับแผ่น E-01 และ E-02 ; '
          'เส้นประสีส้ม = สายป้อน/สายเมนฝังดินในท่อ HDPE ลึก 0.65 ม. ; ตำแหน่งจุดเป็นแนวทาง ปรับหน้างานได้')
    V = View(24 * mm, 26 * mm, -3.0, -16.5, 125)
    legend_e(c, 24 * mm, PH - 24 * mm)
    slab_outlines(c, V)
    outline_walls(c, V)
    orange = colors.HexColor('#d9822b')
    for e in M.E:
        if e[0] == 'IfcCableCarrierSegment':
            for p in e[5]:
                (x1, y1), (x2, y2) = V.p(*p[1][:2]), V.p(*p[2][:2])
                c.setStrokeColor(orange); c.setLineWidth(0.9); c.setDash(3, 1.5); c.line(x1, y1, x2, y2); c.setDash()
    circ_of = {'E-L-A-PEND': 'A-L1', 'E-L-A-DL': 'A-L1', 'E-L-A-WALL': 'A-L2', 'E-L-C': 'C-L1', 'E-L-C-WALL': 'C-L2', 'E-L-D-BAT': 'D-L1',
               'E-L-D-IN': 'D-L1', 'E-L-D-FL': 'D-L2', 'E-L-SITE': 'SITE-L', 'E-L-PG': 'SITE-L'}
    for e in M.E:
        ifc, nm = e[0], e[1]
        if ifc not in SYMBOL and nm not in ('E-MDB', 'E-CU-A', 'E-CU-C', 'E-POLE'):
            continue
        for i, p in enumerate(e[5]):
            x, y = centroid(p)
            px, py = V.p(x, y)
            c.setStrokeColor(INK); c.setFillColor(colors.white); c.setLineWidth(0.5)
            if ifc == 'IfcLightFixture':
                c.circle(px, py, 1.3 * mm, fill=1); c.line(px - 0.9 * mm, py - 0.9 * mm, px + 0.9 * mm, py + 0.9 * mm)
                if i % 3 == 0:
                    txt(c, px + 1.6 * mm, py + 0.8 * mm, circ_of.get(nm, ''), 5, color=BLUE)
            elif ifc == 'IfcOutlet':
                path = c.beginPath(); path.moveTo(px, py + 1.3 * mm); path.lineTo(px - 1.2 * mm, py - 0.9 * mm); path.lineTo(px + 1.2 * mm, py - 0.9 * mm); path.close()
                c.setFillColor(INK); c.drawPath(path, fill=1, stroke=0)
            elif ifc == 'IfcSwitchingDevice':
                c.setFillColor(INK); c.rect(px - 0.8 * mm, py - 0.8 * mm, 1.6 * mm, 1.6 * mm, fill=1, stroke=0)
            elif nm in ('E-MDB', 'E-CU-A', 'E-CU-C'):
                c.setFillColor(INK); c.rect(px - 2.2 * mm, py - 1.2 * mm, 4.4 * mm, 2.4 * mm, fill=1, stroke=0)
                txt(c, px + 3 * mm, py - 1 * mm, nm.replace('E-', ''), 7.5, bold=True)
                break
            elif nm == 'E-POLE':
                c.setFillColor(INK); c.circle(px, py, 1.6 * mm, fill=1); txt(c, px + 2.5 * mm, py - 1 * mm, 'เสา+มิเตอร์ กฟภ.', 7.5, bold=True)
                break
            else:
                txt(c, px, py - 1 * mm, SYMBOL[ifc], 6, bold=True, anchor='c', color=RED)
    for lab, (x, y) in (('อาคาร A', (5.5, 11.6)), ('อาคาร C', (25.3, 11.0)), ('อาคาร D', (19.5, -8.5))):
        px, py = V.p(x, y); txt(c, px, py, lab, 9, bold=True, anchor='c')


# ================================================================== build
out = os.path.join(HERE, 'design', 'BaanSaoYongHin_Drawings.pdf')
cv = canvas.Canvas(out, pagesize=(PW, PH))
cv.setTitle('Baan Sao Yong Hin - preliminary drawings')
for fn in (sheet_s01, sheet_s02, sheet_s03, sheet_e01, sheet_e02, sheet_e03):
    fn(cv)
    cv.showPage()
cv.save()
print('wrote', out, ' sheets:', ', '.join(n for n, _ in SHEETS))
