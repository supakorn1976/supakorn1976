# encoding: utf-8
# =============================================================================
#  ModernHouse_BIM.rb  -  บ้านพักอาศัย 2 ชั้น สไตล์โมเดิร์น หลังคาแบน ที่จอดรถ 2 คัน  โมเดล BIM (SketchUp Ruby)  v0.1
#  แหล่งข้อมูล: ภาพเดียว (ผังพื้นชั้นล่าง/ชั้นบน + ภาพ render ด้านหน้า) — ไม่มีมิติในแบบ
#  ขนาดทั้งหมดเป็นค่าประมาณ: สเกลผังจากรถ 2 คัน (~32 px/ม.), ความสูงจากภาพ render (~85 px/ม.)
#  ตัวอาคาร 10.00 x 12.40 ม. ; พื้นชั้นล่าง +0.30 ; พื้นชั้นบน +3.50 ; หลังพื้นหลังคา +6.80 ; ยื่นหลังคาหน้า 0.80 ม.
#  ชั้นล่าง: ที่จอดรถ 2 คัน, ห้องนั่งเล่น, ซักล้าง, ห้องน้ำแขก, ครัว+รับประทานอาหาร, บันได U
#  ชั้นบน : ห้องนอนใหญ่ + ห้องน้ำ (อ่างอาบน้ำ) + walk-in closet + ระเบียง, ห้องนอน 2 ห้อง, ห้องน้ำรวม
#  ด้านหน้า: กรอบสีขาว, ผนังกระจก 2 ชั้น, ครีบหินกาบ, ระเบียงราวกระจก, ฝ้าชายคาลายไม้, ไฟ LED เส้น
#  โครงสร้างเป็นขนาดสมมติ (ยังไม่ได้ออกแบบ) — ต้องให้สถาปนิก/วิศวกรตรวจและกำหนดขนาดจริง
#  รวม 137 องค์ประกอบ  ทุกชิ้นเป็น Group: IFC 2x3 classification + attribute 'MH_BIM' + Tag
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
  MATS = {
    "concrete"=>[196,194,188,1.0],
    "concrete_dark"=>[150,148,142,1.0],
    "wall_white"=>[236,234,228,1.0],
    "stone"=>[168,150,128,1.0],
    "wood"=>[160,108,64,1.0],
    "glass"=>[159,195,210,0.35],
    "frame_black"=>[28,28,28,1.0],
    "roof_dark"=>[48,50,54,1.0],
    "rail"=>[21,21,21,1.0],
    "paving"=>[190,188,182,1.0],
    "ground"=>[126,160,92,1.0],
    "tile_floor"=>[216,212,204,1.0],
    "wood_floor"=>[168,120,74,1.0],
    "counter"=>[120,116,112,1.0],
    "sanitary"=>[255,255,255,1.0],
    "light"=>[255,230,128,1.0]
  }
  STOREYS = { 'FND'=>'Foundation (below ±0.00)', 'GF'=>'Ground floor (FFL +0.30)', '1F'=>'Upper floor (FFL +3.50)', 'ROOF'=>'Roof (+6.80)' }
  DISC = { structure: /\AS-/, architecture: /\AA-/, mep: /\A[PE]-/, site: /\ASite\z/ }

  # [ifc, name, mark, level, tag, parts, attrs]
  #  part: [:box, x0,x1,y0,y1,z0,z1, mat]
  DATA = [
    ["IfcFooting","F1-1A","F1","FND","S-Foundation",[[:box,-0.35,0.65,-0.35,0.65,-1.5,-1.2,"concrete_dark"]],{"Size_m"=>"1.00x1.00x0.30", "Rebar"=>"6-DB12 each way", "Note"=>"Footing size ASSUMED (no soil data, no structural design)"}],
    ["IfcColumn","ST-1A","ST1","FND","S-Column",[[:box,0.025,0.275,0.025,0.275,-1.2,-0.1,"concrete_dark"]],{"Section"=>"0.25x0.25", "Note"=>"stub column"}],
    ["IfcColumn","C1-1A","C1","GF","S-Column",[[:box,0.025,0.275,0.025,0.275,-0.1,3.0,"concrete"]],{"Section"=>"0.25x0.25", "Top_m"=>3.5, "Rebar"=>"4-DB16", "Ties"=>"RB9@0.15", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcFooting","F1-1B","F1","FND","S-Foundation",[[:box,-0.35,0.65,4.5,5.5,-1.5,-1.2,"concrete_dark"]],{"Size_m"=>"1.00x1.00x0.30", "Rebar"=>"6-DB12 each way", "Note"=>"Footing size ASSUMED (no soil data, no structural design)"}],
    ["IfcColumn","ST-1B","ST1","FND","S-Column",[[:box,0.025,0.275,4.875,5.125,-1.2,-0.1,"concrete_dark"]],{"Section"=>"0.25x0.25", "Note"=>"stub column"}],
    ["IfcColumn","C1-1B","C1","GF","S-Column",[[:box,0.025,0.275,4.875,5.125,-0.1,3.0,"concrete"]],{"Section"=>"0.25x0.25", "Top_m"=>3.5, "Rebar"=>"4-DB16", "Ties"=>"RB9@0.15", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcFooting","F1-2B","F1","FND","S-Foundation",[[:box,1.0,2.0,4.5,5.5,-1.5,-1.2,"concrete_dark"]],{"Size_m"=>"1.00x1.00x0.30", "Rebar"=>"6-DB12 each way", "Note"=>"Footing size ASSUMED (no soil data, no structural design)"}],
    ["IfcColumn","ST-2B","ST1","FND","S-Column",[[:box,1.375,1.625,4.875,5.125,-1.2,-0.1,"concrete_dark"]],{"Section"=>"0.25x0.25", "Note"=>"stub column"}],
    ["IfcColumn","C1-2B","C1","GF","S-Column",[[:box,1.375,1.625,4.875,5.125,-0.1,6.3,"concrete"]],{"Section"=>"0.25x0.25", "Top_m"=>6.8, "Rebar"=>"4-DB16", "Ties"=>"RB9@0.15", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcFooting","F1-2C","F1","FND","S-Foundation",[[:box,1.0,2.0,6.8,7.8,-1.5,-1.2,"concrete_dark"]],{"Size_m"=>"1.00x1.00x0.30", "Rebar"=>"6-DB12 each way", "Note"=>"Footing size ASSUMED (no soil data, no structural design)"}],
    ["IfcColumn","ST-2C","ST1","FND","S-Column",[[:box,1.375,1.625,7.175,7.425,-1.2,-0.1,"concrete_dark"]],{"Section"=>"0.25x0.25", "Note"=>"stub column"}],
    ["IfcColumn","C1-2C","C1","GF","S-Column",[[:box,1.375,1.625,7.175,7.425,-0.1,6.3,"concrete"]],{"Section"=>"0.25x0.25", "Top_m"=>6.8, "Rebar"=>"4-DB16", "Ties"=>"RB9@0.15", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcFooting","F1-2D","F1","FND","S-Foundation",[[:box,1.0,2.0,11.75,12.75,-1.5,-1.2,"concrete_dark"]],{"Size_m"=>"1.00x1.00x0.30", "Rebar"=>"6-DB12 each way", "Note"=>"Footing size ASSUMED (no soil data, no structural design)"}],
    ["IfcColumn","ST-2D","ST1","FND","S-Column",[[:box,1.375,1.625,12.125,12.375,-1.2,-0.1,"concrete_dark"]],{"Section"=>"0.25x0.25", "Note"=>"stub column"}],
    ["IfcColumn","C1-2D","C1","GF","S-Column",[[:box,1.375,1.625,12.125,12.375,-0.1,6.3,"concrete"]],{"Section"=>"0.25x0.25", "Top_m"=>6.8, "Rebar"=>"4-DB16", "Ties"=>"RB9@0.15", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcFooting","F1-3A","F1","FND","S-Foundation",[[:box,4.8,5.8,-0.35,0.65,-1.5,-1.2,"concrete_dark"]],{"Size_m"=>"1.00x1.00x0.30", "Rebar"=>"6-DB12 each way", "Note"=>"Footing size ASSUMED (no soil data, no structural design)"}],
    ["IfcColumn","ST-3A","ST1","FND","S-Column",[[:box,5.175,5.425,0.025,0.275,-1.2,-0.1,"concrete_dark"]],{"Section"=>"0.25x0.25", "Note"=>"stub column"}],
    ["IfcColumn","C1-3A","C1","GF","S-Column",[[:box,5.175,5.425,0.025,0.275,-0.1,6.3,"concrete"]],{"Section"=>"0.25x0.25", "Top_m"=>6.8, "Rebar"=>"4-DB16", "Ties"=>"RB9@0.15", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcFooting","F1-3B","F1","FND","S-Foundation",[[:box,4.8,5.8,4.5,5.5,-1.5,-1.2,"concrete_dark"]],{"Size_m"=>"1.00x1.00x0.30", "Rebar"=>"6-DB12 each way", "Note"=>"Footing size ASSUMED (no soil data, no structural design)"}],
    ["IfcColumn","ST-3B","ST1","FND","S-Column",[[:box,5.175,5.425,4.875,5.125,-1.2,-0.1,"concrete_dark"]],{"Section"=>"0.25x0.25", "Note"=>"stub column"}],
    ["IfcColumn","C1-3B","C1","GF","S-Column",[[:box,5.175,5.425,4.875,5.125,-0.1,6.3,"concrete"]],{"Section"=>"0.25x0.25", "Top_m"=>6.8, "Rebar"=>"4-DB16", "Ties"=>"RB9@0.15", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcFooting","F1-3C","F1","FND","S-Foundation",[[:box,4.8,5.8,6.8,7.8,-1.5,-1.2,"concrete_dark"]],{"Size_m"=>"1.00x1.00x0.30", "Rebar"=>"6-DB12 each way", "Note"=>"Footing size ASSUMED (no soil data, no structural design)"}],
    ["IfcColumn","ST-3C","ST1","FND","S-Column",[[:box,5.175,5.425,7.175,7.425,-1.2,-0.1,"concrete_dark"]],{"Section"=>"0.25x0.25", "Note"=>"stub column"}],
    ["IfcColumn","C1-3C","C1","GF","S-Column",[[:box,5.175,5.425,7.175,7.425,-0.1,6.3,"concrete"]],{"Section"=>"0.25x0.25", "Top_m"=>6.8, "Rebar"=>"4-DB16", "Ties"=>"RB9@0.15", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcFooting","F1-3D","F1","FND","S-Foundation",[[:box,4.8,5.8,11.75,12.75,-1.5,-1.2,"concrete_dark"]],{"Size_m"=>"1.00x1.00x0.30", "Rebar"=>"6-DB12 each way", "Note"=>"Footing size ASSUMED (no soil data, no structural design)"}],
    ["IfcColumn","ST-3D","ST1","FND","S-Column",[[:box,5.175,5.425,12.125,12.375,-1.2,-0.1,"concrete_dark"]],{"Section"=>"0.25x0.25", "Note"=>"stub column"}],
    ["IfcColumn","C1-3D","C1","GF","S-Column",[[:box,5.175,5.425,12.125,12.375,-0.1,6.3,"concrete"]],{"Section"=>"0.25x0.25", "Top_m"=>6.8, "Rebar"=>"4-DB16", "Ties"=>"RB9@0.15", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcFooting","F1-4A","F1","FND","S-Foundation",[[:box,9.35,10.35,-0.35,0.65,-1.5,-1.2,"concrete_dark"]],{"Size_m"=>"1.00x1.00x0.30", "Rebar"=>"6-DB12 each way", "Note"=>"Footing size ASSUMED (no soil data, no structural design)"}],
    ["IfcColumn","ST-4A","ST1","FND","S-Column",[[:box,9.725,9.975,0.025,0.275,-1.2,-0.1,"concrete_dark"]],{"Section"=>"0.25x0.25", "Note"=>"stub column"}],
    ["IfcColumn","C1-4A","C1","GF","S-Column",[[:box,9.725,9.975,0.025,0.275,-0.1,6.3,"concrete"]],{"Section"=>"0.25x0.25", "Top_m"=>6.8, "Rebar"=>"4-DB16", "Ties"=>"RB9@0.15", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcFooting","F1-4B","F1","FND","S-Foundation",[[:box,9.35,10.35,4.5,5.5,-1.5,-1.2,"concrete_dark"]],{"Size_m"=>"1.00x1.00x0.30", "Rebar"=>"6-DB12 each way", "Note"=>"Footing size ASSUMED (no soil data, no structural design)"}],
    ["IfcColumn","ST-4B","ST1","FND","S-Column",[[:box,9.725,9.975,4.875,5.125,-1.2,-0.1,"concrete_dark"]],{"Section"=>"0.25x0.25", "Note"=>"stub column"}],
    ["IfcColumn","C1-4B","C1","GF","S-Column",[[:box,9.725,9.975,4.875,5.125,-0.1,6.3,"concrete"]],{"Section"=>"0.25x0.25", "Top_m"=>6.8, "Rebar"=>"4-DB16", "Ties"=>"RB9@0.15", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcFooting","F1-4C","F1","FND","S-Foundation",[[:box,9.35,10.35,6.8,7.8,-1.5,-1.2,"concrete_dark"]],{"Size_m"=>"1.00x1.00x0.30", "Rebar"=>"6-DB12 each way", "Note"=>"Footing size ASSUMED (no soil data, no structural design)"}],
    ["IfcColumn","ST-4C","ST1","FND","S-Column",[[:box,9.725,9.975,7.175,7.425,-1.2,-0.1,"concrete_dark"]],{"Section"=>"0.25x0.25", "Note"=>"stub column"}],
    ["IfcColumn","C1-4C","C1","GF","S-Column",[[:box,9.725,9.975,7.175,7.425,-0.1,6.3,"concrete"]],{"Section"=>"0.25x0.25", "Top_m"=>6.8, "Rebar"=>"4-DB16", "Ties"=>"RB9@0.15", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcFooting","F1-4D","F1","FND","S-Foundation",[[:box,9.35,10.35,11.75,12.75,-1.5,-1.2,"concrete_dark"]],{"Size_m"=>"1.00x1.00x0.30", "Rebar"=>"6-DB12 each way", "Note"=>"Footing size ASSUMED (no soil data, no structural design)"}],
    ["IfcColumn","ST-4D","ST1","FND","S-Column",[[:box,9.725,9.975,12.125,12.375,-1.2,-0.1,"concrete_dark"]],{"Section"=>"0.25x0.25", "Note"=>"stub column"}],
    ["IfcColumn","C1-4D","C1","GF","S-Column",[[:box,9.725,9.975,12.125,12.375,-0.1,6.3,"concrete"]],{"Section"=>"0.25x0.25", "Top_m"=>6.8, "Rebar"=>"4-DB16", "Ties"=>"RB9@0.15", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcBeam","GB1-A","GB1","GF","S-Beam",[[:box,5.2,9.95,0.05,0.25,-0.1,0.3,"concrete"]],{"Section"=>"0.20x0.40", "Top_m"=>0.3, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcBeam","GB1-B","GB1","GF","S-Beam",[[:box,1.4,9.95,4.9,5.1,-0.1,0.3,"concrete"]],{"Section"=>"0.20x0.40", "Top_m"=>0.3, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcBeam","GB1-C","GB1","GF","S-Beam",[[:box,1.4,9.95,7.2,7.4,-0.1,0.3,"concrete"]],{"Section"=>"0.20x0.40", "Top_m"=>0.3, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcBeam","GB1-D","GB1","GF","S-Beam",[[:box,1.4,9.95,12.15,12.35,-0.1,0.3,"concrete"]],{"Section"=>"0.20x0.40", "Top_m"=>0.3, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcBeam","GB1-2","GB1","GF","S-Beam",[[:box,1.4,1.6,5.1,12.15,-0.1,0.3,"concrete"]],{"Section"=>"0.20x0.40", "Top_m"=>0.3, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcBeam","GB1-3","GB1","GF","S-Beam",[[:box,5.2,5.4,0.25,12.15,-0.1,0.3,"concrete"]],{"Section"=>"0.20x0.40", "Top_m"=>0.3, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcBeam","GB1-4","GB1","GF","S-Beam",[[:box,9.75,9.95,0.25,12.15,-0.1,0.3,"concrete"]],{"Section"=>"0.20x0.40", "Top_m"=>0.3, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcBeam","B1-A","B1","1F","S-Beam",[[:box,0.05,9.95,0.05,0.25,3.0,3.5,"concrete"]],{"Section"=>"0.20x0.50", "Top_m"=>3.5, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcBeam","B1-B","B1","1F","S-Beam",[[:box,0.05,9.95,4.9,5.1,3.0,3.5,"concrete"]],{"Section"=>"0.20x0.50", "Top_m"=>3.5, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcBeam","B1-C","B1","1F","S-Beam",[[:box,1.4,9.95,7.2,7.4,3.0,3.5,"concrete"]],{"Section"=>"0.20x0.50", "Top_m"=>3.5, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcBeam","B1-D","B1","1F","S-Beam",[[:box,1.4,9.95,12.15,12.35,3.0,3.5,"concrete"]],{"Section"=>"0.20x0.50", "Top_m"=>3.5, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcBeam","B1-1","B1","1F","S-Beam",[[:box,0.05,0.25,0.25,4.9,3.0,3.5,"concrete"]],{"Section"=>"0.20x0.50", "Top_m"=>3.5, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcBeam","B1-2","B1","1F","S-Beam",[[:box,1.4,1.6,5.1,12.15,3.0,3.5,"concrete"]],{"Section"=>"0.20x0.50", "Top_m"=>3.5, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcBeam","B1-3","B1","1F","S-Beam",[[:box,5.2,5.4,0.25,12.15,3.0,3.5,"concrete"]],{"Section"=>"0.20x0.50", "Top_m"=>3.5, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcBeam","B1-4","B1","1F","S-Beam",[[:box,9.75,9.95,0.25,12.15,3.0,3.5,"concrete"]],{"Section"=>"0.20x0.50", "Top_m"=>3.5, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcBeam","RB1-A","RB1","ROOF","S-RoofBeam",[[:box,5.2,9.95,0.05,0.25,6.3,6.8,"concrete"]],{"Section"=>"0.20x0.50", "Top_m"=>6.8, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcBeam","RB1-B","RB1","ROOF","S-RoofBeam",[[:box,1.4,9.95,4.9,5.1,6.3,6.8,"concrete"]],{"Section"=>"0.20x0.50", "Top_m"=>6.8, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcBeam","RB1-C","RB1","ROOF","S-RoofBeam",[[:box,1.4,9.95,7.2,7.4,6.3,6.8,"concrete"]],{"Section"=>"0.20x0.50", "Top_m"=>6.8, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcBeam","RB1-D","RB1","ROOF","S-RoofBeam",[[:box,1.4,9.95,12.15,12.35,6.3,6.8,"concrete"]],{"Section"=>"0.20x0.50", "Top_m"=>6.8, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcBeam","RB1-2","RB1","ROOF","S-RoofBeam",[[:box,1.4,1.6,5.1,12.15,6.3,6.8,"concrete"]],{"Section"=>"0.20x0.50", "Top_m"=>6.8, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcBeam","RB1-3","RB1","ROOF","S-RoofBeam",[[:box,5.2,5.4,0.25,12.15,6.3,6.8,"concrete"]],{"Section"=>"0.20x0.50", "Top_m"=>6.8, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcBeam","RB1-4","RB1","ROOF","S-RoofBeam",[[:box,9.75,9.95,0.25,12.15,6.3,6.8,"concrete"]],{"Section"=>"0.20x0.50", "Top_m"=>6.8, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcSlab","S1-GF-living","S1","GF","S-Slab",[[:box,5.3,10.0,0,5.0,0.18,0.3,"concrete"]],{"Thickness_m"=>0.12, "Area_m2"=>23.5, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcSlab","S1-GF-rear","S1","GF","S-Slab",[[:box,1.4,10.0,5.0,12.4,0.18,0.3,"concrete"]],{"Thickness_m"=>0.12, "Area_m2"=>63.64, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcSlab","S0-carport","S0","GF","S-Slab",[[:box,0,5.3,0,5.0,0.0,0.12,"paving"]],{"Thickness_m"=>0.12, "Area_m2"=>26.5, "Description"=>"Slab on grade, carport (2 cars)", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcSlab","S2-1F-front","S2","1F","S-Slab",[[:box,0,7.2,-0.3,5.0,3.35,3.5,"concrete"],[:box,7.2,10.0,0.05,5.0,3.35,3.5,"concrete"]],{"Thickness_m"=>0.15, "Area_m2"=>53.0, "Description"=>"Upper floor + balcony + carport canopy", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcSlab","S2-1F-rear","S2","1F","S-Slab",[[:box,1.4,6.7,5.0,12.4,3.35,3.5,"concrete"],[:box,6.7,10.0,8.5,12.4,3.35,3.5,"concrete"]],{"Thickness_m"=>0.15, "Area_m2"=>52.09, "Description"=>"stair opening 3.15x3.50", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcSlab","S3-canopy-band","S3","1F","S-Slab",[[:box,0,7.15,-0.3,0.05,3.0,3.35,"concrete"]],{"Description"=>"Deep white edge band of carport canopy / balcony (render)", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcSlab","RS-roof","RS","ROOF","S-Slab",[[:box,1.1,10.2,-0.8,12.6,6.65,6.8,"concrete"]],{"Thickness_m"=>0.15, "Area_m2"=>121.94, "Description"=>"Flat RC roof, 0.80 m front overhang", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcStair","ST1","ST1","GF","S-Stair",[[:box,6.8,8.25,5.0,5.27,0.3,0.46,"concrete"],[:box,6.8,8.25,5.27,5.54,0.32,0.62,"concrete"],[:box,6.8,8.25,5.54,5.81,0.48,0.78,"concrete"],[:box,6.8,8.25,5.81,6.08,0.64,0.94,"concrete"],[:box,6.8,8.25,6.08,6.35,0.8,1.1,"concrete"],[:box,6.8,8.25,6.35,6.62,0.96,1.26,"concrete"],[:box,6.8,8.25,6.62,6.89,1.12,1.42,"concrete"],[:box,6.8,8.25,6.89,7.16,1.28,1.58,"concrete"],[:box,6.8,8.25,7.16,7.43,1.44,1.74,"concrete"],[:box,6.8,8.25,7.43,7.7,1.6,1.9,"concrete"],[:box,6.8,9.85,7.43,8.5,1.75,1.9,"concrete"],[:box,8.35,9.85,7.16,7.43,1.76,2.06,"concrete"],[:box,8.35,9.85,6.89,7.16,1.92,2.22,"concrete"],[:box,8.35,9.85,6.62,6.89,2.08,2.38,"concrete"],[:box,8.35,9.85,6.35,6.62,2.24,2.54,"concrete"],[:box,8.35,9.85,6.08,6.35,2.4,2.7,"concrete"],[:box,8.35,9.85,5.81,6.08,2.56,2.86,"concrete"],[:box,8.35,9.85,5.54,5.81,2.72,3.02,"concrete"],[:box,8.35,9.85,5.27,5.54,2.88,3.18,"concrete"],[:box,8.35,9.85,5.0,5.27,3.04,3.34,"concrete"]],{"Risers"=>20, "Riser_m"=>0.16, "Tread_m"=>0.27, "Description"=>"RC U-stair 2 flights x 1.45 m, landing +1.90", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWall","W-GF-front-entry","P1","GF","A-Wall",[[:box,5.3,5.55,0.0,0.2,0.3,3.0,"wall_white"],[:box,5.55,6.45,0.0,0.2,2.5,3.0,"wall_white"],[:box,6.45,7.2,0.0,0.2,0.3,3.0,"wall_white"]],{"Thickness_m"=>0.2, "Height_m"=>2.7, "NetArea_m2(one face)"=>3.15, "IsExternal"=>true, "Description"=>"RC frame infill: AAC block, plaster + paint", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcDoor","D1","D1","GF","A-Door",[[:box,5.55,6.45,0.07,0.13,2.45,2.5,"frame_black"],[:box,5.55,5.6,0.07,0.13,0.3,2.45,"frame_black"],[:box,6.4,6.45,0.07,0.13,0.3,2.45,"frame_black"],[:box,5.61,6.39,0.085,0.115,0.3,2.45,"wood"]],{"Size_WxH_m"=>"0.90x2.20", "Leaves"=>1, "Description"=>"Entrance door, solid timber, black frame", "SillFromFloor_m"=>0.0, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWall","W-GF-front-low","P1","GF","A-Wall",[[:box,7.2,9.0,0.0,0.2,0.3,0.9,"wall_white"]],{"Thickness_m"=>0.2, "Height_m"=>0.6, "NetArea_m2(one face)"=>1.08, "IsExternal"=>true, "Description"=>"RC frame infill: AAC block, plaster + paint", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWall","W-GF-carport-side","P1","GF","A-Wall",[[:box,5.2,5.4,0.0,5.0,0.3,3.0,"wall_white"]],{"Thickness_m"=>0.2, "Height_m"=>2.7, "NetArea_m2(one face)"=>13.5, "IsExternal"=>true, "Description"=>"RC frame infill: AAC block, plaster + paint", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWall","W-GF-carport-back","P1","GF","A-Wall",[[:box,1.4,3.6,4.9,5.1,0.3,3.0,"wall_white"],[:box,3.6,5.0,4.9,5.1,0.3,1.9,"wall_white"],[:box,3.6,5.0,4.9,5.1,2.3,3.0,"wall_white"],[:box,5.0,5.3,4.9,5.1,0.3,3.0,"wall_white"]],{"Thickness_m"=>0.2, "Height_m"=>2.7, "NetArea_m2(one face)"=>9.97, "IsExternal"=>true, "Description"=>"RC frame infill: AAC block, plaster + paint", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWindow","W1-WC","W1","GF","A-Window",[[:box,3.6,5.0,4.97,5.03,2.25,2.3,"frame_black"],[:box,3.6,3.65,4.97,5.03,1.9,2.25,"frame_black"],[:box,4.95,5.0,4.97,5.03,1.9,2.25,"frame_black"],[:box,3.65,4.95,4.97,5.03,1.9,1.95,"frame_black"],[:box,3.66,4.29,4.994,5.006,1.95,2.25,"glass"],[:box,4.31,4.94,4.994,5.006,1.95,2.25,"glass"],[:box,4.28,4.32,4.97,5.03,1.95,2.25,"frame_black"]],{"Size_WxH_m"=>"1.40x0.40", "Leaves"=>2, "Description"=>"High strip window (WC / laundry)", "SillFromFloor_m"=>1.6, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWall","W-GF-left","P1","GF","A-Wall",[[:box,1.4,1.6,5.0,12.4,0.3,3.0,"wall_white"]],{"Thickness_m"=>0.2, "Height_m"=>2.7, "NetArea_m2(one face)"=>19.98, "IsExternal"=>true, "Description"=>"RC frame infill: AAC block, plaster + paint", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWall","W-GF-back","P1","GF","A-Wall",[[:box,1.4,2.2,12.2,12.4,0.3,3.0,"wall_white"],[:box,2.2,4.4,12.2,12.4,0.3,0.4,"wall_white"],[:box,2.2,4.4,12.2,12.4,2.6,3.0,"wall_white"],[:box,4.4,6.3,12.2,12.4,0.3,3.0,"wall_white"],[:box,6.3,8.1,12.2,12.4,0.3,1.4,"wall_white"],[:box,6.3,8.1,12.2,12.4,2.4,3.0,"wall_white"],[:box,8.1,10.0,12.2,12.4,0.3,3.0,"wall_white"]],{"Thickness_m"=>0.2, "Height_m"=>2.7, "NetArea_m2(one face)"=>16.58, "IsExternal"=>true, "Description"=>"RC frame infill: AAC block, plaster + paint", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWindow","W2-DIN","W2","GF","A-Window",[[:box,2.2,4.4,12.27,12.33,2.55,2.6,"frame_black"],[:box,2.2,2.25,12.27,12.33,0.4,2.55,"frame_black"],[:box,4.35,4.4,12.27,12.33,0.4,2.55,"frame_black"],[:box,2.25,4.35,12.27,12.33,0.4,0.45,"frame_black"],[:box,2.26,3.29,12.294,12.306,0.45,2.55,"glass"],[:box,3.31,4.34,12.294,12.306,0.45,2.55,"glass"],[:box,3.28,3.32,12.27,12.33,0.45,2.55,"frame_black"]],{"Size_WxH_m"=>"2.20x2.20", "Leaves"=>2, "Description"=>"Sliding glass door to rear garden (dining)", "SillFromFloor_m"=>0.1, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWindow","W3-KIT","W3","GF","A-Window",[[:box,6.3,8.1,12.27,12.33,2.35,2.4,"frame_black"],[:box,6.3,6.35,12.27,12.33,1.4,2.35,"frame_black"],[:box,8.05,8.1,12.27,12.33,1.4,2.35,"frame_black"],[:box,6.35,8.05,12.27,12.33,1.4,1.45,"frame_black"],[:box,6.36,7.19,12.294,12.306,1.45,2.35,"glass"],[:box,7.21,8.04,12.294,12.306,1.45,2.35,"glass"],[:box,7.18,7.22,12.27,12.33,1.45,2.35,"frame_black"]],{"Size_WxH_m"=>"1.80x1.00", "Leaves"=>2, "Description"=>"Kitchen window over counter", "SillFromFloor_m"=>1.1, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWall","W-GF-right","P1","GF","A-Wall",[[:box,9.8,10.0,0.0,1.5,0.3,3.0,"wall_white"],[:box,9.8,10.0,1.5,3.5,0.3,1.2,"wall_white"],[:box,9.8,10.0,1.5,3.5,2.6,3.0,"wall_white"],[:box,9.8,10.0,3.5,12.4,0.3,3.0,"wall_white"]],{"Thickness_m"=>0.2, "Height_m"=>2.7, "NetArea_m2(one face)"=>30.68, "IsExternal"=>true, "Description"=>"RC frame infill: AAC block, plaster + paint", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWindow","W4-LIV","W4","GF","A-Window",[[:box,9.87,9.93,1.5,3.5,2.55,2.6,"frame_black"],[:box,9.87,9.93,1.5,1.55,1.2,2.55,"frame_black"],[:box,9.87,9.93,3.45,3.5,1.2,2.55,"frame_black"],[:box,9.87,9.93,1.55,3.45,1.2,1.25,"frame_black"],[:box,9.894,9.906,1.56,2.49,1.25,2.55,"glass"],[:box,9.894,9.906,2.51,3.44,1.25,2.55,"glass"],[:box,9.87,9.93,2.48,2.52,1.25,2.55,"frame_black"]],{"Size_WxH_m"=>"2.00x1.40", "Leaves"=>2, "Description"=>"Living room side window", "SillFromFloor_m"=>0.9, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWall","W-GF-wc-split","P2","GF","A-Wall",[[:box,3.05,3.15,5.1,7.15,0.3,3.35,"wall_white"]],{"Thickness_m"=>0.1, "Height_m"=>3.05, "NetArea_m2(one face)"=>6.25, "IsExternal"=>false, "Description"=>"RC frame infill: AAC block, plaster + paint", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWall","W-GF-service","P2","GF","A-Wall",[[:box,1.6,1.9,7.15,7.25,0.3,3.0,"wall_white"],[:box,1.9,2.7,7.15,7.25,2.4,3.0,"wall_white"],[:box,2.7,5.3,7.15,7.25,0.3,3.0,"wall_white"]],{"Thickness_m"=>0.1, "Height_m"=>2.7, "NetArea_m2(one face)"=>8.31, "IsExternal"=>false, "Description"=>"RC frame infill: AAC block, plaster + paint", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcDoor","D3-LDY","D3","GF","A-Door",[[:box,1.9,2.7,7.17,7.23,2.35,2.4,"frame_black"],[:box,1.9,1.95,7.17,7.23,0.3,2.35,"frame_black"],[:box,2.65,2.7,7.17,7.23,0.3,2.35,"frame_black"],[:box,1.96,2.64,7.185,7.215,0.3,2.35,"wood"]],{"Size_WxH_m"=>"0.80x2.10", "Leaves"=>1, "Description"=>"Laundry door", "SillFromFloor_m"=>0.0, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWall","W-GF-wc-hall","P2","GF","A-Wall",[[:box,5.25,5.35,5.0,5.7,0.3,3.0,"wall_white"],[:box,5.25,5.35,5.7,6.45,2.4,3.0,"wall_white"],[:box,5.25,5.35,6.45,7.2,0.3,3.0,"wall_white"]],{"Thickness_m"=>0.1, "Height_m"=>2.7, "NetArea_m2(one face)"=>4.37, "IsExternal"=>false, "Description"=>"RC frame infill: AAC block, plaster + paint", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcDoor","D2-WC","D2","GF","A-Door",[[:box,5.27,5.33,5.7,6.45,2.35,2.4,"frame_black"],[:box,5.27,5.33,5.7,5.75,0.3,2.35,"frame_black"],[:box,5.27,5.33,6.4,6.45,0.3,2.35,"frame_black"],[:box,5.285,5.315,5.76,6.39,0.3,2.35,"wood"]],{"Size_WxH_m"=>"0.75x2.10", "Leaves"=>1, "Description"=>"Guest WC door", "SillFromFloor_m"=>0.0, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcCurtainWall","CW1","CW1","GF","A-Window",[[:box,7.25,9.0,-0.02,0.0,0.9,5.65,"glass"],[:box,7.23,7.29,-0.06,0.0,0.9,5.65,"frame_black"],[:box,8.1,8.16,-0.06,0.0,0.9,5.65,"frame_black"],[:box,8.94,9.0,-0.06,0.0,0.9,5.65,"frame_black"],[:box,7.23,9.0,-0.06,0.0,0.87,0.93,"frame_black"],[:box,7.23,9.0,-0.06,0.0,2.17,2.23,"frame_black"],[:box,7.23,9.0,-0.06,0.0,3.42,3.48,"frame_black"],[:box,7.23,9.0,-0.06,0.0,4.52,4.58,"frame_black"],[:box,7.23,9.0,-0.06,0.0,5.62,5.68,"frame_black"]],{"Size_WxH_m"=>"1.80x4.75", "Leaves"=>8, "Description"=>"Double-height aluminium curtain wall, 2x4 panels (render)", "SillFromFloor_m"=>0.6, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcCovering","STONE-FIN","ST","GF","A-Cladding",[[:box,9.0,10.0,-0.3,0.1,0.9,6.9,"stone"]],{"PredefinedType"=>"CLADDING", "Description"=>"Vertical wall fin clad in split-face stone (render)", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcCovering","STONE-PLANTER","ST","GF","A-Cladding",[[:box,6.7,10.0,-0.6,0.1,0.3,0.9,"stone"]],{"PredefinedType"=>"CLADDING", "Description"=>"Stone-clad planter band under curtain wall", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWall","W-1F-front","P1","1F","A-Wall",[[:box,1.4,3.6,1.6,1.8,3.5,6.65,"wall_white"],[:box,3.6,5.4,1.6,1.8,5.9,6.65,"wall_white"],[:box,5.4,6.5,1.6,1.8,3.5,6.65,"wall_white"]],{"Thickness_m"=>0.2, "Height_m"=>3.15, "NetArea_m2(one face)"=>11.74, "IsExternal"=>true, "Description"=>"RC frame infill: AAC block, plaster + paint", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcDoor","D4-BAL","D4","1F","A-Door",[[:box,3.6,5.4,1.67,1.73,5.85,5.9,"frame_black"],[:box,3.6,3.65,1.67,1.73,3.5,5.85,"frame_black"],[:box,5.35,5.4,1.67,1.73,3.5,5.85,"frame_black"],[:box,3.66,4.49,1.694,1.706,3.5,5.85,"glass"],[:box,4.51,5.34,1.694,1.706,3.5,5.85,"glass"],[:box,4.48,4.52,1.67,1.73,3.5,5.85,"frame_black"]],{"Size_WxH_m"=>"1.80x2.40", "Leaves"=>2, "Description"=>"Sliding glass door, master bedroom to balcony", "SillFromFloor_m"=>0.0, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWall","W-1F-front-r2","P1","1F","A-Wall",[[:box,9.0,9.8,0.0,0.2,5.65,6.3,"wall_white"]],{"Thickness_m"=>0.2, "Height_m"=>0.65, "NetArea_m2(one face)"=>0.52, "IsExternal"=>true, "Description"=>"RC frame infill: AAC block, plaster + paint", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWall","W-1F-front-top","P1","1F","A-Wall",[[:box,7.2,9.0,0.0,0.2,5.65,6.3,"wall_white"]],{"Thickness_m"=>0.2, "Height_m"=>0.65, "NetArea_m2(one face)"=>1.17, "IsExternal"=>true, "Description"=>"RC frame infill: AAC block, plaster + paint", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWall","W-1F-left","P1","1F","A-Wall",[[:box,1.4,1.6,1.7,9.2,3.5,6.3,"wall_white"],[:box,1.4,1.6,9.2,10.8,3.5,4.4,"wall_white"],[:box,1.4,1.6,9.2,10.8,5.7,6.3,"wall_white"],[:box,1.4,1.6,10.8,12.4,3.5,6.3,"wall_white"]],{"Thickness_m"=>0.2, "Height_m"=>2.8, "NetArea_m2(one face)"=>27.88, "IsExternal"=>true, "Description"=>"RC frame infill: AAC block, plaster + paint", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWindow","W5-BED2","W5","1F","A-Window",[[:box,1.47,1.53,9.2,10.8,5.65,5.7,"frame_black"],[:box,1.47,1.53,9.2,9.25,4.4,5.65,"frame_black"],[:box,1.47,1.53,10.75,10.8,4.4,5.65,"frame_black"],[:box,1.47,1.53,9.25,10.75,4.4,4.45,"frame_black"],[:box,1.494,1.506,9.26,9.99,4.45,5.65,"glass"],[:box,1.494,1.506,10.01,10.74,4.45,5.65,"glass"],[:box,1.47,1.53,9.98,10.02,4.45,5.65,"frame_black"]],{"Size_WxH_m"=>"1.60x1.30", "Leaves"=>2, "Description"=>"Bedroom 2 side window", "SillFromFloor_m"=>0.9, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWall","W-1F-back","P1","1F","A-Wall",[[:box,1.4,2.4,12.2,12.4,3.5,6.3,"wall_white"],[:box,2.4,4.2,12.2,12.4,3.5,4.4,"wall_white"],[:box,2.4,4.2,12.2,12.4,5.7,6.3,"wall_white"],[:box,4.2,5.4,12.2,12.4,3.5,6.3,"wall_white"],[:box,5.4,6.2,12.2,12.4,3.5,5.1,"wall_white"],[:box,5.4,6.2,12.2,12.4,5.7,6.3,"wall_white"],[:box,6.2,7.4,12.2,12.4,3.5,6.3,"wall_white"],[:box,7.4,9.2,12.2,12.4,3.5,4.4,"wall_white"],[:box,7.4,9.2,12.2,12.4,5.7,6.3,"wall_white"],[:box,9.2,10.0,12.2,12.4,3.5,6.3,"wall_white"]],{"Thickness_m"=>0.2, "Height_m"=>2.8, "NetArea_m2(one face)"=>18.92, "IsExternal"=>true, "Description"=>"RC frame infill: AAC block, plaster + paint", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWindow","W6-BED2","W6","1F","A-Window",[[:box,2.4,4.2,12.27,12.33,5.65,5.7,"frame_black"],[:box,2.4,2.45,12.27,12.33,4.4,5.65,"frame_black"],[:box,4.15,4.2,12.27,12.33,4.4,5.65,"frame_black"],[:box,2.45,4.15,12.27,12.33,4.4,4.45,"frame_black"],[:box,2.46,3.29,12.294,12.306,4.45,5.65,"glass"],[:box,3.31,4.14,12.294,12.306,4.45,5.65,"glass"],[:box,3.28,3.32,12.27,12.33,4.45,5.65,"frame_black"]],{"Size_WxH_m"=>"1.80x1.30", "Leaves"=>2, "Description"=>"Bedroom 2 window", "SillFromFloor_m"=>0.9, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWindow","W7-BATH","W7","1F","A-Window",[[:box,5.4,6.2,12.27,12.33,5.65,5.7,"frame_black"],[:box,5.4,5.45,12.27,12.33,5.1,5.65,"frame_black"],[:box,6.15,6.2,12.27,12.33,5.1,5.65,"frame_black"],[:box,5.45,6.15,12.27,12.33,5.1,5.15,"frame_black"],[:box,5.46,6.14,12.294,12.306,5.15,5.65,"glass"]],{"Size_WxH_m"=>"0.80x0.60", "Leaves"=>1, "Description"=>"Shared bath high window", "SillFromFloor_m"=>1.6, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWindow","W6-BED3","W6","1F","A-Window",[[:box,7.4,9.2,12.27,12.33,5.65,5.7,"frame_black"],[:box,7.4,7.45,12.27,12.33,4.4,5.65,"frame_black"],[:box,9.15,9.2,12.27,12.33,4.4,5.65,"frame_black"],[:box,7.45,9.15,12.27,12.33,4.4,4.45,"frame_black"],[:box,7.46,8.29,12.294,12.306,4.45,5.65,"glass"],[:box,8.31,9.14,12.294,12.306,4.45,5.65,"glass"],[:box,8.28,8.32,12.27,12.33,4.45,5.65,"frame_black"]],{"Size_WxH_m"=>"1.80x1.30", "Leaves"=>2, "Description"=>"Bedroom 3 window", "SillFromFloor_m"=>0.9, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWall","W-1F-right","P1","1F","A-Wall",[[:box,9.8,10.0,0.0,2.0,3.5,6.3,"wall_white"],[:box,9.8,10.0,2.0,2.8,3.5,5.1,"wall_white"],[:box,9.8,10.0,2.0,2.8,5.7,6.3,"wall_white"],[:box,9.8,10.0,2.8,12.4,3.5,6.3,"wall_white"]],{"Thickness_m"=>0.2, "Height_m"=>2.8, "NetArea_m2(one face)"=>34.24, "IsExternal"=>true, "Description"=>"RC frame infill: AAC block, plaster + paint", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWindow","W7-MBATH","W7","1F","A-Window",[[:box,9.87,9.93,2.0,2.8,5.65,5.7,"frame_black"],[:box,9.87,9.93,2.0,2.05,5.1,5.65,"frame_black"],[:box,9.87,9.93,2.75,2.8,5.1,5.65,"frame_black"],[:box,9.87,9.93,2.05,2.75,5.1,5.15,"frame_black"],[:box,9.894,9.906,2.06,2.74,5.15,5.65,"glass"]],{"Size_WxH_m"=>"0.80x0.60", "Leaves"=>1, "Description"=>"Master bath high window", "SillFromFloor_m"=>1.6, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWall","W-1F-master-bath","P2","1F","A-Wall",[[:box,6.45,6.55,0.2,2.8,3.5,6.65,"wall_white"],[:box,6.45,6.55,2.8,3.55,5.6,6.65,"wall_white"],[:box,6.45,6.55,3.55,4.1,3.5,6.65,"wall_white"],[:box,6.45,6.55,4.1,4.9,5.6,6.65,"wall_white"],[:box,6.45,6.55,4.9,5.0,3.5,6.65,"wall_white"]],{"Thickness_m"=>0.1, "Height_m"=>3.15, "NetArea_m2(one face)"=>11.86, "IsExternal"=>false, "Description"=>"RC frame infill: AAC block, plaster + paint", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcDoor","D5-MB","D5","1F","A-Door",[[:box,6.47,6.53,2.8,3.55,5.55,5.6,"frame_black"],[:box,6.47,6.53,2.8,2.85,3.5,5.55,"frame_black"],[:box,6.47,6.53,3.5,3.55,3.5,5.55,"frame_black"],[:box,6.485,6.515,2.86,3.49,3.5,5.55,"wood"]],{"Size_WxH_m"=>"0.75x2.10", "Leaves"=>1, "Description"=>"Master bath door", "SillFromFloor_m"=>0.0, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcDoor","D6-MBR","D6","1F","A-Door",[[:box,6.47,6.53,4.1,4.9,5.55,5.6,"frame_black"],[:box,6.47,6.53,4.1,4.15,3.5,5.55,"frame_black"],[:box,6.47,6.53,4.85,4.9,3.5,5.55,"frame_black"],[:box,6.485,6.515,4.16,4.84,3.5,5.55,"wood"]],{"Size_WxH_m"=>"0.80x2.10", "Leaves"=>1, "Description"=>"Master bedroom door (from stair hall)", "SillFromFloor_m"=>0.0, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWall","W-1F-mbath-back","P2","1F","A-Wall",[[:box,6.55,9.8,3.95,4.05,3.5,6.65,"wall_white"]],{"Thickness_m"=>0.1, "Height_m"=>3.15, "NetArea_m2(one face)"=>10.24, "IsExternal"=>false, "Description"=>"RC frame infill: AAC block, plaster + paint", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWall","W-1F-closet","P2","1F","A-Wall",[[:box,1.6,2.4,4.95,5.05,3.5,6.3,"wall_white"],[:box,2.4,3.2,4.95,5.05,5.6,6.3,"wall_white"],[:box,3.2,6.5,4.95,5.05,3.5,6.3,"wall_white"]],{"Thickness_m"=>0.1, "Height_m"=>2.8, "NetArea_m2(one face)"=>12.04, "IsExternal"=>false, "Description"=>"RC frame infill: AAC block, plaster + paint", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcDoor","D7-WIC","D7","1F","A-Door",[[:box,2.4,3.2,4.97,5.03,5.55,5.6,"frame_black"],[:box,2.4,2.45,4.97,5.03,3.5,5.55,"frame_black"],[:box,3.15,3.2,4.97,5.03,3.5,5.55,"frame_black"],[:box,2.46,3.14,4.985,5.015,3.5,5.55,"wood"]],{"Size_WxH_m"=>"0.80x2.10", "Leaves"=>1, "Description"=>"Walk-in closet door", "SillFromFloor_m"=>0.0, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWall","W-1F-closet-hall","P2","1F","A-Wall",[[:box,3.75,3.85,5.0,7.3,3.5,6.65,"wall_white"]],{"Thickness_m"=>0.1, "Height_m"=>3.15, "NetArea_m2(one face)"=>7.24, "IsExternal"=>false, "Description"=>"RC frame infill: AAC block, plaster + paint", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWall","W-1F-bed2-front","P2","1F","A-Wall",[[:box,1.6,4.0,7.3,7.4,3.5,6.3,"wall_white"],[:box,4.0,4.8,7.3,7.4,5.6,6.3,"wall_white"],[:box,4.8,6.7,7.3,7.4,3.5,6.3,"wall_white"]],{"Thickness_m"=>0.1, "Height_m"=>2.8, "NetArea_m2(one face)"=>12.6, "IsExternal"=>false, "Description"=>"RC frame infill: AAC block, plaster + paint", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcDoor","D6-BED2","D6","1F","A-Door",[[:box,4.0,4.8,7.32,7.38,5.55,5.6,"frame_black"],[:box,4.0,4.05,7.32,7.38,3.5,5.55,"frame_black"],[:box,4.75,4.8,7.32,7.38,3.5,5.55,"frame_black"],[:box,4.06,4.74,7.335,7.365,3.5,5.55,"wood"]],{"Size_WxH_m"=>"0.80x2.10", "Leaves"=>1, "Description"=>"Bedroom 2 door", "SillFromFloor_m"=>0.0, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWall","W-1F-bed2-bath","P2","1F","A-Wall",[[:box,4.95,5.05,7.4,12.2,3.5,6.65,"wall_white"]],{"Thickness_m"=>0.1, "Height_m"=>3.15, "NetArea_m2(one face)"=>15.12, "IsExternal"=>false, "Description"=>"RC frame infill: AAC block, plaster + paint", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWall","W-1F-landing","P2","1F","A-Wall",[[:box,5.05,5.4,8.5,8.6,3.5,6.65,"wall_white"],[:box,5.4,6.15,8.5,8.6,5.6,6.65,"wall_white"],[:box,6.15,7.0,8.5,8.6,3.5,6.65,"wall_white"],[:box,7.0,7.8,8.5,8.6,5.6,6.65,"wall_white"],[:box,7.8,9.8,8.5,8.6,3.5,6.65,"wall_white"]],{"Thickness_m"=>0.1, "Height_m"=>3.15, "NetArea_m2(one face)"=>11.71, "IsExternal"=>false, "Description"=>"RC frame infill: AAC block, plaster + paint", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcDoor","D5-BATH","D5","1F","A-Door",[[:box,5.4,6.15,8.52,8.58,5.55,5.6,"frame_black"],[:box,5.4,5.45,8.52,8.58,3.5,5.55,"frame_black"],[:box,6.1,6.15,8.52,8.58,3.5,5.55,"frame_black"],[:box,5.46,6.09,8.535,8.565,3.5,5.55,"wood"]],{"Size_WxH_m"=>"0.75x2.10", "Leaves"=>1, "Description"=>"Shared bath door", "SillFromFloor_m"=>0.0, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcDoor","D6-BED3","D6","1F","A-Door",[[:box,7.0,7.8,8.52,8.58,5.55,5.6,"frame_black"],[:box,7.0,7.05,8.52,8.58,3.5,5.55,"frame_black"],[:box,7.75,7.8,8.52,8.58,3.5,5.55,"frame_black"],[:box,7.06,7.74,8.535,8.565,3.5,5.55,"wood"]],{"Size_WxH_m"=>"0.80x2.10", "Leaves"=>1, "Description"=>"Bedroom 3 door", "SillFromFloor_m"=>0.0, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWall","W-1F-bath-bed3","P2","1F","A-Wall",[[:box,6.55,6.65,8.6,12.2,3.5,6.65,"wall_white"]],{"Thickness_m"=>0.1, "Height_m"=>3.15, "NetArea_m2(one face)"=>11.34, "IsExternal"=>false, "Description"=>"RC frame infill: AAC block, plaster + paint", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcMember","FRAME-L","FR","1F","A-Trim",[[:box,1.33,1.95,-0.3,1.6,3.5,5.8,"wall_white"]],{"Description"=>"White box frame around balcony (render)", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcMember","FRAME-R","FR","1F","A-Trim",[[:box,6.45,7.2,-0.3,0.0,3.5,5.8,"wall_white"]],{"Description"=>"White box frame around balcony (render)", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcMember","FRAME-TOP","FR","1F","A-Trim",[[:box,1.33,7.2,-0.3,0.0,5.8,6.3,"wall_white"]],{"Description"=>"Frame head; LED strip in soffit", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcCovering","ROOF-MEMBRANE","RF","ROOF","A-Roof",[[:box,1.1,10.2,-0.8,12.6,6.8,6.85,"roof_dark"]],{"PredefinedType"=>"ROOFING", "Description"=>"Waterproofing membrane + insulation, slope 1%", "Area_m2"=>121.94, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcCovering","ROOF-FASCIA","FS","ROOF","A-Roof",[[:box,1.1,10.2,-0.85,-0.8,6.6,6.9,"roof_dark"]],{"PredefinedType"=>"CLADDING", "Description"=>"Dark metal fascia (render)", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcCovering","SOFFIT-WOOD","SF","ROOF","A-Ceiling",[[:box,1.1,10.2,-0.8,-0.3,6.6,6.65,"wood"]],{"PredefinedType"=>"CEILING", "Description"=>"Timber-look soffit under roof overhang (render)", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcRailing","RAIL-BAL","GR1","1F","A-Railing",[[:box,1.95,6.45,-0.24,-0.22,3.5,4.55,"glass"],[:box,1.98,2.02,-0.26,-0.2,3.5,4.55,"rail"],[:box,3.08,3.12,-0.26,-0.2,3.5,4.55,"rail"],[:box,4.18,4.22,-0.26,-0.2,3.5,4.55,"rail"],[:box,5.28,5.32,-0.26,-0.2,3.5,4.55,"rail"],[:box,6.38,6.42,-0.26,-0.2,3.5,4.55,"rail"]],{"Description"=>"Frameless glass balustrade 12 mm, h 1.05 m, black posts", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcDoor","GATE-SIDE","G1","GF","A-Door",[[:box,0.2,1.3,4.96,5.04,0.12,2.0,"frame_black"]],{"Size_WxH_m"=>"1.10x2.00", "Leaves"=>1, "Description"=>"Black aluminium slat gate to side yard (render)", "SillFromFloor_m"=>-0.3, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWall","W-PIER-L","P1","GF","A-Wall",[[:box,0.0,1.4,-0.3,0.3,0.12,3.0,"wall_white"]],{"Description"=>"Carport left pier (render)", "NetArea_m2(one face)"=>4.2, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcWall","W-BOUNDARY-L","P4","GF","A-Wall",[[:box,0.0,0.15,0.3,12.4,0.12,2.0,"wall_white"]],{"Description"=>"Side boundary wall h 2.00", "NetArea_m2(one face)"=>24.2, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcLightFixture","LED-STRIPS","LED","GF","E-Lighting",[[:box,1.8,4.8,1.2,1.25,2.98,3.0,"light"],[:box,1.8,4.8,2.4,2.45,2.98,3.0,"light"],[:box,1.8,4.8,3.6,3.65,2.98,3.0,"light"],[:box,2.2,6.2,0.6,0.65,5.78,5.8,"light"]],{"Description"=>"Linear LED in carport and frame soffits", "Count"=>4, "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcCovering","FL-GF-tile","F1","GF","A-Floor",[[:box,5.4,9.8,0.2,5.0,0.3,0.31,"tile_floor"],[:box,1.6,9.8,7.25,12.2,0.3,0.31,"tile_floor"]],{"PredefinedType"=>"FLOORING", "Description"=>"Porcelain tile 60x60", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcCovering","FL-1F-wood","F2","1F","A-Floor",[[:box,1.6,6.45,1.8,4.95,3.5,3.51,"wood_floor"],[:box,1.6,4.95,7.4,12.2,3.5,3.51,"wood_floor"],[:box,6.65,9.8,8.6,12.2,3.5,3.51,"wood_floor"]],{"PredefinedType"=>"FLOORING", "Description"=>"Engineered wood, bedrooms", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcFurnishingElement","KITCHEN","KC1","GF","A-Casework",[[:box,5.6,9.8,11.6,12.2,0.31,1.2,"counter"],[:box,6.6,8.6,9.6,10.5,0.31,1.2,"counter"]],{"Description"=>"Kitchen counter 0.60 + island 2.00x0.90", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcSanitaryTerminal","WC-GF","WC","GF","P-Sanitary",[[:box,3.81,4.19,6.35,7.05,0.3,0.7,"sanitary"]],{"Description"=>"Close-coupled WC", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcSanitaryTerminal","WC-MBATH","WC","1F","P-Sanitary",[[:box,9.01,9.39,3.05,3.75,3.5,3.9,"sanitary"]],{"Description"=>"Close-coupled WC", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcSanitaryTerminal","WC-BATH","WC","1F","P-Sanitary",[[:box,5.61,5.99,11.25,11.95,3.5,3.9,"sanitary"]],{"Description"=>"Close-coupled WC", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcSanitaryTerminal","TUB-MBATH","BT","1F","P-Sanitary",[[:box,7.0,8.7,0.4,1.15,3.5,4.05,"sanitary"]],{"Description"=>"Freestanding bathtub 1.70x0.75", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcSite","GROUND","SITE","GF","Site",[[:box,-1.0,11.0,-5.5,14.4,-0.05,0.0,"ground"]],{"Description"=>"Lot (size ASSUMED)", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcSlab","DRIVEWAY","DW","GF","Site",[[:box,0.0,5.3,-3.8,0.0,0.0,0.1,"paving"]],{"Description"=>"Concrete driveway strips", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcSlab","WALK","WK","GF","Site",[[:box,5.3,6.9,-3.8,-0.9,0.0,0.08,"paving"],[:box,5.3,6.9,-0.9,-0.45,0.0,0.15,"paving"],[:box,5.3,6.9,-0.45,0.0,0.0,0.3,"paving"]],{"Description"=>"Entrance walk + 2 steps", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}],
    ["IfcSlab","SIDEWALK","SW","GF","Site",[[:box,-1.0,11.0,-5.5,-3.8,0.0,0.12,"paving"]],{"Description"=>"Public sidewalk", "Note"=>"ASSUMED from concept image (no dimensions) - verify"}]
  ]

  # ---------------------------------------------------------------- helpers
  VALID_DISCIPLINES = DISC.keys.freeze

  def self.pt(a); Geom::Point3d.new(a[0].to_f.m, a[1].to_f.m, a[2].to_f.m); end

  def self.dist(a, b); Math.sqrt((0..2).sum { |i| (b[i] - a[i])**2 }); end

  def self.material(model, key)
    name = "MH_#{key}"
    mt = model.materials[name]
    return mt if mt
    mt = model.materials.add(name)
    r, g, b, a = MATS[key] || [200, 200, 200, 1.0]
    mt.color = Sketchup::Color.new(r, g, b)
    mt.alpha = a if a < 1.0
    mt
  end

  def self.tag(model, name); model.layers[name] || model.layers.add(name); end

  # face -> solid, extruded along 'dir'; sign taken from the face normal, never guessed
  def self.extrude(ents, pts, dir, len)
    f = ents.add_face(pts)
    raise 'add_face returned nil (tiny / non-planar face)' unless f
    f.reverse! if f.normal.dot(dir) < 0
    f.pushpull(len.m)
    f
  end

  def self.build_part(ents, part)
    case part[0]
    when :box
      _, x0, x1, y0, y1, z0, z1, _m = part
      pts = [[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0]].map { |p| pt(p) }
      extrude(ents, pts, Geom::Vector3d.new(0, 0, 1), z1 - z0)
    when :poly
      _, pts, n, t, _m = part
      extrude(ents, pts.map { |p| pt(p) }, Geom::Vector3d.new(*n), t)
    when :bar
      _, p1, p2, b, h, _m = part
      u = Geom::Vector3d.new(p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2])
      len = u.length.to_f                  # metres (vector built from raw metre numbers)
      raise 'zero-length bar' if len < 1e-9
      u = u.normalize
      side = u.cross(Geom::Vector3d.new(0, 0, 1))
      side = Geom::Vector3d.new(1, 0, 0) if side.length < 1e-6
      side = side.normalize
      up = side.cross(u).normalize
      up = up.reverse if up.z < 0
      c = pt(p1)
      pts = [[-1, -1], [1, -1], [1, 1], [-1, 1]].map { |sx, sy| c.offset(side, sx * b.m / 2).offset(up, sy * h.m / 2) }
      extrude(ents, pts, u, len)
    else
      raise "unknown part type #{part[0].inspect}"
    end
  end

  def self.ifc_ready?(model)
    return @ifc_ok unless @ifc_ok.nil?
    @ifc_ok = begin
      cl = model.classifications
      unless cl[SCHEMA]
        file = Sketchup.find_support_file("#{SCHEMA}.skc", 'Classifications')
        cl.load_schema(file) if file
      end
      !cl[SCHEMA].nil?
    rescue StandardError
      false
    end
  end

  def self.classify(model, grp, ifc)
    return unless ifc_ready?(model)
    grp.definition.add_classification(SCHEMA, ifc)
  rescue StandardError
    nil
  end

  def self.volume(part)
    case part[0]
    when :box then (part[2] - part[1]) * (part[4] - part[3]) * (part[6] - part[5])
    when :bar then dist(part[1], part[2]) * part[3] * part[4]
    when :poly
      pts, n, t = part[1], part[2], part[3]
      s = [0.0, 0.0, 0.0]
      pts.each_with_index do |a, i|
        b = pts[(i + 1) % pts.size]
        s[0] += a[1] * b[2] - a[2] * b[1]; s[1] += a[2] * b[0] - a[0] * b[2]; s[2] += a[0] * b[1] - a[1] * b[0]
      end
      nl = Math.sqrt(n.sum { |v| v * v })
      ((s[0] * n[0] + s[1] * n[1] + s[2] * n[2]).abs / nl / 2.0) * t
    else 0.0
    end
  end

  def self.selected(row, only)
    return true if only.nil?
    Array(only).any? { |d| row[4] =~ DISC[d] }
  end

  # ---------------------------------------------------------------- data validation (runs outside SketchUp too)
  def self.validate
    errs = []
    names = Hash.new(0)
    DATA.each_with_index do |row, i|
      unless row.size == 7
        errs << "row #{i}: expected 7 fields, got #{row.size}"
        next
      end
      ifc, name, _mark, lvl, tagname, parts, attrs = row
      names[name] += 1
      errs << "#{name}: IFC class #{ifc.inspect} must start with 'Ifc'" unless ifc.to_s.start_with?('Ifc')
      errs << "#{name}: unknown level #{lvl.inspect}" unless STOREYS.key?(lvl)
      errs << "#{name}: tag #{tagname.inspect} matches no discipline" unless DISC.values.any? { |rx| tagname =~ rx }
      errs << "#{name}: attrs must be a Hash" unless attrs.is_a?(Hash)
      errs << "#{name}: no parts" if parts.nil? || parts.empty?
      (parts || []).each do |p|
        errs << "#{name}: unknown material #{p.last.inspect}" unless MATS.key?(p.last)
        case p[0]
        when :box then errs << "#{name}: degenerate box #{p[1..6].inspect}" if p[2] <= p[1] || p[4] <= p[3] || p[6] <= p[5]
        when :bar then errs << "#{name}: zero-length or zero-section bar" if dist(p[1], p[2]) < 1e-9 || p[3] <= 0 || p[4] <= 0
        when :poly then errs << "#{name}: poly needs >= 3 points and thickness > 0" if p[1].size < 3 || p[3] <= 0
        else errs << "#{name}: unknown part type #{p[0].inspect}"
        end
      end
    end
    names.each { |n, c| errs << "duplicate element name #{n.inspect} x#{c}" if c > 1 }
    puts errs.empty? ? "DATA OK: #{DATA.size} elements, no problems found" : "#{errs.size} DATA problems:\n  " + errs.first(50).join("\n  ")
    errs
  end

  # ---------------------------------------------------------------- build
  def self.build(only: nil)
    bad = Array(only) - VALID_DISCIPLINES
    raise ArgumentError, "unknown discipline #{bad.inspect}; use #{VALID_DISCIPLINES.inspect}" unless bad.empty?
    model = Sketchup.active_model
    @ifc_ok = nil
    @qto = nil
    @failed = []
    n = 0
    model.start_operation('Build Modern House BIM', true)
    begin
      clear_existing(model)
      root = model.active_entities.add_group
      root.name = NAME
      root.set_attribute('MH_ROOT', 'built', true)
      classify(model, root, 'IfcBuilding')
      storeys = {}
      STOREYS.each do |k, label|
        s = root.entities.add_group
        s.name = label
        classify(model, s, 'IfcBuildingStorey')
        storeys[k] = s
      end
      rows = DATA.select { |row| selected(row, only) }
      rows.each_with_index do |row, idx|
        Sketchup.status_text = "Building #{NAME}: #{idx + 1}/#{rows.size}" if idx % 25 == 0
        n += 1 if build_element(model, storeys, row)
      end
      make_scenes(model)
      model.commit_operation
    rescue StandardError
      model.abort_operation
      raise
    ensure
      Sketchup.status_text = ''
    end
    show(:all)
    puts "#{NAME}: built #{n} elements (IFC classification #{ifc_ready?(model) ? 'ON' : 'OFF - schema not found'})"
    unless @failed.empty?
      puts "  #{@failed.size} elements FAILED (the rest were built):"
      @failed.first(30).each { |f| puts "    #{f}" }
    end
    n
  end

  # builds one DATA row inside its storey group; a failing element is logged and removed, never left half-built
  def self.build_element(model, storeys, row)
    ifc, name, mark, lvl, tagname, parts, attrs = row
    host = storeys[lvl] || storeys['GF']
    g = host.entities.add_group
    begin
      layer = tag(model, tagname)
      if parts.size == 1
        build_part(g.entities, parts[0])
        g.material = material(model, parts[0].last)
      else
        parts.each do |p|
          sub = g.entities.add_group
          build_part(sub.entities, p)
          sub.material = material(model, p.last)
          sub.layer = layer
        end
      end
      g.name = name
      g.layer = layer
      classify(model, g, ifc)
      g.set_attribute('MH_BIM', 'IfcClass', ifc)
      g.set_attribute('MH_BIM', 'Mark', mark)
      g.set_attribute('MH_BIM', 'Level', lvl)
      attrs.each { |k, v| g.set_attribute('MH_BIM', k, v) }
      g.set_attribute('MH_BIM', 'Volume_m3', parts.sum { |p| volume(p) }.round(4))
      true
    rescue StandardError => e
      @failed << "#{name}: #{e.class} #{e.message}"
      g.erase! if g.valid?
      false
    end
  end

  def self.clear_existing(model)
    model.active_entities.grep(Sketchup::Group).each do |g|
      g.erase! if g.valid? && g.get_attribute('MH_ROOT', 'built')
    end
  end

  def self.visible_for(what, name)
    case what
    when :structure then name.start_with?('S-')
    when :architecture then name.start_with?('A-', 'S-Column', 'S-Slab')
    when :mep then name.start_with?('P-', 'E-', 'S-Column', 'S-Slab', 'S-Foundation')
    when :site then name == 'Site'
    when :all then true
    else raise ArgumentError, "unknown view #{what.inspect}; use :structure :architecture :mep :site :all"
    end
  end

  def self.bim_tag?(name); name =~ /\A[SAPE]-|\ASite\z/ ? true : false; end

  # scenes store their own tag visibility (Page#set_visibility); global tag visibility is never left hidden
  def self.make_scenes(model)
    return unless model.respond_to?(:pages) && model.pages
    show(:all)
    [['01 Structure', :structure], ['02 Architecture', :architecture], ['03 MEP', :mep], ['04 Site', :site], ['05 All', :all]].each do |nm, w|
      pg = model.pages[nm] || model.pages.add(nm)
      model.layers.each do |l|
        next unless bim_tag?(l.name)
        pg.set_visibility(l, visible_for(w, l.name)) if pg.respond_to?(:set_visibility)
      end
    end
    model.pages.selected_page = model.pages['05 All'] if model.pages.respond_to?(:selected_page=)
  rescue StandardError => e
    puts "scenes skipped: #{e.message}"
  ensure
    show(:all)
  end

  # quick diagnosis: element count per tag + tag visibility
  def self.diag
    model = Sketchup.active_model
    root = model.active_entities.grep(Sketchup::Group).find { |g| g.valid? && g.get_attribute('MH_ROOT', 'built') }
    return puts('model not built yet - run ModernHouseBIM.build') unless root
    cnt = Hash.new(0)
    root.entities.grep(Sketchup::Group).each { |s| s.entities.grep(Sketchup::Group).each { |g| cnt[g.layer.name] += 1 } }
    cnt.sort.each { |k, v| l = model.layers[k]; puts format('%-16s %4d  %s', k, v, (l && l.visible?) ? 'visible' : 'HIDDEN') }
    puts "expected #{DATA.size} elements, found #{cnt.values.sum}"
    puts(@failed && !@failed.empty? ? "failed: #{@failed.size}" : 'no build failures recorded')
    nil
  end

  def self.show(what = :all)
    Sketchup.active_model.layers.each do |l|
      l.visible = visible_for(what, l.name) if bim_tag?(l.name)
    end
  end

  # ---------------------------------------------------------------- quantities / schedules
  def self.qto
    @qto ||= begin
      rows = Hash.new { |h, k| h[k] = { count: 0, vol: 0.0, area: 0.0, len: 0.0, kg: 0.0 } }
      DATA.each do |ifc, _name, mark, _lvl, tagname, parts, attrs|
        r = rows[[tagname, ifc.sub('Ifc', ''), mark]]
        r[:count] += 1
        r[:vol] += parts.sum { |p| volume(p) }
        r[:area] += (attrs['NetArea_m2(one face)'] || attrs['Area_m2'] || attrs['SlopeArea_m2'] || 0).to_f
        bars = parts.select { |p| p[0] == :bar }
        r[:len] += bars.sum { |p| dist(p[1], p[2]) }
        r[:kg] += (attrs['Weight_kg'] || 0).to_f unless bars.empty?
      end
      rows
    end
  end

  def self.schedule
    DATA.select { |r| %w[IfcDoor IfcWindow].include?(r[0]) }.map do |ifc, name, mark, _lvl, _tg, _parts, a|
      [mark, name, ifc.sub('Ifc', ''), a['Size_WxH_m'], a['Leaves'], a['Description'], a['SillFromFloor_m']]
    end.sort_by { |r| r.map(&:to_s) }
  end

  def self.report
    puts '%-14s %-24s %-12s %5s %9s %9s %8s %8s' % %w[Tag Class Mark Count Vol_m3 Area_m2 Len_m kg]
    qto.sort.each do |(t, c, m), r|
      puts '%-14s %-24s %-12s %5d %9.2f %9.2f %8.1f %8.0f' % [t, c, m, r[:count], r[:vol], r[:area], r[:len], r[:kg]]
    end
    # a model whose structural tags also hold timber or stone parts lists those materials in NON_RC_MATS;
    # material keys are render colours, so RC members drawn in a finish colour still count as RC
    non_rc = const_defined?(:NON_RC_MATS, false) ? NON_RC_MATS : []
    struct = DATA.select { |r| r[4] =~ /\AS-(Foundation|Column|Beam|RoofBeam|Slab)/ }.flat_map { |r| r[5] }
    other, conc = struct.partition { |p| non_rc.include?(p.last) }
    puts 'RC concrete (gross, joints counted once per member): %.2f m3 ; roof steel: %.0f kg' % [conc.sum { |p| volume(p) }, qto.values.sum { |r| r[:kg] }]
    puts 'Other structural material (not RC): ' + other.group_by(&:last).map { |m, ps| '%s %.2f m3' % [m, ps.sum { |p| volume(p) }] }.join(', ') unless other.empty?
    puts "\nDOOR / WINDOW SCHEDULE"
    schedule.each { |r| puts r.map(&:to_s).join(' | ') }
    nil
  end

  def self.csv_cell(v)
    s = v.to_s
    s =~ /[",\r\n]/ ? "\"#{s.gsub('"', '""')}\"" : s
  end

  def self.export_csv(prefix)
    dir = File.dirname(prefix)
    raise ArgumentError, "folder does not exist: #{dir}" unless File.directory?(dir)
    File.open("#{prefix}_qto.csv", 'w:UTF-8') do |f|
      f.puts "﻿Tag,Class,Mark,Count,Volume_m3,Area_m2,Length_m,Steel_kg"
      qto.sort.each { |(t, c, m), r| f.puts [t, c, m, r[:count], r[:vol].round(3), r[:area].round(2), r[:len].round(2), r[:kg].round(1)].map { |v| csv_cell(v) }.join(',') }
    end
    File.open("#{prefix}_schedule.csv", 'w:UTF-8') do |f|
      f.puts "﻿Mark,Name,Class,Size_WxH_m,Leaves,Description,Sill_m"
      schedule.each { |r| f.puts r.map { |v| csv_cell(v) }.join(',') }
    end
    puts "wrote #{prefix}_qto.csv and #{prefix}_schedule.csv"
  end

  # ---------------------------------------------------------------- clash check (part bounding boxes)
  def self.part_bbox(p)
    case p[0]
    when :box then [p[1], p[2], p[3], p[4], p[5], p[6]]
    when :poly
      pts = p[1]; n = p[2]; t = p[3]; nl = Math.sqrt(n.sum { |v| v * v })
      all = pts + pts.map { |q| (0..2).map { |i| q[i] + n[i] / nl * t } }
      (0..2).flat_map { |i| [all.map { |q| q[i] }.min, all.map { |q| q[i] }.max] }
    when :bar
      a, b, w, h = p[1], p[2], p[3], p[4]; r = [w, h].max / 2.0
      (0..2).flat_map { |i| [[a[i], b[i]].min - r, [a[i], b[i]].max + r] }
    end
  end

  CLASH_SKIP_TAGS = %w[Site A-Roof A-Cladding A-Deck].freeze

  # returns { [nameA, nameB] => overlapping part pairs }; architecture/MEP x structure, plus architecture/MEP x each other
  def self.clashes(tol = 0.005)
    items = []
    struct = []
    DATA.each_with_index do |r, i|
      r[5].each do |p|
        bb = part_bbox(p)
        struct << [i, bb] if r[4] =~ /\AS-(Column|Beam|RoofBeam|Slab)/
        items << [i, bb] unless r[4].start_with?('S-') || CLASH_SKIP_TAGS.include?(r[4])
      end
    end
    ov = ->(a, b) { (0..2).all? { |k| [a[2 * k + 1], b[2 * k + 1]].min - [a[2 * k], b[2 * k]].max > tol } }
    found = Hash.new(0)
    hit = ->(i, j) { found[[DATA[i][1], DATA[j][1]].sort] += 1 }
    items.each_with_index do |(i, a), n|
      items[(n + 1)..-1].each { |(j, b)| hit.(i, j) if i != j && ov.(a, b) }
      struct.each { |(j, b)| hit.(i, j) if ov.(a, b) }
    end
    puts "#{found.size} element pairs with overlapping bounding boxes (architecture/MEP x structure and x each other; sloped-roof, cladding and site excluded; tol #{tol} m)"
    found.sort.first(80).each { |k, v| puts "  #{k[0]}  x  #{k[1]}#{v > 1 ? "  (#{v} part pairs)" : ''}" }
    found
  end
end

puts "Modern House BIM script loaded (#{ModernHouseBIM::DATA.size} elements). Run: ModernHouseBIM.build"
