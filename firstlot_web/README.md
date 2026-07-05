# First Lot Web — เว็บกรอกผลตรวจ + Dashboard (หลายเครื่องพร้อมกัน)

เว็บแอปสำหรับ **กรอกผลตรวจ First Lot ทั้ง 3 ประเภท (Base Assy · Kashime · Manual & Auto) ผ่านเว็บ**
ใช้งานพร้อมกันได้หลายเครื่อง และมี **dashboard แสดงผลสด** จากฐานข้อมูลกลางเดียวกัน

## สถาปัตยกรรม

```
[คอมพิวเตอร์แต่ละไลน์ — เบราว์เซอร์]                 [เครื่อง server 1 เครื่อง]
  http://<server-ip>:8000/entry/base   ─┐
  http://<server-ip>:8000/entry/kashime ─┼─ POST ─▶  Flask (app.py)  ─▶  SQLite (firstlot.db, WAL)
  http://<server-ip>:8000/entry/manual  ─┘                 ▲
  http://<server-ip>:8000/  (dashboard) ◀── อ่านสด ────────┘
```

- **Backend:** Python **Flask** + **SQLite** (เปิดโหมด WAL รองรับหลายเครื่องเขียน/อ่านพร้อมกัน)
- **Frontend:** HTML + vanilla JS (ไม่ต้อง build, ไม่พึ่ง CDN) — ทุกเครื่องแค่เปิดเบราว์เซอร์
- **ทำไม SQLite ไม่ใช่ MySQL/SQL Server:** ที่ปริมาณระดับพัน–หมื่นรายการ SQLite เพียงพอ ดูแลง่าย
  เป็นไฟล์เดียว ไม่ต้องตั้ง DB server แยก · ค่อยย้ายไป PostgreSQL/MySQL เมื่อโตมากหรือต้องการ replication

## ติดตั้ง (บนเครื่อง server เครื่องเดียว)

```bash
cd firstlot_web
pip install -r requirements.txt

# 1) นำเข้าประวัติเดิมจาก .xlsm เข้าฐานข้อมูล (ทำครั้งเดียว)
python import_history.py

# 2) รันเซิร์ฟเวอร์
#    - ทดสอบ:
python app.py
#    - ใช้งานจริง (รองรับหลายผู้ใช้ดีกว่า):
waitress-serve --host=0.0.0.0 --port=8000 app:app
```

จากนั้นทุกเครื่องในเครือข่ายเปิด `http://<ip-ของ-server>:8000`
(ดู ip ของ server ด้วย `ipconfig` บน Windows — ต้องอยู่วง LAN เดียวกัน / เปิด firewall port 8000)

### ให้รันอัตโนมัติเมื่อเปิดเครื่อง (Windows)
ตั้ง **Task Scheduler** ให้รัน `waitress-serve ...` ตอน startup
(หรือใช้ NSSM สร้างเป็น Windows Service เพื่อความเสถียร)

## หน้าจอ

| URL | หน้าที่ |
|-----|--------|
| `/` | **Dashboard** — KPI, แนวโน้มรายเดือน, สัดส่วนประเภท, Top Line/Checker, ตารางค้นหา/เรียง/Export CSV |
| `/entry/base` | ฟอร์มกรอก **Base Assy** (146 ฟิลด์ ตามไฟล์จริง) |
| `/entry/kashime` | ฟอร์มกรอก **Kashime** (103 ฟิลด์) |
| `/entry/manual` | ฟอร์มกรอก **Manual & Auto** (87 ฟิลด์) |

ฟอร์มถูกสร้างอัตโนมัติจาก `fields.json` (generate จากหัวคอลัมน์ HISTORYLOG ของไฟล์ Excel จริง)
ช่องผลตรวจ (APPEARANCE / Sensor / OK,NG) เป็นปุ่มกด **OK / NG** · ช่องวัดค่าเป็นตัวเลข
ส่วน Finish Lot / Tag 2-5 / Final check อยู่ในกล่องพับ "ข้อมูลเพิ่มเติม" (ไม่บังคับ)

## API

| Method | Endpoint | ใช้ทำอะไร |
|--------|----------|-----------|
| POST | `/api/inspections` | บันทึกผลตรวจ `{type, data:{...}}` (ตรวจ required ฝั่ง server) |
| GET | `/api/inspections?type=&month=&line=&checker=` | ดึงรายการ (dashboard) |
| GET | `/api/facets` | ค่า filter (เดือน/line/checker/จำนวนต่อประเภท) |
| GET | `/api/record/<id>` | ดูข้อมูลเต็มของ 1 รายการ |
| GET | `/export.csv` | ดาวน์โหลด CSV |

## โครงสร้างไฟล์

```
firstlot_web/
├── app.py              Flask app (routes + DB + validation)
├── fields.json         สเปกฟิลด์ของทั้ง 3 ฟอร์ม (generate จาก Excel)
├── import_history.py   นำเข้าประวัติ HISTORYLOG → firstlot.db
├── requirements.txt
├── firstlot.db         ฐานข้อมูล SQLite (สร้างอัตโนมัติ — ไม่ commit ลง git)
├── templates/          base / dashboard / entry (Jinja2)
└── static/             style.css, dashboard.js, entry.js, common.js
```

## หมายเหตุ / งานต่อได้ในอนาคต
- **การยืนยันตัวตน (login):** ยังไม่มี — ถ้าต้องการแยกสิทธิ์ checker/หัวหน้า เพิ่ม Flask-Login ได้
- **Export PDF ต่อรายการ** (เหมือน macro เดิม) ยังไม่ทำ — dashboard + CSV ครอบคลุมการดูภาพรวมแล้ว
- **NG:** ปัจจุบันประวัติทั้งหมดเป็น OK (ระบบเดิมบล็อกการบันทึกถ้าไม่ผ่าน) เว็บนี้เปิดให้บันทึก NG ได้
  และ dashboard แสดงผล NG ไว้พร้อมแล้ว
- ระบบเดิม (.xlsm) ยังใช้คู่ขนานได้ — `import_history.py` ดึงข้อมูลใหม่เพิ่มได้ถ้ายังกรอกผ่าน Excel บางส่วน
