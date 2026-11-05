
(function(){
'use strict';
var persList = document.getElementById('persList');
if(!persList) return;

var curCh = null;
var lastTsByCh = {};
var state = { channels: {} };

function $(id){return document.getElementById(id);}

async function refreshStatus(){
  try{
    var r = await fetch('/api/status', {cache:'no-store'});
    if(!r.ok) return;
    var d = await r.json();
    if(d && d.channels){
      state.channels = d.channels;
      renderList();
    }
  }catch(e){}
}

function renderList(){
  persList.innerHTML='';
  var keys = Object.keys(state.channels).sort();
  if(!keys.length){
    persList.innerHTML = '<div class="dim">нет каналов</div>';
    return;
  }
  keys.forEach(function(L){
    var c = state.channels[L];
    var el = document.createElement('div');
    el.className = 'pers-item' + (curCh === L ? ' active' : '');
    el.dataset.ch = L;
    el.textContent = (c.name || L);
    var online = c.agent_alive || c.cdp_alive;
    el.style.opacity = online ? '1' : '0.5';
    el.addEventListener('click', function(){ select(L); });
    persList.appendChild(el);
  });
}

function select(L){
  curCh = L;
  if(!(L in lastTsByCh)) lastTsByCh[L] = 0;
  document.querySelectorAll('.pers-item').forEach(function(el){
    el.classList.toggle('active', el.dataset.ch === L);
  });
  var title = $('persTitle');
  if(title) title.textContent = (state.channels[L] && state.channels[L].name) || L;
  var feed = $('persFeed');
  if(feed) feed.innerHTML = '';
  poll();
}

async function poll(){
  if(!curCh) return;
  var ch = curCh;
  try{
    var r = await fetch('/api/chat/' + ch, {cache:'no-store'});
    if(!r.ok) return;
    var d = await r.json();
    if(ch !== curCh) return;
    var msgs = d.messages || [];
    var feed = $('persFeed');
    if(!feed) return;
    var lastTs = lastTsByCh[ch] || 0;
    var added = false;
    msgs.forEach(function(m){
      if(m.ts <= lastTs) return;
      lastTsByCh[ch] = m.ts;
      var div = document.createElement('div');
      div.className = 'pers-msg ' + (m.from === 'operator' ? 'from-operator' : 'from-agent');
      var h = document.createElement('span');
      h.className = 'pers-h';
      h.textContent = (m.from === 'operator' ? 'Вы' : (state.channels[ch] && state.channels[ch].name) || m.from) + ': ';
      div.appendChild(h);
      var t = document.createElement('span');
      t.className = 'pers-text';
      t.textContent = m.text;
      div.appendChild(t);
      feed.appendChild(div);
      added = true;
    });
    if(added) feed.scrollTop = feed.scrollHeight;
  }catch(e){}
}

async function send(){
  if(!curCh) return;
  var inp = $('persInput');
  if(!inp) return;
  var text = inp.value.trim();
  if(!text) return;
  inp.value = '';
  try{
    await fetch('/api/chat/' + curCh, {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({from:'operator', text:text})
    });
    poll();
  }catch(e){}
}

function init(){
  var btn = $('persSend');
  if(btn) btn.addEventListener('click', send);
  var inp = $('persInput');
  if(inp){
    inp.addEventListener('keydown', function(e){
      if(e.key === 'Enter' && !e.shiftKey){ e.preventDefault(); send(); }
    });
  }
  refreshStatus();
  setInterval(refreshStatus, 10000);
  setInterval(poll, 3000);
}

if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
else init();
})();
