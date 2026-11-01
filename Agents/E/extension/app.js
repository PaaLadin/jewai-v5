
const els = {
  log: document.getElementById('crt-log'),
  sign: document.getElementById('walk-sign'),
  pause: document.getElementById('btn-pause'),
  letter: document.getElementById('agent-letter'),
  name: document.getElementById('agent-name'),
  ledCdp: document.getElementById('led-cdp'),
  ledWd: document.getElementById('led-wd'),
  ledRec: document.getElementById('led-rec'),
  url: document.getElementById('agentUrl')
};
let isPaused = false;
let agentName = 'UNKNOWN';
let agentChannel = '?';
let agentVersion = chrome.runtime.getManifest().version;
let lastPingOk = null;

function addLog(msg) {
  const t = new Date().toLocaleTimeString();
  els.log.innerText += `\n[${t}] ${msg}`;
  if (!document.getElementById('scroll-lock').checked) {
    els.log.scrollTop = els.log.scrollHeight;
  }
}

async function ping(silent = false) {
  const url = els.url.value.trim();
  if (!url) {
    if (!silent) addLog('PING: URL не задан.');
    return;
  }
  if (!silent) addLog(`PING: ${url} ...`);
  try {
    const r = await fetch(url + '/ping', { cache: 'no-store' });
    const j = await r.json();
    if (j.ok) {
      if (!silent || lastPingOk !== true) {
        addLog(`PING OK: agent v${agentVersion} | ch: ${agentChannel} | port: ${url.split(':').pop()}`);
      }
      els.letter.textContent = agentChannel;
      els.name.textContent = agentName;
      els.ledCdp.className = 'led green';
      if (!isPaused) els.sign.className = 'walk-sign running';
      lastPingOk = true;
    } else {
      throw new Error('bad response');
    }
  } catch (e) {
    if (!silent || lastPingOk !== false) {
      addLog(`PING FAIL: ${e.message}`);
    }
    els.sign.className = 'walk-sign error';
    els.ledCdp.className = 'led red';
    lastPingOk = false;
  }
}

async function load() {
  addLog(`BIOS INIT: Agent v${agentVersion}. Проверка коннектов...`);
  const s = await chrome.storage.local.get({ agentUrl: '', paused: false, name: 'UNKNOWN', channel: '?' });
  
  agentName = s.name || 'UNKNOWN';
  agentChannel = s.channel || '?';
  els.letter.textContent = agentChannel;
  els.name.textContent = agentName;
  
  let url = s.agentUrl || '';
  if (!url) {
    addLog('Поиск агента...');
    for (let port = 8666; port <= 8675; port++) {
      try {
        const r = await fetch('http://127.0.0.1:' + port + '/ping', { cache: 'no-store' });
        if (r.ok) { url = 'http://127.0.0.1:' + port; break; }
      } catch (e) {}
    }
    if (url) await chrome.storage.local.set({ agentUrl: url });
  }
  
  els.url.value = url;
  isPaused = s.paused;
  updatePauseUI();
  
  if (url) {
    addLog('Агент найден: ' + url);
    ping(false);
  } else {
    addLog('Агент не найден. Введи URL вручную.');
    els.sign.className = 'walk-sign error';
  }
}

function updatePauseUI() {
  if (isPaused) {
    els.pause.classList.add('active');
    els.sign.className = 'walk-sign paused';
  } else {
    els.pause.classList.remove('active');
    if (els.ledCdp.className.includes('green')) els.sign.className = 'walk-sign running';
  }
}

document.getElementById('btnSaveUrl').onclick = async () => {
  await chrome.storage.local.set({ agentUrl: els.url.value.trim() });
  ping(false);
};

els.pause.onclick = async () => {
  isPaused = !isPaused;
  await chrome.storage.local.set({ paused: isPaused });
  updatePauseUI();
  addLog(isPaused ? 'PAUSE ON' : 'PAUSE OFF');
  ping(false);
};

document.getElementById('btn-reboot').onclick = () => addLog('REBOOT (заглушка)');
document.getElementById('btn-selftest').onclick = () => { addLog('SELF-TEST (заглушка)'); ping(false); };

load();
setInterval(() => { if (!isPaused) ping(true); }, 10000);
