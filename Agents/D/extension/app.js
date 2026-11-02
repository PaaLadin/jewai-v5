const els = {
  log: document.getElementById('crt-log'),
  sign: document.getElementById('walk-sign'),
  pause: document.getElementById('btn-pause'),
  letter: document.getElementById('agent-letter'),
  name: document.getElementById('agent-name'),
  ledCdp: document.getElementById('led-cdp'),
  ledWd: document.getElementById('led-wd'),
  ledRec: document.getElementById('led-rec'),
  url: document.getElementById('agentUrl'),
  swWd: document.getElementById('sw-wd'),
  swRec: document.getElementById('sw-rec'),
  inpWd: document.getElementById('inp-wd'),
  inpRec: document.getElementById('inp-rec'),
  saveWd: document.getElementById('save-wd'),
  saveRec: document.getElementById('save-rec'),
  reboot: document.getElementById('btn-reboot'),
  selftest: document.getElementById('btn-selftest')
};

let isPaused = false;
let agentName = 'UNKNOWN';
let agentChannel = '?';
let agentVersion = chrome.runtime.getManifest().version;
let lastPingOk = null;
let agentBaseUrl = '';

function addLog(msg) {
  const t = new Date().toLocaleTimeString();
  els.log.innerText += '\n[' + t + '] ' + msg;
  if (!document.getElementById('scroll-lock').checked) {
    els.log.scrollTop = els.log.scrollHeight;
  }
}

function setLed(el, kind) {
  el.className = 'led ' + kind;
}

async function apiGet(path) {
  const r = await fetch(agentBaseUrl + path, {cache: 'no-store'});
  return await r.json();
}

async function apiPost(path, body) {
  const r = await fetch(agentBaseUrl + path, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body || {})
  });
  return await r.json();
}

async function ping(silent) {
  if (!agentBaseUrl) { if (!silent) addLog('PING: URL не задан.'); return; }
  if (!silent) addLog('PING: ' + agentBaseUrl + ' ...');
  try {
    const j = await apiGet('/ping');
    if (j.ok) {
      if (!silent || lastPingOk !== true) {
        addLog('PING OK: agent v' + (j.version || agentVersion) + ' | ch: ' + (j.channel || agentChannel) + ' | name: ' + (j.name || agentName) + ' | port: ' + agentBaseUrl.split(':').pop());
      }
      if (j.channel) { agentChannel = j.channel; els.letter.textContent = j.channel; }
      if (j.name) { agentName = j.name; els.name.textContent = j.name; }
      setLed(els.ledCdp, 'green');
      if (!isPaused) els.sign.className = 'walk-sign running';
      lastPingOk = true;
    } else { throw new Error('bad response'); }
  } catch (e) {
    if (!silent || lastPingOk !== false) addLog('PING FAIL: ' + e.message);
    els.sign.className = 'walk-sign error';
    setLed(els.ledCdp, 'red');
    lastPingOk = false;
  }
}

async function loadIdentity() {
  try {
    const id = await apiGet('/identity');
    if (id.ok) {
      agentChannel = id.channel || '?';
      agentName = id.name || 'UNKNOWN';
      els.letter.textContent = agentChannel;
      els.name.textContent = agentName;
      await chrome.storage.local.set({channel: agentChannel, name: agentName, agentUrl: agentBaseUrl});
      addLog('IDENTITY: ch=' + agentChannel + ' name=' + agentName + ' prefix=' + (id.prefix || '?') + ' model=' + (id.model || '?'));
      return true;
    }
  } catch (e) {
    addLog('IDENTITY FAIL: ' + e.message);
  }
  return false;
}

async function loadSvcStatus() {
  try {
    const j = await apiGet('/svc_status');
    if (!j.ok) return;
    const wd = j.watchdog || {state: 'off', alive: false};
    const rec = j.recovery || {state: 'off', alive: false};
    if (wd.alive) { setLed(els.ledWd, 'green'); els.swWd.checked = true; }
    else if (wd.state === 'on') { setLed(els.ledWd, 'yellow'); els.swWd.checked = true; }
    else { setLed(els.ledWd, 'red'); els.swWd.checked = false; }
    if (rec.alive) { setLed(els.ledRec, 'green'); els.swRec.checked = true; }
    else if (rec.state === 'on') { setLed(els.ledRec, 'yellow'); els.swRec.checked = true; }
    else { setLed(els.ledRec, 'red'); els.swRec.checked = false; }
  } catch (e) { /* silent */ }
}

async function loadPauseState() {
  try {
    const j = await apiGet('/pause_state');
    isPaused = !!j.paused;
    updatePauseUI();
  } catch (e) { /* silent */ }
}

