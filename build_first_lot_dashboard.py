# -*- coding: utf-8 -*-
"""
build_first_lot_dashboard.py
----------------------------
อ่านไฟล์ .xlsm 3 ไฟล์ในโฟลเดอร์ "First lot" (ชีต HISTORYLOG)
แล้วสร้าง dashboard เดียว: First_Lot_Dashboard.html (self-contained, ไม่พึ่ง internet)

วิธีใช้ :
    python build_first_lot_dashboard.py

อัปเดตอัตโนมัติ (Windows) : ตั้ง Task Scheduler ให้รันคำสั่งนี้ทุก X นาที
    เอาต์พุต HTML วางไว้บน shared folder ให้ทุกเครื่องเปิดดูแบบอ่านอย่างเดียว
"""
import openpyxl, json, datetime, os, sys, html

BASE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(BASE, "First lot")
OUT  = os.path.join(BASE, "First_Lot_Dashboard.html")

# (ชื่อประเภท, ไฟล์, คอลัมน์ APPEARANCE 1-indexed)
FILES = {
    "Base Assy":     ("BASE ASSY MASTER RECORD LINE 10 R4.xlsm", 26),
    "Kashime":       ("KASHIME MASTER RECORD LINE 7 R3.xlsm", 25),
    "Manual & Auto": ("MANUAL & AUTO MASTER RECORD MASTER R4.xlsm", 15),
}
# คอลัมน์ร่วม 14 ช่องแรก (เหมือนกันทั้ง 3 ไฟล์) 1-indexed
COMMON = {"datetime":1,"line":2,"setdie":3,"checker":4,"shift":5,"order":6,
          "item":7,"des":8,"prodline":9,"seq":10,"lot":11,"month":12,
          "model":13,"desmodel":14}

def clean(v):
    if v is None: return ""
    if isinstance(v,(datetime.datetime,datetime.date,datetime.time)): return v.isoformat()
    if isinstance(v,str): return v.strip()
    return v

def extract():
    records, summary = [], {}
    for typ,(fn,appcol) in FILES.items():
        path = os.path.join(SRC, fn)
        if not os.path.exists(path):
            print(f"  ! ไม่พบไฟล์: {fn} — ข้าม");
            summary[typ]={"total":0,"ok":0,"ng":0,"other":0}; continue
        print(f"  อ่าน {fn} ...", flush=True)
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True, keep_links=False)
        ws = wb["HISTORYLOG"]
        n=ok=ng=other=0
        for row in ws.iter_rows(min_row=3, values_only=True):
            rec={"type":typ}
            for k,ci in COMMON.items():
                rec[k]=clean(row[ci-1]) if ci-1 < len(row) else ""
            app = clean(row[appcol-1]) if appcol-1 < len(row) else ""
            rec["appearance"]=app
            if rec["datetime"]=="" and rec["order"]=="":  # ข้ามแถวว่าง
                continue
            u=str(app).strip().upper()
            if u=="OK": ok+=1
            elif u in ("NG","NG HAVE"): ng+=1
            elif u=="": pass
            else: other+=1
            records.append(rec); n+=1
        summary[typ]={"total":n,"ok":ok,"ng":ng,"other":other}
        wb.close()
        print(f"    -> {n} รายการ")
    return {"generated":datetime.datetime.now().isoformat(timespec="seconds"),
            "summary":summary,"records":records}

def main():
    print("First Lot Dashboard generator")
    data = extract()
    tpl = HTML_TEMPLATE.replace("/*__DATA__*/null",
                                json.dumps(data, ensure_ascii=False))
    with open(OUT,"w",encoding="utf-8") as f:
        f.write(tpl)
    kb = os.path.getsize(OUT)/1024
    print(f"สร้างเสร็จ: {OUT}  ({kb:.0f} KB, {len(data['records'])} รายการ)")

