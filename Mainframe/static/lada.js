document.addEventListener('DOMContentLoaded', () => {
  let currentChatId = null;
  const feed = document.getElementById('lada-feed');
  const input = document.getElementById('lada-input');
  const btnSend = document.getElementById('lada-send');
  const chatList = document.getElementById('lada-chat-list');
  const btnNew = document.getElementById('lada-new-chat');

  async function fetchChats() {
    const r = await fetch('/api/chats'); const j = await r.json();
    chatList.innerHTML = '';
    (j.chats || []).forEach(c => {
      const div = document.createElement('div');
      div.textContent = c.title || 'Без названия';
      div.style.cssText = 'padding: 8px; cursor: pointer; border: 1px solid #222; color: #0f0; word-break: break-all;';
      if (c.id === currentChatId) div.style.background = '#222';
      div.onclick = () => loadChat(c.id);
      chatList.appendChild(div);
    });
  }

  async function loadChat(id) {
    currentChatId = id;
    const r = await fetch('/api/chats/' + id);
    const j = await r.json();
    feed.innerHTML = '';
    (j.messages || []).forEach(m => {
      const d = document.createElement('div');
      d.style.cssText = 'padding: 10px; border-left: 3px solid ' + (m.role === 'user' ? '#0f0' : '#555') + '; white-space: pre-wrap;';
      d.textContent = (m.role === 'user' ? '> ' : '🤖 ') + m.content;
      feed.appendChild(d);
    });
    feed.scrollTop = feed.scrollHeight;
    fetchChats();
  }

  async function sendMsg() {
    const text = input.value.trim();
    if (!text) return;
    input.value = '';
    
    const uDiv = document.createElement('div');
    uDiv.style.cssText = 'padding: 10px; border-left: 3px solid #0f0; white-space: pre-wrap;';
    uDiv.textContent = '> ' + text;
    feed.appendChild(uDiv);
    feed.scrollTop = feed.scrollHeight;

    const aDiv = document.createElement('div');
    aDiv.style.cssText = 'padding: 10px; border-left: 3px solid #555; color: #aaa; font-style: italic;';
    aDiv.textContent = 'Думает...';
    feed.appendChild(aDiv);
    feed.scrollTop = feed.scrollHeight;

    try {
      const r = await fetch('/api/llm/query', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text, chat_id: currentChatId })
      });
      const j = await r.json();
      if (j.ok) {
        currentChatId = j.chat_id;
        aDiv.style.color = '#0f0'; aDiv.style.fontStyle = 'normal';
        aDiv.textContent = '🤖 ' + j.text;
        fetchChats();
      } else {
        aDiv.style.color = '#f00'; aDiv.textContent = 'Ошибка: ' + j.error;
      }
    } catch(e) {
      aDiv.style.color = '#f00'; aDiv.textContent = 'Ошибка сети: ' + e;
    }
    feed.scrollTop = feed.scrollHeight;
  }

  btnSend.onclick = sendMsg;
  input.onkeydown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMsg();
    }
  };

  btnNew.onclick = async () => {
    const title = prompt("Название нового чата:", "Новый чат");
    if (!title) return;
    const r = await fetch('/api/chats', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: title }) });
    const j = await r.json();
    if (j.ok) loadChat(j.chat_id);
  };

  fetchChats();
});
