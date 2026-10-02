# -*- coding: utf-8 -*-
"""Thai calculation report (รายการคำนวณเบื้องต้น) from design/design_results.json -> design/design_report.pdf"""
import datetime as dt
import json
import math
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, 'design', 'design_results.json'), encoding='utf-8'))
A = R['assumptions']

FB = '/usr/share/fonts/truetype/tlwg/'
pdfmetrics.registerFont(TTFont('TH', FB + 'Laksaman.ttf'))
pdfmetrics.registerFont(TTFont('TH-Bold', FB + 'Laksaman-Bold.ttf'))
pdfmetrics.registerFontFamily('TH', normal='TH', bold='TH-Bold', italic='TH', boldItalic='TH-Bold')

W, H = A4
INK = colors.HexColor('#1e2925'); ACC = colors.HexColor('#35524a'); WOOD = colors.HexColor('#8a5a2b')
GRAY = colors.HexColor('#eef2ef'); LINE = colors.HexColor('#9aa8a1'); BAD = colors.HexColor('#b33a2e'); OKC = colors.HexColor('#2f7a4f')
WARNBG = colors.HexColor('#f6ebd3')


def st(name, size=12, bold=False, color=INK, align=0, sb=0, sa=4, li=0):
    return ParagraphStyle(name, fontName='TH-Bold' if bold else 'TH', fontSize=size, leading=size * 1.55, textColor=color,
                          alignment=align, spaceBefore=sb, spaceAfter=sa, leftIndent=li, wordWrap='CJK')


S_T = st('t', 24, True, ACC, 1, 0, 8); S_ST = st('st', 15, False, INK, 1, 0, 4)
S_H1 = st('h1', 16, True, ACC, 0, 10, 4); S_H2 = st('h2', 13.5, True, WOOD, 0, 6, 2)
S_B = st('b', 12); S_S = st('s', 10.5, color=colors.HexColor('#4a5652')); S_F = st('f', 11.5, li=14)
S_CELL = st('c', 10.5, sa=0); S_CELLB = st('cb', 10.5, True, colors.white, sa=0)


pdfmetrics.registerFont(TTFont('SYM', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
TH_WORDS = [(' each way, 90° hooks', ' ทั้งสองทาง ปลายงอ 90°'), (' top + ', ' บน + '), (' bottom', ' ล่าง'),
            (', ties ', ' ปลอก '), (' (135° hooks)', ' งอขอ 135°'), ('stirrups', 'ปลอก'),
            (' each end, capacity ', ' ต่อปลาย รับได้ '), ('(wind on the long side)', '(ลมตั้งฉากด้านยาว)'),
            ('(wind on the gable)', '(ลมตั้งฉากด้านจั่ว)'), ('(north plate)', '(อะเสด้านเหนือ)'), ('(veranda beam)', '(คานระเบียง)'),
            ('(C-W | C-E wall)', '(ผนังระหว่าง C-W/C-E)'), ('(C west wall)', '(ผนังตะวันตก C)'), ('(garage plates)', '(อะเสโรงจอดรถ)'),
            ('galvanised hurricane strap 1.5 mm + 4 screws each side at every rafter-plate joint (capacity ~3 kN)',
             'เหล็กรัดชุบสังกะสีหนา 1.5 มม. + สกรู 4 ตัวต่อข้าง ทุกจุดต่อจันทัน-อะเส (รับได้ประมาณ 3 kN)'),
            ('2 steel plates 6x60x300 mm (cast 150 mm into stump) + 2 through-bolts M12 (galvanised)',
             'แผ่นเหล็ก 6x60x300 มม. 2 แผ่น (ฝังในตอม่อ 150 มม.) + สลักเกลียวชุบสังกะสี M12 2 ตัว')]


def th(t):
    t = str(t)
    for a, b in TH_WORDS:
        t = t.replace(a, b)
    for ch in 'φ→∥':                                   # Laksaman has no glyph for these
        t = t.replace(ch, '<font name="SYM">%s</font>' % ch)
    return t


def P(t, s=S_B):
    return Paragraph(th(t), s)


def table(head, rows, widths, num_cols=(), hl=None):
    data = [[P(h, S_CELLB) for h in head]] + [[P(str(c), S_CELL) for c in r] for r in rows]
    t = Table(data, colWidths=widths, repeatRows=1)
    style = [('BACKGROUND', (0, 0), (-1, 0), ACC), ('GRID', (0, 0), (-1, -1), 0.4, LINE),
             ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, GRAY]), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
             ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2), ('LEFTPADDING', (0, 0), (-1, -1), 4)]
    for c in num_cols:
        style.append(('ALIGN', (c, 1), (c, -1), 'RIGHT'))
    t.setStyle(TableStyle(style))
    return t


def box(lines, bg=WARNBG):
    t = Table([[P('<br/>'.join(lines), st('w', 11.5, sa=0))]], colWidths=[W - 4 * cm])
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), bg), ('BOX', (0, 0), (-1, -1), 0.6, WOOD),
                           ('LEFTPADDING', (0, 0), (-1, -1), 8), ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6)]))
    return t


ok = lambda b: '<font color="#2f7a4f"><b>ผ่าน</b></font>' if b else '<font color="#b33a2e"><b>ไม่ผ่าน</b></font>'
f1 = lambda x: '%.1f' % x
f2 = lambda x: '%.2f' % x


