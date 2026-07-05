// shared helpers
window.FL = {
  esc: s => String(s==null?"":s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])),
  async postJSON(url, body){
    const r = await fetch(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
    return {ok:r.ok, status:r.status, data: await r.json().catch(()=>({}))};
  },
  async getJSON(url){ const r=await fetch(url); return r.json(); }
};
