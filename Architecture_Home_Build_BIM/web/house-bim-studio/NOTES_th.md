# House BIM Studio — เว็บแอปส่วนตัว (MVP ขั้นที่ 1)

Artifact: https://claude.ai/artifact/EmEpQhrJ3R3U6hQkXRGzDy — ส่วนตัว ผู้ใช้คนเดียว (Supakorn)

## ทำอะไรได้
- ข้อมูลแบบ (JSON "spec") → โมเดล 3D (three.js, คลิกดูข้อมูลชิ้นส่วน, เปิด/ปิด Tag) → ตรวจการชน (จุดตัวอย่างในรูปทรงจริง) → ถอดปริมาณ → BOQ 4 หมวด (แก้ราคา/เผื่อ/กิจกรรมในตาราง) → แผนงาน CPM + Gantt (แก้ผลิตภาพ ทีม วันคงที่ ก่อนหน้า:lag) → S-Curve รายสัปดาห์แยกหมวด + งวดทุก 4 สัปดาห์
- ส่งออก: Excel (Summary, BOQ มีสูตร, Takeoff, Openings, Schedule, S-Curve), สคริปต์ SketchUp เป็น .rb.txt (`load` ได้ตรง ๆ), ไฟล์ JSON โครงการ, CSV takeoff
- บันทึกโครงการใน db ของ artifact: collection `projects/<id>` = {name, updatedAt, spec}; rules read/write = owner เท่านั้น; บันทึกอัตโนมัติ 1.5 วินาทีหลังแก้; seed `projects/type03` แล้ว
- แม่แบบ TYPE03 ฝังอยู่ในหน้า (ปุ่ม "ใหม่จากแม่แบบ")

## ความถูกต้อง
- engine.js (JS ล้วน) เทียบกับ Python ของ TYPE03: รูปทรง 378/378 ตรง, takeoff 92 รายการตรง, BOQ 1,898,425.40 / ×F 2,438,793.35 ตรง, วันเริ่ม-เสร็จ-float ทุกกิจกรรมตรง, S-Curve รายสัปดาห์ตรง
- .rb ที่ส่งออกจากเว็บ รันผ่าน stub ได้ 378 ชิ้น รูปทรงตรง Python; Excel ที่ส่งออก recalc 453 สูตร ไม่มี error
- ทดสอบใน Chromium headless: ทุกแท็บ, แก้ราคา/ทีมแล้วคำนวณใหม่, บันทึก, ดาวน์โหลด 4 แบบ, จอกว้าง 400px ไม่มีเลื่อนแนวนอน

## ข้อจำกัด / ขั้นต่อไป
- รองรับบ้าน ค.ส.ล. ชั้นเดียว หลังคาจั่วโครงเหล็ก + หลังคาเฉลียงแบบ TYPE03 เท่านั้น — L-7 (2 ชั้น หลังคาโค้ง) ยังไม่รองรับ
- แก้รูปทรง (คาน ผนัง ช่องเปิด ฯลฯ) ผ่านตัวแก้ JSON — ยังไม่มีฟอร์ม/ตัววาดผัง
- ไม่มีส่งออก IFC ตรง (ใช้ SketchUp Pro ส่งออกจาก .rb ที่ใส่ classification แล้ว)
- ขั้นที่ 2–3 ตามแผน: ฟอร์มแก้ชิ้นส่วน/ตัวแก้ผัง, รองรับหลายชั้นและหลังคาแบบอื่น, AI ช่วยอ่านแบบ PDF (capability `sample`) แล้วให้ยืนยันทีละหมวด

## ไฟล์ต้นทาง (โฟลเดอร์ type03/web)
- engine.js, app.html, inline.py (รวมเป็น house_bim_studio.html), test.js (เทียบ Python), ../make_spec.py (สร้าง type03_spec.json)