def on_page(c, d):
    c.saveState()
    c.setFillColor(ACC); c.rect(0, H - 1.0 * cm, W, 1.0 * cm, fill=1, stroke=0)
    c.setFillColor(colors.white); c.setFont('TH-Bold', 11)
    c.drawString(1.8 * cm, H - 0.68 * cm, 'รายการคำนวณเบื้องต้น — บ้านเสายงหิน (Baan Sao Yong Hin)')
    c.drawRightString(W - 1.8 * cm, H - 0.68 * cm, 'โครงสร้างและระบบไฟฟ้า')
    c.setFillColor(LINE); c.rect(0, 0, W, 0.7 * cm, fill=1, stroke=0)
    c.setFillColor(colors.white); c.setFont('TH', 10)
    c.drawString(1.8 * cm, 0.24 * cm, 'ร่างเพื่อการประมาณราคาและประสานงาน — ต้องให้วิศวกรผู้มีใบอนุญาตตรวจสอบและลงนามก่อนใช้ก่อสร้าง')
    c.drawRightString(W - 1.8 * cm, 0.24 * cm, 'หน้า %d' % d.page)
    c.restoreState()


ft = R['footings']
posts = sorted(ft.values(), key=lambda f: -f['Ps'])
worst = posts[0]
E_ = R['electrical']
story = []

# ---------------------------------------------------------------- cover
story += [Spacer(1, 3 * cm), P('รายการคำนวณเบื้องต้น', S_T), P('ฐานราก คสล. ตอม่อ คานคอดิน โครงสร้างไม้ส่วนบน และการคำนวณโหลดไฟฟ้า', S_ST),
          P('โครงการ บ้านเสายงหิน (Baan Sao Yong Hin) — กลุ่มอาคารไม้ชั้นเดียว 3 หลัง + งานภายนอก', S_ST), Spacer(1, 1 * cm),
          table(['รายการ', 'รายละเอียด'], [
              ['มาตรฐานที่ใช้', 'ACI 318-19 (หน่วย SI) ตามแนวทาง วสท. ; แรงลม มยผ. 1311-50 ; ระบบไฟฟ้าตามแนวทางมาตรฐานการติดตั้งทางไฟฟ้า วสท.'],
              ['วัสดุ', "คอนกรีต fc' = 240 กก./ตร.ซม. (%.1f MPa) ; เหล็กข้ออ้อย SD40 fy = %d MPa ; เหล็กกลม SR24 fy = %d MPa" % (A['fc_MPa'], A['fy_MPa'], A['fyt_MPa'])],
              ['ที่มาของข้อมูล', 'ตำแหน่งเสา หลังคา ผนัง ดวงโคม เต้ารับ และแนวสาย อ่านจากโมเดล BIM (make_model.py) โดยสคริปต์ design_calc.py'],
              ['วันที่จัดทำ', dt.date.today().strftime('%d/%m/%Y')],
              ['ผลการตรวจสอบ', 'ทุกข้อผ่าน' if R['all_structural_checks_ok'] else 'มีบางข้อไม่ผ่าน — ดูตาราง']],
              [4 * cm, W - 8 * cm]), Spacer(1, 0.8 * cm),
          box(['<b>ข้อจำกัดสำคัญ</b>',
               '1. ไม่มีผลเจาะสำรวจดิน — ใช้กำลังรับน้ำหนักดินที่ยอมให้ qa = %.0f kN/ตร.ม. (10 ตัน/ตร.ม.) ที่ระดับ -%.2f ม. เป็นค่าสมมติ ต้องยืนยันด้วยการเจาะสำรวจดินหรือ plate load test ก่อนก่อสร้าง' % (A['qa_kPa'], A['Df_m']),
               '2. โครงสร้างไม้ใช้วิธีหน่วยแรงที่ยอมให้ของไม้เนื้อแข็งลดลง 20%% สำหรับไม้เก่า — ต้องยืนยันชนิดและคุณภาพไม้จริง (ทดสอบตัวอย่าง) ก่อนใช้ขนาดตามรายการนี้' % (),
               '3. ตารางขนาดสาย/กระแสที่ใช้เป็นค่าประมาณจากตารางมาตรฐาน — วิศวกรไฟฟ้าต้องตรวจกับตาราง วสท. ฉบับปัจจุบัน และยืนยันขนาดมิเตอร์กับการไฟฟ้าส่วนภูมิภาค',
               '4. เอกสารนี้เป็นร่างเพื่อประมาณราคา ต้องให้วิศวกรโยธาและวิศวกรไฟฟ้าผู้มีใบอนุญาตตรวจสอบ แก้ไข และลงนามรับรอง']),
          PageBreak()]

