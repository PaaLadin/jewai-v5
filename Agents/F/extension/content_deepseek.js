// content_deepseek.js - content script for chat.deepseek.com.
// Parses command blocks from last N assistant messages, sends to background.

const V = '5.0.0';
const POLL_MS = 2000;
const STABLE_MS = 1200;
const MIN_GAP_MS = 5000;
const SCAN_LAST = 3;

const H = '#'.repeat(3);
const BEGIN = H + 'BEGIN' + H;
const ID_RE = /^[A-Z]{4}[0-9]{4}$/;

let lastPreCount = -1;
let lastChangeAt = Date.now();
let lastSendAt = 0;
let inflight = false;
const recentlySent = new Set();
const RECENT_LIMIT = 500;

try {
  chrome.storage.local.get({ recentlySent: [] }, (d) => {
    (d.recentlySent || []).forEach((x) => recentlySent.add(x));
  });
} catch (e) {}

function addRecent(id) {
  recentlySent.add(id);
  if (recentlySent.size > RECENT_LIMIT) {
    recentlySent.delete(recentlySent.values().next().value);
  }
  try { chrome.storage.local.set({ recentlySent: Array.from(recentlySent).slice(-RECENT_LIMIT) }); } catch (e) {}
}

function isStable() {
  const root = document.querySelector('main') || document.body;
  const n = root.querySelectorAll('pre, code').length;
  const t = Date.now();
  if (n !== lastPreCount) { lastPreCount = n; lastChangeAt = t; return false; }
  return t - lastChangeAt > STABLE_MS;
}

function parseBlocks(text) {
  const out = [];
  const re = new RegExp(H + '\\s*BEGIN\\s*' + H + '([\\s\\S]*?)' + H + '\\s*END\\s*' + H, 'g');
  let m;
  while ((m = re.exec(text)) !== null) {
    const inner = m[1];
    const cIdx = inner.search(new RegExp(H + '\\s*CONTENT\\s*' + H));
    let headers, body = '';
    if (cIdx >= 0) {
      headers = inner.slice(0, cIdx);
      const after = inner.slice(cIdx);
      const cm = new RegExp(H + '\\s*CONTENT\\s*' + H).exec(after);
      body = after.slice(cm[0].length).replace(/^\r?\n/, '').replace(/\r?\n$/, '');
    } else { headers = inner; }
    const h = {};
    for (const line of headers.split(/\r?\n/)) {
      const i = line.indexOf(':'); if (i < 0) continue;
      h[line.slice(0, i).trim().toLowerCase()] = line.slice(i + 1).trim();
    }
    if (!h.id || !ID_RE.test(h.id) || !h.op) continue;
    const obj = { id: h.id, op: h.op, path: h.path, cmd: h.cmd, timeout: parseInt(h.timeout || '60', 10) };
    if (h.op === 'write') obj.content = body;
    else if (h.op === 'run') obj.cmd = body.trim() || h.cmd || '';
    out.push(obj);
  }
  return out;
}

function collect() {
  const msgs = document.querySelectorAll('.ds-message');
  const out = [], seen = new Set();
  const start = Math.max(0, msgs.length - SCAN_LAST);
  for (let i = start; i < msgs.length; i++) {
    const c = msgs[i].querySelector('.ds-assistant-message-main-content');
    if (!c) continue;
    for (const pre of c.querySelectorAll('pre, code')) {
      const t = pre.textContent || '';
      if (!t.includes(BEGIN)) continue;
      for (const b of parseBlocks(t)) {
        if (!seen.has(b.id)) { seen.add(b.id); out.push(b); }
      }
    }
  }
  return out;
}

function fresh(blocks, st) {
  return blocks.filter((b) => !recentlySent.has(b.id) && !(st.ledger || []).some((e) => e.id === b.id));
}

async function scan() {
  if (inflight) return;
  if (!isStable()) return;
  const st = await chrome.runtime.sendMessage({ type: 'get-state' });
  if (!st || st.paused || !st.token) return;
  const fr = fresh(collect(), st);
  if (!fr.length) return;
  if (Date.now() - lastSendAt < MIN_GAP_MS) return;
  inflight = true;
  try {
    fr.forEach((b) => addRecent(b.id));
    const r = await chrome.runtime.sendMessage({ type: 'batch', actions: fr });
    if (r && r.results && r.results.length) {
      await typeAndSend(buildReport(r.results, r.nextId));
      lastSendAt = Date.now();
    }
  } finally { inflight = false; }
}

function buildReport(results, nextId) {
  const lines = ['[AGENT REPORT]'];
  for (const r of results) {
    lines.push('id: ' + r.id + ' | op: ' + r.op + ' | ' + r.status);
    const res = r.result || {};
    if (res.error) lines.push('error: ' + res.error);
    if (res.path) lines.push('path: ' + res.path);
    if (res.sha256) lines.push('sha256: ' + res.sha256.slice(0, 16));
    if (r.op === 'read' && typeof res.content === 'string') lines.push('content:\n' + res.content);
    lines.push('---');
  }
  if (nextId) lines.push('next_id: ' + nextId);
  return lines.join('\n');
}

function userHasTyped() {
  const ta = document.querySelector('textarea');
  if (!ta) return false;
  const v = (ta.value || '').trim();
  return v.length > 0 && !v.startsWith('[AGENT REPORT]');
}

async function typeAndSend(text) {
  if (userHasTyped()) return false;
  const ta = document.querySelector('textarea');
  if (!ta) return false;
  const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
  setter.call(ta, text);
  ta.dispatchEvent(new Event('input', { bubbles: true }));
  ta.focus();
  await new Promise((r) => setTimeout(r, 200));
  if (!ta.value || ta.value.length < 10) return false;
  for (let round = 0; round < 2; round++) {
    for (const t of ['keydown', 'keypress', 'keyup']) {
      ta.dispatchEvent(new KeyboardEvent(t, {
        key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true, cancelable: true,
      }));
    }
    await new Promise((r) => setTimeout(r, 150));
    if (!ta.value || ta.value.length < 5) return true;
  }
  return false;
}

console.log('[jewai-v5-deepseek] content script loaded v' + V);
setInterval(scan, POLL_MS);
window.addEventListener('load', () => setTimeout(scan, 800));