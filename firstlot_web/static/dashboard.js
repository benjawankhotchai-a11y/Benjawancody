(function(){
const TYPES={"base":{label:"Base Assy",c:"#2563EB",cls:"t-base"},
             "kashime":{label:"Kashime",c:"#6C63FF",cls:"t-kashime"},
             "manual":{label:"Manual & Auto",c:"#EF9F27",cls:"t-manual"}};
const COLS=[["insp_datetime","วันที่-เวลา"],["type","ประเภท"],["line","Line Prod."],
  ["checker","Checker"],["shift","Shift"],["prod_order","Prod. Order"],
  ["item","Item"],["des","Description"],["model","Model"],["lot","Lot"],["appearance","ผล"]];
const $=s=>document.querySelector(s);
const esc=FL.esc;
function fmtDate(iso){ if(!iso)return ""; const d=new Date(iso);
  if(isNaN(d))return String(iso).slice(0,16).replace("T"," ");
  const p=n=>String(n).padStart(2,"0");
  return `${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;}

let ALL=[], ACTIVE=new Set(Object.keys(TYPES)), sortKey="insp_datetime", sortDir=-1, page=1, PAGE=25, CUR=[];

async function load(){
  const d=await FL.getJSON("/api/inspections");
  ALL=d.records; ALL.forEach(r=>r._m=(r.month||String(r.insp_datetime||"").slice(0,7)));
  $("#genTime").textContent=(d.generated||"").replace("T"," ").slice(0,16);
  buildFacets(); render();
}
async function buildFacets(){
  const f=await FL.getJSON("/api/facets");
  const mSel=$("#fMonth"),lSel=$("#fLine"),cSel=$("#fChecker");
  mSel.length=1;lSel.length=1;cSel.length=1;
  (f.months||[]).forEach(m=>mSel.insertAdjacentHTML("beforeend",`<option>${m}</option>`));
  (f.lines||[]).forEach(l=>lSel.insertAdjacentHTML("beforeend",`<option>${esc(l)}</option>`));
  (f.checkers||[]).forEach(c=>cSel.insertAdjacentHTML("beforeend",`<option>${esc(c)}</option>`));
  const tc=$("#typeChips"); if(!tc.dataset.built){ tc.dataset.built=1;
    Object.keys(TYPES).forEach(t=>{ const el=document.createElement("div");
      el.className="chip on"; el.textContent=TYPES[t].label; el.dataset.t=t;
      el.onclick=()=>{ el.classList.toggle("on");
        el.classList.contains("on")?ACTIVE.add(t):ACTIVE.delete(t); render(); };
      tc.appendChild(el); });
  }
}
function currentFilter(){
  const m=$("#fMonth").value,l=$("#fLine").value,c=$("#fChecker").value,
        q=$("#fSearch").value.trim().toLowerCase();
  return ALL.filter(r=>{
    if(!ACTIVE.has(r.type))return false;
    if(m&&r._m!==m)return false;
    if(l&&String(r.line).trim()!==l)return false;
    if(c&&String(r.checker).trim()!==c)return false;
    if(q){const hay=(r.prod_order+" "+r.item+" "+r.model+" "+r.lot+" "+r.des).toLowerCase();
      if(!hay.includes(q))return false;}
    return true;
  });
}
function renderKpis(rows){
  const total=rows.length,by={};Object.keys(TYPES).forEach(t=>by[t]=0);
  let ok=0,ng=0;const nowM=new Date().toISOString().slice(0,7);let tm=0;
  rows.forEach(r=>{by[r.type]=(by[r.type]||0)+1;
    const u=String(r.appearance).trim().toUpperCase();
    if(u==="OK")ok++;else if(u==="NG"||u==="NG HAVE")ng++;
    if(r._m===nowM)tm++;});
  const rate=total?(ok/total*100):0;
  const cards=[
    ["b-blue","รายการตรวจทั้งหมด",total.toLocaleString(),"records หลังกรอง"],
    ["b-ok","ผ่าน (OK)",ok.toLocaleString(),rate.toFixed(1)+"%"],
    ["b-amber","ไม่ผ่าน / อื่นๆ",(total-ok).toLocaleString(),ng?(ng+" NG"):"ไม่มี NG"],
    ["b-purple","เดือนนี้",tm.toLocaleString(),nowM],
    ["b-slate","Base / Kash / Man",`${by.base} / ${by.kashime} / ${by.manual}`,"แยกประเภท"]];
  $("#kpis").innerHTML=cards.map(c=>`<div class="kpi ${c[0]}"><div class="bar"></div>
    <div class="label">${c[1]}</div><div class="num">${c[2]}</div><div class="foot">${c[3]}</div></div>`).join("");
}
function renderTrend(rows){
  const by={};rows.forEach(r=>{if(r._m)by[r._m]=(by[r._m]||0)+1;});
  const ms=Object.keys(by).sort();
  $("#trendSub").textContent=ms.length?`${ms[0]} – ${ms[ms.length-1]}`:"";
  if(!ms.length){$("#trend").innerHTML='<div class="empty">ไม่มีข้อมูล</div>';return;}
  const max=Math.max(...ms.map(m=>by[m])),W=Math.max(ms.length*54,300),H=200,pad=28,bw=34;
  let bars="";
  ms.forEach((m,i)=>{const h=(by[m]/max)*(H-pad-20),x=i*54+14,y=H-pad-h;
    bars+=`<rect x="${x}" y="${y}" width="${bw}" height="${h}" rx="4" fill="#2563EB"><title>${m}: ${by[m]}</title></rect>
      <text x="${x+bw/2}" y="${y-5}" text-anchor="middle" font-size="11" fill="#525873" font-weight="600">${by[m]}</text>
      <text x="${x+bw/2}" y="${H-pad+14}" text-anchor="middle" font-size="10" fill="#878DA6">${m.slice(2)}</text>`;});
  $("#trend").innerHTML=`<div style="overflow-x:auto"><svg width="${W}" height="${H}" style="min-width:100%">
    <line x1="10" y1="${H-pad}" x2="${W-4}" y2="${H-pad}" stroke="#E3E7EF"/>${bars}</svg></div>`;
}
function renderDonut(rows){
  const by={};Object.keys(TYPES).forEach(t=>by[t]=0);rows.forEach(r=>by[r.type]=(by[r.type]||0)+1);
  const total=rows.length||1,R=70,r0=44,cx=90,cy=90;let a=-Math.PI/2,seg="";
  Object.keys(TYPES).forEach(t=>{const frac=by[t]/total;if(frac<=0)return;
    const a2=a+frac*2*Math.PI,large=frac>0.5?1:0;
    const x1=cx+R*Math.cos(a),y1=cy+R*Math.sin(a),x2=cx+R*Math.cos(a2),y2=cy+R*Math.sin(a2);
    const xi2=cx+r0*Math.cos(a2),yi2=cy+r0*Math.sin(a2),xi1=cx+r0*Math.cos(a),yi1=cy+r0*Math.sin(a);
    seg+=`<path d="M${x1} ${y1} A${R} ${R} 0 ${large} 1 ${x2} ${y2} L${xi2} ${yi2} A${r0} ${r0} 0 ${large} 0 ${xi1} ${yi1} Z" fill="${TYPES[t].c}"><title>${TYPES[t].label}: ${by[t]}</title></path>`;
    a=a2;});
  $("#donut").innerHTML=`<svg width="180" height="180">${seg}
    <text x="90" y="86" text-anchor="middle" font-size="26" font-weight="700" fill="#161A2B">${rows.length}</text>
    <text x="90" y="104" text-anchor="middle" font-size="11" fill="#878DA6">รายการ</text></svg>`;
  $("#donutLegend").innerHTML=Object.keys(TYPES).map(t=>
    `<span><i style="background:${TYPES[t].c}"></i>${TYPES[t].label} <b style="margin-left:3px">${by[t]}</b></span>`).join("");
}
function renderTop(rows,key,el){
  const by={};rows.forEach(r=>{const k=String(r[key]).trim();if(k)by[k]=(by[k]||0)+1;});
  const arr=Object.entries(by).sort((a,b)=>b[1]-a[1]).slice(0,10);
  if(!arr.length){el.innerHTML='<div class="empty">ไม่มีข้อมูล</div>';return;}
  const max=arr[0][1];
  el.innerHTML=arr.map(([k,v])=>`<div class="barrow"><div class="bl" title="${esc(k)}">${esc(k)}</div>
    <div class="bt"><div class="bf" style="width:${(v/max)*100}%">${v>=max*0.15?v:""}</div></div>
    <div class="bv">${v}</div></div>`).join("");
}
function renderTable(rows){
  const sorted=[...rows].sort((a,b)=>{let x=a[sortKey]||"",y=b[sortKey]||"";
    return x<y?-sortDir:x>y?sortDir:0;});
  const pages=Math.max(1,Math.ceil(sorted.length/PAGE));if(page>pages)page=pages;
  const slice=sorted.slice((page-1)*PAGE,page*PAGE);
  $("#thead").innerHTML=COLS.map(c=>`<th data-k="${c[0]}">${c[1]} ${c[0]===sortKey?(sortDir<0?"▼":"▲"):""}</th>`).join("");
  $("#tbody").innerHTML=slice.map(r=>{
    const u=String(r.appearance).trim().toUpperCase();
    const res=u==="OK"?'<span class="res-ok">OK</span>':(u?`<span class="res-ng">${esc(r.appearance)}</span>`:'<span class="muted">-</span>');
    const T=TYPES[r.type]||{label:r.type,cls:""};
    return `<tr><td>${fmtDate(r.insp_datetime)}</td><td><span class="tag ${T.cls}">${T.label}</span></td>
      <td>${esc(r.line)}</td><td>${esc(r.checker)}</td><td>${esc(r.shift)||'<span class=muted>-</span>'}</td>
      <td>${esc(r.prod_order)}</td><td>${esc(r.item)}</td>
      <td title="${esc(r.des)}">${esc(String(r.des||"").slice(0,26))}</td>
      <td>${esc(r.model)}</td><td>${esc(r.lot)}</td><td>${res}</td></tr>`;
  }).join("")||`<tr><td colspan="${COLS.length}" class="empty">ไม่พบรายการ</td></tr>`;
  $("#tableCount").textContent=`(${rows.length.toLocaleString()} รายการ)`;
  $("#rowsInfo").textContent=`แสดง ${slice.length?(page-1)*PAGE+1:0}–${(page-1)*PAGE+slice.length} จาก ${rows.length.toLocaleString()}`;
  $("#pInfo").textContent=`หน้า ${page}/${pages}`;
  $("#pPrev").disabled=page<=1;$("#pNext").disabled=page>=pages;
  document.querySelectorAll("#thead th").forEach(th=>th.onclick=()=>{
    const k=th.dataset.k;if(k===sortKey)sortDir*=-1;else{sortKey=k;sortDir=1;}page=1;renderTable(CUR);});
}
function render(){CUR=currentFilter();
  renderKpis(CUR);renderTrend(CUR);renderDonut(CUR);
  renderTop(CUR,"line",$("#topLine"));renderTop(CUR,"checker",$("#topChecker"));
  renderTable(CUR);}
["fMonth","fLine","fChecker"].forEach(id=>$("#"+id).onchange=()=>{page=1;render();});
$("#fSearch").oninput=()=>{page=1;render();};
$("#btnReset").onclick=()=>{["fMonth","fLine","fChecker"].forEach(i=>$("#"+i).value="");$("#fSearch").value="";
  ACTIVE=new Set(Object.keys(TYPES));document.querySelectorAll("#typeChips .chip").forEach(c=>c.classList.add("on"));page=1;render();};
$("#btnReload").onclick=load;
$("#pPrev").onclick=()=>{if(page>1){page--;renderTable(CUR);}};
$("#pNext").onclick=()=>{page++;renderTable(CUR);};
load();
})();