# ---------------------------------------------------------------- 1 assumptions
story += [P('1. ข้อมูลและข้อสมมติในการออกแบบ', S_H1),
          table(['รายการ', 'ค่าที่ใช้', 'หมายเหตุ'], [
              ['กำลังรับน้ำหนักดินที่ยอมให้ qa', '%.0f kN/ตร.ม.' % A['qa_kPa'], 'สมมติ — ต้องเจาะสำรวจดิน'],
              ['ระดับท้องฐานราก Df', '-%.2f ม.' % A['Df_m'], 'จากผิวดินเดิม'],
              ['หน่วยน้ำหนักดิน / คอนกรีต', '%.0f / %.0f kN/ลบ.ม.' % (A['gamma_soil'], A['gamma_conc']), ''],
              ['หลังคากระเบื้องลอนไฟเบอร์ซีเมนต์', '%.2f kN/ตร.ม. (ตามแนวลาด)' % A['roof_sheet_kPa'], 'รวมขอยึด'],
              ['ไม้เนื้อแข็งเก่า (เต็ง/รัง)', '%.1f kN/ลบ.ม.' % A['timber_kN_m3'], 'จันทัน แป อกไก่ เสา คาน ผนังไม้'],
              ['ผนังอิฐมวลเบา 0.12 + ฉาบ 2 ด้าน', '%.1f kN/ลบ.ม. (≈1.4 kN/ตร.ม.)' % A['aac_wall_kN_m3'], ''],
              ['น้ำหนักบรรทุกจรหลังคา', '%.2f kN/ตร.ม. (30 กก./ตร.ม.)' % A['roof_LL_kPa'], 'ตามกฎกระทรวง'],
              ['ชานไม้ / ระเบียง', 'DL %.1f + LL %.1f kN/ตร.ม.' % (A['deck_DL_kPa'], A['deck_LL_kPa']), 'LL 300 กก./ตร.ม.'],
              ['ความเร็วลมอ้างอิง V50', '%.0f ม./วินาที' % A['V50_m_s'], 'เขต 1 มยผ. 1311-50'],
              ['สัมประสิทธิ์แรงยก CgCp สุทธิ', 'อาคาร A, C: %.1f ; อาคาร D (เปิดโล่ง): %.1f' % (A['CgCp_net_enclosed'], A['CgCp_net_open']), 'รวมแรงดันภายใน'],
              ['ระยะหุ้มคอนกรีตฐานราก', '%.0f มม.' % (A['cover_ftg_m'] * 1000), 'หล่อติดดิน'],
              ['ตอม่อ', '0.20 x 0.20 ม. ยึดรั้งโดยคานคอดิน/พื้นที่ +0.30', 'โครงไม่เซ (non-sway)']],
              [6.2 * cm, 6.0 * cm, W - 4 * cm - 12.2 * cm]),
          P('การรวมน้ำหนัก (ACI 318-19): U = 1.2D + 1.6Lr (หรือ 1.4D) สำหรับออกแบบกำลัง ; D + Lr สำหรับตรวจแรงดันดิน ; 0.9D − 1.0W สำหรับตรวจแรงยก', S_S)]

# ---------------------------------------------------------------- 2 loads
q = 0.5 * A['rho_air'] * A['V50_m_s'] ** 2 / 1000
story += [P('2. น้ำหนักบรรทุกหลังคาและแรงลม', S_H1),
          P('แรงดันลมอ้างอิง q = ½ρV² = 0.5 x %.2f x %.0f² = %.3f kN/ตร.ม. ; คูณ Ce = %.1f ได้ %.3f kN/ตร.ม. ; แรงยกสุทธิ p = q·Ce·CgCp' % (
              A['rho_air'], A['V50_m_s'], q, A['Ce'], q * A['Ce'])),
          table(['หลังคา', 'อาคาร', 'พื้นที่ฉาย (ตร.ม.)', 'น้ำหนักตัวเองรวม (kN)', 'DL ต่อพื้นที่ฉาย (kN/ตร.ม.)', 'แรงยกลม (kN/ตร.ม.)'],
                [[r['key'], r['bld'], f2(r['plan']), f2(r['W']), '%.3f' % r['dl'], '%.3f' % r['wind']] for r in R['roofs']],
                [2.2 * cm, 1.6 * cm, 3.0 * cm, 3.6 * cm, 3.6 * cm, W - 4 * cm - 14.0 * cm], (2, 3, 4, 5)),
          P('น้ำหนักหลังคา ฝ้า ผนัง ประตู-หน้าต่าง ระแนง และคานไม้ ถอดจากปริมาตรชิ้นส่วนในโมเดล แล้วแบ่งให้เสาที่ใกล้ที่สุด '
            '(สุ่มจุดทุก 0.25 ม. บนพื้นที่หลังคา และทุก 0.50 ม. ตามแนวผนัง/คาน) — เทียบเท่าวิธีพื้นที่รับน้ำหนัก (tributary area)', S_S)]

# ---------------------------------------------------------------- 3 column loads
rows = [[f['post'], f['bld'], f1(f['P_D']), f1(f['P_L']), f1(f['Ps']), f1(f['Pu']), f2(f['uplift']['Wup'])] for f in posts]
story += [P('3. น้ำหนักลงเสาและฐานราก (49 ต้น)', S_H1),
          table(['เสา', 'อาคาร', 'D (kN)', 'Lr (kN)', 'D+Lr (kN)', 'Pu (kN)', 'แรงยกลม (kN)'], rows,
                [3.6 * cm, 1.6 * cm, 2.2 * cm, 2.2 * cm, 2.4 * cm, 2.4 * cm, W - 4 * cm - 14.4 * cm], (2, 3, 4, 5, 6)),
          PageBreak()]

