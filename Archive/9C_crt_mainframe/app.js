'use strict';
const API = '';
const state = { channels: {}, activeLog: 'chat', chatCh: 'A' };

function $(id) { return document.getElementById(id); }
function el(tag, cls, txt) { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; }

async function jget(p) {
  const r = await fetch(API + p, { cache: 'no-store' });
  if (!r.ok) throw new Error('HTTP ' + r.status + ' ' + p);
  return r.json();
}
async function jpost(p, b) {
  const r = await fetch(API + p, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(b || {})
  });
  if (!r.ok) throw new Error('HTTP ' + r.status + ' ' + p);
  return r.json();
}

function log(msg) { const s = $('log-strip'); if (s) s.textContent = new Date().toLocaleTimeString() + '  ' + msg; }

function tickClock() {
  const c = $('clock');
  if (c) c.textContent = new Date().toLocaleTimeString('ru-RU');
}

function lamp(v) {
  if (v === true) return 'led on';
  if (v === false) return 'led err';
  if (v === 'warn') return 'led warn';
  return 'led unk';
}

function setupTabs() {
  document.querySelectorAll('.tab').forEach(function(t) {
    t.addEventListener('click', function() {
      const n = t.dataset.tab;
      document.querySelectorAll('.tab').forEach(function(x) { x.classList.toggle('active', x === t); });
      document.querySelectorAll('.tab-body').forEach(function(x) { x.classList.toggle('active', x.id === 'tab-' + n); });
      if (n === 'chat') loadChat();
      else if (n === 'projects') loadProjects();
      else if (n === 'logs') loadLog(state.activeLog);
      else if (n === 'roadmap') loadRoadmap();
    });
  });
}async function refreshStatus() {
  try {
    const j = await jget('/api/status');
    state.channels = j.channels || {};
    const m = $('bulk-meta');
    if (m) m.textContent = 'v' + (j.version || '?') + '  |  каналов: ' + Object.keys(state.channels).length;
    const ns = $('netstat');
    if (ns) ns.textContent = 'СЕТЬ: ' + (Object.keys(state.channels).length ? 'OK' : '---');
    renderAgents();
    populateChatChannels();
  } catch (e) { log('status: ' + e.message); }
}

function renderAgents() {
  const grid = $('agents-grid'); if (!grid) return;
  grid.innerHTML = '';
  const keys = Object.keys(state.channels).sort();
  if (!keys.length) { grid.appendChild(el('div', 'dim', 'нет каналов')); return; }
  keys.forEach(function(L) {
    const c = state.channels[L] || {};
    const card = el('div', 'card');
    const h = el('div', 'card-h');
    h.appendChild(el('b', null, L));
    h.appendChild(el('span', null, (c.name || '?') + '  //  ' + (c.model || '?') + '  //  ' + (c.prefix || '?')));
    card.appendChild(h);

    const leds = el('div', 'leds');
    [['AG', c.agent_alive], ['CH', c.cdp_alive], ['WD', c.watchdog], ['RC', c.recovery]].forEach(function(p) {
      const s = el('span', 'row');
      s.appendChild(document.createTextNode(p[0]));
      s.appendChild(el('span', lamp(p[1])));
      leds.appendChild(s);
    });
    card.appendChild(leds);

    card.appendChild(el('div', 'dim', 'agent:' + (c.agent_port || '?') + '  cdp:' + (c.cdp_port || '?') + '  lastId:' + (c.lastId || '-')));
    card.appendChild(el('div', 'dim', 'cmds: ' + (c.cmds_from_start != null ? c.cmds_from_start : '-')));    const auth = c.auth_status || 'unknown';
    const ab = el('div', 'auth ' + (auth === 'logged_in' ? 'ok' : 'bad'));
    ab.appendChild(document.createTextNode(auth === 'logged_in' ? 'ЗАЛОГИНЕН' : (auth === 'needs_login' ? 'ТРЕБУЕТСЯ ЛОГИН' : (auth === 'no_chrome' ? 'CHROME МЁРТВ' : 'СТАТУС ?'))));
    if (auth !== 'logged_in') {
      const btn = el('button', null, 'LOGIN');
      btn.addEventListener('click', function() { window.open(c.chat_url || 'https://chat.deepseek.com/', '_blank'); });
      ab.appendChild(btn);
    }
    card.appendChild(ab);

    const btns = el('div', 'btns');
    const b1 = el('button', null, 'PAUSE');
    b1.addEventListener('click', function() { doPause(L, true); });
    const b2 = el('button', null, 'RESUME');
    b2.addEventListener('click', function() { doPause(L, false); });
    const b3 = el('button', null, 'REBOOT');
    b3.addEventListener('click', function() { doRestart('chrome:' + L); });
    btns.appendChild(b1); btns.appendChild(b2); btns.appendChild(b3);
    card.appendChild(btns);
    grid.appendChild(card);
  });
}

