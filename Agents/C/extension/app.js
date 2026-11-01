const els = {
  log: document.getElementById('crt-log'),
  sign: document.getElementById('walk-sign'),
  pause: document.getElementById('btn-pause'),
  letter: document.getElementById('agent-letter'),
  ledCdp: document.getElementById('led-cdp'),
  ledWd: document.getElementById('led-wd'),
  ledRec: document.getElementById('led-rec'),
  url: document.getElementById('agentUrl')
};
let isPaused = false;

function addLog(msg) {
  const t = new Date().toLocaleTimeString();
  els.log.innerText += `\n[${t}] ${msg}`;
  const lock = document.getElementById('scroll-lock');
  if (!lock || !lock.checked) {
    els.log.scrollTop = els.log.scrollHeight;
  }
}

async function autodetect() {
  for (let port = 8666; port <= 8675; port++) {
    try {
      const r = await fetch('http://127.0.0.1:' + port + '/ping', { cache: 'no-store' });
      if (r.ok) return 'http://127.0.0.1:' + port;
    } catch (e) {}
  }
  return '';
}

async function ping() {
  const url = els.url.value.trim();
  if (!url) return;
  try {
    const r = await fetch(url + '/ping', { cache: 'no-store' });
    const j = await r.json();
    if (j.ok) {
      els.letter.textContent = j.channel || '?';
      els.ledCdp.className = 'led green';
      els.ledWd.className = 'led red';
      els.ledRec.className = 'led red';
      if (!isPaused) els.sign.className = 'walk-sign running';
    } else {
      throw new Error('ping fail');
    }
  } catch (e) {
    els.sign.className = 'walk-sign error';
    els.ledCdp.className = 'led red';
  }
}

async function load() {
  const s = await chrome.storage.local.get({ agentUrl: '', paused: false });
  let url = s.agentUrl || '';
  if (!url) {
    addLog('Автопоиск агента...');
    url = await autodetect();
    if (url) await chrome.storage.local.set({ agentUrl: url });
  }
  els.url.value = url;
  isPaused = s.paused;
  updatePauseUI();
  if (url) { addLog('Агент: ' + url); ping(); }
  else { addLog('Агент не найден.'); }
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
  addLog('Сохранено. Пинг...');
  ping();
};

els.pause.onclick = async () => {
  isPaused = !isPaused;
  await chrome.storage.local.set({ paused: isPaused });
  updatePauseUI();
  addLog(isPaused ? 'CMD PAUSE ON' : 'CMD PAUSE OFF');
  ping();
};

document.getElementById('btn-reboot').onclick = () => addLog('REBOOT CMD');
document.getElementById('btn-selftest').onclick = () => addLog('SELF-TEST CMD');

load();
setInterval(ping, 5000);