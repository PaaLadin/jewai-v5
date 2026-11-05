
(function(){
'use strict';
var canvas = document.getElementById('mnemo-fx');
var wrap = document.getElementById('mnemo-wrap');
var blocksContainer = document.getElementById('mnemo-blocks');
if(!canvas||!wrap||!blocksContainer) return;
var ctx = canvas.getContext('2d');
var GRID = 10;
var AW=308, AH=154, CW=262, CH=140, RW=210, RH=80, MW=560, MH=240;
var HG=42, VG=40;
var COLORS = {'A':'#33ff33','B':'#33d6ff','C':'#c573ff','D':'#ffb000','E':'#4ecdc4','F':'#f7b731','J':'#ff6688','H':'#66aaff','K':'#cc66ff','L':'#66ffcc'};
var BLOCKS = {};
var agentOrder = [];
var particles = [];
var lastCounts = {};
var BASE_W = 1400, BASE_H = 700;
var canvasScale = 1.0;
var obstacleMap = new Uint8Array(0);

function plan(_N){
  var b = {}, EDGE = 30, i;
  var SLOT = ['A','B','C','D','E','F','J','H','K','L'];
  for (i=0; i<5; i++) b['slot-'+SLOT[i]] = {x:EDGE + i*(AW+HG), y:EDGE, w:AW, h:AH};
  var blockH = Math.max(MH, 2*CH+20, 4*RH+3*20);
  var centerY = EDGE + AH + 60 + blockH/2;
  var mfY = centerY - MH/2;
  b.mainframe = {x:EDGE, y:mfY, w:MW, h:MH};
  var ctrl = ['rebirth','mailbot','llm','proxy'];
  var cx0 = EDGE + MW + 40;
  var cy0 = centerY - (2*CH+20)/2;
  for (i=0; i<4; i++) {
    var col = i%2, row = (i/2)|0;
    b[ctrl[i]] = {x:cx0 + col*(CW+20), y:cy0 + row*(CH+20), w:CW, h:CH};
  }
  var res = ['sandbox','projects','rag','profiles'];
  var rtotal = 4*RH + 3*20;
  var rx = cx0 + 2*CW + 60;
  var ry = centerY - rtotal/2;
  for (i=0; i<4; i++) b[res[i]] = {x:rx, y:ry + i*(RH+20), w:RW, h:RH};
  var by = mfY + MH + 80;
  for (i=0; i<5; i++) b['slot-'+SLOT[5+i]] = {x:EDGE + i*(AW+HG), y:by, w:AW, h:AH};
  var minX=Infinity, minY=Infinity, maxX=-Infinity, maxY=-Infinity, id, bb;
  for (id in b) { bb=b[id]; if(bb.x<minX)minX=bb.x; if(bb.y<minY)minY=bb.y; if(bb.x+bb.w>maxX)maxX=bb.x+bb.w; if(bb.y+bb.h>maxY)maxY=bb.y+bb.h; }
  for (id in b) { b[id].x -= minX - EDGE; b[id].y -= minY - EDGE; }
  BASE_W = (maxX - minX) + 2*EDGE;
  BASE_H = (maxY - minY) + 2*EDGE;
  return b;
}

function build(id, b, def){
  var el = document.createElement('div');
  el.className = 'mnemo-block ' + def.type;
  el.id = 'mnemo-'+id;
  el.style.left = b.x+'px'; el.style.top = b.y+'px';
  el.style.width = b.w+'px'; el.style.height = b.h+'px';
  if(def.color) el.style.color = def.color;
  if(def.type==='agent'){
    el.innerHTML =
      '<div class="mnemo-agent-letter">' + def.letter + '</div>' +
      '<div class="mnemo-agent-name">' + def.name + '</div>' +
      '<div class="mnemo-agent-status"><div class="mnemo-agent-status-dot"></div><span>ONLINE</span></div>' +
      '<div class="mnemo-agent-port">port ' + (def.port||'\u2014') + '</div>' +
      '<div class="mnemo-agent-lamps">' +
        '<div class="mnemo-lamp-row"><div class="mnemo-lamp-dot" data-lamp="agent"></div><span>AGENT</span></div>' +
        '<div class="mnemo-lamp-row"><div class="mnemo-lamp-dot" data-lamp="bridge"></div><span>BRIDGE</span></div>' +
        '<div class="mnemo-lamp-row"><div class="mnemo-lamp-dot" data-lamp="chrome"></div><span>CHROME</span></div>' +
      '</div>' +
      '<div class="mnemo-agent-reboot">' +
        '<button class="mnemo-btn" data-act="reboot-agent" data-target="' + def.letter + '">\u21bba</button>' +
        '<button class="mnemo-btn" data-act="reboot-bridge" data-target="' + def.letter + '">\u21bbb</button>' +
        '<button class="mnemo-btn" data-act="reboot-chrome" data-target="' + def.letter + '">\u21bbc</button>' +
      '</div>' +
      '<div class="mnemo-agent-mainbtns">' +
        '<button class="mnemo-btn" data-act="boot" data-target="agent:' + def.letter + '">\u25b6</button>' +
        '<button class="mnemo-btn" data-act="stop" data-target="agent:' + def.letter + '">\u25a0</button>' +
        '<button class="mnemo-btn" data-act="restart" data-target="agent:' + def.letter + '">\u21bb</button>' +
      '</div>';
  } else if(def.type==='mainframe' || def.type==='control'){
    el.innerHTML =
      '<div class="mnemo-title">' + def.label + '</div>' +
      '<div class="mnemo-info" data-info="1">\u2026</div>' +
      '<div class="mnemo-btns">' +
        '<button class="mnemo-btn" data-act="boot" data-target="' + id + '">\u25b6</button>' +
        '<button class="mnemo-btn" data-act="stop" data-target="' + id + '">\u25a0</button>' +
        '<button class="mnemo-btn" data-act="restart" data-target="' + id + '">\u21bb</button>' +
      '</div>';
  } else {
    el.innerHTML =
      '<div class="mnemo-title">' + (def.icon||'') + ' ' + def.label + '</div>' +
      '<div class="mnemo-info" data-info="1">\u2014</div>';
  }
  blocksContainer.appendChild(el);
  return el;
}

function buildPlaceholder(slotId, b){
  var el = document.createElement('div');
  el.className = 'mnemo-block mnemo-placeholder';
  el.id = 'mnemo-' + slotId;
  el.style.left = b.x + 'px'; el.style.top = b.y + 'px';
  el.style.width = b.w + 'px'; el.style.height = b.h + 'px';
  el.innerHTML = '<div class="mnemo-ph-label">SLOT ' + slotId.replace('slot-','') + '</div>';
  blocksContainer.appendChild(el);
  return el;
}

function buildMap(){
  var gw = Math.ceil(BASE_W/GRID), gh = Math.ceil(BASE_H/GRID);
  obstacleMap = new Uint8Array(gw*gh);
  var PAD = 2;
  for(var id in BLOCKS){
    var b = BLOCKS[id];
    if(b.type==='resource') continue;
    var x0 = Math.max(0, Math.floor(b.x/GRID)-PAD);
    var y0 = Math.max(0, Math.floor(b.y/GRID)-PAD);
    var x1 = Math.min(gw-1, Math.ceil((b.x+b.w)/GRID)+PAD);
    var y1 = Math.min(gh-1, Math.ceil((b.y+b.h)/GRID)+PAD);
    for(var y=y0;y<=y1;y++) for(var x=x0;x<=x1;x++) obstacleMap[y*gw+x] = 1;
  }
}

function nearest(gx, gy){
  var gw = Math.ceil(BASE_W/GRID), gh = Math.ceil(BASE_H/GRID);
  gx = Math.max(0, Math.min(gw-1, gx));
  gy = Math.max(0, Math.min(gh-1, gy));
  if(obstacleMap[gy*gw+gx]===0) return {gx:gx,gy:gy};
  for(var r=1;r<50;r++){
    for(var dy=-r;dy<=r;dy++) for(var dx=-r;dx<=r;dx++){
      if(Math.abs(dx)!==r && Math.abs(dy)!==r) continue;
      var nx=gx+dx, ny=gy+dy;
      if(nx<0||ny<0||nx>=gw||ny>=gh) continue;
      if(obstacleMap[ny*gw+nx]===0) return {gx:nx,gy:ny};
    }
  }
  return {gx:gx,gy:gy};
}

function aStar(s, g){
  var gw = Math.ceil(BASE_W/GRID), gh = Math.ceil(BASE_H/GRID);
  var ss = nearest(s.gx,s.gy), gg = nearest(g.gx,g.gy);
  var sK=ss.gy*gw+ss.gx, gK=gg.gy*gw+gg.gx;
  if(sK===gK) return [ss];
  var open=new Set([sK]), gs=new Map([[sK,0]]);
  var fs=new Map([[sK, Math.abs(ss.gx-gg.gx)+Math.abs(ss.gy-gg.gy)]]);
  var came=new Map(), closed=new Set();
  while(open.size>0){
    var cK=null, cF=Infinity;
    open.forEach(function(k){var f=fs.get(k)||Infinity; if(f<cF){cF=f;cK=k;}});
    if(cK===null) break;
    if(cK===gK){
      var path=[]; var cur=cK;
      while(cur!==undefined){path.unshift({gx:cur%gw,gy:Math.floor(cur/gw)}); cur=came.get(cur);}
      return path;
    }
    open.delete(cK); closed.add(cK);
    var cx=cK%gw, cy=Math.floor(cK/gw);
    var dirs=[[1,0],[-1,0],[0,1],[0,-1]];
    for(var di=0;di<4;di++){
      var nx=cx+dirs[di][0], ny=cy+dirs[di][1];
      if(nx<0||ny<0||nx>=gw||ny>=gh) continue;
      var nK=ny*gw+nx;
      if(closed.has(nK)||obstacleMap[nK]===1) continue;
      var tg=(gs.get(cK)||0)+1;
      if(tg<(gs.get(nK)||Infinity)){
        came.set(nK,cK); gs.set(nK,tg);
        fs.set(nK, tg+Math.abs(nx-gg.gx)+Math.abs(ny-gg.gy));
        open.add(nK);
      }
    }
  }
  return null;
}

function simplify(p){
  if(!p||p.length<3) return p||[];
  var out=[p[0]];
  for(var i=1;i<p.length-1;i++){
    var a=p[i-1], b=p[i], c=p[i+1];
    if((b.gx-a.gx)!==(c.gx-b.gx) || (b.gy-a.gy)!==(c.gy-b.gy)) out.push(b);
  }
  out.push(p[p.length-1]);
  return out;
}

var pathCache = {};
function getPath(f, t){
  var key = f+'>'+t;
  if(pathCache[key]) return pathCache[key];
  var fb=BLOCKS[f], tb=BLOCKS[t];
  if(!fb||!tb) return null;
  var s={gx:Math.floor((fb.x+fb.w/2)/GRID), gy:Math.floor((fb.y+fb.h/2)/GRID)};
  var g={gx:Math.floor((tb.x+tb.w/2)/GRID), gy:Math.floor((tb.y+tb.h/2)/GRID)};
  var raw = aStar(s,g);
  if(!raw) return null;
  var px = simplify(raw).map(function(p){return {x:p.gx*GRID+GRID/2, y:p.gy*GRID+GRID/2};});
  pathCache[key] = px;
  return px;
}

function dist(a,b){return Math.hypot(b.x-a.x, b.y-a.y);}

function startPulse(f, t){
  var path = getPath(f, t);
  if(!path||path.length<2) return;
  var color = (BLOCKS[f] && BLOCKS[f].color) || '#33ff33';
  var total = 0;
  for(var i=1;i<path.length;i++) total += dist(path[i-1], path[i]);
  var src = document.getElementById('mnemo-'+f);
  if(src){src.classList.remove('flashing'); src.classList.add('source-active');}
  particles.push({path:path, color:color, f:f, t:t, total:total, prog:0, dur:Math.max(0.4,total/500), trail:[], fading:false, alpha:1});
}

function targetFor(e){
  if(!e) return 'mainframe';
  var op=(e.op||'').toLowerCase();
  var p=((e.path||'')+' '+((e.result&&e.result.path)||'')).toLowerCase();
  if(op==='read'||op==='list'||op==='hash'){
    if(p.indexOf('rag')>=0) return 'rag';
    if(p.indexOf('profile')>=0) return 'profiles';
    if(p.indexOf('project')>=0) return 'projects';
    return 'rag';
  }
  if(op==='write'||op==='mkdir'||op==='delete'){
    if(p.indexOf('project')>=0) return 'projects';
    return 'sandbox';
  }
  if(op==='run') return 'sandbox';
  return 'mainframe';
}

function pollTel(){
  fetch('/api/telemetry',{cache:'no-store'}).then(function(r){return r.ok?r.json():null;}).then(function(d){
    if(!d||!d.channels) return;
    for(var L in d.channels){
      var t=d.channels[L], cur=t.count||0, prev=lastCounts[L]||0;
      if(cur>prev && t.last) startPulse('agent-'+L, targetFor(t.last));
      lastCounts[L]=cur;
    }
  }).catch(function(){});
}

function pollSt(){
  fetch('/api/status',{cache:'no-store'}).then(function(r){return r.ok?r.json():null;}).then(function(d){
    if(!d||!d.channels) return;
    for(var L in d.channels){
      var ch=d.channels[L];
      var el=document.getElementById('mnemo-agent-'+L);
      if(!el) continue;
      var set=function(name,on){var dot=el.querySelector('[data-lamp="'+name+'"]'); if(dot) dot.classList.toggle('off',!on);};
      set('agent', ch.agent_alive);
      set('chrome', ch.cdp_alive);
      set('bridge', ch.agent_alive && ch.cdp_alive);
    }
    var mf=document.querySelector('#mnemo-mainframe [data-info="1"]');
    if(mf) mf.textContent = Object.keys(d.channels).length ? '● ONLINE' : '○ OFFLINE';
  }).catch(function(){});
}

var lastT = performance.now();
function render(t){
  var dt = Math.min(0.05,(t-lastT)/1000); lastT = t;
  ctx.clearRect(0,0,BASE_W,BASE_H);
  for(var i=particles.length-1;i>=0;i--){
    var p=particles[i];
    if(!p.fading){
      p.prog += dt/p.dur;
      if(p.prog>=1){
        p.prog=1; p.fading=true;
        var s1=document.getElementById('mnemo-'+p.f);
        if(s1){s1.classList.remove('source-active'); s1.classList.add('flashing'); setTimeout(function(){s1.classList.remove('flashing');},2000);}
        var s2=document.getElementById('mnemo-'+p.t);
        if(s2){s2.classList.add('flashing'); setTimeout(function(){s2.classList.remove('flashing');},2000);}
      }
    } else {
      p.alpha -= dt/0.4;
      if(p.alpha<=0){particles.splice(i,1); continue;}
    }
    var cx=p.path[0].x, cy=p.path[0].y;
    if(p.prog>0 && p.prog<=1){
      var trav = p.prog*p.total;
      for(var j=1;j<p.path.length;j++){
        var seg = dist(p.path[j-1], p.path[j]);
        if(trav<=seg){
          var r = trav/seg;
          cx = p.path[j-1].x + (p.path[j].x - p.path[j-1].x)*r;
          cy = p.path[j-1].y + (p.path[j].y - p.path[j-1].y)*r;
          break;
        }
        trav -= seg;
      }
    }
    if(!p.fading){p.trail.push({x:cx,y:cy,age:0}); if(p.trail.length>30) p.trail.shift();}
    if(p.trail.length>1){
      ctx.beginPath(); ctx.moveTo(p.trail[0].x, p.trail[0].y);
      for(var k=1;k<p.trail.length;k++) ctx.lineTo(p.trail[k].x, p.trail[k].y);
      ctx.strokeStyle = p.color;
      ctx.globalAlpha = p.fading ? 0.2*p.alpha : 0.2;
      ctx.lineWidth = 4; ctx.stroke();
      ctx.globalAlpha = 1;
    }
    for(var ii=0;ii<p.trail.length;ii++) p.trail[ii].age += dt;
    p.trail = p.trail.filter(function(tt){return tt.age<0.5;});
    if(!p.fading){
      for(var kk=0;kk<p.trail.length;kk++){
        var tt=p.trail[kk];
        var a=Math.max(0,1-tt.age/0.5)*(kk/p.trail.length);
        if(a<=0) continue;
        ctx.beginPath(); ctx.arc(tt.x,tt.y,2+(kk/p.trail.length)*4,0,Math.PI*2);
        ctx.fillStyle = p.color; ctx.globalAlpha = a; ctx.fill();
      }
      ctx.globalAlpha = 1;
      ctx.beginPath(); ctx.arc(cx,cy,6,0,Math.PI*2);
      ctx.fillStyle = '#fff'; ctx.shadowColor = p.color; ctx.shadowBlur = 20; ctx.fill();
      ctx.shadowBlur = 0;
    }
  }
  requestAnimationFrame(render);
}

function fit(){
  var vw=wrap.clientWidth, vh=wrap.clientHeight;
  if(vw<100||vh<100) return;
  var sx=(vw-20)/BASE_W, sy=(vh-20)/BASE_H;
  canvasScale = Math.min(sx, sy, 3.0);
  canvas.width = BASE_W; canvas.height = BASE_H;
  canvas.style.width = (BASE_W*canvasScale)+'px';
  canvas.style.height = (BASE_H*canvasScale)+'px';
  blocksContainer.style.transform = 'scale('+canvasScale+')';
  blocksContainer.style.transformOrigin = 'top left';
  blocksContainer.style.width = BASE_W+'px';
  blocksContainer.style.height = BASE_H+'px';
}
window.addEventListener('resize', fit);

document.addEventListener('click', function(e){
  var btn = e.target.closest('.mnemo-btn');
  if(!btn) return;
  e.preventDefault();
  var act = btn.dataset.act, target = btn.dataset.target;
  var ep = act==='boot'?'/api/boot':act==='stop'?'/api/stop':act==='restart'?'/api/restart':null;
  if(!ep) return;
  fetch(ep, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({target:target})}).catch(function(){});
});

function init(){
  fetch('/api/status',{cache:'no-store'}).then(function(r){return r.json();}).then(function(st){
    return fetch('/api/telemetry',{cache:'no-store'}).then(function(r){return r.json();}).catch(function(){return {channels:{}};}).then(function(tel){
      agentOrder = Object.keys(st.channels||{}).sort();
      if(!agentOrder.length) return;
      var layout = plan(agentOrder.length);
      var sdefs = {
        mainframe:{type:'mainframe',label:'MAINFRAME'},
        rebirth:{type:'control',label:'REBIRTH'},
        mailbot:{type:'control',label:'MAILBOT'},
        llm:{type:'control',label:'LLM'},
        proxy:{type:'control',label:'PROXY'},
        sandbox:{type:'resource',label:'SANDBOX',icon:'⚗'},
        projects:{type:'resource',label:'PROJECTS',icon:'▣'},
        rag:{type:'resource',label:'RAG',icon:'≡'},
        profiles:{type:'resource',label:'PROFILES',icon:'◯'}
      };
      var activeSet = {};
      agentOrder.forEach(function(L){ activeSet[L] = true; });
      for(var rawId in layout){
        var b = layout[rawId], def, realId = rawId;
        if(rawId.indexOf('slot-')===0){
          var SL = rawId.replace('slot-','');
          if(activeSet[SL]){
            var ch = st.channels[SL]||{};
            def = {type:'agent', letter:SL, name:ch.name||SL, color:COLORS[SL]||'#33ff33', port:ch.agent_port||ch.agent||''};
            realId = 'agent-' + SL;
          } else {
            continue; // placeholder handled later
          }
        } else {
          def = sdefs[rawId];
        }
        if(!def) continue;
        build(realId, b, def);
        BLOCKS[realId] = {x:b.x, y:b.y, w:b.w, h:b.h, type:def.type, color:def.color, letter:def.letter, label:def.label};
        if(realId.indexOf('agent-')===0){
          var L = realId.replace('agent-','');
          lastCounts[L] = (tel.channels[L] && tel.channels[L].count) || 0;
        }
      }
      // Placeholders for all 10 slots; active agents overlay them
      var SLOT_LETTERS = ['A','B','C','D','E','F','J','H','K','L'];
      var activeSet = {};
      agentOrder.forEach(function(L){ activeSet[L] = true; });
      for (var si=0; si<SLOT_LETTERS.length; si++){
        var SL = SLOT_LETTERS[si];
        if (activeSet[SL]) continue;
        var slotId = 'slot-' + SL;
        var slotB = layout[slotId];
        if (!slotB) continue;
        buildPlaceholder(slotId, slotB);
      }

      buildMap();
      fit();
      setTimeout(fit, 150);
      setTimeout(fit, 500);
      pollSt();
      setInterval(pollTel, 2000);
      setInterval(pollSt, 5000);
      requestAnimationFrame(render);
    });
  });
}

window.__mnemo = { particles: particles, BLOCKS: BLOCKS, agentOrder: agentOrder };
init();
})();