async function doPause(L, on) {
  try { await jpost('/api/pause', { channel: L, on: on }); log('pause ' + L + ' ' + (on ? 'ON' : 'OFF')); refreshStatus(); }
  catch (e) { log('pause err: ' + e.message); }
}
async function doRestart(t) {
  try { await jpost('/api/restart', { target: t }); log('restart ' + t); refreshStatus(); }
  catch (e) { log('restart err: ' + e.message); }
}
async function bulkPause() {
  const ks = Object.keys(state.channels);
  for (let i = 0; i < ks.length; i++) { try { await jpost('/api/pause', { channel: ks[i], on: true }); } catch (e) {} }
  log('PAUSE ALL'); refreshStatus();
}
async function bulkResume() {
  const ks = Object.keys(state.channels);
  for (let i = 0; i < ks.length; i++) { try { await jpost('/api/pause', { channel: ks[i], on: false }); } catch (e) {} }
  log('RESUME ALL'); refreshStatus();
}
async function selftest() { try { await jpost('/api/diagnose', {}); log('SELF-TEST done'); } catch (e) { log('diag err: ' + e.message); } }async function populateChatChannels() {
  const sel = $('chat-ch'); if (!sel) return;
  const ks = Object.keys(state.channels).sort();
  const cur = sel.value || 'A';
  sel.innerHTML = '';
  ks.forEach(function(L) { const o = el('option', null, L); o.value = L; sel.appendChild(o); });
  if (ks.indexOf(cur) >= 0) sel.value = cur;
  if (!ks.length) { const o = el('option', null, '--'); sel.appendChild(o); }
}

async function loadChat() {
  try {
    const sel = $('chat-ch'); const L = (sel && sel.value) || 'A';
    const j = await jget('/api/messages');
    const feed = $('chat-feed'); if (!feed) return;
    feed.innerHTML = '';
    const msgs = j.messages || [];
    if (!msgs.length) { feed.appendChild(el('div', 'dim', 'нет сообщений')); return; }
    msgs.slice(-100).forEach(function(m) {
      const d = el('div', 'msg');
      const b = el('b', null, (m.from || '?'));
      d.appendChild(b);
      d.appendChild(document.createTextNode(' → '));
      const t = el('span', 'to', (m.to || 'ALL'));
      d.appendChild(t);
      d.appendChild(document.createTextNode(': ' + (m.text || '')));
      const tm = el('span', 't', (m.time || ''));
      d.appendChild(tm);
      feed.appendChild(d);
    });
    feed.scrollTop = feed.scrollHeight;
  } catch (e) { log('chat: ' + e.message); }
}

