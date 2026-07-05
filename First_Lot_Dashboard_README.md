# First Lot Inspection Dashboard

รวมผลตรวจ First Lot งานโลหะจาก 3 ไฟล์ (`Base Assy`, `Kashime`, `Manual & Auto`)
ให้อยู่ในหน้าเว็บเดียว — ดูได้หลายเครื่องพร้อมกัน ไฟล์เล็ก ไม่ต้องมี server/อินเทอร์เน็ต

## ไฟล์ในระบบ

| ไฟล์ | หน้าที่ |
|------|--------|
| `build_first_lot_dashboard.py` | สคริปต์อ่านชีต **HISTORYLOG** ของ .xlsm ทั้ง 3 ไฟล์ในโฟลเดอร์ `First lot` แล้วสร้าง dashboard |
| `First_Lot_Dashboard.html` | **ผลลัพธ์** — dashboard สำเร็จรูป (self-contained, ฝังข้อมูล + กราฟในตัว) เปิดด้วยเบราว์เซอร์ได้เลย |

## วิธีสร้าง / อัปเดต dashboard

```bash
python build_first_lot_dashboard.py
```

เงื่อนไข: ติดตั้ง Python + `pip install openpyxl` และวางสคริปต์ไว้ระดับเดียวกับโฟลเดอร์ `First lot`

## แนวทางใช้งานหลายเครื่องพร้อมกัน (แนะนำ)

หลักการ: **แยก"การกรอกข้อมูล" ออกจาก "การดู dashboard" และให้ dashboard เป็นแบบอ่านอย่างเดียว**
จึงไม่มีปัญหาแย่งกันเขียน (write conflict) แม้เปิดพร้อมกันหลายเครื่อง

```
[พนักงานแต่ละไลน์]                    [เครื่อง server 1 เครื่อง]           [ทุกเครื่องในโรงงาน]
กรอกใน .xlsm (เดิม)  ──บันทึก──▶  HISTORYLOG   ──สคริปต์รันตามเวลา──▶  First_Lot_Dashboard.html
                                  (บน shared drive)                    (บน shared folder / intranet)
                                                                         เปิดดู read-only พร้อมกันได้
```

1. **การกรอกข้อมูล** — ใช้ไฟล์ `.xlsm` เดิมตามปกติ ไม่ต้องเปลี่ยนอะไร (macro บันทึกลง HISTORYLOG อยู่แล้ว)
2. **สร้าง dashboard** — ให้ **เครื่อง server เพียงเครื่องเดียว** รันสคริปต์ (มีแค่เครื่องเดียวที่เขียนไฟล์ → ไม่ชนกัน)
3. **อัปเดตอัตโนมัติ** — ตั้ง **Windows Task Scheduler** ให้รันสคริปต์ทุก 15–30 นาที (ดูด้านล่าง)
4. **การดู** — วาง `First_Lot_Dashboard.html` ไว้บน **shared folder** หรือ **intranet web** ให้ทุกเครื่องเปิดดู

### ทำไมไม่ใช้ database server เต็มรูปแบบ (MySQL/SQL Server)?
ที่ปริมาณข้อมูลระดับพันกว่ารายการยัง overkill — ต้องตั้ง server ดูแลสิทธิ์เข้าถึงและ backup เอง
วิธี "สคริปต์ + ไฟล์ HTML บน shared folder" ให้ผลเหมือนกันแต่ดูแลง่ายกว่ามาก และทุกเครื่องเปิดได้โดยไม่ต้องติดตั้งอะไร
ค่อยพิจารณา database จริงเมื่อข้อมูลโตหลักแสนรายการหรือต้องการอัปเดตแบบ real-time

### เรื่องขนาดไฟล์
รูปภาพหนัก (EMF/PNG รวมหลายสิบ MB) อยู่ใน `.xlsm` เท่านั้น — dashboard เก็บแค่ **ข้อความ**
ปัจจุบัน ~720 KB (2,056 รายการ) แม้โตเป็นหมื่นรายการก็ยังเพียงไม่กี่ MB

## ตั้ง Windows Task Scheduler (อัปเดตอัตโนมัติ)

1. เปิด **Task Scheduler → Create Basic Task**
2. Trigger: `Daily` แล้วตั้ง **Repeat task every 15 minutes** (หรือทุกชั่วโมง)
3. Action: `Start a program`
   - Program: `python`
   - Arguments: `build_first_lot_dashboard.py`
   - Start in: โฟลเดอร์ที่วางสคริปต์ (เช่น `\\server\share\FirstLot`)

## ข้อมูลใน dashboard

- **KPI**: จำนวนตรวจทั้งหมด, ผ่าน (OK), ไม่ผ่าน/อื่นๆ, เดือนนี้, แยกตามประเภท
- **ตัวกรอง**: ประเภทงาน, เดือน, Line, Checker, ค้นหา (Order/Item/Model/Lot)
- **กราฟ**: แนวโน้มการตรวจรายเดือน, สัดส่วนตามประเภท, Top 10 Line, Top 10 Checker
- **ตาราง**: เรียงลำดับได้ทุกคอลัมน์, แบ่งหน้า, Export CSV

> หมายเหตุ: ปัจจุบันทุกรายการใน HISTORYLOG เป็น **OK** ทั้งหมด เพราะระบบ macro (`CopyToHistoryLog`)
> บล็อกไม่ให้บันทึกถ้าผลตรวจไม่ผ่าน จึงยังไม่มี NG ในฐานประวัติ — dashboard รองรับการแสดง NG
> ไว้แล้วหากอนาคตมีการบันทึกผลไม่ผ่าน