# ---------------------------------------------------------------- 4 footing detail (worst)
f = worst
B, h, d = f['B'], f['h'], f['d']
fc = A['fc_MPa']
story += [P('4. ฐานรากแผ่ F1 — ตัวอย่างการคำนวณ (เสาที่รับน้ำหนักมากที่สุด %s)' % f['post'], S_H1)]
for line in [
    'น้ำหนักใช้งาน Ps = %.1f kN ; น้ำหนักประลัย Pu = %.1f kN ; ลองฐานราก B x B x h = %.2f x %.2f x %.2f ม.' % (f['Ps'], f['Pu'], B, B, h),
    '<b>4.1 แรงดันดิน</b> : q = (Ps + น้ำหนักฐานราก + ตอม่อ + ดินถมทับ) / B² = <b>%.1f kN/ตร.ม.</b> ≤ qa = %.0f → %s' % (f['q'], A['qa_kPa'], ok(f['q'] <= A['qa_kPa'])),
    '<b>4.2 แรงดันประลัยสุทธิ</b> : qu = Pu / B² = %.1f kN/ตร.ม. ; ความลึกประสิทธิผล d = h − 75 − 12 = %.0f มม.' % (f['qu'], d * 1000),
    '<b>4.3 แรงเฉือนทะลุ</b> (หน้าตัดวิกฤตห่างผิวตอม่อ d/2) : bo = 4(c + d) = %.3f ม. ; Vu = qu(B² − (c+d)²) = %.1f kN ; '
    'φVc = 0.75·0.33√fc′·bo·d = %.1f kN → %s' % (4 * (0.2 + d), f['Vp'], f['phiVp'], ok(f['Vp'] <= f['phiVp'])),
    '<b>4.4 แรงเฉือนแบบคาน</b> (ห่างผิวตอม่อ d) : Vu = qu·B·(L′ − d) = %.1f kN ; φVc = 0.75·0.17√fc′·B·d = %.1f kN → %s' % (f['V1'], f['phiV1'], ok(f['V1'] <= f['phiV1'])),
    '<b>4.5 โมเมนต์ดัด</b> ที่ผิวตอม่อ : L′ = (B − 0.20)/2 = %.3f ม. ; Mu = qu·B·L′²/2 = %.2f kN·ม. ; As ที่ต้องการ = %d ตร.มม. ; '
    'As ต่ำสุด = 0.0018·B·h = %d ตร.มม. → ใช้ <b>%s</b>' % ((B - 0.2) / 2, f['Mu'], f['As_req'], f['As_min'], f['bars']),
    '<b>4.6 ระยะฝังยึด</b> : เหล็กปลายงอ 90° ldh = fy/(23√fc′)·db<sup>1.5</sup> ≥ 150 มม. = %.0f มม. ≤ ระยะที่มี %.0f มม. → %s' % (f['ldh'] * 1000, f['ld_avail'] * 1000, ok(f['ldh'] <= f['ld_avail'])),
]:
    story.append(P(line, S_F))
ftype = R['footing_types']
story += [Spacer(1, 6), P('สรุปแบบฐานราก', S_H2),
          table(['แบบ', 'ขนาด (ม.)', 'เหล็กเสริม', 'จำนวน', 'Ps สูงสุด (kN)', 'เหล็ก/ฐาน (กก.)'],
                [[k, '%.2f x %.2f x %.2f' % (v['B'], v['B'], v['h']), v['bars'], v['count'], f1(v['maxP']), f1(v['kg'])] for k, v in ftype.items()],
                [1.6 * cm, 3.6 * cm, 5.6 * cm, 1.8 * cm, 2.8 * cm, W - 4 * cm - 15.4 * cm], (3, 4, 5)),
          P('ฐานรากทุกต้นใช้ขนาดเดียวกัน (ขนาดเล็กสุดที่ใช้ในการก่อสร้างคือ 0.70 ม.) เพราะน้ำหนักจากอาคารไม้มีค่าน้อย — ขนาดถูกควบคุมด้วยแรงดันดินที่สมมติ หากผลเจาะดินได้ qa ต่ำกว่านี้ต้องคำนวณใหม่', S_S),
          P('ผลตรวจฐานรากทุกต้น', S_H2),
          table(['ฐานราก', 'B (ม.)', 'q (kN/ตร.ม.)', 'Vu/φVc ทะลุ', 'Vu/φVc คาน', 'Mu (kN·ม.)', 'ผล'],
                [[k.replace('F-', ''), f2(v['B']), f1(v['q']), '%.1f / %.1f' % (v['Vp'], v['phiVp']), '%.1f / %.1f' % (v['V1'], v['phiV1']), f2(v['Mu']), ok(v['ok'])]
                 for k, v in sorted(ft.items())],
                [3.6 * cm, 1.6 * cm, 2.4 * cm, 3.0 * cm, 2.8 * cm, 2.2 * cm, W - 4 * cm - 15.6 * cm], (1, 2, 3, 4, 5)),
          PageBreak()]

