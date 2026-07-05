# -*- coding: utf-8 -*-
"""
First Lot Web — เว็บกรอกผลตรวจ First Lot + dashboard (หลายเครื่องพร้อมกัน)
Backend: Flask + SQLite (WAL)  |  รันครั้งเดียวบนเครื่อง server ในเครือข่าย

รัน dev:      python app.py
รัน prod:     waitress-serve --host=0.0.0.0 --port=8000 app:app
เข้าจากเครื่องอื่น: http://<ip-ของ-server>:8000
"""
import os, json, sqlite3, datetime, csv, io
from flask import (Flask, g, request, jsonify, render_template,
                   redirect, url_for, Response, abort)

BASE = os.path.dirname(os.path.abspath(__file__))
DB   = os.path.join(BASE, "firstlot.db")
FIELDS = json.load(open(os.path.join(BASE, "fields.json"), encoding="utf-8"))

COMMON_LABELS = {
 "datetime":"วันที่-เวลา","line":"Line Prod.","setdie":"Set Die","checker":"Checker",
 "shift":"Shift","prod_order":"Prod. Order","item":"Item","des":"Description",
 "prodline":"Line","seq":"Seq.","lot":"Lot","month":"Prod. month",
 "model":"Model","desmodel":"Des. Model"}
# ฟิลด์ที่บังคับกรอก (ฝั่ง server) — อิงเงื่อนไขหลักจาก macro เดิม
REQUIRED = ["line","checker","prod_order","model"]

app = Flask(__name__)

# ---------- DB ----------
def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB, timeout=15)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
        g.db.execute("PRAGMA busy_timeout=8000")
    return g.db

@app.teardown_appcontext
def _close(e=None):
    d = g.pop("db", None)
    if d: d.close()

def init_db():
    con = sqlite3.connect(DB)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("""CREATE TABLE IF NOT EXISTS inspections(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        created_at TEXT NOT NULL,
        insp_datetime TEXT,
        line TEXT, setdie TEXT, checker TEXT, shift TEXT,
        prod_order TEXT, item TEXT, des TEXT, model TEXT, desmodel TEXT,
        lot TEXT, month TEXT, seq TEXT, itemc TEXT,
        appearance TEXT,
        data_json TEXT NOT NULL
    )""")
    for c in ("type","insp_datetime","line","checker","model","prod_order"):
        con.execute(f"CREATE INDEX IF NOT EXISTS ix_{c} ON inspections({c})")
    con.commit(); con.close()

# ---------- helpers ----------
def spec(tid):
    s = FIELDS.get(tid)
    if not s: abort(404)
    return s

def label_for(f):
    return COMMON_LABELS.get(f["key"], f["label"])

def grouped(fields, primary):
    """คืน list ของ (group_name, [fields]) เรียงตามลำดับคอลัมน์"""
    out, cur, bucket = [], None, []
    for f in fields:
        if f["primary"] != primary: continue
        if f["group"] != cur:
            if bucket: out.append((cur, bucket))
            cur, bucket = f["group"], []
        bucket.append(f)
    if bucket: out.append((cur, bucket))
    return out

# ---------- routes: pages ----------
@app.route("/favicon.ico")
def favicon():
    # emoji favicon (svg) — keeps browser console clean, no external file
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y="82" font-size="82">🏭</text></svg>'
    return Response(svg, mimetype="image/svg+xml")

@app.route("/")
def dashboard():
    return render_template("dashboard.html", specs=FIELDS)

@app.route("/entry/<tid>")
def entry(tid):
    s = spec(tid)
    return render_template("entry.html", tid=tid, spec=s,
        primary=grouped(s["fields"], True),
        secondary=grouped(s["fields"], False),
        label_for=label_for, specs=FIELDS)

# ---------- routes: API ----------
@app.route("/api/inspections", methods=["POST"])
def create():
    payload = request.get_json(force=True, silent=True) or {}
    tid = payload.get("type")
    s = spec(tid)
    data = payload.get("data") or {}
    # validate required
    errors = []
    for k in REQUIRED:
        if not str(data.get(k, "")).strip():
            errors.append(f"กรุณากรอก {COMMON_LABELS.get(k,k)}")
    app_key = s["fields"][s["appcol_idx"]]["key"] if s["appcol_idx"] < len(s["fields"]) else None
    appearance = str(data.get(app_key, "")).strip() if app_key else ""
    if errors:
        return jsonify({"ok": False, "errors": errors}), 400
    now = datetime.datetime.now().isoformat(timespec="seconds")
    insp_dt = str(data.get("datetime") or now)
    month = insp_dt[:7]
    con = db()
    cur = con.execute("""INSERT INTO inspections
       (type,created_at,insp_datetime,line,setdie,checker,shift,prod_order,item,des,
        model,desmodel,lot,month,seq,itemc,appearance,data_json)
       VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
       (tid, now, insp_dt,
        data.get("line",""), data.get("setdie",""), data.get("checker",""),
        data.get("shift",""), data.get("prod_order",""), data.get("item",""),
        data.get("des",""), data.get("model",""), data.get("desmodel",""),
        data.get("lot",""), month, data.get("seq",""), data.get("item",""),
        appearance, json.dumps(data, ensure_ascii=False)))
    con.commit()
    return jsonify({"ok": True, "id": cur.lastrowid})

@app.route("/api/inspections")
def list_inspections():
    q = "SELECT id,type,insp_datetime,line,setdie,checker,shift,prod_order,item,des,model,lot,month,appearance FROM inspections"
    where, args = [], []
    tp = request.args.get("type")
    if tp: where.append("type=?"); args.append(tp)
    mo = request.args.get("month")
    if mo: where.append("month=?"); args.append(mo)
    ln = request.args.get("line")
    if ln: where.append("line=?"); args.append(ln)
    ck = request.args.get("checker")
    if ck: where.append("checker=?"); args.append(ck)
    if where: q += " WHERE " + " AND ".join(where)
    q += " ORDER BY insp_datetime DESC, id DESC"
    rows = [dict(r) for r in db().execute(q, args).fetchall()]
    return jsonify({"records": rows, "generated": datetime.datetime.now().isoformat(timespec="seconds")})

@app.route("/api/record/<int:rid>")
def record(rid):
    r = db().execute("SELECT type,data_json FROM inspections WHERE id=?", (rid,)).fetchone()
    if not r: abort(404)
    return jsonify({"type": r["type"], "data": json.loads(r["data_json"])})

@app.route("/api/facets")
def facets():
    con = db()
    def uniq(col):
        return [r[0] for r in con.execute(
            f"SELECT DISTINCT {col} v FROM inspections WHERE {col}<>'' ORDER BY {col}").fetchall()]
    return jsonify({
        "months": [r[0] for r in con.execute(
            "SELECT DISTINCT month FROM inspections WHERE month<>'' ORDER BY month DESC").fetchall()],
        "lines": uniq("line"), "checkers": uniq("checker"),
        "counts": {r["type"]: r["n"] for r in con.execute(
            "SELECT type, COUNT(*) n FROM inspections GROUP BY type").fetchall()}
    })

@app.route("/export.csv")
def export_csv():
    rows = list_inspections().json["records"]
    cols = ["insp_datetime","type","line","checker","shift","prod_order",
            "item","des","model","lot","appearance"]
    buf = io.StringIO(); buf.write("﻿")
    w = csv.writer(buf); w.writerow(cols)
    for r in rows: w.writerow([r.get(c,"") for c in cols])
    return Response(buf.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=first_lot.csv"})

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8000, threaded=True, debug=False)
