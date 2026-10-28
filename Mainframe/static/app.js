
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
      if(st && d.channels){
        var html = '<table style="width:100%; border-collapse: collapse; text-align: left; font-family: monospace;">';
        html += '<tr style="border-bottom: 1px solid #0f0;"><th>CH</th><th>NAME</th><th>AGENT</th><th>CDP</th></tr>';
        for (var L in d.channels) {
            var c = d.channels[L];
            var ag = c.agent_alive ? '<span style="color:#0f0">ON</span>' : '<span style="color:#f00">OFF</span>';
            var cd = c.cdp_alive ? '<span style="color:#0f0">ON</span>' : '<span style="color:#f00">OFF</span>';
            html += '<tr><td>'+L+'</td><td>'+c.name+'</td><td>'+c.agent_port+' ('+ag+')</td><td>'+c.cdp+' ('+cd+')</td></tr>';
        }
        html += '</table>';
        st.innerHTML = html;
      }
    }).catch(e=>{});
  }
  setInterval(refreshStatus,3000); refreshStatus();

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