async function sendChat() {
  const txt = ($('chat-text') || {}).value || '';
  if (!txt.trim()) return;
  try {
    await jpost('/api/send', { from: 'operator', to: 'ALL', text: txt });
    $('chat-text').value = '';
    log('sent');
    loadChat();
  } catch (e) { log('send err: ' + e.message); }
}async function loadProjects() {
  try {
    const j = await jget('/api/projects');
    const wrap = $('projects-list'); if (!wrap) return;
    wrap.innerHTML = '';
    const ps = j.projects || [];
    if (!ps.length) { wrap.appendChild(el('div', 'dim', 'нет проектов')); return; }
    ps.forEach(function(p) {
      const row = el('div', 'row');
      const a = el('a', null, p.name); a.href = p.url || ('/roadmap/' + p.name); a.target = '_blank';
      row.appendChild(a);
      const m = el('span', 'm', 'mtime ' + new Date((p.mtime || 0) * 1000).toLocaleString('ru-RU') + '  size ' + (p.size || 0) + 'b');
      row.appendChild(m);
      wrap.appendChild(row);
    });
  } catch (e) { log('projects: ' + e.message); }
}

async function loadLog(name) {
  try {
    state.activeLog = name;
    document.querySelectorAll('.log-tab').forEach(function(x) { x.classList.toggle('active', x.dataset.log === name); });
    const j = await jget('/api/logs?name=' + encodeURIComponent(name));
    const body = $('log-body'); if (!body) return;
    body.textContent = j.content || '(empty)';
  } catch (e) { log('log: ' + e.message); }
}

function setupLogTabs() {
  document.querySelectorAll('.log-tab').forEach(function(t) {
    t.addEventListener('click', function() { loadLog(t.dataset.log); });
  });
}async function loadRoadmap() {
  try {
    const j = await jget('/api/projects');
    const sel = $('rm-name'); if (!sel) return;
    sel.innerHTML = '';
    const ps = j.projects || [];
    ps.forEach(function(p) { const o = el('option', null, p.name); o.value = p.name; sel.appendChild(o); });
    if (!ps.length) { const o = el('option', null, '--'); sel.appendChild(o); return; }
    await fetchRoadmap();
  } catch (e) { log('rm: ' + e.message); }
}

async function fetchRoadmap() {
  const n = ($('rm-name') || {}).value;
  if (!n) return;
  try {
    const r = await fetch('/roadmap/' + encodeURIComponent(n), { cache: 'no-store' });
    const body = $('rm-content'); if (!body) return;
    if (!r.ok) { body.textContent = 'ошибка ' + r.status; return; }
    body.textContent = await r.text();
  } catch (e) { log('rm fetch: ' + e.message); }
}

async function doMeeting() {
  try { await jpost('/api/meeting', { on: true }); log('MEETING ON'); }
  catch (e) { log('meeting: ' + e.message); }
}
async function doPauseAll() { try { await jpost('/api/pause_all', { on: true }); log('PAUSE ALL'); } catch (e) { log('pa: ' + e.message); } }
async function doResumeAll() { try { await jpost('/api/pause_all', { on: false }); log('RESUME ALL'); } catch (e) { log('pa: ' + e.message); } }

function bindGlobal() {
  const bp = $('btn-pause-all'); if (bp) bp.addEventListener('click', bulkPause);
  const br = $('btn-resume-all'); if (br) br.addEventListener('click', bulkResume);
  const st = $('btn-selftest'); if (st) st.addEventListener('click', selftest);
  const cs = $('chat-send'); if (cs) cs.addEventListener('click', sendChat);
  const ct = $('chat-text'); if (ct) ct.addEventListener('keydown', function(e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); } });
  const chs = $('chat-ch'); if (chs) chs.addEventListener('change', loadChat);
  const bm = $('btn-meeting'); if (bm) bm.addEventListener('click', doMeeting);
  const bpa = $('btn-pauseall'); if (bpa) bpa.addEventListener('click', doPauseAll);
  const bra = $('btn-resumeall'); if (bra) bra.addEventListener('click', doResumeAll);
  const rl = $('rm-load'); if (rl) rl.addEventListener('click', fetchRoadmap);
}

document.addEventListener('DOMContentLoaded', function() {
  setupTabs();
  setupLogTabs();
  bindGlobal();
  tickClock();
  setInterval(tickClock, 1000);
  refreshStatus();
  setInterval(refreshStatus, 5000);
  loadChat();
});