async function fetch_json(url) {
  try { const r = await fetch(url); return await r.json(); }
  catch (e) { return {ok:false, error:String(e)}; }
}

async function render() {
  const root = document.getElementById('root');
  const st = await fetch_json('/api/status');
  if (!st.ok) { root.innerHTML = '<p class="off">status FAIL: ' + (st.error||'') + '</p>'; return; }
  const rows = Object.entries(st.channels).map(([L, c]) => {
    const a = c.agent_alive ? '<span class="ok">up</span>' : '<span class="off">down</span>';
    const d = c.cdp_alive ? '<span class="ok">up</span>' : '<span class="off">down</span>';
    return '<tr><td>'+L+'</td><td>'+c.name+'</td><td>'+c.agent_port+' '+a+'</td><td>'+c.cdp_port+' '+d+'</td></tr>';
  }).join('');
  root.innerHTML = '<table><tr><th>Ch</th><th>Name</th><th>Agent</th><th>CDP</th></tr>'+rows+'</table>' +
    '<p>root: '+st.root+' v'+st.version+'</p>';
}

render();
setInterval(render, 5000);