async function load() {
  addLog('BIOS INIT: Agent v' + agentVersion + '. Проверка коннектов...');
  const s = await chrome.storage.local.get({agentUrl: '', paused: false, name: 'UNKNOWN', channel: '?'});
  agentName = s.name || 'UNKNOWN';
  agentChannel = s.channel || '?';
  els.letter.textContent = agentChannel;
  els.name.textContent = agentName;

  agentBaseUrl = s.agentUrl || '';
  if (!agentBaseUrl) {
    addLog('Поиск агента...');
    for (let port = 8666; port <= 8675; port++) {
      try {
        const r = await fetch('http://127.0.0.1:' + port + '/ping', {cache: 'no-store'});
        if (r.ok) { agentBaseUrl = 'http://127.0.0.1:' + port; break; }
      } catch (e) { /* next */ }
    }
    if (agentBaseUrl) await chrome.storage.local.set({agentUrl: agentBaseUrl});
  }
  els.url.value = agentBaseUrl;

  if (!agentBaseUrl) {
    addLog('Агент не найден. Введи URL вручную.');
    els.sign.className = 'walk-sign error';
    return;
  }

  addLog('Агент найден: ' + agentBaseUrl);
  if (agentChannel === '?' || agentName === 'UNKNOWN') {
    await loadIdentity();
  }
  await loadPauseState();
  await loadSvcStatus();
  ping(false);
}

function updatePauseUI() {
  if (isPaused) {
    els.pause.classList.add('active');
    els.sign.className = 'walk-sign paused';
  } else {
    els.pause.classList.remove('active');
    if (els.ledCdp.className.indexOf('green') >= 0) els.sign.className = 'walk-sign running';
  }
}

document.getElementById('btnSaveUrl').onclick = async () => {
  agentBaseUrl = els.url.value.trim();
  await chrome.storage.local.set({agentUrl: agentBaseUrl});
  await loadIdentity();
  ping(false);
};

els.pause.onclick = async () => {
  isPaused = !isPaused;
  try {
    await apiPost('/pause', {paused: isPaused, by: 'operator'});
  } catch (e) {
    addLog('PAUSE FAIL: ' + e.message);
  }
  updatePauseUI();
  addLog(isPaused ? 'PAUSE ON (мост остановлен)' : 'PAUSE OFF (мост возобновлён)');
};

async function toggleSvc(kind, on, interval, cooldown) {
  try {
    const body = {kind: kind, action: on ? 'start' : 'stop', interval: interval, cooldown: cooldown};
    const r = await apiPost('/svc_toggle', body);
    addLog('SVC ' + kind + ' ' + (on ? 'START' : 'STOP') + ': ' + JSON.stringify(r).slice(0, 120));
  } catch (e) {
    addLog('SVC ' + kind + ' FAIL: ' + e.message);
  }
  setTimeout(loadSvcStatus, 800);
}

els.swWd.onchange = () => toggleSvc('watchdog', els.swWd.checked, parseInt(els.inpWd.value) || 300, null);
els.swRec.onchange = () => toggleSvc('recovery', els.swRec.checked, null, parseInt(els.inpRec.value) || 60);

els.saveWd.onclick = async () => {
  const iv = parseInt(els.inpWd.value) || 300;
  if (els.swWd.checked) {
    await toggleSvc('watchdog', false);
    await toggleSvc('watchdog', true, iv);
  } else {
    addLog('WATCHDOG: интервал сохранён (' + iv + 'с), применится при следующем старте.');
  }
};
els.saveRec.onclick = async () => {
  const cd = parseInt(els.inpRec.value) || 60;
  if (els.swRec.checked) {
    await toggleSvc('recovery', false);
    await toggleSvc('recovery', true, null, cd);
  } else {
    addLog('RECOVERY: cooldown сохранён (' + cd + 'с), применится при следующем старте.');
  }
};

els.selftest.onclick = async () => {
  addLog('SELF-TEST (запуск)...');
  try {
    const r = await apiPost('/selftest', {});
    if (r.checks) {
      for (const c of r.checks) addLog('  [' + (c.ok ? 'OK' : 'FAIL') + '] ' + c.name);
      addLog('SELF-TEST: ' + (r.ok ? 'ВСЁ ОК' : 'ЕСТЬ ОШИБКИ'));
    } else {
      addLog('SELF-TEST: ' + JSON.stringify(r).slice(0, 200));
    }
  } catch (e) {
    addLog('SELF-TEST FAIL: ' + e.message);
  }
};

els.reboot.onclick = async () => {
  addLog('REBOOT: перезапуск моста...');
  try {
    const r = await apiPost('/reboot', {});
    addLog('REBOOT: ' + JSON.stringify(r).slice(0, 200));
  } catch (e) {
    addLog('REBOOT FAIL: ' + e.message);
  }
};

load();
setInterval(() => { if (!isPaused) ping(true); }, 10000);
setInterval(loadSvcStatus, 10000);
