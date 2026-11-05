
(function(){
'use strict';
var feed = document.getElementById('feed');
if(!feed) return;

var API = '';
var currentTo = 'ALL';
var lastTs = 0;
var msgCount = 0;
var sessionStart = Date.now();
var lastSeen = {};
var state = { channels: {}, roster: [] };

function $(id){return document.getElementById(id);}
function pad(n){return String(n).padStart(2,'0');}
function nowTime(){var d=new Date(); return pad(d.getHours())+':'+pad(d.getMinutes())+':'+pad(d.getSeconds());}
function fmtSession(){
  var s=Math.floor((Date.now()-sessionStart)/1000);
  var m=Math.floor(s/60), h=Math.floor(m/60);
  return (h>0?h+'ч ':'')+(m%60)+'м '+(s%60)+'с';
}

function chanName(ch){
  var c = state.channels[ch];
  if(c && c.name) return c.name;
  return ch;
}

function renderChannels(){
  var cl = $('chanList');
  if(!cl) return;
  cl.innerHTML='';
  var keys = Object.keys(state.channels).sort();
  keys.forEach(function(L){
    var c = state.channels[L];
    var online = c.agent_alive || c.cdp_alive;
    var el = document.createElement('div');
    el.className = 'chan' + (online ? '' : ' off');
    var last = lastSeen[L] || 0;
    var ago = last ? Math.floor(Date.now()/1000 - last) + 'с' : '—';
    el.innerHTML = '<span class="led ' + (online?'on':'off') + '"></span>' +
                   '<span class="nm">' + (c.name || L) + '</span>' +
                   '<span class="v">' + ago + '</span>';
    cl.appendChild(el);
  });
}

function renderRoster(){
  var roster = $('roster');
  if(!roster) return;
  roster.innerHTML = '';
  var all = document.createElement('div');
  all.className = 'person all' + (currentTo==='ALL'?' active':'');
  all.dataset.to = 'ALL';
  all.innerHTML = '<span class="name">ВСЕ</span><span class="tag">broadcast</span>';
  all.addEventListener('click', function(){setTarget('ALL');});
  roster.appendChild(all);
  var keys = Object.keys(state.channels).sort();
  keys.forEach(function(L){
    var c = state.channels[L];
    var el = document.createElement('div');
    el.className = 'person from-' + L + (currentTo===L?' active':'');
    el.dataset.to = L;
    el.innerHTML = '<span class="name">' + (c.name||L) + '</span><span class="tag">' + L + '</span>';
    el.addEventListener('click', function(){setTarget(L);});
    roster.appendChild(el);
  });
  var op = document.createElement('div');
  op.className = 'person op';
  op.innerHTML = '<span class="name">Оператор</span><span class="tag">я</span>';
  roster.appendChild(op);
}

function renderMsg(m){
  var div = document.createElement('div');
  div.className = 'msg from-' + m.from;
  var who = m.from === 'operator' ? 'Оператор' : chanName(m.from);
  var to = (m.to==='ALL'||!m.to) ? '' : ' → ' + chanName(m.to);
  div.innerHTML = '<span class="time">[' + (m.time || nowTime()) + ']</span>' +
                  '<span class="who">' + who + ':</span>' +
                  '<span class="to">' + to + '</span>' +
                  '<span class="text"></span>';
  div.querySelector('.text').textContent = m.text;
  feed.appendChild(div);
}

function updateMetrics(){
  if($('mSession')) $('mSession').textContent = fmtSession();
  if($('mMsgs')) $('mMsgs').textContent = msgCount;
  if($('mTo')) $('mTo').textContent = currentTo === 'ALL' ? 'ВСЕ' : chanName(currentTo);
}

function setTarget(to){
  currentTo = to;
  document.querySelectorAll('.person').forEach(function(el){
    el.classList.toggle('active', el.dataset.to === to);
  });
  var badge = $('targetBadge');
  if(badge) badge.textContent = '→ ' + (to === 'ALL' ? 'ВСЕ' : chanName(to));
  updateMetrics();
}

async function poll(){
  try{
    var r = await fetch(API+'/api/messages', {cache:'no-store'});
    if(!r.ok) return;
    var msgs = await r.json();
    if(Array.isArray(msgs)) msgs = msgs;
    else msgs = msgs.messages || [];
    var added = false;
    msgs.forEach(function(m){
      if(m.ts > lastTs){
        renderMsg(m);
        lastTs = m.ts;
        msgCount++;
        added = true;
        if(m.from in lastSeen) lastSeen[m.from] = m.ts;
      }
    });
    if(added) feed.scrollTop = feed.scrollHeight;
    updateMetrics();
  }catch(e){}
}

async function send(){
  var inp = $('input');
  if(!inp) return;
  var text = inp.value.trim();
  if(!text) return;
  inp.value = '';
  try{
    await fetch(API+'/api/send', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({from:'operator', to:currentTo, text:text})
    });
    poll();
  }catch(e){}
}

async function refreshStatus(){
  try{
    var r = await fetch(API+'/api/status', {cache:'no-store'});
    if(!r.ok) return;
    var d = await r.json();
    if(d && d.channels){
      state.channels = d.channels;
      renderChannels();
      renderRoster();
      updateMetrics();
    }
  }catch(e){}
}

async function toggleMeeting(){
  try{
    var r = await fetch(API+'/api/meeting', {cache:'no-store'});
    var j = r.ok ? await r.json() : {on:false};
    await fetch(API+'/api/meeting', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({on: !j.on})
    });
  }catch(e){}
}

