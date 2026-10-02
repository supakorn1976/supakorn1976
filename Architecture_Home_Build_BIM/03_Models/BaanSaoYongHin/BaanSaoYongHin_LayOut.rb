# encoding: utf-8
# =============================================================================
#  BaanSaoYongHin_LayOut.rb  -  ส่งออกโมเดลบ้านเสายงหินเป็นเอกสาร SketchUp LayOut (.layout)
#
#  ต้องใช้ SketchUp Pro 2018 ขึ้นไป (มี LayOut Ruby API) และสร้างโมเดลด้วย BaanSaoYongHin_BIM.rb ก่อน
#
#  วิธีใช้ (Window > Ruby Console):
#      load 'C:/path/BaanSaoYongHin_BIM.rb'
#      BaanSaoYongHinBIM.build
#      (File > Save As...  บันทึกโมเดลเป็น .skp ก่อน — LayOut อ้างอิงไฟล์ .skp)
#      load 'C:/path/BaanSaoYongHin_LayOut.rb'
#      BaanSaoYongHinLayOut.export                        # -> BaanSaoYongHin.layout ข้างไฟล์ .skp
#      BaanSaoYongHinLayOut.export('C:/temp/bsy.layout')  # กำหนดที่บันทึกเอง
#      BaanSaoYongHinLayOut.make_scenes                   # สร้างเฉพาะ scene L01-L12 (ไม่สร้าง .layout)
#      BaanSaoYongHinLayOut.export(flip: true)            # ถ้ารูปตัด/ผังพื้นแสดงด้านที่ถูกตัดทิ้งผิดข้าง
#
#  ผลลัพธ์: กระดาษ A3 แนวนอน
#    A-01 ผังหลังคา/ผังบริเวณ 1:200   A-02 ผังพื้น (ตัดที่ +1.50) 1:125
#    A-03 รูปด้านทิศใต้/ทิศเหนือ 1:150   A-04 รูปด้านทิศตะวันออก/ทิศตะวันตก 1:150
#    A-05 รูปตัด A-A, B-B, C-C 1:100 + ทัศนียภาพโครงสร้าง   A-06 ทัศนียภาพรวม + งานระบบ
#    S-01..E-03 แบบ 2 มิติจาก drawings.py (ภาพ PNG จาก layout_sheets/ — สร้างด้วย python3 layout_sheets.py)
#  viewport ทุกช่องเชื่อมกับไฟล์ .skp: แก้โมเดลแล้วกด Update Model Reference ใน LayOut ได้
#  หน่วยในสคริปต์: เมตร (โมเดล) และ มิลลิเมตร (กระดาษ) ; LayOut API ใช้นิ้ว แปลงใน mm()
# =============================================================================
module BaanSaoYongHinLayOut
  constants.each { |c| remove_const(c) }

  DIR        = File.dirname(File.expand_path(__FILE__))
  SHEET_DIR  = File.join(DIR, 'layout_sheets')
  PAPER      = [420.0, 297.0]                 # A3 landscape, mm
  FONT       = 'Tahoma'                       # มีอักษรไทยทั้ง Windows และ macOS
  PROJECT    = 'บ้านเสายงหิน  (กลุ่มอาคารไม้ชั้นเดียว อาคาร A, C, D)'
  STAMP      = 'แบบร่างเบื้องต้น — ห้ามใช้ก่อสร้าง'
  ATTR       = 'BSY_LAYOUT'

  # ---------------------------------------------------------------- model geometry (m), from make_model.py
  SITE_C   = [15.4, -1.45]                    # centre of the three buildings (x -1.2..32.0, y -15.3..12.4)
  D_O      = [16.87, -0.48]                   # garage frame origin, turned 26 deg
  TH       = 26.0 * Math::PI / 180
  D_U      = [Math.cos(TH), -Math.sin(TH)]    # along the 7.90 m side (tie beams span this way)
  D_V      = [-Math.sin(TH), -Math.cos(TH)]   # along the 10.40 m side
  def self.d_pt(a, b); [D_O[0] + D_U[0] * a + D_V[0] * b, D_O[1] + D_U[1] * a + D_V[1] * b]; end

  BURIED  = %w[P-Water P-Drain E-Power].freeze            # pipes / feeders under ground and slab
  ELEV_HIDE = (BURIED + %w[S-Foundation A-Ceiling]).freeze

  # scene: name, camera [eye, target, up, perspective, height(m)|fov], tags hidden, cut [point, view dir] or nil
  # a cut keeps what lies beyond the plane in the view direction (the camera looks at the cut face)
  def self.views
    cx, cy = SITE_C
    dc = d_pt(3.95, 5.15)
    dp = d_pt(0.0, 5.15)
    [
      ['L01 Roof plan',      [[cx, cy, 100], [cx, cy, 0], [0, 1, 0], false, 48], [], nil],
      ['L02 Floor plan',     [[cx, cy, 100], [cx, cy, 0], [0, 1, 0], false, 40], BURIED + %w[E-Lighting], [[cx, cy, 1.50], [0, 0, -1]]],
      ['L03 South elev',     [[cx, -80, 2.5], [cx, 0, 2.5], [0, 0, 1], false, 16], ELEV_HIDE, nil],
      ['L04 North elev',     [[cx, 80, 2.5], [cx, 0, 2.5], [0, 0, 1], false, 16], ELEV_HIDE, nil],
      ['L05 East elev',      [[90, cy, 2.5], [0, cy, 2.5], [0, 0, 1], false, 16], ELEV_HIDE, nil],
      ['L06 West elev',      [[-70, cy, 2.5], [0, cy, 2.5], [0, 0, 1], false, 16], ELEV_HIDE, nil],
      # A-A: building A, N-S cut between trusses, looking west (only A lies beyond)
      ['L07 Section A-A',    [[60, 5.6, 2.3], [0, 5.6, 2.3], [0, 0, 1], false, 9], BURIED, [[5.6, 5.6, 0], [-1, 0, 0]]],
      # B-B: building C, E-W cut between truss lines CYS / CYM, looking north
      ['L08 Section B-B',    [[24.3, -60, 2.4], [24.3, 0, 2.4], [0, 0, 1], false, 9], BURIED, [[24.3, 4.0, 0], [0, 1, 0]]],
      # C-C: garage, cut across mid-length between tie lines, looking along +v (south-west)
      ['L09 Section C-C',    [[dc[0] - D_V[0] * 60, dc[1] - D_V[1] * 60, 2.5], [dc[0], dc[1], 2.5], [0, 0, 1], false, 9], BURIED,
                              [[dp[0], dp[1], 0], [D_V[0], D_V[1], 0]]],
      ['L10 3D overall',     [[-22, -42, 24], [cx, cy, 1.5], [0, 0, 1], true, 35], %w[A-Ceiling], nil],
      ['L11 3D structure',   [[cx - 60, cy - 60, 48], [cx, cy, 0], [0, 0, 1], false, 42], :structure, nil],
      ['L12 3D MEP',         [[cx - 60, cy - 60, 48], [cx, cy, 0], [0, 0, 1], false, 42], :mep, nil],
    ]
  end

  # sheets: number, Thai title, viewports [scene, x, y, w, h (mm), scale denominator | nil, caption]
  SHEETS = [
    ['A-01', 'ผังหลังคาและผังบริเวณ', [['L01 Roof plan', 15, 15, 320, 255, 200, 'ผังหลังคาและผังบริเวณ']]],
    ['A-02', 'ผังพื้น', [['L02 Floor plan', 15, 15, 320, 255, 125, 'ผังพื้น (ตัดที่ระดับ +1.50)']]],
    ['A-03', 'รูปด้านทิศใต้ และทิศเหนือ', [['L03 South elev', 15, 15, 320, 115, 150, 'รูปด้านทิศใต้'],
                                          ['L04 North elev', 15, 148, 320, 115, 150, 'รูปด้านทิศเหนือ']]],
    ['A-04', 'รูปด้านทิศตะวันออก และทิศตะวันตก', [['L05 East elev', 15, 15, 320, 115, 150, 'รูปด้านทิศตะวันออก'],
                                                 ['L06 West elev', 15, 148, 320, 115, 150, 'รูปด้านทิศตะวันตก']]],
    ['A-05', 'รูปตัด', [['L07 Section A-A', 15, 15, 120, 115, 100, 'รูปตัด A-A (อาคาร A)'],
                       ['L08 Section B-B', 145, 15, 190, 115, 100, 'รูปตัด B-B (อาคาร C)'],
                       ['L09 Section C-C', 15, 148, 170, 115, 100, 'รูปตัด C-C (โรงจอดรถ D)'],
                       ['L11 3D structure', 195, 148, 140, 115, nil, 'ทัศนียภาพโครงสร้าง']]],
    ['A-06', 'ทัศนียภาพ', [['L10 3D overall', 15, 15, 320, 160, nil, 'ทัศนียภาพรวม'],
                          ['L12 3D MEP', 15, 190, 320, 75, nil, 'งานระบบสุขาภิบาลและไฟฟ้า (ซ่อนหลังคาและผนัง)']]],
  ].freeze

  IMAGE_SHEETS = [%w[S-01 แปลนฐานราก], %w[S-02 แบบขยายฐานราก], %w[S-03 รูปตัดโครงหลังคา],
                  %w[E-01 แผนผังวงจรไฟฟ้า], %w[E-02 ตารางโหลดตู้], %w[E-03 แปลนไฟฟ้า]].freeze

  # ---------------------------------------------------------------- SketchUp side: scenes
  def self.pt(a); Geom::Point3d.new(a[0].to_f.m, a[1].to_f.m, a[2].to_f.m); end

  def self.camera_for(c)
    eye, target, up, persp, size = c
    cam = Sketchup::Camera.new(pt(eye), pt(target), Geom::Vector3d.new(*up))
    if persp
      cam.perspective = true
      cam.fov = size
    else
      cam.perspective = false
      cam.height = size.to_f.m
    end
    cam
  end

  def self.tag_visible?(hide, name)
    case hide
    when :structure then name.start_with?('S-')
    when :mep then name.start_with?('P-', 'E-', 'S-Column', 'S-Slab', 'S-Foundation')
    else !hide.include?(name)
    end
  end

  def self.bim_tag?(name); name =~ /\A[SAPE]-|\ASite\z/ ? true : false; end

  def self.built?(model)
    model.entities.grep(Sketchup::Group).any? { |g| g.valid? && g.get_attribute('BSY_ROOT', 'built') }
  end

  # creates (or recreates) scenes L01-L12 with their own camera, tag visibility and section cut
  def self.make_scenes(flip: false)
    model = Sketchup.active_model
    raise 'model not built yet - run BaanSaoYongHinBIM.build first' unless built?(model)
    ents = model.entities
    ro = model.rendering_options
    old_planes = ro['DisplaySectionPlanes']
    model.start_operation('Baan Sao Yong Hin LayOut scenes', true)
    begin
      ents.grep(Sketchup::SectionPlane).each { |s| s.erase! if s.valid? && s.get_attribute(ATTR, 'cut') }
      model.pages.to_a.each { |p| model.pages.erase(p) if p.name.start_with?('L') && p.name =~ /\AL\d\d / }
      ro['DisplaySectionPlanes'] = false
      ro['DisplaySectionCuts'] = true
      layer = model.layers['L-Sections'] || model.layers.add('L-Sections')
      views.each do |name, cam, hide, cut|
        sp = nil
        if cut
          p0, dir = cut
          n = flip ? dir.map { |v| -v } : dir   # section arrows (normal) point at the part that stays visible
          sp = ents.add_section_plane(pt(p0), Geom::Vector3d.new(*n))
          sp.name = name.sub(/\AL\d\d /, '')
          sp.layer = layer
          sp.set_attribute(ATTR, 'cut', true)
        end
        ents.active_section_plane = sp
        model.layers.each { |l| l.visible = tag_visible?(hide, l.name) if bim_tag?(l.name) }
        model.active_view.camera = camera_for(cam)
        model.pages.add(name)
      end
    ensure
      ents.active_section_plane = nil
      model.layers.each { |l| l.visible = true if bim_tag?(l.name) }
      ro['DisplaySectionPlanes'] = old_planes
    end
    model.commit_operation
    puts "#{views.size} scenes L01-L#{format('%02d', views.size)} created#{flip ? ' (flipped cuts)' : ''}"
    views.size
  rescue StandardError
    model.abort_operation if model
    raise
  end

  # ---------------------------------------------------------------- LayOut side
  def self.mm(v); v.to_f / 25.4; end
  def self.p2(x, y); Geom::Point2d.new(mm(x), mm(y)); end
  def self.box(x, y, w, h); Geom::Bounds2d.new(mm(x), mm(y), mm(w), mm(h)); end

  def self.add(doc, page, ent)
    doc.add_entity(ent, doc.layers.first, page)
    ent
  end

  def self.text(doc, page, str, x, y, size, bold: false, anchor: :tl)
    a = { tl: Layout::FormattedText::ANCHOR_TYPE_TOP_LEFT, tc: Layout::FormattedText::ANCHOR_TYPE_TOP_CENTER,
          tr: Layout::FormattedText::ANCHOR_TYPE_TOP_RIGHT, cc: Layout::FormattedText::ANCHOR_TYPE_CENTER_CENTER }[anchor]
    t = add(doc, page, Layout::FormattedText.new(str, p2(x, y), a))
    st = t.style
    st.font_family = FONT
    st.font_size = size.to_f
    st.text_bold = bold
    t.style = st
    t
  end

  def self.rect(doc, page, x, y, w, h, width = 0.5)
    r = add(doc, page, Layout::Rectangle.new(box(x, y, w, h)))
    st = r.style
    st.solid_filled = false
    st.stroke_width = width.to_f
    r.style = st
    r
  end

  def self.line(doc, page, x0, y0, x1, y1, width = 0.35)
    l = add(doc, page, Layout::Path.new(p2(x0, y0), p2(x1, y1)))
    st = l.style
    st.stroke_width = width.to_f
    l.style = st
    l
  end

  # border + title block on the right (x 340..410 mm), same layout as drawings.py
  def self.title_block(doc, page, no, title, scales, idx, total)
    w, h = PAPER
    rect(doc, page, 10, 10, w - 20, h - 20, 1.0)
    x0 = 340
    line(doc, page, x0, 10, x0, h - 10, 0.7)
    y = 16
    text(doc, page, 'โครงการ', x0 + 4, y, 7); y += 5
    text(doc, page, PROJECT, x0 + 4, y, 9, bold: true); y += 16
    line(doc, page, x0, y, w - 10, y); y += 4
    text(doc, page, 'ชื่อแบบ', x0 + 4, y, 7); y += 5
    text(doc, page, title, x0 + 4, y, 11, bold: true); y += 14
    line(doc, page, x0, y, w - 10, y); y += 4
    text(doc, page, "มาตราส่วน  #{scales}", x0 + 4, y, 8); y += 6
    text(doc, page, "วันที่  #{Time.now.strftime('%d/%m/%Y')}", x0 + 4, y, 8); y += 6
    text(doc, page, 'หน่วย  เมตร (ยกเว้นระบุ)', x0 + 4, y, 8); y += 8
    line(doc, page, x0, y, w - 10, y); y += 4
    text(doc, page, 'หมายเหตุ', x0 + 4, y, 7, bold: true); y += 5
    ['viewport เชื่อมกับไฟล์ .skp ของโมเดล BIM', 'ขนาดโครงสร้างจากรายการคำนวณเบื้องต้น',
     '(design/design_report.pdf)', 'ตรวจสอบระยะในสนามก่อนก่อสร้าง'].each do |s|
      text(doc, page, "- #{s}", x0 + 4, y, 7); y += 4.5
    end
    # signature boxes
    sy = 190
    [['สถาปนิก', sy], ['วิศวกรโยธา', sy + 18], ['วิศวกรไฟฟ้า', sy + 36]].each do |lbl, yy|
      rect(doc, page, x0 + 4, yy, w - 10 - x0 - 8, 15, 0.35)
      text(doc, page, "#{lbl}  ............................", x0 + 6, yy + 2, 7)
      text(doc, page, 'ลงนาม / เลขทะเบียน', x0 + 6, yy + 9, 6)
    end
    st = rect(doc, page, x0 + 4, 247, w - 10 - x0 - 8, 9, 0.7)
    stl = st.style; stl.stroke_color = Sketchup::Color.new(200, 0, 0); st.style = stl
    text(doc, page, STAMP, (x0 + w - 10) / 2.0, 251.5, 8, bold: true, anchor: :cc)
    line(doc, page, x0, 259, w - 10, 259, 0.7)
    text(doc, page, 'แผ่นที่', x0 + 4, 262, 7)
    text(doc, page, no, x0 + 4, 267, 20, bold: true)
    text(doc, page, "แผ่น #{idx} / #{total}", w - 14, 280, 8, anchor: :tr)
  end

  def self.viewport(doc, page, skp, scene, x, y, w, h, scale, caption)
    vp = Layout::SketchUpModel.new(skp, box(x, y, w, h))
    add(doc, page, vp)
    i = vp.scenes.index(scene)
    raise "scene #{scene} not found in #{skp}" unless i
    vp.current_scene = i
    if scale
      vp.perspective = false
      vp.scale = 1.0 / scale
      vp.preserve_scale_on_resize = true
      vp.render_mode = Layout::SketchUpModel::HYBRID_RENDER
      vp.display_background = false
    else
      vp.render_mode = Layout::SketchUpModel::RASTER_RENDER
    end
    text(doc, page, caption + (scale ? "   มาตราส่วน 1:#{scale}" : ''), x + w / 2.0, y + h + 2, 9, bold: true, anchor: :tc)
    line(doc, page, x + w / 2.0 - 35, y + h + 7.5, x + w / 2.0 + 35, y + h + 7.5, 0.5)
    vp
  end

  def self.export(path = nil, flip: false)
    raise 'LayOut API not available: needs SketchUp Pro 2018 or newer' unless defined?(Layout::Document)
    model = Sketchup.active_model
    skp = model.path
    raise 'save the model as .skp first (File > Save As), LayOut links to the file' if skp.nil? || skp.empty?
    make_scenes(flip: flip)
    model.save                                           # LayOut reads scenes from the saved file
    path ||= File.join(File.dirname(skp), 'BaanSaoYongHin.layout')
    doc = Layout::Document.new
    doc.page_info.width = mm(PAPER[0])
    doc.page_info.height = mm(PAPER[1])
    doc.units = Layout::Document::DECIMAL_MILLIMETERS if doc.respond_to?(:units=)
    images = IMAGE_SHEETS.map { |no, t| [no, t, File.join(SHEET_DIR, "#{no}.png")] }.select { |r| File.exist?(r[2]) }
    total = SHEETS.size + images.size
    failed = []
    SHEETS.each_with_index do |(no, title, vps), k|
      page = k.zero? ? doc.pages.first : doc.pages.add
      page.name = "#{no} #{title}"
      scales = vps.map { |v| v[5] }.compact.uniq.map { |s| "1:#{s}" }.join(', ')
      title_block(doc, page, no, title, scales.empty? ? 'ไม่มีมาตราส่วน' : scales, k + 1, total)
      vps.each do |scene, x, y, w, h, scale, cap|
        begin
          viewport(doc, page, skp, scene, x, y, w, h, scale, cap)
        rescue StandardError => e
          failed << "#{no} #{scene}: #{e.class} #{e.message}"
        end
      end
    end
    images.each do |no, title, png|
      page = doc.pages.add
      page.name = "#{no} #{title}"
      add(doc, page, Layout::Image.new(png, box(0, 0, PAPER[0], PAPER[1])))
    end
    doc.save(path)
    puts "LayOut: #{path}  (#{total} pages: #{SHEETS.size} model sheets + #{images.size} drawing sheets)"
    puts "  #{images.size} of #{IMAGE_SHEETS.size} drawing PNG found in #{SHEET_DIR}" if images.size < IMAGE_SHEETS.size
    failed.each { |f| puts "  viewport FAILED #{f}" }
    puts '  if the floor plan / sections show the wrong half, run export(flip: true)'
    path
  end
end
