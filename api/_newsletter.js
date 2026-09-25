// Shared helpers for /api/subscribe and /api/unsubscribe (files starting with "_" are not routes on Vercel).
// Welcome email (Brevo transactional API) + HMAC-signed unsubscribe links + small localized pages.
// The Brevo key is read ONLY from process.env.BREVO_API_KEY and never sent to the browser or logged.
'use strict';

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const SITE = {
  "brand": "Devon México",
  "wordmark": "DEVON",
  "sub": "MÉXICO Y LATINOAMÉRICA",
  "subscribePath": "/newsletter.html",
  "welcome": {
    "subject": "Bienvenido a Devon México: esto es lo último",
    "title": "Bienvenido a Devon México",
    "line": "Gracias por suscribirte. Cada mañana te enviaremos lo nuevo de Devon México; para empezar, aquí está nuestra edición más reciente.",
    "preheader": "Gracias por suscribirte: esta es la edición más reciente de Devon México.",
    "fallback": "Muy pronto recibirás nuestra próxima edición con lo mejor de moda, belleza y cultura. Mientras tanto, descubre lo último en Devon México.",
    "visit": "Visitar Devon México",
    "why": "Recibes este correo porque te suscribiste al newsletter de Devon México en devonrevista.vercel.app.",
    "unsub": "Darse de baja"
  },
  "key": "devon-mx",
  "listId": 4,
  "domain": "https://devonrevista.vercel.app",
  "lang": "es",
  "senderName": "Devon México",
  "senderEmail": "stadeereck@gmail.com",
  "logo": null
};
const BREVO = 'https://api.brevo.com/v3';

const PAGE_COPY = {
  es: {
    doneTitle: 'Te diste de baja', done: 'Ya no recibirás el newsletter de {brand} en {email}.',
    again: '¿Fue un error? Puedes volver a suscribirte cuando quieras.', back: 'Volver a {brand}', resub: 'Volver a suscribirme',
    badTitle: 'Enlace no válido', bad: 'Este enlace para darte de baja no es válido o está incompleto. Usa el enlace del último correo que recibiste de {brand}.',
    errTitle: 'Algo salió mal', err: 'No pudimos procesar tu solicitud. Inténtalo de nuevo en unos minutos.',
  },
  en: {
    doneTitle: 'You’re unsubscribed', done: 'You will no longer receive the {brand} newsletter at {email}.',
    again: 'Changed your mind? You can resubscribe anytime.', back: 'Back to {brand}', resub: 'Resubscribe',
    badTitle: 'Invalid link', bad: 'This unsubscribe link is invalid or incomplete. Please use the link in the latest email you received from {brand}.',
    errTitle: 'Something went wrong', err: 'We couldn’t process your request. Please try again in a few minutes.',
  },
  ko: {
    doneTitle: '구독이 해지되었습니다', done: '{email} 주소로 더 이상 {brand} 뉴스레터가 발송되지 않습니다.',
    again: '실수로 해지하셨나요? 언제든지 다시 구독하실 수 있습니다.', back: '{brand} 홈으로', resub: '다시 구독하기',
    badTitle: '유효하지 않은 링크입니다', bad: '수신 거부 링크가 올바르지 않거나 불완전합니다. 최근에 받은 {brand} 메일의 링크를 이용해 주세요.',
    errTitle: '문제가 발생했습니다', err: '요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.',
  },
};

const SERIF = "Georgia,'Times New Roman',Times,serif";
const SANS = SITE.lang === 'ko'
  ? "'Apple SD Gothic Neo','Malgun Gothic','Noto Sans KR',Helvetica,Arial,sans-serif"
  : "'Helvetica Neue',Helvetica,Arial,sans-serif";

function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
function fmt(s, vars) { return String(s).replace(/\{(\w+)\}/g, (m, k) => (k in vars ? vars[k] : m)); }

async function brevo(p, init, timeoutMs) {
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), timeoutMs || 8000);
  try {
    const r = await fetch(BREVO + p, Object.assign({}, init, {
      signal: ctl.signal,
      headers: { 'api-key': process.env.BREVO_API_KEY, accept: 'application/json', 'content-type': 'application/json' },
    }));
    const text = await r.text();
    let data = null;
    if (text) { try { data = JSON.parse(text); } catch (e) { data = { message: text.slice(0, 200) }; } }
    return { status: r.status, ok: r.ok, data };
  } finally { clearTimeout(timer); }
}

