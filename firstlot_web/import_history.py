# -*- coding: utf-8 -*-
"""
import_history.py — นำเข้าประวัติเดิมจากชีต HISTORYLOG ของ .xlsm ทั้ง 3 ไฟล์
เข้าฐานข้อมูล firstlot.db (ทำครั้งเดียวตอนติดตั้ง เพื่อให้ dashboard มีข้อมูลย้อนหลัง)

    python import_history.py
"""
import os, json, sqlite3, datetime, openpyxl
from app import init_db, DB, FIELDS

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "First lot")
FILES = {
    "base":    "BASE ASSY MASTER RECORD LINE 10 R4.xlsm",
    "kashime": "KASHIME MASTER RECORD LINE 7 R3.xlsm",
    "manual":  "MANUAL & AUTO MASTER RECORD MASTER R4.xlsm",
}

def clean(v):
    if v is None: return ""
    if isinstance(v,(datetime.datetime,datetime.date,datetime.time)): return v.isoformat()
    if isinstance(v,str): return v.strip()
    return v

def main():
    init_db()
    con = sqlite3.connect(DB)
    existing = con.execute("SELECT COUNT(*) FROM inspections").fetchone()[0]
    if existing:
        print(f"มีข้อมูลอยู่แล้ว {existing} รายการ — ข้ามการนำเข้า (ลบ firstlot.db ก่อนถ้าต้องการ import ใหม่)")
        return
    total = 0
    for tid, fn in FILES.items():
        path = os.path.join(SRC, fn)
        if not os.path.exists(path):
            print(f"  ! ไม่พบ {fn} — ข้าม"); continue
        spec = FIELDS[tid]; fields = spec["fields"]; appidx = spec["appcol_idx"]
        print(f"  อ่าน {fn} ...", flush=True)
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True, keep_links=False)
        ws = wb["HISTORYLOG"]; n = 0
        for row in ws.iter_rows(min_row=3, values_only=True):
            data = {}
            for f in fields:
                i = f["idx"]
                data[f["key"]] = clean(row[i]) if i < len(row) else ""
            if not data.get("prod_order") and not data.get("datetime"):
                continue
            appearance = clean(row[appidx]) if appidx < len(row) else ""
            insp_dt = str(data.get("datetime") or "")
            month = insp_dt[:7]
            con.execute("""INSERT INTO inspections
                (type,created_at,insp_datetime,line,setdie,checker,shift,prod_order,item,des,
                 model,desmodel,lot,month,seq,itemc,appearance,data_json)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (tid, insp_dt or datetime.datetime.now().isoformat(timespec="seconds"),
                 insp_dt, data.get("line",""), data.get("setdie",""), data.get("checker",""),
                 data.get("shift",""), data.get("prod_order",""), data.get("item",""),
                 data.get("des",""), data.get("model",""), data.get("desmodel",""),
                 data.get("lot",""), month, data.get("seq",""), data.get("item",""),
                 appearance, json.dumps(data, ensure_ascii=False)))
            n += 1
        wb.close(); con.commit()
        print(f"    -> นำเข้า {n} รายการ"); total += n
    print(f"เสร็จ: นำเข้าทั้งหมด {total} รายการ เข้า {DB}")

if __name__ == "__main__":
    main()