# ---------------------------------------------------------------- 5 stumps, uplift, anchor
s = worst['stump']
story += [P('5. ตอม่อ คสล. 0.20 x 0.20 ม.', S_H1),
          P('กำลังรับแรงอัดสูงสุด (เสาปลอก) φPn,max = 0.80·φ[0.85fc′(Ag − Ast) + fy·Ast] , φ = 0.65 , 4-DB12 (ρg = %.2f%% อยู่ในช่วง 1–8%%)' % (s['rho'] * 100), S_F),
          P('ตอม่อที่รับน้ำหนักมากที่สุด (%s): Pu = %.1f kN ≤ φPn = %.0f kN → %s' % (worst['post'], s['Pu'], s['phiPn'], ok(s['Pu'] <= s['phiPn'])), S_F),
          P('ความชะลูด: ยึดรั้งด้วยคานคอดิน/พื้น ที่ +0.30 → lu = %.2f ม. ; r = 0.3h = 0.06 ม. ; klu/r = %.1f ≤ 34 (โครงไม่เซ) → %s ; ไม่ต้องขยายโมเมนต์' % (s['lu'], s['klr'], ok(s['klr'] <= 34)), S_F),
          P('เหล็กปลอก RB9 @0.15 ม. (≤ 16db = 192, ≤ 48dt = 432, ≤ 200 มม.) งอขอ 135° ; เหล็กยืนงอเข้าฐานราก 0.30 ม.', S_F),
          P('6. แรงยกจากลมและรอยต่อเสาไม้-ตอม่อ', S_H1),
          P('ตรวจ 0.9(D + น้ำหนักฐานราก + ตอม่อ + ดินถมทับ) ≥ 1.0W(แรงยก) สำหรับเสาทุกต้น — ค่าวิกฤต:', S_F),
          table(['เสา', 'แรงยก W (kN)', 'แรงต้าน 0.9×น้ำหนัก (kN)', 'แรงดึงที่รอยต่อ (kN)', 'ผล'],
                [[v['post'], f2(v['uplift']['Wup']), f2(v['uplift']['resist']), f2(v['uplift']['conn_T']), ok(v['uplift']['ok'])]
                 for v in sorted(ft.values(), key=lambda v: -v['uplift']['Wup'])[:8]],
                [3.8 * cm, 3.0 * cm, 4.4 * cm, 3.8 * cm, W - 4 * cm - 15.0 * cm], (1, 2, 3)),
          Spacer(1, 4),
          P('รอยต่อเสา-ตอม่อ: %s ; กำลังรับแรงด้านข้างของสลักเกลียว M12 ในไม้เนื้อแข็ง (ใช้แผ่นเหล็กประกบ) ประมาณ 6.0 kN/ตัว '
            '→ ความสามารถ %.1f kN ≥ แรงดึงสูงสุด %.2f kN → %s (ค่ากำลังสลักต้องยืนยันตามชนิดไม้จริง)' % (
                R['anchor']['detail'], R['anchor']['capacity'], R['anchor']['max_T'], ok(R['anchor']['ok'])), S_F)]

# ---------------------------------------------------------------- 7 grade beams
story += [P('7. คานคอดิน คสล. 0.20 x 0.40 ม.', S_H1),
          P('น้ำหนัก: ผนังบนแนวคาน (ถอดจากโมเดล) + น้ำหนักคาน 1.92 kN/ม. + ขอบพื้นวางบนดินกว้าง %.2f ม. ; Mu = wu·L²/10 , Vu = 1.15·wu·L/2 ; '
            'As ต่ำสุด = max(0.25√fc′, 1.4)/fy·b·d ; d = 345 มม.' % A['slab_edge_strip_m'], S_F),
          table(['ช่วงคาน', 'ช่วงยาวสุด (ม.)', 'ผนัง (kN/ม.)', 'wu (kN/ม.)', 'Mu / φMn (kN·ม.)', 'Vu / φVc (kN)', 'เหล็กเสริม', 'ผล'],
                [[g['name'], f2(g['span']), f2(g['w_wall']), f2(g['wu']), '%.2f / %.2f' % (g['Mu'], g['phiMn']), '%.1f / %.1f' % (g['Vu'], g['phiVc']),
                  g['bars'].replace(', stirrups', '<br/>ปลอก'), ok(g['ok'])] for g in R['grade_beams']],
                [2.0 * cm, 1.9 * cm, 1.9 * cm, 1.8 * cm, 2.6 * cm, 2.3 * cm, 3.6 * cm, W - 4 * cm - 16.1 * cm], (1, 2, 3, 4, 5)),
          P('8. ตอม่อชานไม้', S_H1),
          P('พื้นที่รับน้ำหนัก %.2f ตร.ม./ตอม่อ (ระยะ ~1.50 ม.) ; P = %.2f kN ; ฐาน 0.40 x 0.40 x 0.15 ม. ; q = %.1f kN/ตร.ม. ≤ qa → %s' % (
              R['deck_pier']['trib'], R['deck_pier']['P'], R['deck_pier']['q'], ok(R['deck_pier']['ok'])), S_F),
          PageBreak()]

# ---------------------------------------------------------------- 9 timber
T = R['timber']
TA = T['assumptions']['stresses_ksc']
GRP = {'purlin': 'แป', 'rafter': 'จันทัน', 'ridge': 'อกไก่ / คานรับหลังคายก', 'tie': 'ขื่อ (คู่ ยึดสลักกับเสา)', 'kingpost': 'ดั้ง / เสาหลังคายก',
       'strut': 'ตะเกียบ (ค้ำดั้ง-จันทัน)', 'brace': 'ค้ำยันเสา (knee brace)'}
