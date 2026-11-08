// background.js - service worker v5.
// Reads state (token, agent url, paused) from chrome.storage, routes batches
// from content scripts to local agent (agent.py) HTTP endpoint.

const DEFAULTS = { agentUrl: '', token: '', paused: false, pausedQueue: [] };

async function getState() {
  return new Promise((resolve) => {
    chrome.storage.local.get(DEFAULTS, (s) => resolve(s || DEFAULTS));
  });
}

async function setState(patch) {
  return new Promise((resolve) => {
    chrome.storage.local.set(patch, () => resolve(true));
  });
}

async function callAgent(url, token, path, body) {
  const resp = await fetch(url + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Token': token },
    body: JSON.stringify(body || {}),
  });
  if (!resp.ok) {
    return { ok: false, error: 'HTTP ' + resp.status };
  }
  return await resp.json();
}

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  (async () => {
    try {
      if (msg.type === 'get-state') {
        sendResponse(await getState());
        return;
      }
      if (msg.type === 'set-state') {
        await setState(msg.patch || {});
        sendResponse({ ok: true });
        return;
      }
      if (msg.type === 'batch') {
        const st = await getState();
        if (!st.agentUrl || !st.token) {
          sendResponse({ status: 'NO_STATE', results: [] });
          return;
        }
        if (st.paused) {
          // buffer incoming blocks while paused; drain on resume
          const q = Array.isArray(st.pausedQueue) ? st.pausedQueue.slice() : [];
          for (const a of (msg.actions || [])) q.push(a);
          const cap = 200;
          const trimmed = q.slice(-cap);
          await setState({ pausedQueue: trimmed });
          sendResponse({ status: 'PAUSED', results: [], queued: trimmed.length });
          return;
        }
        // drain buffered queue first (from pause), then current batch
        const buffered = Array.isArray(st.pausedQueue) ? st.pausedQueue.slice() : [];
        if (buffered.length) await setState({ pausedQueue: [] });
        const allActions = buffered.concat(msg.actions || []);
        const results = [];
        let nextId = null;
        for (const action of allActions) {
          try {
            const r = await callAgent(st.agentUrl, st.token, '/' + action.op, action);
            results.push({ id: action.id, op: action.op, status: r.ok ? 'OK' : 'FAIL', result: r });
            if (r && r.next_id) nextId = r.next_id;
          } catch (e) {
            results.push({ id: action.id, op: action.op, status: 'ERR', result: { error: String(e) } });
          }
        }
        sendResponse({ status: 'DONE', results: results, nextId: nextId });
        return;
      }
      if (msg.type === 'status') {
        // no-op, for content script logging
        sendResponse({ ok: true });
        return;
      }
      if (msg.type === 'notify') {
        // 9C: start voice notification (returns immediately, fire-and-forget)
        const st = await getState();
        if (!st.agentUrl || !st.token) {
          sendResponse({ ok: false, error: 'NO_STATE' });
          return;
        }
        try {
          const r = await callAgent(st.agentUrl, st.token, '/notify', {
            text: msg.text || '',
            repeat: msg.repeat || 5,
            interval: msg.interval || 300,
          });
          sendResponse(r);
        } catch (e) {
          sendResponse({ ok: false, error: String(e) });
        }
        return;
      }
      if (msg.type === 'notify-stop') {
        // 9C: create runtime/notify.stop. Fire-and-forget so onMessage never blocks.
        const st = await getState();
        if (!st.agentUrl || !st.token) {
          sendResponse({ ok: true, skipped: 'NO_STATE' });
          return;
        }
        (async () => {
          const ctrl = new AbortController();
          const timer = setTimeout(() => ctrl.abort(), 5 * 60 * 1000);
          try {
            const resp = await fetch(st.agentUrl + '/notify-stop', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json', 'X-Token': st.token },
              body: '{}',
              signal: ctrl.signal,
            });
            await resp.json();
          } catch (e) {
            // silent — fire-and-forget
          } finally {
            clearTimeout(timer);
          }
        })();
        sendResponse({ ok: true, queued: true });
        return;
      }
    } catch (e) {
      sendResponse({ ok: false, error: String(e) });
    }
  })();
  return true;
});

chrome.runtime.onInstalled.addListener(() => {
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => {});
});