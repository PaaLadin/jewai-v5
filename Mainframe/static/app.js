(function(){
  function $(id){return document.getElementById(id);}
  function clock(){
    var d=new Date();
    var h=('0'+d.getHours()).slice(-2), m=('0'+d.getMinutes()).slice(-2), s=('0'+d.getSeconds()).slice(-2);
    if($('clock')) $('clock').textContent=h+':'+m+':'+s;
  }
  setInterval(clock,1000); clock();

  function refreshStatus(){
    fetch('/api/status').then(r=>r.json()).then(d=>{
      if(!d.ok) return;
      var st=$('lpState');
      if(st){
        var html='';
        var s=d.services||d;
        if(s.agents){ html+='<div>AGENTS: '+JSON.stringify(s.agents)+'</div>'; }
        else { html+='<pre>'+JSON.stringify(d,null,2)+'</pre>'; }
        st.innerHTML=html;
      }
    }).catch(e=>{});
  }
  setInterval(refreshStatus,3000); refreshStatus();

  // Tabs
  var tabs=document.querySelectorAll('.tab');
  tabs.forEach(function(t){
    t.addEventListener('click',function(){
      tabs.forEach(x=>x.classList.remove('active'));
      document.querySelectorAll('.screen').forEach(x=>x.classList.remove('active'));
      t.classList.add('active');
      var s=$('screen-'+t.dataset.tab);
      if(s) s.classList.add('active');
    });
  });
})();