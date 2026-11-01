const API = '';
let currentLetter = 'A';
let isPaused = false;
let lastStateStr = '';

async function fetchJSON(path, opts) {
    const r = await fetch(API + path, opts);
    return await r.json();
}

function addLog(type, text) {
    const box = document.getElementById('crt-log');
    const div = document.createElement('div');
    div.className = 'log-line ' + (type === 'IN' ? 'log-in' : type === 'OUT' ? 'log-out' : 'log-err');
    const time = new Date().toLocaleTimeString();
    div.textContent = `[${time}] [${type}] ${text}`;
    box.appendChild(div);
    
    if (!document.getElementById('scroll-lock').checked) {
        box.scrollTop = box.scrollHeight;
    }
}

// Функция обновления 3 ламп
function setLamps(prefix, isOn) {
    const red = document.getElementById(`led-${prefix}-r`);
    const yellow = document.getElementById(`led-${prefix}-y`);
    const green = document.getElementById(`led-${prefix}-g`);
    
    // Сбрасываем все
    if(red) red.className = 'led';
    if(yellow) yellow.className = 'led';
    if(green) green.className = 'led';

    if (isOn) {
        if(green) green.className = 'led green'; // Горит зелёный
    } else {
        if(red) red.className = 'led red'; // Горит красный
    }
}

async function refresh() {
    try {
        const j = await fetchJSON('/api/status');
        const ch = j.channels[currentLetter] || {};
        
        document.getElementById('agent-letter').textContent = currentLetter;
        document.getElementById('agent-name').textContent = ch.name || 'UNKNOWN';
        
        // Лампы
        setLamps('cdp', ch.content);
        setLamps('wd', ch.watchdog);
        setLamps('rec', ch.recovery);

        // Тумблеры
        const swWd = document.getElementById('sw-wd');
        if (swWd) swWd.checked = ch.watchdog;
        const swRec = document.getElementById('sw-rec');
        if (swRec) swRec.checked = ch.recovery;

        // Светофор
        const sign = document.getElementById('walk-sign');
        if (isPaused) {
            sign.className = 'walk-sign paused';
        } else if (ch.agent && ch.content) {
            sign.className = 'walk-sign running';
        } else {
            sign.className = 'walk-sign error';
        }

        const currentStateStr = JSON.stringify(ch);
        if (currentStateStr !== lastStateStr) {
            if (ch.agent !== undefined) addLog('SYS', 'Status updated: ALIVE=' + ch.agent + ' CDP=' + ch.content);
            lastStateStr = currentStateStr;
        }

    } catch (e) {
        addLog('ERR', 'Connect fail: ' + e.message);
    }
}

// Логика паузы
const togglePause = async () => {
    isPaused = !isPaused;
    const btn = document.getElementById('btn-pause');
    if (isPaused) {
        btn.classList.add('active');
        addLog('OUT', 'CMD PAUSE ON -> СТОП');
        await fetchJSON('/api/pause', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({channel: currentLetter, on: true}) });
        await fetchJSON('/api/send', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({from: 'operator', to: currentLetter, text: 'СТОП'}) });
    } else {
        btn.classList.remove('active');
        addLog('OUT', 'CMD PAUSE OFF -> ПРОДОЛЖАЙ РАБОТУ');
        await fetchJSON('/api/pause', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({channel: currentLetter, on: false}) });
        await fetchJSON('/api/send', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({from: 'operator', to: currentLetter, text: 'ПРОДОЛЖАЙ РАБОТУ'}) });
    }
    refresh();
};

document.getElementById('btn-pause').onclick = togglePause;
document.getElementById('walk-sign').onclick = togglePause;

document.getElementById('save-wd').onclick = async () => {
    const val = document.getElementById('inp-wd').value;
    addLog('OUT', `Save WD interval: ${val}s`);
    await fetchJSON('/api/svc', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({channel: currentLetter, kind: 'watchdog', action: 'start', interval: parseInt(val) || 300}) });
};

document.getElementById('save-rec').onclick = async () => {
    const val = document.getElementById('inp-rec').value;
    addLog('OUT', `Save REC interval: ${val}s`);
    await fetchJSON('/api/svc', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({channel: currentLetter, kind: 'recovery', action: 'start', interval: parseInt(val) || 60}) });
};

document.getElementById('sw-wd').onchange = async (e) => {
    const action = e.target.checked ? 'start' : 'stop';
    addLog('OUT', `CMD svc ${action} watchdog`);
    await fetchJSON('/api/svc', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({channel: currentLetter, kind: 'watchdog', action: action}) });
    refresh();
};

document.getElementById('sw-rec').onchange = async (e) => {
    const action = e.target.checked ? 'start' : 'stop';
    addLog('OUT', `CMD svc ${action} recovery`);
    await fetchJSON('/api/svc', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({channel: currentLetter, kind: 'recovery', action: action}) });
    refresh();
};

document.getElementById('btn-reboot').onclick = async () => {
    addLog('OUT', `CMD REBOOT (CDP+AGENT) ${currentLetter}`);
    await fetchJSON('/api/restart', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({target: `agent:${currentLetter}`}) });
    addLog('SYS', 'Reboot signal sent. Waiting...');
    setTimeout(refresh, 3000);
};

document.getElementById('btn-selftest').onclick = async () => {
    const btn = document.getElementById('btn-selftest');
    btn.className = 'self-test-btn testing';
    btn.disabled = true;
    addLog('OUT', 'Self-test started...');
    
    try {
        const j = await fetchJSON('/api/diagnose', { method: 'POST' });
        if (j && j.ok) {
            btn.className = 'self-test-btn success';
            addLog('IN', 'Self-test OK');
            setTimeout(() => { btn.className = 'self-test-btn'; btn.disabled = false; }, 5000);
        } else { throw new Error('Diagnose failed'); }
    } catch (e) {
        btn.className = 'self-test-btn error';
        addLog('ERR', 'Self-test failed: ' + e.message);
        setTimeout(() => { btn.className = 'self-test-btn'; btn.disabled = false; }, 5000);
    }
};

document.addEventListener('DOMContentLoaded', () => {
    addLog('SYS', 'Panel initialized');
    refresh();
    setInterval(refresh, 3000);
});