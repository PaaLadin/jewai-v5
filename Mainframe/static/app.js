
const term = document.getElementById('chatFeed');
const input = document.getElementById('chatInput');
const persFeed = document.getElementById('persFeed');
const persInput = document.getElementById('persInput');
let lastTs = 0, persLastTs = 0, curPersCh = null;

function clock(){
    const d = new Date();
    document.getElementById('clock').textContent = [d.getHours(), d.getMinutes(), d.getSeconds()].map(n => String(n).padStart(2,'0')).join(':');
}
setInterval(clock, 1000); clock();

// Tabs
document.querySelectorAll('.tab').forEach(t => {
    t.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(x => x.classList.remove('active'));
        document.querySelectorAll('.screen').forEach(x => x.classList.remove('active'));
        t.classList.add('active');
        document.getElementById('screen-' + t.dataset.tab).classList.add('active');
    });
});

// Status
function fetchStatus() {
    fetch('/api/status').then(r => r.json()).then(d => {
        if (!d.ok || !d.channels) return;
        let html = '<table><tr><th>CH</th><th>NAME</th><th>AGENT</th><th>CDP</th></tr>';
        let phtml = '';
        for (let L in d.channels) {
            let c = d.channels[L];
            let ag = c.agent_alive ? '<span style="color:#0f0">ON</span>' : '<span style="color:#f00">OFF</span>';
            let cd = c.cdp_alive ? '<span style="color:#0f0">ON</span>' : '<span style="color:#f00">OFF</span>';
            html += `<tr><td>${L}</td><td>${c.name || L}</td><td>${c.agent_port} (${ag})</td><td>${c.cdp} (${cd})</td></tr>`;
            phtml += `<div style="cursor:pointer; padding:5px; border-bottom:1px solid #333;" onclick="selectPers('${L}', '${c.name||L}')">${L}: ${c.name||L}</div>`;
        }
        html += '</table>';
        document.getElementById('chanList').innerHTML = html;
        if (document.getElementById('persList').innerHTML === 'Загрузка...') document.getElementById('persList').innerHTML = phtml;
    }).catch(() => {});
}
setInterval(fetchStatus, 3000); fetchStatus();

// Chat
function fetchChat() {
    fetch('/api/messages').then(r => r.json()).then(d => {
        if (!d.messages) return;
        let added = false;
        d.messages.forEach(m => {
            if (m.ts > lastTs) {
                lastTs = m.ts;
                let el = document.createElement('div');
                el.innerHTML = `<span style="color:#888">[${m.time || ''}]</span> <span style="color:#0f0">${m.from}:</span> ${m.text}`;
                term.appendChild(el);
                added = true;
            }
        });
        if (added) term.scrollTop = term.scrollHeight;
    }).catch(() => {});
}
setInterval(fetchChat, 2000);

function sendChat() {
    let text = input.value.trim();
    if (!text) return;
    input.value = '';
    fetch('/api/send', {
        method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({from: 'operator', to: 'ALL', text: text})
    }).then(() => fetchChat());
}
document.getElementById('chatSend').addEventListener('click', sendChat);
input.addEventListener('keydown', e => { if (e.key === 'Enter') sendChat(); });

// Personal
window.selectPers = function(ch, name) {
    curPersCh = ch;
    persLastTs = 0;
    document.getElementById('persTitle').textContent = name;
    persFeed.innerHTML = '';
    fetchPers();
};
function fetchPers() {
    if (!curPersCh) return;
    fetch('/api/chat/' + curPersCh).then(r => r.json()).then(d => {
        if (!d.messages) return;
        let added = false;
        d.messages.forEach(m => {
            if (m.ts > persLastTs) {
                persLastTs = m.ts;
                let el = document.createElement('div');
                el.innerHTML = `<span style="color:#888">[${m.time || ''}]</span> <span style="color:#0f0">${m.from}:</span> ${m.text}`;
                persFeed.appendChild(el);
                added = true;
            }
        });
        if (added) persFeed.scrollTop = persFeed.scrollHeight;
    }).catch(() => {});
}
setInterval(fetchPers, 3000);
function sendPers() {
    if (!curPersCh) return;
    let text = persInput.value.trim();
    if (!text) return;
    persInput.value = '';
    fetch('/api/chat/' + curPersCh, {
        method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({from: 'operator', text: text})
    }).then(() => fetchPers());
}
document.getElementById('persSend').addEventListener('click', sendPers);
persInput.addEventListener('keydown', e => { if (e.key === 'Enter') sendPers(); });

// Logs
window.loadLog = function(name) {
    document.querySelectorAll('.log-btn').forEach(x => x.classList.remove('active'));
    event.target.classList.add('active');
    fetch('/api/logs?name=' + name).then(r => r.json()).then(d => {
        document.getElementById('logBody').textContent = d.content || '(пусто)';
    }).catch(() => {
        document.getElementById('logBody').textContent = '[лог недоступен]';
    });
};
