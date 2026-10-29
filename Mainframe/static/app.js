// JewAI v5 mainframe - dynamic by config.letters
const API = '';
let state = { channels: {}, letters: [] };
let chatData = [];

async function fetchJSON(path, opts) {
  const r = await fetch(API + path, opts);
  return await r.json();
}

function renderTabs() {
  document.querySelectorAll('nav button').forEach(b => {
    b.onclick = () => {
      document.querySelectorAll('nav button').forEach(x => x.classList.remove('active'));
      b.classList.add('active');
      document.querySelectorAll('main .tab').forEach(t => t.classList.add('hidden'));
      document.getElementById('tab-' + b.dataset.tab).classList.remove('hidden');
      if (b.dataset.tab === 'chat') loadChat();
      if (b.dataset.tab === 'roadmap') loadProjects();
    };
  });
}

function blockCard(L, ch) {
  const agentOn = ch.agent_alive;
  const cdpOn = ch.cdp_alive;
  const cmds = ch.cmds_from_start ?? '?';
  const lastId = ch.lastId ?? '(empty)';
  const agentDot = `<span class="dot ${agentOn ? 'on' : 'off'}"></span>`;
  const cdpDot = `<span class="dot ${cdpOn ? 'on' : 'off'}"></span>`;
  return `
    <div class="card" id="card-${L}">
      <h3>${L} · ${ch.name || L}</h3>
      <div class="kv">
        <span class="k">agent</span><span>${agentDot} :${ch.agent_port} ${agentOn?'UP':'DOWN'}</span>
        <span class="k">cdp</span><span>${cdpDot} :${ch.cdp_port} ${cdpOn?'UP':'DOWN'}</span>
        <span class="k">lastId</span><span>${lastId}</span>
        <span class="k">cmds</span><span>${cmds}</span>
      </div>
      <div class="btn-row">
        <button onclick="ctl('boot','agent:${L}')">START</button>
        <button onclick="ctl('stop','agent:${L}')">STOP</button>
        <button onclick="ctl('restart','agent:${L}')">REBOOT</button>
        <button onclick="ctl('boot','chrome:${L}')">CHROME</button>
      </div>
    </div>`;
}

function renderLaunchpad() {
  const letters = state.letters || [];
  const cards = letters.map(L => blockCard(L, state.channels[L] || {})).join('');
  document.getElementById('lp-grid').innerHTML = cards;
}

function renderMnemonic() {
  const letters = state.letters || [];
  const dots = letters.map(L => {
    const ch = state.channels[L] || {};
    const ok = ch.agent_alive && ch.cdp_alive;
    return `<div class="card" style="text-align:center;">
      <div class="dot ${ok?'on':'off'}" style="width:20px;height:20px;"></div>
      <h3 style="margin-top:6px;">${L}</h3>
      <div>${ch.name||L}</div>
    </div>`;
  }).join('');
  document.getElementById('mnemo-grid').innerHTML = dots;
}

async function refresh() {
  try {
    const j = await fetchJSON('/api/status');
    state.channels = j.channels || {};
    const letters = Object.keys(state.channels).sort();
    state.letters = letters;
    renderLaunchpad();
    renderMnemonic();
    document.getElementById('status-line').textContent =
      `${letters.length} agents · ${new Date().toLocaleTimeString()}`;
  } catch (e) {
    document.getElementById('status-line').textContent = 'STATUS ERR: ' + e;
  }
}

async function ctl(action, target) {
  try {
    const j = await fetchJSON('/api/' + action, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({target})
    });
    console.log(action, target, j);
    setTimeout(refresh, 500);
  } catch (e) {
    alert(action + ' ' + target + ': ' + e);
  }
}

async function loadChat() {
  try {
    const j = await fetchJSON('/api/messages');
    const msgs = j.messages || [];
    const box = document.getElementById('chat-box');
    box.innerHTML = msgs.map(m => `<div class="chat-msg"><span class="from">${m.from||'?'}</span> → ${m.to||'ALL'}: ${m.text||''}</div>`).join('');
    box.scrollTop = box.scrollHeight;
  } catch (e) { console.error(e); }
}

async function sendChat() {
  const inp = document.getElementById('chat-input');
  const text = inp.value.trim();
  if (!text) return;
  try {
    await fetchJSON('/api/send', {method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({from: 'operator', to: 'ALL', text})});
    inp.value = '';
    loadChat();
  } catch (e) { alert('send failed: ' + e); }
}

async function loadProjects() {
  try {
    const j = await fetchJSON('/api/projects');
    const list = j.projects || [];
    document.getElementById('projects-list').innerHTML = list.map(p =>
      `<div class="card"><h3>${p.name}</h3>
        <div class="btn-row"><a href="${p.url||'#'}" target="_blank" style="color:#33ff33;">Открыть roadmap</a></div>
      </div>`).join('') || '<div class="stub">Проектов нет</div>';
  } catch (e) { console.error(e); }
}

function clock() {
  document.getElementById('clock').textContent = new Date().toLocaleTimeString();
}

document.addEventListener('DOMContentLoaded', () => {
  renderTabs();
  clock();
  setInterval(clock, 1000);
  refresh();
  setInterval(refresh, 5000);
  document.getElementById('chat-send').onclick = sendChat;
  document.getElementById('chat-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') sendChat();
  });
});