# ======================================================================
# HTML TEMPLATE (self-contained: no CDN, charts drawn with inline SVG)
# ======================================================================
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>First Lot Inspection Dashboard</title>
<style>
:root{
  --blue:#2563EB;--blue-dark:#1D4FD7;--blue-light:#E7EEFE;
  --ok:#0EA571;--ok-light:#E4F6EF;--ng:#E14B4B;--ng-light:#FCEBEB;
  --amber:#EF9F27;--amber-light:#FCF1DE;--purple:#6C63FF;--purple-light:#EEEDFE;
  --bg:#EEF1F6;--surface:#FFFFFF;--surface2:#F4F6FA;
  --border:#E3E7EF;--border-strong:#D2D8E3;
  --text:#161A2B;--text2:#525873;--text3:#878DA6;
  --radius:12px;--radius-lg:16px;
  --shadow:0 1px 2px rgba(20,26,45,.04),0 6px 16px -8px rgba(20,26,45,.10);
  --shadow-md:0 4px 12px -4px rgba(20,26,45,.10),0 12px 28px -10px rgba(20,26,45,.12);
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
  font-family:"IBM Plex Sans Thai","IBM Plex Sans","Segoe UI",Tahoma,sans-serif;
  font-size:14px;line-height:1.5;-webkit-font-smoothing:antialiased}
.wrap{max-width:1440px;margin:0 auto;padding:20px 22px 60px}
h1{font-size:22px;margin:0;font-weight:700;letter-spacing:-.3px}
.sub{color:var(--text2);font-size:13px;margin-top:3px}
header.top{display:flex;justify-content:space-between;align-items:flex-start;
  gap:16px;flex-wrap:wrap;margin-bottom:20px}
.badge{display:inline-flex;align-items:center;gap:6px;background:var(--surface);
  border:1px solid var(--border);border-radius:99px;padding:6px 13px;font-size:12px;
  color:var(--text2);box-shadow:var(--shadow)}
.dot{width:8px;height:8px;border-radius:50%;background:var(--ok)}
/* KPI */
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin-bottom:20px}
.kpi{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);
  padding:16px 18px;box-shadow:var(--shadow);position:relative;overflow:hidden}
.kpi .label{font-size:12px;color:var(--text2);font-weight:500}
.kpi .num{font-size:28px;font-weight:700;margin-top:4px;letter-spacing:-.5px;
  font-family:"IBM Plex Sans","JetBrains Mono",monospace}
.kpi .foot{font-size:11px;color:var(--text3);margin-top:2px}
.kpi .bar{position:absolute;left:0;top:0;bottom:0;width:4px}
.kpi.b-blue .bar{background:var(--blue)} .kpi.b-ok .bar{background:var(--ok)}
.kpi.b-amber .bar{background:var(--amber)} .kpi.b-purple .bar{background:var(--purple)}
.kpi.b-slate .bar{background:var(--text3)}
/* card */
.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);
  box-shadow:var(--shadow);padding:16px 18px;margin-bottom:18px}
.card h3{margin:0 0 14px;font-size:14px;font-weight:600;display:flex;align-items:center;gap:8px}
.card h3 small{font-weight:400;color:var(--text3);font-size:12px}
.grid2{display:grid;grid-template-columns:1.55fr 1fr;gap:18px}
.grid2b{display:grid;grid-template-columns:1fr 1fr;gap:18px}
@media(max-width:960px){.grid2,.grid2b{grid-template-columns:1fr}}
/* filters */
.filters{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-bottom:18px}
.chip{border:1px solid var(--border-strong);background:var(--surface);border-radius:99px;
  padding:7px 15px;font-size:13px;cursor:pointer;color:var(--text2);font-weight:500;
  transition:.12s;user-select:none}
