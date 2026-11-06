'use strict';
const select = document.getElementById('provider');
const save = document.getElementById('save-provider');
const status = document.getElementById('provider-status');
const models = ['deepseek', 'qwen', 'alice', 'perplexity'];
let busy = false, dirty = false, current = '', context = null;
const labels = {deepseek:'DeepSeek', qwen:'Qwen', alice:'Алиса', perplexity:'Perplexity (experimental)'};
models.forEach(id => select.add(new Option(labels[id], id)));
select.onchange = () => { dirty = true; };

async function getContext() {
  const s = await chrome.storage.local.get({agentUrl:'', token:'', channel:''});
  if (!s.agentUrl) throw new Error('URL агента ещё не задан. Дождитесь запуска профиля.');
  const u = new URL(s.agentUrl);
  if (u.protocol !== 'http:' || u.hostname !== '127.0.0.1' || u.username || u.password ||
      u.pathname !== '/' || u.search || u.hash || !s.token || !/^[A-J]$/.test(s.channel)) {
    throw new Error('Нет корректных локальных настроек агента. Дождитесь launcher или задайте URL в панели.');
  }
  const ctx = {base:u.origin, token:s.token, channel:s.channel};
  const r = await fetch(ctx.base + '/identity', {cache:'no-store', signal:AbortSignal.timeout(4000)});
  if (!r.ok) throw new Error('Агент недоступен: HTTP ' + r.status);
  const identity = await r.json();
  if (!identity.ok || identity.channel !== ctx.channel) throw new Error('Канал URL не совпадает с профилем. Save заблокирован.');
  return ctx;
}

async function post(ctx, path, body, timeout=5000) {
  const r = await fetch(ctx.base + path, {method:'POST',
    headers:{'Content-Type':'application/json', 'X-Token':ctx.token},
    body:JSON.stringify(body), signal:AbortSignal.timeout(timeout)});
  const j = await r.json();
  if (path === '/run' && !j.ok && j.stdout) {
    let detail; try { detail = JSON.parse(j.stdout.trim()); } catch (_) {}
    if (detail && detail.error) throw new Error(detail.error);
  }
  if (!r.ok || !j.ok) throw new Error(r.status === 423 ?
    'Канал на паузе: существующий API запрещает Save через /run. Пауза автоматически не снимается.' :
    (j.error || 'HTTP ' + r.status));
  return j;
}

async function readState(ctx) {
  try {
    const r = await post(ctx, '/read', {path:'Profiles/' + ctx.channel + '/logs/provider_state.json'});
    return JSON.parse(r.content);
  } catch (e) {
    if (String(e.message).includes('FileNotFoundError')) return {};
    throw e;
  }
}

const phases = {
  queued:'Запрос принят. Ожидаю завершения текущего цикла моста.',
  awaiting_input:'Настройки сохранены. Ожидаю вход в сервис или доступное пустое поле ввода.',
  sending_activation:'Отправляю инструкцию новому чату.',
  confirmation_required:'Отправка инструкции неоднозначна. Канал заблокирован; нужна ручная проверка.',
  error:'Ошибка переключения; проверьте подробности ниже.',
  ready:'Адаптер применён, инструкция отправлена. Это не подтверждение ответа модели.',
  unchanged:'Этот адаптер уже выбран.'
};

async function refresh() {
  if (busy) return;
  try {
    context = await getContext();
    const r = await post(context, '/read', {path:'config.json'});
    const cfg = JSON.parse(r.content);
    const channel = cfg.channels && cfg.channels[context.channel];
    if (!channel || !models.includes(channel.model)) throw new Error('Адаптер в config.json не поддерживается.');
    current = channel.model;
    if (!dirty) select.value = current;
    const state = await readState(context);
    const phase = state.phase;
    const pending = phase && !['ready','error','unchanged'].includes(phase);
    select.disabled = !!pending;
    save.disabled = !!pending;
    status.textContent = 'Канал ' + context.channel + ' · ' + labels[current] + '\n' +
      (phases[phase] || 'Выберите адаптер и нажмите Save.') + (state.error ? '\n' + state.error : '');
  } catch (e) {
    select.disabled = save.disabled = true;
    status.textContent = e.message;
  }
}

save.onclick = async () => {
  if (busy) return;
  busy = true; select.disabled = save.disabled = true;
  try {
    const ctx = await getContext();
    const model = select.value;
    if (!models.includes(model) || !models.includes(current)) throw new Error('Недопустимый адаптер.');
    if (model === current) { status.textContent = 'Этот адаптер уже выбран.'; return; }
    // All shell arguments are fixed identifiers, never URLs, paths or free text.
    const cmd = 'python Tools/select_provider.py --channel ' + ctx.channel +
      ' --provider ' + model + ' --expected ' + current;
    status.textContent = 'Сохраняю запрос…';
    const r = await post(ctx, '/run', {cmd, cwd:'.', timeout:15}, 20000);
    const result = JSON.parse((r.stdout || '').trim());
    if (!result.ok) throw new Error(result.error || 'Запрос отклонён.');
    if (result.phase === 'queued') {
      const s = await chrome.storage.local.get({pausedQueue:[], providerQueueArchive:[]});
      if (s.pausedQueue.length) {
        await chrome.storage.local.set({pausedQueue:[], providerQueueArchive:
          s.providerQueueArchive.concat([{nonce:result.nonce, from:current, actions:s.pausedQueue}])});
      }
    }
    dirty = false;
    status.textContent = phases[result.phase] || result.phase;
  } catch (e) { status.textContent = 'Save: ' + e.message; }
  finally { busy = false; select.disabled = save.disabled = false; }
};
chrome.storage.onChanged.addListener(() => { if (!busy) refresh(); });
refresh();
setInterval(refresh, 3000);
