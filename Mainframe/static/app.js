let state = { channels: {}, letters: [] };
let currentLetter = 'A';

async function fetchJSON(path, opts) {
  const r = await fetch(path, opts);
  return await r.json();
}

function crtLog(msg) {
  const log = document.getElementById('crt-log');
  const t = new Date().toLocaleTimeString();
  log.innerHTML += `\n[${t}] ${msg}`;
  log.scrollTop = log.scrollHeight;
}

async function refresh() {
  try {
    const j = await fetchJSON('/api/status');
    state.channels = j.channels || {};
    state.letters = Object.keys(state.channels).sort();
    if (!state.letters.includes(currentLetter) && state.letters.length > 0) {
      currentLetter = state.letters[0];
    }
    renderCockpit();
    document.getElementById('crt-time').textContent = new Date().toLocaleTimeString();
  } catch (e) {
    crtLog('STATUS ERR: ' + e);
  }
}

function renderCockpit() {
  const ch = state.channels[currentLetter] || {};
  document.getElementById('portrait-L').textContent = currentLetter;
  document.getElementById('portrait-name-L').textContent = ch.name || 'UNKNOWN';
  setLED('led-alive', ch.agent);
  setLED('led-cdp', ch.content);
  setLED('led-wd', ch.watchdog);
  document.getElementById('val-cmds').textContent = ch.cmds_from_start !== null ? ch.cmds_from_start : '---';
  document.getElementById('crt-ch').textContent = currentLetter;

  const log = document.getElementById('crt-log');
  log.innerHTML = `> CHANNEL: ${currentLetter} (${ch.name || '?'})\n` +
                  `> LAST ID: ${ch.lastId || '(none)'}\n` +
                  `> CMDS:    ${ch.cmds_from_start ?? '?'}\n` +
                  `> ALIVE:   ${ch.agent ? 'YES' : 'NO'}\n` +
                  `> CDP:     ${ch.content ? 'YES' : 'NO'}\n` +
                  `> WD:      ${ch.watchdog ? 'ON' : 'OFF'}\n` +
                  `> REC:     ${ch.recovery ? 'ON' : 'OFF'}\n` +
                  `--------------------------------\n` +
                  `WAITING FOR TELEMETRY...\n`;
}

function setLED(id, isOn) {
  const el = document.getElementById(id);
  if (!el) return;
  el.className = isOn ? 'led on' : 'led off';
}

async function ctl(action, target) {
  crtLog(`> EXEC: ${action} ${target}`);
  try {
    const j = await fetchJSON('/api/' + action, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({target, channel: currentLetter})
    });
    crtLog(`> RESULT: ${JSON.stringify(j).substring(0, 80)}`);
    setTimeout(refresh, 1000);
  } catch (e) {
    crtLog(`> FAIL: ${e}`);
  }
}

async function pauseChannel() {
  crtLog(`> EXEC: PAUSE ${currentLetter}`);
  try {
    const j = await fetchJSON('/api/pause', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({channel: currentLetter, on: true})
    });
    crtLog(`> RESULT: ${JSON.stringify(j).substring(0, 80)}`);
    await fetchJSON('/api/send', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({from: 'operator', to: currentLetter, text: '[SYS] PAUSE ON. Оператор приостановил канал.'})
    });
    crtLog('> PAUSE ON. Agent notified.');
  } catch (e) {
    crtLog(`> PAUSE FAIL: ${e}`);
  }
}

async function resumeChannel() {
  crtLog(`> EXEC: RESUME ${currentLetter}`);
  try {
    const j = await fetchJSON('/api/resume', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({channel: currentLetter})
    });
    crtLog(`> RESULT: ${JSON.stringify(j).substring(0, 80)}`);
    await fetchJSON('/api/send', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({from: 'operator', to: currentLetter, text: '[SYS] PAUSE OFF. Работа продолжается.'})
    });
    crtLog('> RESUME OK.');
  } catch (e) {
    crtLog(`> RESUME FAIL: ${e}`);
  }
}

async function runDiagnose() {
  crtLog('> EXEC: DIAGNOSE');
  try {
    const j = await fetchJSON('/api/diagnose', { method: 'POST' });
    crtLog(`> DIAGNOSE: ${JSON.stringify(j).substring(0, 200)}`);
  } catch (e) {
    crtLog(`> DIAGNOSE FAIL: ${e}`);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('btn-start').onclick = () => ctl('boot', `agent:${currentLetter}`);
  document.getElementById('btn-stop').onclick = () => ctl('stop', `agent:${currentLetter}`);
  document.getElementById('btn-reboot').onclick = () => ctl('restart', `agent:${currentLetter}`);
  document.getElementById('btn-chrome').onclick = () => ctl('boot', `chrome:${currentLetter}`);
  document.getElementById('btn-pause').onclick = pauseChannel;
  document.getElementById('btn-resume').onclick = resumeChannel;
  document.getElementById('btn-reload').onclick = () => location.reload();
  document.getElementById('btn-selftest').onclick = runDiagnose;

  document.getElementById('portrait-L').onclick = () => {
    if (state.letters.length === 0) return;
    let idx = state.letters.indexOf(currentLetter);
    idx = (idx + 1) % state.letters.length;
    currentLetter = state.letters[idx];
    renderCockpit();
    crtLog(`> SWITCHED TO CHANNEL ${currentLetter}`);
  };

  refresh();
  setInterval(refresh, 5000);
});