ROOFN = {'A': 'อาคาร A', 'CW': 'C ตะวันตก', 'CE': 'C ตะวันออก', 'D': 'D ล่าง', 'DU': 'D หลังคายก'}
story += [P('9. โครงสร้างไม้ส่วนบน (วิธีหน่วยแรงที่ยอมให้)', S_H1),
          P('ไม้เนื้อแข็ง (เต็ง/รัง): Fb = %d , Ft = %d , Fc∥ = %d , Fv = %d , E = %s กก./ตร.ซม. ; คูณ %.2f สำหรับไม้เก่า ; '
            'เพิ่มหน่วยแรง 25%% สำหรับน้ำหนักจรหลังคา และ 33%% สำหรับแรงลม ; ระยะแอ่นตัวยอมให้ L/240 ; เสาใช้สูตรเสาไม้ วสท. (สั้น / ปานกลาง / ยาว)' % (
                TA['Fb'], TA['Ft'], TA['Fc'], TA['Fv'], format(TA['E'], ','), T['assumptions']['reclaimed_factor']), S_F),
          P('ระบบหลังคา: อาคาร A และ C ใช้โครง <b>ขื่อ-ดั้ง-ตะเกียบ</b> ทุกแนวเสา ให้ดั้งรับอกไก่ (ช่วงอกไก่ ≤ 4.1 ม.) ; อาคาร D เพิ่ม<b>เสากลาง</b>ใต้ขื่อ '
            'ทุกแนว (ตามภาพถ่ายโรงจอดรถ) เสาหลังคายกตั้งบนขื่อ ; โครงเปิด (โรงจอดรถ ระเบียง ทางเดิน ซุ้ม) ใช้ค้ำยันเสา 45° ; ผนังไม้ใส่ค้ำยันทแยง', S_F),
          P('9.1 หน้าตัดที่เลือก (ขนาดเล็กสุดที่ผ่านทุกหลังคา)', S_H2),
          table(['ชิ้นส่วน', 'หน้าตัด (มม.)'] + [ROOFN[k] for k in ('A', 'CW', 'CE', 'D', 'DU')],
                [[GRP[g], '%d x %d' % (T['sections'][g][0] * 1000, T['sections'][g][1] * 1000)] +
                 [next(('%.2f' % r['ratio'] + ('' if r['ok'] else ' !')) for r in T['checks'][g] if r['case'] == k) if any(r['case'] == k for r in T['checks'].get(g, [])) else '–'
                  for k in ('A', 'CW', 'CE', 'D', 'DU')] for g in ('purlin', 'rafter', 'ridge', 'tie', 'kingpost', 'strut')],
                [4.6 * cm, 2.6 * cm] + [(W - 4 * cm - 7.2 * cm) / 5] * 5, (2, 3, 4, 5, 6)),
          P('ตัวเลขในตาราง = อัตราส่วนหน่วยแรงสูงสุด (ดัด เฉือน ดัดย้อนจากแรงยกลม 0.6D−W หรือการแอ่นตัว) ต่อค่าที่ยอมให้ ต้อง ≤ 1.00', S_S),
          P('9.2 คานอะเส/คานรับจันทันบนเสา (ขนาดตามโมเดล)', S_H2),
          table(['คาน', 'หน้าตัด', 'ช่วงยาวสุด (ม.)', 'ความกว้างรับน้ำหนัก (ม.)', 'M (kN·ม.)', 'แอ่นตัว / ยอมให้ (มม.)', 'อัตราส่วน', 'ผล'],
                [[p['name'], p['size'], f2(p['span']), f2(p['trib']), f2(p['M']), '%.1f / %.1f' % (p['defl_mm'], p['lim_mm']), '%.2f' % p['ratio'], ok(p['ok'])]
                 for p in T['plates']],
                [3.8 * cm, 2.0 * cm, 1.7 * cm, 2.0 * cm, 1.6 * cm, 2.4 * cm, 1.6 * cm, W - 4 * cm - 15.1 * cm], (2, 3, 4, 5, 6)),
          P('9.3 เสาไม้', S_H2),
          P('ตรวจแรงอัดจากน้ำหนักลงเสา (D+Lr) และแรงอัดร่วมแรงดัดจากลมสำหรับเสาโครงเปิดที่มีค้ำยัน (โรงจอดรถ ระเบียง) — ค่าวิกฤต:', S_F),
          table(['เสา', 'หน้าตัด', 'ยาว (ม.)', 'l/d', 'P (kN)', 'M ลม (kN·ม.)', 'อัตราส่วน', 'ผล'],
                [[p['post'], p['size'], f2(p['L']), f1(p['ld']), f1(p['P']), f2(p['M_wind']), '%.2f' % p['ratio'], ok(p['ok'])]
                 for p in sorted(T['posts'], key=lambda p: -p['ratio'])[:8]],
                [3.4 * cm, 2.0 * cm, 1.6 * cm, 1.4 * cm, 1.8 * cm, 2.4 * cm, 2.0 * cm, W - 4 * cm - 14.6 * cm], (2, 3, 4, 5, 6)),
          P('9.4 ค้ำยันเสา ค้ำยันผนัง และรอยต่อ', S_H2),
          P('โรงจอดรถ: แรงลมต่อเสา H = %.2f kN ; แรงในค้ำยัน 45° = %.2f kN ; ใช้ <b>ค้ำยัน %s</b> %s → %s' % (
              T['brace']['H_post'], T['brace']['F'], T['brace']['size'], T['brace']['bolts'], ok(T['brace']['ok'])), S_F),
          table(['กรณี', 'แรงลมรวม (kN)', 'จำนวนแนวผนัง', 'ต่อแนว (kN)', 'แรงในค้ำยันทแยง (kN)', 'ผล'],
                [[r['case'], f1(r['W']), r['wall_lines'], f2(r['per_line']), f2(r['brace_force']), ok(r['ok'])] for r in T['racking']],
                [5.0 * cm, 2.4 * cm, 2.4 * cm, 2.2 * cm, 3.0 * cm, W - 4 * cm - 15.0 * cm], (1, 2, 3, 4)),
          P('ผนังรับแรงด้านข้าง: ค้ำยันทแยง 50x100 2 ตัวต่อแนวผนัง ยึดสลัก M12 2 ตัวต่อปลาย', S_S),
          P('แรงยกจันทันจากลมสูงสุด %.2f kN ต่อตัว → ยึดจันทันกับอะเสด้วย%s' % (T['rafter_uplift_kN'], T['rafter_tie']), S_F),
          PageBreak()]

