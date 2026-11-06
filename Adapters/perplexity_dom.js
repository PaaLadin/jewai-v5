(() => {
  const cfg = __JEWAI_SELECTORS__;
  const visible = el => !!el && el.getClientRects().length > 0;
  const editable = el => visible(el) && !el.disabled && !el.readOnly &&
    el.getAttribute('aria-disabled') !== 'true' && !el.closest(cfg.exclude);
  let input = null;
  for (const selector of cfg.inputs) {
    input = [...document.querySelectorAll(selector)].find(editable);
    if (input) break;
  }
  const busy = [...document.querySelectorAll(cfg.stop)].filter(visible).some(el =>
    /^(stop|stop generating|stop response|stop model response|остановить|остановить генерацию)$/i
      .test((el.getAttribute('aria-label') || '').trim()) ||
    /^(stop-generating|stop-generation|stop-response|stop-generating-response-button)$/
      .test(el.getAttribute('data-testid') || ''));
  const roots = [...document.querySelectorAll(cfg.container)].filter(visible);
  const found = [...new Set(roots.flatMap(root => [...root.querySelectorAll(cfg.answer)]))]
    .filter(el => visible(el) && !el.closest(cfg.exclude));
  const messages = found.filter(el => !found.some(other => other !== el && other.contains(el)));
  const answers = messages.map(el => {
    const pres = [...el.querySelectorAll('pre')].filter(p => !p.closest(cfg.exclude));
    return pres.length ? pres.map(p => p.innerText || p.textContent || '').join('\n')
                       : (el.innerText || el.textContent || '');
  });
  return {url: location.href, input: !!input,
          draft: !input ? '' : (input.value === undefined ? input.innerText : input.value),
          busy, supported: roots.length > 0 && messages.length > 0, answers};
})()