// ---------------------------------------------------------------- unsubscribe tokens
function secret() {
  if (process.env.UNSUBSCRIBE_SECRET) return process.env.UNSUBSCRIBE_SECRET;
  return crypto.createHmac('sha256', String(process.env.BREVO_API_KEY || '')).update('devon-unsubscribe-v1').digest('hex');
}
function token(email) {
  return crypto.createHmac('sha256', secret()).update('unsub:' + SITE.key + ':' + String(email).trim().toLowerCase())
    .digest('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '').slice(0, 32);
}
function verify(email, t) {
  if (!email || !t || !process.env.BREVO_API_KEY) return false;
  const a = Buffer.from(token(email));
  const b = Buffer.from(String(t));
  return a.length === b.length && crypto.timingSafeEqual(a, b);
}
function unsubscribeUrl(email) {
  return SITE.domain + '/api/unsubscribe?e=' + encodeURIComponent(String(email).trim().toLowerCase()) + '&t=' + token(email);
}

// ---------------------------------------------------------------- latest edition
async function readLatest(host) {
  // 1) file bundled with this deployment; 2) same deployment over HTTP; 3) production domain.
  try {
    const html = fs.readFileSync(path.join(process.cwd(), 'newsletter', 'latest.html'), 'utf8');
    let meta = {};
    try { meta = JSON.parse(fs.readFileSync(path.join(process.cwd(), 'newsletter', 'latest.json'), 'utf8')); } catch (e) {}
    if (html && html.length > 500) return { html, meta, source: 'bundle' };
  } catch (e) { /* not bundled */ }
  const bases = [];
  if (host && /^[a-z0-9.-]+(:\d+)?$/i.test(host)) bases.push('https://' + host);
  if (!bases.includes(SITE.domain)) bases.push(SITE.domain);
  for (const base of bases) {
    const ctl = new AbortController();
    const timer = setTimeout(() => ctl.abort(), 4000);
    try {
      const r = await fetch(base + '/newsletter/latest.html', { signal: ctl.signal, headers: { 'cache-control': 'no-cache' } });
      const html = r.ok ? await r.text() : '';
      if (html && html.length > 500 && /<html/i.test(html)) return { html, meta: {}, source: base };
    } catch (e) { /* try next */ } finally { clearTimeout(timer); }
  }
  return null;
}

function welcomeRow() {
  const w = SITE.welcome;
  return '<tr><td class="px" style="padding:30px 30px 8px 30px;">' +
    '<div style="font-family:' + (SITE.lang === 'ko' ? SANS : SERIF) + ';font-size:26px;line-height:1.25;color:#000;margin:0 0 12px 0;">' + esc(w.title) + '</div>' +
    '<div style="font-family:' + SANS + ';font-size:15px;line-height:1.6;color:#444;margin:0 0 4px 0;">' + esc(w.line) + '</div>' +
    '</td></tr>';
}

function logoHtml() {
  if (SITE.logo) {
    return '<a href="' + esc(SITE.domain) + '" style="text-decoration:none;"><img src="' + esc(SITE.logo) + '" alt="' + esc(SITE.brand) +
      '" width="150" style="display:block;margin:0 auto;width:150px;max-width:150px;height:auto;border:0;"></a>';
  }
  return '<a href="' + esc(SITE.domain) + '" style="text-decoration:none;color:#000;"><span style="font-family:' + SERIF +
    ';font-size:44px;line-height:1;letter-spacing:10px;font-weight:700;color:#000;">' + esc(SITE.wordmark || SITE.brand) + '</span></a>' +
    (SITE.sub ? '<div style="font-family:' + SANS + ';font-size:10px;letter-spacing:3px;color:#000;margin-top:8px;">' + esc(SITE.sub) + '</div>' : '');
}

function genericWelcome(unsub) {
  const w = SITE.welcome;
  return '<!DOCTYPE html><html lang="' + SITE.lang + '"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' +
    '<title>' + esc(w.subject) + '</title></head><body style="margin:0;padding:0;background:#f4f4f4;">' +
    '<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:#f4f4f4;">' + esc(w.preheader) + '</div>' +
    '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f4f4f4;"><tr><td align="center" style="padding:24px 10px;">' +
    '<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="width:600px;max-width:600px;background:#ffffff;">' +
    '<tr><td align="center" style="padding:28px 30px 22px 30px;border-bottom:1px solid #000;">' + logoHtml() + '</td></tr>' +
    welcomeRow() +
    '<tr><td style="padding:14px 30px 34px 30px;"><div style="font-family:' + SANS + ';font-size:15px;line-height:1.6;color:#444;margin:0 0 20px 0;">' + esc(w.fallback) + '</div>' +
    '<a href="' + esc(SITE.domain) + '" style="display:inline-block;background:#000;color:#fff;font-family:' + SANS + ';font-size:11px;letter-spacing:3px;font-weight:700;text-transform:uppercase;text-decoration:none;padding:14px 26px;">' + esc(w.visit) + '</a></td></tr>' +
    '<tr><td align="center" style="background:#000;padding:30px;">' +
    '<div style="font-family:' + SANS + ';font-size:11px;line-height:1.6;color:#999;">' + esc(w.why) + '</div>' +
    '<div style="font-family:' + SANS + ';font-size:11px;line-height:1.6;margin-top:10px;"><a href="' + esc(unsub) + '" style="color:#fff;text-decoration:underline;">' + esc(w.unsub) + '</a></div>' +
    '</td></tr></table></td></tr></table></body></html>';
}

function buildWelcome(latest, email) {
  const w = SITE.welcome;
  const unsub = unsubscribeUrl(email);
  if (!latest || !latest.html) return { html: genericWelcome(unsub), unsub, source: 'generic' };
  let html = latest.html;
  const row = welcomeRow();
  if (html.includes('<!--WELCOME-->')) html = html.replace('<!--WELCOME-->', row);
  else return { html: genericWelcome(unsub), unsub, source: 'generic' };
  // personalised unsubscribe link (latest.html carries a plain placeholder link to /api/unsubscribe)
  const plain = SITE.domain + '/api/unsubscribe';
  html = html.split('href="' + plain + '"').join('href="' + esc(unsub) + '"');
  html = html.replace(/<title>[\s\S]*?<\/title>/i, '<title>' + esc(w.subject) + '</title>');
  html = html.replace(/(<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:#f4f4f4;">)[^<]*/i, '$1' + esc(w.preheader));
  return { html, unsub, source: latest.source || 'latest' };
}

async function sendWelcome(email, host) {
  const latest = await readLatest(host);
  const built = buildWelcome(latest, email);
  const r = await brevo('/smtp/email', {
    method: 'POST',
    body: JSON.stringify({
      sender: { name: SITE.senderName, email: SITE.senderEmail },
      to: [{ email }],
      subject: SITE.welcome.subject,
      htmlContent: built.html,
      tags: ['welcome-' + SITE.key],
      headers: { 'List-Unsubscribe': '<' + built.unsub + '>', 'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click' },
    }),
  }, 10000);
  return { ok: r.ok, status: r.status, messageId: r.data && r.data.messageId, code: r.data && r.data.code, source: built.source };
}

// ---------------------------------------------------------------- pages
function page(kind, email) {
  const c = PAGE_COPY[SITE.lang] || PAGE_COPY.es;
  const vars = { brand: esc(SITE.brand), email: '<strong>' + esc(email || '') + '</strong>' };
  const title = kind === 'done' ? c.doneTitle : kind === 'bad' ? c.badTitle : c.errTitle;
  const body = fmt(esc(kind === 'done' ? c.done : kind === 'bad' ? c.bad : c.err), vars);
  const extra = kind === 'done'
    ? '<p class="muted">' + esc(c.again) + '</p><p class="actions"><a class="btn" href="' + esc(SITE.domain) + '/">' + esc(fmt(c.back, { brand: SITE.brand })) +
      '</a><a class="link" href="' + esc(SITE.domain + SITE.subscribePath) + '">' + esc(c.resub) + '</a></p>'
    : '<p class="actions"><a class="btn" href="' + esc(SITE.domain) + '/">' + esc(fmt(c.back, { brand: SITE.brand })) + '</a></p>';
  const logo = SITE.logo
    ? '<a href="' + esc(SITE.domain) + '/"><img src="' + esc(SITE.logo) + '" alt="' + esc(SITE.brand) + '" width="150" style="width:150px;height:auto;border:0;"></a>'
    : '<a class="wordmark" href="' + esc(SITE.domain) + '/">' + esc(SITE.wordmark || SITE.brand) + '</a>' + (SITE.sub ? '<div class="sub">' + esc(SITE.sub) + '</div>' : '');
  return '<!DOCTYPE html><html lang="' + SITE.lang + '"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' +
    '<meta name="robots" content="noindex"><title>' + esc(title) + ' · ' + esc(SITE.brand) + '</title><style>' +
    'body{margin:0;background:#f4f4f4;color:#111;font-family:' + SANS + ';}' +
    '.card{max-width:560px;margin:48px auto;background:#fff;padding:0 0 40px;text-align:center;}' +
    'header{padding:34px 24px 24px;border-bottom:1px solid #000;margin-bottom:34px;}' +
    '.wordmark{font-family:' + SERIF + ';font-size:44px;letter-spacing:10px;font-weight:700;color:#000;text-decoration:none;}' +
    '.sub{font-size:10px;letter-spacing:3px;margin-top:8px;}' +
    'h1{font-family:' + (SITE.lang === 'ko' ? SANS : SERIF) + ';font-weight:400;font-size:30px;margin:0 32px 16px;}' +
    'p{font-size:15px;line-height:1.6;color:#444;margin:0 36px 14px;}p.muted{color:#777;font-size:14px;}' +
    '.actions{margin-top:28px;}.btn{display:inline-block;background:#000;color:#fff;text-decoration:none;font-size:11px;letter-spacing:3px;font-weight:700;text-transform:uppercase;padding:14px 26px;margin:6px;}' +
    '.link{display:inline-block;color:#000;font-size:11px;letter-spacing:2px;font-weight:700;text-transform:uppercase;text-decoration:none;border-bottom:1px solid #000;margin:6px 12px;}' +
    '@media(max-width:600px){.card{margin:0;min-height:100vh;}}' +
    '</style></head><body><main class="card"><header>' + logo + '</header><h1>' + esc(title) + '</h1><p>' + body + '</p>' + extra + '</main></body></html>';
}

module.exports = { SITE, brevo, token, verify, unsubscribeUrl, readLatest, buildWelcome, sendWelcome, page, esc };
