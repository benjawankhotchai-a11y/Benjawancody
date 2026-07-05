(function(){
  const form = document.getElementById("entryForm");
  const tid  = form.dataset.type;
  const msg  = document.getElementById("msg");

  // OK/NG toggle buttons
  form.querySelectorAll(".field[data-kind='okng']").forEach(fld=>{
    const hidden = fld.querySelector(".val");
    fld.querySelectorAll(".okng button").forEach(b=>{
      b.addEventListener("click",()=>{
        const on = b.classList.contains("on");
        fld.querySelectorAll(".okng button").forEach(x=>x.classList.remove("on"));
        if(!on){ b.classList.add("on"); hidden.value=b.dataset.v; }
        else hidden.value="";
      });
    });
  });

  function collect(){
    const data={};
    form.querySelectorAll(".field").forEach(fld=>{
      const key=fld.dataset.key;
      if(key==="datetime") return; // server sets time
      const inp=fld.querySelector(".val");
      if(inp && inp.value!=="") data[key]=inp.value;
    });
    return data;
  }

  function showMsg(kind, html){ msg.className="msg "+kind; msg.innerHTML=html; window.scrollTo({top:0,behavior:"smooth"}); }

  form.addEventListener("submit", async e=>{
    e.preventDefault();
    const btn=document.getElementById("saveBtn");
    btn.disabled=true; btn.textContent="กำลังบันทึก...";
    const res = await FL.postJSON("/api/inspections",{type:tid,data:collect()});
    btn.disabled=false; btn.textContent="💾 บันทึกผลตรวจ";
    if(res.ok && res.data.ok){
      showMsg("ok","✅ บันทึกสำเร็จ (เลขที่ #"+res.data.id+") — ฟอร์มถูกล้างพร้อมกรอกงานถัดไป");
      document.getElementById("lastSaved").textContent="#"+res.data.id+" · "+new Date().toLocaleTimeString("th-TH");
      form.reset();
      form.querySelectorAll(".okng button").forEach(x=>x.classList.remove("on"));
      form.querySelectorAll(".field[data-kind='okng'] .val").forEach(v=>v.value="");
    } else {
      const errs=(res.data.errors||["เกิดข้อผิดพลาด กรุณาลองใหม่"]);
      showMsg("err","<b>ไม่สามารถบันทึกได้:</b><br>• "+errs.map(FL.esc).join("<br>• "));
    }
  });

  form.addEventListener("reset", ()=>{
    setTimeout(()=>{
      form.querySelectorAll(".okng button").forEach(x=>x.classList.remove("on"));
      form.querySelectorAll(".field[data-kind='okng'] .val").forEach(v=>v.value="");
    },0);
  });
})();
