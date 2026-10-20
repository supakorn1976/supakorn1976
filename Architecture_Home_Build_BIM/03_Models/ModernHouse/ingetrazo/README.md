# Modern House → IngeTrazo (AI Bridge / MCP)

สร้างบ้าน Modern House 2 ชั้น (ข้อมูลเดียวกับ `../model.js`) ลงในเอกสารที่เปิดอยู่ใน IngeTrazo

## วิธีใช้ (Windows)

1. เปิด IngeTrazo แล้วไปที่ **Extensions > AI Bridge (MCP)** (พอร์ต 4763 ต้องเปิด)
2. ใน PowerShell:
   ```powershell
   cd <repo>\Architecture_Home_Build_BIM\03_Models\ModernHouse\ingetrazo
   powershell -ExecutionPolicy Bypass -File build_house.ps1
   ```

## สิ่งที่สคริปต์ทำ (`build_house.json`)

| ขั้น | เนื้อหา | กลุ่ม |
|---|---|---|
| setup | ตรวจว่ายังไม่มีกลุ่ม `MH_*` และนับกลุ่มเดิม | 0 |
| FND | ฐานราก 13 + ตอม่อ 13 | 26 |
| GF | ชั้น 1: เสา คาน พื้น ผนัง ประตู หน้าต่าง บันได | 140 |
| 1F | ชั้น 2 | 132 |
| ROOF | คานหลังคา พื้นหลังคา ชายคา | 11 |
| export | ติด IFC class, บันทึก `.igz` / `.ifc` / `_quantities.csv` / `_elements.json` | |

- 1 ชิ้นกล่อง = 1 group ที่สร้างด้วย `extrude()` รวม 309 groups (298 ติด IFC class) ปริมาตรกล่องรวม 172.608 m³
- 1 layer ต่อ BIM tag (S-Foundation, S-Column, A-Wall ...)
- บ้านเลื่อนไป (2, 2) เพื่อไม่ทับหุ่นวัดขนาด `Engineer` ที่จุดกำเนิด
- ไฟล์ผลลัพธ์อยู่ที่ `%USERPROFILE%\Documents\IngeTrazo_ModernHouse\HOME-ARC-ALL-MODEL-R01.*`
- ภาพหน้าจอบันทึกเป็น `modern_house.png` ในโฟลเดอร์นี้
- แต่ละขั้นเป็น undo 1 ครั้ง (Ctrl+Z) ถ้ามี error สคริปต์จะหยุดที่ขั้นนั้น

## ข้อจำกัด

- ผนังที่มีช่องเปิดถูกแยกเป็นหลายชิ้น (`MH_W...#1`, `#2` ...) จึงนับเป็นหลาย IFC element
- `IfcCurtainWall` ถูก map เป็น `IfcWindow`; สุขภัณฑ์ ไฟ เฟอร์นิเจอร์ และพื้นที่ site ไม่ติด class (IngeTrazo export ไม่รองรับ) จึงไม่อยู่ใน IFC
- ทุกขนาดเป็นค่าสมมติจากภาพ concept ไม่ใช่แบบที่ออกแบบโดยวิศวกร

สร้างใหม่หลังแก้ `make_model.py`: `python3 make_model.py && python3 make_ingetrazo.py`