# ---------------------------------------------------------------- 9 electrical
m = E_['main']
KIND = {'lighting': 'แสงสว่าง', 'receptacle': 'เต้ารับ', 'water heater': 'เครื่องทำน้ำอุ่น', 'air conditioner': 'เครื่องปรับอากาศ', 'motor': 'มอเตอร์ปั๊ม'}
story += [P('10. การคำนวณโหลดไฟฟ้า', S_H1),
          P('<b>หลักเกณฑ์</b>: แสงสว่างคิดตามวัตต์จริงของดวงโคม (PF 0.9) ดีมานด์ 100%% ; เต้ารับ 180 VA/จุด — 10 kVA แรก 100%% ส่วนเกิน 50%% '
            '(ได้ตัวคูณ %.2f) ; เครื่องทำน้ำอุ่นและเครื่องปรับอากาศ 100%% (ไม่ใช้ดีมานด์ — เผื่อปลอดภัย) ; มอเตอร์ 125%% ; '
            'ขนาดสายวงจรย่อยไม่เล็กกว่า 2.5 ตร.มม. ; แรงดันตกรวมจากมิเตอร์ถึงโหลด ≤ 5%%' % m['receptacle_factor'], S_F),
          table(['วงจร', 'ตู้', 'ประเภท', 'จุด', 'ดีมานด์ (VA)', 'I (A)', 'เฟส', 'เบรกเกอร์', 'สาย', 'ยาว (ม.)', 'Vd (%)'],
                [[c['id'], c['cu'], KIND[c['kind']], c['n'], c['demand'], f1(c['I']), c['phase'], '%dA%s' % (c['cb'], ' RCD' if c['rcd'] else ''),
                  c['cable'].replace('mm2', 'ตร.มม.'), f1(c['L']), f2(c['vd'])] for c in E_['circuits']],
                [x * cm * (W - 4 * cm) / (17.0 * cm) for x in (1.45, 1.15, 2.2, 0.8, 1.55, 1.05, 0.9, 1.75, 3.65, 1.2, 1.3)], (3, 4, 5, 9, 10)),
          P('RCD = ป้องกันด้วยเครื่องตัดไฟรั่ว 30 mA (วงจรเต้ารับ ห้องน้ำ/เครื่องทำน้ำอุ่น และวงจรภายนอกอาคาร)', S_S),
          P('10.1 การจัดเฟสและสายป้อน', S_H2),
          P('ตู้ CU-A เป็นแบบ 1 เฟส ทั้งตู้อยู่บนเฟส L1 ; ตู้ CU-C เปลี่ยนเป็น <b>3 เฟส 4 สาย</b> (เดิมสมมติ 1 เฟส) เพราะมีเครื่องทำน้ำอุ่น 2 ชุด '
            'หากเป็น 1 เฟสจะมีกระแสเกิน 60 A บนเฟสเดียว ; วงจรที่เหลือกระจายเฟสจากโหลดใหญ่ไปเล็ก', S_F),
          table(['เฟส', 'กระแสดีมานด์ (A)'], [[k, f1(v)] for k, v in m['phase_A'].items()] + [['ความไม่สมดุล', '%.1f %%' % m['imbalance']]],
                [5 * cm, 4 * cm], (1,)),
          Spacer(1, 4),
          table(['สายป้อน', 'ไปยัง', 'ระบบ', 'ดีมานด์ (kVA)', 'I สูงสุด/เฟส (A)', 'เบรกเกอร์', 'สาย', 'ยาว (ม.)', 'Vd (%)'],
                [[fd['name'], fd['to'], '3 เฟส' if fd['three_phase'] else '1 เฟส', f2(fd['demand_kVA']), f1(fd['I']), '%dA' % fd['cb'],
                  fd['cable'].replace('mm2', 'ตร.มม.') + ' ใน ' + fd['conduit'].replace('mm', 'มม.'), f1(fd['L']), f2(fd['vd'])] for fd in E_['feeders']] +
                [['E-FD-MAIN', 'MDB', '3 เฟส', f2(m['total_demand_kVA']), f1(m['I_max']), m['main_cb'].split(' +')[0],
                  m['cable'].replace('mm2', 'ตร.มม.').replace(' in ', ' ใน ').replace('mm', 'มม.'), f1(m['L']), f2(m['vd'])]],
                [1.9 * cm, 1.3 * cm, 1.3 * cm, 1.8 * cm, 2.1 * cm, 1.6 * cm, 4.5 * cm, 1.4 * cm, W - 4 * cm - 15.9 * cm], (3, 4, 7, 8)),
          P('10.2 สรุปมิเตอร์และเมน', S_H2),
          table(['รายการ', 'ผล'], [
              ['โหลดติดตั้งรวม', '%.2f kVA' % m['total_connected_kVA']],
              ['ดีมานด์รวม', '%.2f kVA' % m['total_demand_kVA']],
              ['กระแสสูงสุดต่อเฟส', '%.1f A' % m['I_max']],
              ['ขนาดมิเตอร์ (ขอ กฟภ.)', m['meter'].replace('3-phase 4-wire', '3 เฟส 4 สาย')],
              ['เมนเบรกเกอร์ที่ MDB', m['main_cb']],
              ['สายเมน', m['cable'].replace('mm2', 'ตร.มม.').replace(' in ', ' ใน ').replace('mm', 'มม.')],
              ['สายต่อหลักดิน', 'THW 10 ตร.มม. ต่อหลักดินทองแดง 5/8" x 2.4 ม. (สายเมนไม่เกิน 35 ตร.มม.)'],
              ['แรงดันตกรวมสูงสุด (มิเตอร์ → โหลด)', '%.2f %% ≤ 5 %% → %s' % (m['worst_total_vd'], ok(m['worst_total_vd'] <= 5))]],
              [6 * cm, W - 10 * cm]),
          Spacer(1, 6),
          box(['<b>สิ่งที่เปลี่ยนจากแบบร่างเดิม</b>',
               '• สายเมน NYY 4x25 → %s (ดีมานด์ ~%.0f A/เฟส) ; เมน 3P 63A → %s' % (m['cable'].split(' in')[0], m['I_max'], m['main_cb'].split(' +')[0]),
               '• สายป้อนอาคาร A: NYY 2x16 → %s ; อาคาร C: NYY 2x25 (1 เฟส) → %s (3 เฟส)' % (E_['feeders'][0]['cable'], E_['feeders'][1]['cable']),
               '• สายวงจรแสงสว่าง THW 1.5 → 2.5 ตร.มม. (ขนาดต่ำสุดของวงจรย่อย) ; ตู้ CU-C เป็นแบบ 3 เฟส',
               '• ฐานราก 0.80 x 0.80 → %.2f x %.2f x %.2f ม. ; เหล็กเสริมคิดตามรายการคำนวณแทนอัตราส่วน กก./ลบ.ม.' % (B, B, h),
               '• โครงหลังคา: เพิ่มขื่อ-ดั้ง-ตะเกียบ ทุกแนวเสา (A, C) เสากลางโรงจอดรถ ค้ำยันเสาโครงเปิด ; จันทัน 50x150 → %dx%d แป 50x100 → %dx%d' % (
                   R['timber']['sections']['rafter'][0] * 1000, R['timber']['sections']['rafter'][1] * 1000,
                   R['timber']['sections']['purlin'][0] * 1000, R['timber']['sections']['purlin'][1] * 1000)], colors.HexColor('#dce9f1')),
          P('11. สิ่งที่วิศวกรผู้ออกแบบต้องดำเนินการต่อ', S_H1)]
