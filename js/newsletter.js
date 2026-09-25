/* Newsletter signup (Brevo via /api/subscribe). No secrets here: the key lives only in the
   Vercel serverless function. Handles every newsletter form on the page:
   - <form data-newsletter> or any form with an <input type="email"> (search forms ignored)
   - elements with [data-newsletter-open] (and site-specific triggers) open a signup modal. */
(function () {
  'use strict';
  var CFG = {"list": "devon-mx", "lang": "es", "brand": "DEVON", "storageKey": "devonNewsletterSubscribed", "modalTitle": {"es": "Devon más cerca de ti: ¡Suscríbete!"}, "endpoint": "/api/subscribe"};
  var T = {
    es: { sending: 'Enviando…', ok: '¡Gracias por suscribirte! Revisa tu bandeja de entrada.', invalid: 'Ingresa un correo electrónico válido.',
          error: 'No pudimos completar tu suscripción. Inténtalo de nuevo en unos minutos.', placeholder: 'Tu correo electrónico',
          button: 'Suscribirme', title: CFG.modalTitle && CFG.modalTitle.es || '¡Suscríbete al newsletter!',
          dek: CFG.modalDek && CFG.modalDek.es || 'Lo mejor de moda, belleza y cultura, directo en tu email cada mañana.', close: 'Cerrar' },
    en: { sending: 'Sending…', ok: 'Thanks for subscribing! Check your inbox.', invalid: 'Please enter a valid email address.',
          error: 'We couldn’t complete your signup. Please try again in a few minutes.', placeholder: 'Your email address',
          button: 'Sign up', title: CFG.modalTitle && CFG.modalTitle.en || 'Sign up for the newsletter',
          dek: CFG.modalDek && CFG.modalDek.en || 'The best of fashion, beauty and culture in your inbox every morning.', close: 'Close' },
    ko: { sending: '전송 중…', ok: '구독해 주셔서 감사합니다! 받은편지함을 확인해 주세요.', invalid: '올바른 이메일 주소를 입력해 주세요.',
          error: '구독을 완료하지 못했습니다. 잠시 후 다시 시도해 주세요.', placeholder: '이메일 주소',
          button: '구독하기', title: CFG.modalTitle && CFG.modalTitle.ko || '뉴스레터 구독',
          dek: CFG.modalDek && CFG.modalDek.ko || '패션, 뷰티, 컬처의 최신 소식을 매일 아침 이메일로 받아보세요.', close: '닫기' }
  };
  var EMAIL_RE = /^[^\s@<>()[\]\\,;:"']+@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*\.[A-Za-z]{2,}$/;

  function langFor(el) {
    var l = (el && el.closest && el.closest('[data-lang]') && el.closest('[data-lang]').getAttribute('data-lang')) ||
            CFG.lang || (document.documentElement.lang || 'es');
    l = String(l).slice(0, 2).toLowerCase();
    return T[l] ? l : 'es';
  }
  function isNewsletterForm(f) {
    if (!f || f.tagName !== 'FORM') return false;
    if (f.hasAttribute('data-newsletter')) return true;
    return !!f.querySelector('input[type="email"]');
  }
  function addHoneypot(f) {
    if (f.querySelector('input[name="website"]')) return;
    var hp = document.createElement('input');
    hp.type = 'text'; hp.name = 'website'; hp.tabIndex = -1; hp.autocomplete = 'off';
    hp.setAttribute('aria-hidden', 'true');
    hp.style.cssText = 'position:absolute!important;left:-10000px!important;top:auto!important;width:1px!important;height:1px!important;overflow:hidden!important;opacity:0!important;';
    f.appendChild(hp);
  }
  function msgEl(f) {
    var id = f.getAttribute('data-nl-msg');
    var el = id && document.getElementById(id);
    if (!el) {
      el = document.createElement('p');
      el.id = 'nl-msg-' + Math.random().toString(36).slice(2, 9);
      el.setAttribute('role', 'status'); el.setAttribute('aria-live', 'polite');
      el.className = 'nl-msg';
      el.style.cssText = 'margin:8px 0 12px;font-size:13px;line-height:1.5;font-family:inherit;';
      f.setAttribute('data-nl-msg', el.id);
      f.parentNode.insertBefore(el, f.nextSibling);
      try {
        var cs = window.getComputedStyle(f);
        if (cs.maxWidth && cs.maxWidth !== 'none') el.style.maxWidth = cs.maxWidth;
        if (cs.marginLeft !== '0px' && cs.marginLeft === cs.marginRight) { el.style.marginLeft = 'auto'; el.style.marginRight = 'auto'; }
      } catch (e) {}
    }
    return el;
  }
  function show(f, text, kind) {
    var el = msgEl(f);
    el.textContent = text;
    el.style.color = kind === 'error' ? '#b00020' : (f.getAttribute('data-nl-dark') ? '#fff' : '#111');
    el.style.fontWeight = kind === 'ok' ? '600' : '400';
  }
  function submit(f) {
    var t = T[langFor(f)];
    var input = f.querySelector('input[type="email"]') || f.querySelector('input[name="email"]');
    var email = input ? String(input.value || '').trim() : '';
    if (!EMAIL_RE.test(email)) { show(f, t.invalid, 'error'); if (input) input.focus(); return; }
    var hp = f.querySelector('input[name="website"]');
    var btn = f.querySelector('button[type="submit"], button:not([type]), input[type="submit"]');
    var label = btn ? (btn.tagName === 'INPUT' ? btn.value : btn.innerHTML) : '';
    if (btn) { btn.disabled = true; btn.style.opacity = '0.6'; }
    show(f, t.sending, 'info');
    fetch(CFG.endpoint || '/api/subscribe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email, list: CFG.list, website: hp ? hp.value : '' })
    }).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (d) { return { ok: r.ok && d && d.ok, d: d || {} }; });
    }).then(function (res) {
      if (res.ok) {
        show(f, t.ok, 'ok');
        if (input) input.value = '';
        try { localStorage.setItem(CFG.storageKey || 'newsletterSubscribed', 'true'); } catch (e) {}
        var ev; try { ev = new CustomEvent('newsletter:success', { bubbles: true, detail: { email: email } }); } catch (e) { ev = document.createEvent('Event'); ev.initEvent('newsletter:success', true, true); }
        f.dispatchEvent(ev);
      } else {
        show(f, res.d.error === 'invalid_email' ? t.invalid : t.error, 'error');
      }
    }).catch(function () {
      show(f, t.error, 'error');
    }).then(function () {
      if (btn) { btn.disabled = false; btn.style.opacity = ''; if (btn.tagName === 'INPUT') btn.value = label; else btn.innerHTML = label; }
    });
  }

  // Capture phase on document runs before inline onsubmit handlers on the form, so legacy
  // "onsubmit=... redirect" attributes never fire for newsletter forms.
  document.addEventListener('submit', function (e) {
    var f = e.target;
    if (!isNewsletterForm(f)) return;
    e.preventDefault();
    e.stopImmediatePropagation();
    e.stopPropagation();
    submit(f);
  }, true);

  /* ---------- Modal ---------- */
  var modal = null;
  function buildModal() {
    var t = T[langFor(document.body)];
    var wrap = document.createElement('div');
    wrap.id = 'nl-modal';
    wrap.setAttribute('role', 'dialog'); wrap.setAttribute('aria-modal', 'true'); wrap.setAttribute('aria-labelledby', 'nl-modal-title');
    wrap.style.cssText = 'position:fixed;inset:0;z-index:2147483000;display:none;align-items:center;justify-content:center;background:rgba(0,0,0,.55);padding:16px;';
    wrap.innerHTML =
      '<div style="background:#fff;color:#111;max-width:460px;width:100%;padding:36px 28px 28px;position:relative;box-shadow:0 20px 60px rgba(0,0,0,.35);text-align:center;">' +
        '<button type="button" data-nl-close aria-label="' + t.close + '" style="position:absolute;top:10px;right:14px;background:none;border:0;font-size:26px;line-height:1;cursor:pointer;color:#111;">&times;</button>' +
        (CFG.logo ? '<img src="' + CFG.logo + '" alt="' + (CFG.brand || '') + '" style="height:56px;width:auto;margin:0 auto 14px;display:block;">'
                  : '<div style="font-family:Georgia,\'Times New Roman\',serif;font-weight:700;letter-spacing:.18em;font-size:30px;margin-bottom:10px;">' + (CFG.brand || '') + '</div>') +
        '<h2 id="nl-modal-title" style="font-family:Georgia,\'Times New Roman\',serif;font-size:24px;line-height:1.25;margin:0 0 10px;font-weight:400;">' + t.title + '</h2>' +
        '<p style="font-size:14px;line-height:1.6;color:#555;margin:0 0 20px;">' + t.dek + '</p>' +
        '<form data-newsletter novalidate style="display:flex;flex-direction:column;gap:10px;margin:0;">' +
          '<input type="email" name="email" required autocomplete="email" placeholder="' + t.placeholder + '" aria-label="' + t.placeholder + '" style="border:1px solid #ccc;padding:14px;font-size:14px;outline:none;border-radius:0;width:100%;box-sizing:border-box;">' +
          '<button type="submit" style="background:#000;color:#fff;border:0;padding:15px;font-size:12px;letter-spacing:.2em;text-transform:uppercase;font-weight:700;cursor:pointer;border-radius:0;">' + t.button + '</button>' +
        '</form>' +
      '</div>';
    document.body.appendChild(wrap);
    addHoneypot(wrap.querySelector('form'));
    wrap.addEventListener('click', function (e) { if (e.target === wrap || (e.target.closest && e.target.closest('[data-nl-close]'))) close(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
    return wrap;
  }
  function open(e) {
    if (e && e.preventDefault) e.preventDefault();
    if (!modal) modal = buildModal();
    modal.style.display = 'flex';
    var i = modal.querySelector('input[type="email"]'); if (i) setTimeout(function () { i.focus(); }, 30);
  }
  function close() { if (modal) modal.style.display = 'none'; }
  window.DevonNewsletter = { open: open, close: close };

  function init() {
    Array.prototype.forEach.call(document.querySelectorAll('form'), function (f) { if (isNewsletterForm(f)) addHoneypot(f); });
    var triggers = Array.prototype.slice.call(document.querySelectorAll('[data-newsletter-open]'));
    if (CFG.triggerTexts && CFG.triggerTexts.length) {
      Array.prototype.forEach.call(document.querySelectorAll('button, a'), function (el) {
        var txt = (el.textContent || '').replace(/\s+/g, ' ').trim();
        if (CFG.triggerTexts.indexOf(txt) !== -1 && triggers.indexOf(el) === -1) triggers.push(el);
      });
    }
    triggers.forEach(function (el) {
      el.addEventListener('click', open);
      if (el.tagName === 'A' && (el.getAttribute('href') || '#') === '#') el.setAttribute('href', '#newsletter');
      el.style.cursor = 'pointer';
    });
    if (location.hash === '#newsletter' && triggers.length) open();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
