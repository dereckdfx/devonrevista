// Vercel serverless function: GET/POST /api/unsubscribe?e=<email>&t=<token>
// Removes the address from this site's Brevo list. The token is an HMAC of the address (see _newsletter.js),
// so a link only works for the address it was issued to. Supports RFC 8058 one-click POST (List-Unsubscribe-Post).
'use strict';

const NL = require('./_newsletter');

function html(res, status, body) {
  res.statusCode = status;
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  res.setHeader('X-Robots-Tag', 'noindex');
  res.end(body);
}

module.exports = async function handler(req, res) {
  if (req.method !== 'GET' && req.method !== 'POST' && req.method !== 'HEAD') {
    res.setHeader('Allow', 'GET, POST');
    return html(res, 405, NL.page('bad', ''));
  }
  const url = new URL(req.url, 'https://x.invalid');
  const email = String(url.searchParams.get('e') || '').trim().toLowerCase();
  const t = String(url.searchParams.get('t') || '').trim();
  if (!email || email.length > 254 || !NL.verify(email, t)) return html(res, 400, NL.page('bad', ''));
  if (req.method === 'HEAD') return html(res, 200, '');

  try {
    const r = await NL.brevo('/contacts/lists/' + NL.SITE.listId + '/contacts/remove', {
      method: 'POST',
      body: JSON.stringify({ emails: [email] }),
    });
    const msg = String((r.data && r.data.message) || '');
    // 404 = contact no longer exists; 400 "already removed / not in list" = nothing to do
    const fine = r.ok || r.status === 404 || (r.status === 400 && /already|not (exist|found|in)|does not/i.test(msg));
    if (!fine) {
      console.error('unsubscribe failed', NL.SITE.key, r.status, (r.data && r.data.code) || '', msg.slice(0, 120));
      return html(res, 502, NL.page('error', email));
    }
    console.log('unsubscribed', NL.SITE.key, 'list', NL.SITE.listId, r.status);
    return html(res, 200, NL.page('done', email));
  } catch (e) {
    console.error('unsubscribe error', NL.SITE.key, e && e.message);
    return html(res, 502, NL.page('error', email));
  }
};
