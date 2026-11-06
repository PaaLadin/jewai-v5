(() => {
  // Experimental selectors: fail closed when assistant ownership is unknown.
  const visible = el => !!el && el.getClientRects().length > 0;
  const input = [...document.querySelectorAll(
    'textarea, [contenteditable="true"][role="textbox"], #ask-input[contenteditable="true"]'
  )].find(visible);
  const value = el => !el ? '' : (el.value === undefined ? el.innerText : el.value);
  const busy = [...document.querySelectorAll('button[aria-label], button[data-testid]')]
    .filter(visible).some(el => /^(stop|stop generating|stop response|остановить|остановить генерацию)$/i
      .test((el.getAttribute('aria-label') || '').trim()) ||
      /^(stop-generating|stop-generation|stop-response)$/.test(el.getAttribute('data-testid') || ''));
  const selectors = [
    '[data-message-author-role="assistant"]',
    '[data-role="assistant"]',
    '[data-testid="assistant-message"]'
  ];
  let messages = [];
  for (const sel of selectors) {
    messages = [...document.querySelectorAll(sel)].filter(visible);
    if (messages.length) break;
  }
  // No generic .prose/main fallback: citations and user text are not commands.
  const answers = messages.map(el => {
    const pre = [...el.querySelectorAll('pre')];
    return pre.length ? pre.map(p => p.innerText || p.textContent || '').join('\n')
                      : (el.innerText || el.textContent || '');
  });
  return {url: location.href, input: !!input, draft: value(input), busy,
          supported: messages.length > 0, answers};
})()