for t in ['เจาะสำรวจดินอย่างน้อย 2–3 หลุม (อาคาร A, C, D) และปรับขนาดฐานรากตามค่า qa จริง ; ตรวจระดับน้ำใต้ดินและดินบวมตัว',
          'ยืนยันชนิด ความชื้น และกำลังของไม้เก่าที่ได้จริง (ทดสอบตัวอย่าง) แล้วทบทวนขนาดหน้าตัดไม้ รอยต่อ และระยะสลักเกลียวตามมาตรฐานไม้',
          'ตรวจกำลังสลักเกลียวและแผ่นเหล็กรอยต่อเสา-ตอม่อ กับค่ากำลังของชนิดไม้จริง',
          'ตรวจตารางขนาดกระแสสายไฟ ค่าแรงดันตก และขนาดสายดินกับมาตรฐาน วสท. ฉบับล่าสุด ; ยืนยันขนาดมิเตอร์และจุดต่อกับ กฟภ.',
          'จัดทำแบบขยายฐานราก-ตอม่อ-คานคอดิน แผนผังวงจรไฟฟ้า (single line diagram) และตารางโหลดตู้ (load schedule) เพื่อยื่นขออนุญาต']:
    story.append(P('• ' + t, S_F))

out = os.path.join(HERE, 'design', 'design_report.pdf')
SimpleDocTemplate(out, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.6 * cm, bottomMargin=1.3 * cm,
                  title='รายการคำนวณเบื้องต้น บ้านเสายงหิน', author='design_calc.py').build(story, onFirstPage=on_page, onLaterPages=on_page)
print('wrote', out)
