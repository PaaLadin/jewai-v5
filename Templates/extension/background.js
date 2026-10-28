// background.js - service worker v5.
// Reads state (token, agent url, paused) from chrome.storage, routes batches
// from content scripts to local agent (agent.py) HTTP endpoint.

const DEFAULTS = { agentUrl: '', token: '', paused: false };

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
          sendResponse({ status: 'PAUSED', results: [] });
          return;
        }
        const results = [];
        let nextId = null;
        for (const action of (msg.actions || [])) {
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
    } catch (e) {
      sendResponse({ ok: false, error: String(e) });
    }
  })();
  return true;
});

chrome.runtime.onInstalled.addListener(() => {
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => {});
});