async function pauseAll(){
  try{ await fetch(API+'/api/pause_all', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({on:true})}); }catch(e){}
}
async function resumeAll(){
  try{ await fetch(API+'/api/pause_all', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({on:false})}); }catch(e){}
}
function clearView(){ feed.innerHTML=''; }

var recog = null, recogOn = false;

function initVoice(){
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  var btn = document.getElementById('btnVoice');
  if(!btn) return;
  if(!SR){
    btn.title = 'голосовой ввод не поддерживается';
    btn.style.opacity = '0.4';
    btn.disabled = true;
    return;
  }
  recog = new SR();
  recog.lang = 'ru-RU';
  recog.continuous = true;
  recog.interimResults = true;
  recog.onresult = function(e){
    var fin = '', inter = '';
    for (var i = e.resultIndex; i < e.results.length; i++){
      var t = e.results[i][0].transcript;
      if (e.results[i].isFinal) fin += t;
      else inter += t;
    }
    var inp = document.getElementById('input');
    if (fin && inp){
      inp.value = (inp.value ? inp.value + ' ' : '') + fin.trim();
    }
    var hint = document.getElementById('voiceHint');
    if (hint) hint.textContent = inter ? ('... ' + inter) : '';
  };
  recog.onend = function(){ if (recogOn){ try{ recog.start(); }catch(e){} } };
  recog.onerror = function(e){
    var hint = document.getElementById('voiceHint');
    if (hint) hint.textContent = 'voice: ' + (e.error||'?');
  };
  btn.addEventListener('click', function(){
    if (recogOn){
      recogOn = false;
      try{ recog.stop(); }catch(e){}
      btn.classList.remove('on');
      btn.style.color = '';
    } else {
      recogOn = true;
      try{ recog.start(); }catch(e){}
      btn.classList.add('on');
      btn.style.color = 'var(--amber, #ffb000)';
    }
  });
}

function init(){
  var send_btn = $('btnSend');
  var input = $('input');
  if(send_btn) send_btn.addEventListener('click', send);
  if(input){
    input.addEventListener('keydown', function(e){
      if(e.key === 'Enter' && !e.shiftKey){ e.preventDefault(); send(); }
    });
  }
  var bm = $('btnMeeting'); if(bm) bm.addEventListener('click', toggleMeeting);
  var bp = $('btnPauseAll'); if(bp) bp.addEventListener('click', pauseAll);
  var br = $('btnResumeAll'); if(br) br.addEventListener('click', resumeAll);
  var bc = $('btnClearView'); if(bc) bc.addEventListener('click', clearView);

  initVoice();
  refreshStatus();
  setTarget('ALL');
  poll();
  setInterval(refreshStatus, 5000);
  setInterval(poll, 1500);
  setInterval(updateMetrics, 1000);
}

if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
else init();
})();