.chip:hover{border-color:var(--blue);color:var(--blue)}
.chip.on{background:var(--blue);border-color:var(--blue);color:#fff}
select,input[type=search]{font-family:inherit;font-size:13px;padding:8px 11px;
  border:1px solid var(--border-strong);border-radius:9px;background:var(--surface);
  color:var(--text);outline:none;min-width:140px}
input[type=search]{min-width:200px}
select:focus,input:focus{border-color:var(--blue);box-shadow:0 0 0 3px var(--blue-light)}
.btn{font-family:inherit;font-size:13px;padding:8px 14px;border-radius:9px;border:1px solid var(--border-strong);
  background:var(--surface);color:var(--text2);cursor:pointer;font-weight:500}
.btn:hover{border-color:var(--blue);color:var(--blue)}
.btn.primary{background:var(--blue);border-color:var(--blue);color:#fff}
.spacer{flex:1}
/* table */
.tablewrap{overflow-x:auto;border:1px solid var(--border);border-radius:var(--radius);max-height:560px;overflow-y:auto}
table{border-collapse:collapse;width:100%;font-size:12.5px;white-space:nowrap}
thead th{position:sticky;top:0;background:var(--surface2);z-index:2;text-align:left;
  padding:10px 12px;font-weight:600;color:var(--text2);border-bottom:1px solid var(--border-strong);cursor:pointer}
thead th:hover{color:var(--blue)}
thead th .ar{color:var(--blue);font-size:10px}
tbody td{padding:8px 12px;border-bottom:1px solid var(--border)}
tbody tr:hover{background:var(--surface2)}
.tag{display:inline-block;padding:2px 9px;border-radius:99px;font-size:11px;font-weight:600}
.tag.t-base{background:var(--blue-light);color:var(--blue-dark)}
.tag.t-kash{background:var(--purple-light);color:#4b45b5}
.tag.t-man{background:var(--amber-light);color:#92560c}
.res-ok{color:var(--ok);font-weight:700}
.res-ng{color:var(--ng);font-weight:700}
.muted{color:var(--text3)}
.tablefoot{display:flex;justify-content:space-between;align-items:center;margin-top:10px;
  font-size:12px;color:var(--text2);flex-wrap:wrap;gap:10px}
.pager{display:flex;gap:6px;align-items:center}
.pager button{border:1px solid var(--border-strong);background:var(--surface);border-radius:7px;
  padding:5px 10px;cursor:pointer;font-family:inherit;font-size:12px}
.pager button:disabled{opacity:.4;cursor:default}
/* svg chart helpers */
.legend{display:flex;gap:14px;flex-wrap:wrap;margin-top:10px;font-size:12px;color:var(--text2)}
.legend span{display:inline-flex;align-items:center;gap:6px}
.legend i{width:10px;height:10px;border-radius:3px;display:inline-block}
.barrow{display:flex;align-items:center;gap:10px;margin-bottom:9px;font-size:12.5px}
.barrow .bl{width:120px;text-align:right;color:var(--text2);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.barrow .bt{flex:1;background:var(--surface2);border-radius:6px;height:20px;overflow:hidden}
.barrow .bf{height:100%;border-radius:6px;display:flex;align-items:center;justify-content:flex-end;
  padding-right:7px;color:#fff;font-size:11px;font-weight:600;min-width:22px}
.barrow .bv{width:44px;text-align:right;font-weight:600;font-family:"JetBrains Mono",monospace}
.empty{text-align:center;color:var(--text3);padding:40px}
</style>
</head>
<body>
<div class="wrap">
  <header class="top">
    <div>
      <h1>First Lot Inspection Dashboard</h1>
      <div class="sub">รวมผลตรวจ First Lot งานโลหะ — Base Assy · Kashime · Manual &amp; Auto</div>
    </div>
    <div style="display:flex;gap:8px;flex-wrap:wrap">
      <span class="badge"><span class="dot"></span> ข้อมูล ณ <b id="genTime" style="margin-left:4px">-</b></span>
      <span class="badge" id="rangeBadge">-</span>
    </div>
  </header>

  <section class="kpis" id="kpis"></section>

  <div class="filters">
    <div id="typeChips" style="display:flex;gap:8px"></div>
    <select id="fMonth"><option value="">ทุกเดือน</option></select>
    <select id="fLine"><option value="">ทุก Line</option></select>
    <select id="fChecker"><option value="">ทุก Checker</option></select>
    <input type="search" id="fSearch" placeholder="ค้นหา (Order / Item / Model / Lot)"/>
    <span class="spacer"></span>
    <button class="btn" id="btnReset">ล้างตัวกรอง</button>
    <button class="btn primary" id="btnCsv">Export CSV</button>
  </div>

  <div class="grid2">
    <div class="card">
      <h3>แนวโน้มการตรวจรายเดือน <small id="trendSub"></small></h3>
      <div id="trend"></div>
    </div>
    <div class="card">
      <h3>สัดส่วนตามประเภทงาน</h3>
      <div id="donut" style="display:flex;justify-content:center"></div>
      <div class="legend" id="donutLegend"></div>
    </div>
  </div>

  <div class="grid2b">
    <div class="card"><h3>Top 10 Line Prod. <small>ตามจำนวนตรวจ</small></h3><div id="topLine"></div></div>
    <div class="card"><h3>Top 10 Checker <small>ตามจำนวนตรวจ</small></h3><div id="topChecker"></div></div>
  </div>

  <div class="card">
    <h3>รายการตรวจ <small id="tableCount"></small></h3>
    <div class="tablewrap">
      <table id="tbl">
        <thead><tr id="thead"></tr></thead>
        <tbody id="tbody"></tbody>
      </table>
    </div>
    <div class="tablefoot">
      <div id="rowsInfo"></div>
      <div class="pager">
        <button id="pPrev">‹ ก่อนหน้า</button>
        <span id="pInfo"></span>
        <button id="pNext">ถัดไป ›</button>
      </div>
    </div>
  </div>

  <div class="sub" style="text-align:center;margin-top:24px;color:var(--text3)">
    สร้างจากไฟล์ HISTORYLOG โดยสคริปต์ build_first_lot_dashboard.py · ดูอย่างเดียว (read-only)
  </div>
</div>

<script>
const DASH = /*__DATA__*/null;
const TYPES = {"Base Assy":{c:"#2563EB",cls:"t-base"},
               "Kashime":{c:"#6C63FF",cls:"t-kash"},
               "Manual & Auto":{c:"#EF9F27",cls:"t-man"}};
const COLS = [
  ["datetime","วันที่-เวลา"],["type","ประเภท"],["line","Line Prod."],
  ["checker","Checker"],["shift","Shift"],["order","Prod. Order"],
  ["item","Item"],["des","Description"],["model","Model"],
  ["lot","Lot"],["appearance","ผล"]
];
const $=s=>document.querySelector(s);
const esc=s=>String(s==null?"":s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
function fmtDate(iso){ if(!iso)return ""; const d=new Date(iso);
  if(isNaN(d)) return iso.slice(0,16).replace("T"," ");
  const p=n=>String(n).padStart(2,"0");
  return `${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`; }
function monthKey(iso){ return iso? iso.slice(0,7):""; }

let ACTIVE_TYPES=new Set(Object.keys(TYPES));
let sortKey="datetime", sortDir=-1, page=1, PAGE=25;

// init records: attach parsed fields
DASH.records.forEach(r=>{ r._m=monthKey(r.datetime); });

function buildFacets(){
  const months=[...new Set(DASH.records.map(r=>r._m).filter(Boolean))].sort().reverse();
  const lines=[...new Set(DASH.records.map(r=>String(r.line).trim()).filter(Boolean))].sort();
  const checkers=[...new Set(DASH.records.map(r=>String(r.checker).trim()).filter(Boolean))].sort();
  const mSel=$("#fMonth"),lSel=$("#fLine"),cSel=$("#fChecker");
  months.forEach(m=>mSel.insertAdjacentHTML("beforeend",`<option value="${m}">${m}</option>`));
  lines.forEach(l=>lSel.insertAdjacentHTML("beforeend",`<option value="${esc(l)}">${esc(l)}</option>`));
  checkers.forEach(c=>cSel.insertAdjacentHTML("beforeend",`<option value="${esc(c)}">${esc(c)}</option>`));
  // type chips
  const tc=$("#typeChips");
  Object.keys(TYPES).forEach(t=>{
    const el=document.createElement("div");
    el.className="chip on"; el.textContent=t; el.dataset.t=t;
    el.onclick=()=>{ el.classList.toggle("on");
      if(el.classList.contains("on"))ACTIVE_TYPES.add(t); else ACTIVE_TYPES.delete(t);
      render(); };
    tc.appendChild(el);
  });
}

function currentFilter(){
  const m=$("#fMonth").value, l=$("#fLine").value, c=$("#fChecker").value,
        q=$("#fSearch").value.trim().toLowerCase();
  return DASH.records.filter(r=>{
    if(!ACTIVE_TYPES.has(r.type))return false;
    if(m && r._m!==m)return false;
    if(l && String(r.line).trim()!==l)return false;
    if(c && String(r.checker).trim()!==c)return false;
    if(q){ const hay=(r.order+" "+r.item+" "+r.model+" "+r.desmodel+" "+r.lot+" "+r.des).toLowerCase();
      if(!hay.includes(q))return false; }
    return true;
  });
}

function renderKpis(rows){
  const total=rows.length;
  const byType={}; Object.keys(TYPES).forEach(t=>byType[t]=0);
  let ok=0,ng=0;
  const nowM=new Date().toISOString().slice(0,7); let thisMonth=0;
  rows.forEach(r=>{ byType[r.type]=(byType[r.type]||0)+1;
    const u=String(r.appearance).trim().toUpperCase();
    if(u==="OK")ok++; else if(u==="NG"||u==="NG HAVE")ng++;
    if(r._m===nowM)thisMonth++; });
  const okRate= total? (ok/total*100):0;
  const cards=[
    ["b-blue","รายการตรวจทั้งหมด",total.toLocaleString(),"records หลังกรอง"],
    ["b-ok","ผ่าน (OK)",ok.toLocaleString(),okRate.toFixed(1)+"% ของทั้งหมด"],
    ["b-amber","ไม่ผ่าน / อื่นๆ",(total-ok).toLocaleString(), ng?(ng+" NG"):"ไม่มี NG บันทึกไว้"],
    ["b-purple","เดือนนี้",thisMonth.toLocaleString(),nowM],
    ["b-slate","Base / Kash / Man",`${byType["Base Assy"]} / ${byType["Kashime"]} / ${byType["Manual & Auto"]}`,"แยกตามประเภท"]
  ];
  $("#kpis").innerHTML=cards.map(c=>
    `<div class="kpi ${c[0]}"><div class="bar"></div><div class="label">${c[1]}</div>
     <div class="num">${c[2]}</div><div class="foot">${c[3]}</div></div>`).join("");
}

function renderTrend(rows){
  const by={}; rows.forEach(r=>{ if(r._m) by[r._m]=(by[r._m]||0)+1; });
  const months=Object.keys(by).sort();
  $("#trendSub").textContent = months.length? `${months[0]} – ${months[months.length-1]}`:"";
  if(!months.length){ $("#trend").innerHTML='<div class="empty">ไม่มีข้อมูล</div>'; return; }
  const max=Math.max(...months.map(m=>by[m]));
  const W=Math.max(months.length*54,300),H=200,pad=28,bw=34;
  let bars="";
  months.forEach((m,i)=>{
    const h=(by[m]/max)*(H-pad-20);
    const x=i*54+14, y=H-pad-h;
    bars+=`<rect x="${x}" y="${y}" width="${bw}" height="${h}" rx="4" fill="#2563EB"><title>${m}: ${by[m]}</title></rect>
           <text x="${x+bw/2}" y="${y-5}" text-anchor="middle" font-size="11" fill="#525873" font-weight="600">${by[m]}</text>
           <text x="${x+bw/2}" y="${H-pad+14}" text-anchor="middle" font-size="10" fill="#878DA6">${m.slice(2)}</text>`;
  });
  $("#trend").innerHTML=`<div style="overflow-x:auto"><svg width="${W}" height="${H}" style="min-width:100%">
     <line x1="10" y1="${H-pad}" x2="${W-4}" y2="${H-pad}" stroke="#E3E7EF"/>${bars}</svg></div>`;
}

function renderDonut(rows){
  const by={}; Object.keys(TYPES).forEach(t=>by[t]=0);
  rows.forEach(r=>by[r.type]=(by[r.type]||0)+1);
  const total=rows.length||1, R=70,r0=44,cx=90,cy=90;
  let a=-Math.PI/2, seg="";
  Object.keys(TYPES).forEach(t=>{
    const frac=by[t]/total; if(frac<=0)return;
    const a2=a+frac*2*Math.PI;
    const large=frac>0.5?1:0;
    const x1=cx+R*Math.cos(a),y1=cy+R*Math.sin(a),x2=cx+R*Math.cos(a2),y2=cy+R*Math.sin(a2);
    const xi2=cx+r0*Math.cos(a2),yi2=cy+r0*Math.sin(a2),xi1=cx+r0*Math.cos(a);
    const yi1=cy+r0*Math.sin(a);
    seg+=`<path d="M${x1} ${y1} A${R} ${R} 0 ${large} 1 ${x2} ${y2} L${xi2} ${yi2} A${r0} ${r0} 0 ${large} 0 ${xi1} ${yi1} Z" fill="${TYPES[t].c}"><title>${t}: ${by[t]}</title></path>`;
    a=a2;
  });
  $("#donut").innerHTML=`<svg width="180" height="180">${seg}
    <text x="90" y="86" text-anchor="middle" font-size="26" font-weight="700" fill="#161A2B">${rows.length}</text>
    <text x="90" y="104" text-anchor="middle" font-size="11" fill="#878DA6">รายการ</text></svg>`;
  $("#donutLegend").innerHTML=Object.keys(TYPES).map(t=>
    `<span><i style="background:${TYPES[t].c}"></i>${t} <b style="margin-left:3px">${by[t]}</b></span>`).join("");
}

function renderTopBars(rows,key,el){
  const by={}; rows.forEach(r=>{ const k=String(r[key]).trim(); if(k)by[k]=(by[k]||0)+1; });
  const arr=Object.entries(by).sort((a,b)=>b[1]-a[1]).slice(0,10);
  if(!arr.length){ el.innerHTML='<div class="empty">ไม่มีข้อมูล</div>'; return; }
  const max=arr[0][1];
  el.innerHTML=arr.map(([k,v])=>{
    const w=(v/max)*100;
    return `<div class="barrow"><div class="bl" title="${esc(k)}">${esc(k)}</div>
      <div class="bt"><div class="bf" style="width:${w}%;background:#2563EB">${v>=max*0.15?v:""}</div></div>
      <div class="bv">${v}</div></div>`;
  }).join("");
}

function renderTable(rows){
  // sort
  const sorted=[...rows].sort((a,b)=>{
    let x=a[sortKey],y=b[sortKey];
    if(sortKey==="datetime"){x=x||"";y=y||"";}
    if(x<y)return -1*sortDir; if(x>y)return 1*sortDir; return 0;
  });
  const pages=Math.max(1,Math.ceil(sorted.length/PAGE));
  if(page>pages)page=pages;
  const slice=sorted.slice((page-1)*PAGE,page*PAGE);
  $("#thead").innerHTML=COLS.map(c=>{
    const ar=c[0]===sortKey?`<span class="ar">${sortDir<0?"▼":"▲"}</span>`:"";
    return `<th data-k="${c[0]}">${c[1]} ${ar}</th>`;}).join("");
  $("#tbody").innerHTML=slice.map(r=>{
    const u=String(r.appearance).trim().toUpperCase();
    const res=u==="OK"?'<span class="res-ok">OK</span>':(u?`<span class="res-ng">${esc(r.appearance)}</span>`:'<span class="muted">-</span>');
    return `<tr>
      <td>${fmtDate(r.datetime)}</td>
      <td><span class="tag ${TYPES[r.type].cls}">${r.type}</span></td>
      <td>${esc(r.line)}</td><td>${esc(r.checker)}</td><td>${esc(r.shift)||'<span class=muted>-</span>'}</td>
      <td>${esc(r.order)}</td><td>${esc(r.item)}</td>
      <td title="${esc(r.des)}">${esc(String(r.des).slice(0,26))}</td>
      <td>${esc(r.model)}</td><td>${esc(r.lot)}</td><td>${res}</td></tr>`;
  }).join("") || `<tr><td colspan="${COLS.length}" class="empty">ไม่พบรายการตามตัวกรอง</td></tr>`;
  $("#tableCount").textContent=`(${rows.length.toLocaleString()} รายการ)`;
  $("#rowsInfo").textContent=`แสดง ${slice.length? (page-1)*PAGE+1:0}–${(page-1)*PAGE+slice.length} จาก ${rows.length.toLocaleString()}`;
  $("#pInfo").textContent=`หน้า ${page}/${pages}`;
  $("#pPrev").disabled=page<=1; $("#pNext").disabled=page>=pages;
  document.querySelectorAll("#thead th").forEach(th=>th.onclick=()=>{
    const k=th.dataset.k; if(k===sortKey)sortDir*=-1; else{sortKey=k;sortDir=1;}
    page=1; render();
  });
}

let CUR=[];
function render(){
  CUR=currentFilter();
  renderKpis(CUR); renderTrend(CUR); renderDonut(CUR);
  renderTopBars(CUR,"line",$("#topLine"));
  renderTopBars(CUR,"checker",$("#topChecker"));
  renderTable(CUR);
}

function exportCsv(){
  const rows=currentFilter();
  const head=COLS.map(c=>c[1]);
  const lines=[head.join(",")];
  rows.forEach(r=>{
    const vals=COLS.map(c=>{ let v=c[0]==="datetime"?fmtDate(r.datetime):r[c[0]];
      v=String(v==null?"":v).replace(/"/g,'""'); return /[",\n]/.test(v)?`"${v}"`:v; });
    lines.push(vals.join(","));
  });
  const blob=new Blob(["﻿"+lines.join("\r\n")],{type:"text/csv;charset=utf-8"});
  const a=document.createElement("a");
  a.href=URL.createObjectURL(blob);
  a.download="first_lot_"+new Date().toISOString().slice(0,10)+".csv";
  a.click();
}

// wire up
function init(){
  $("#genTime").textContent=(DASH.generated||"").replace("T"," ").slice(0,16);
  const ds=DASH.records.map(r=>r.datetime).filter(Boolean).sort();
  if(ds.length)$("#rangeBadge").textContent=`ช่วง ${ds[0].slice(0,10)} → ${ds[ds.length-1].slice(0,10)}`;
  buildFacets();
  ["fMonth","fLine","fChecker"].forEach(id=>$("#"+id).onchange=()=>{page=1;render();});
  $("#fSearch").oninput=()=>{page=1;render();};
  $("#btnReset").onclick=()=>{ $("#fMonth").value="";$("#fLine").value="";$("#fChecker").value="";$("#fSearch").value="";
    ACTIVE_TYPES=new Set(Object.keys(TYPES));
    document.querySelectorAll("#typeChips .chip").forEach(c=>c.classList.add("on"));
    page=1;render(); };
  $("#btnCsv").onclick=exportCsv;
  $("#pPrev").onclick=()=>{if(page>1){page--;renderTable(CUR);}};
  $("#pNext").onclick=()=>{page++;renderTable(CUR);};
  render();
}
init();
</script>
</body>
</html>
"""

if __name__=="__main__":
    main()
