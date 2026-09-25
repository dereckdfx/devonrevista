// Vercel serverless function: POST /api/subscribe  {email, list, website?}
// Adds/updates the contact in the site's Brevo list. The Brevo key is read ONLY from
// process.env.BREVO_API_KEY (Vercel project env var) and never sent to the browser.
// No dependencies (Node 18+ global fetch).
'use strict';

const SITE_KEY = 'devon-mx';           // value the page sends as "list"
const LIST_NAME = 'Devon MX';         // Brevo list name (looked up if no id is configured)
const LIST_ID = null;               // Brevo list id (null => BREVO_LIST_ID env or lookup by name)
const BREVO = 'https://api.brevo.com/v3';
const EMAIL_RE = /^[^\s@<>()[\]\\,;:"']+@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*\.[A-Za-z]{2,}$/;

let cachedListId = null;

async function brevo(path, init) {
  const r = await fetch(BREVO + path, Object.assign({}, init, {
    headers: {
      'api-key': process.env.BREVO_API_KEY,
      accept: 'application/json',
      'content-type': 'application/json',
    },
  }));
  const text = await r.text();
  let data = null;
  if (text) { try { data = JSON.parse(text); } catch (e) { data = { message: text.slice(0, 200) }; } }
  return { status: r.status, ok: r.ok, data };
}

async function resolveListId() {
  const envId = parseInt(process.env.BREVO_LIST_ID || '', 10);
  if (envId > 0) return envId;
  if (LIST_ID) return LIST_ID;
  if (cachedListId) return cachedListId;
  for (let offset = 0; offset < 1000; offset += 50) {
    const r = await brevo('/contacts/lists?limit=50&offset=' + offset + '&sort=desc');
    if (!r.ok) { console.error('brevo list lookup failed', r.status, r.data && r.data.code); return null; }
    const lists = (r.data && r.data.lists) || [];
    const hit = lists.find((l) => String(l.name || '').trim().toLowerCase() === LIST_NAME.toLowerCase());
    if (hit) { cachedListId = hit.id; return hit.id; }
    if (lists.length < 50) break;
  }
  return null;
}

async function readBody(req) {
  if (req.body && typeof req.body === 'object') return req.body;
  let raw = typeof req.body === 'string' ? req.body : '';
  if (!raw) {
    raw = await new Promise((resolve) => {
      let s = '';
      req.on('data', (c) => { s += c; if (s.length > 1e4) req.destroy(); });
      req.on('end', () => resolve(s));
      req.on('error', () => resolve(''));
    });
  }
  try { return JSON.parse(raw || '{}'); } catch (e) {
    const out = {};
    for (const [k, v] of new URLSearchParams(raw)) out[k] = v;
    return out;
  }
}

function send(res, status, obj) {
  res.statusCode = status;
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  res.end(JSON.stringify(obj));
}

module.exports = async function handler(req, res) {
  if (req.method === 'OPTIONS') { res.setHeader('Allow', 'POST, OPTIONS'); res.statusCode = 204; return res.end(); }
  if (req.method !== 'POST') { res.setHeader('Allow', 'POST, OPTIONS'); return send(res, 405, { ok: false, error: 'method_not_allowed' }); }

  const body = await readBody(req);
  // Honeypot: bots fill the hidden "website" field. Pretend success, do nothing.
  if (body.website || body.company || body.url) return send(res, 200, { ok: true });

  const email = String(body.email || '').trim().toLowerCase();
  if (!email || email.length > 254 || !EMAIL_RE.test(email)) return send(res, 400, { ok: false, error: 'invalid_email' });
  if (body.list && String(body.list) !== SITE_KEY) return send(res, 400, { ok: false, error: 'invalid_list' });

  if (!process.env.BREVO_API_KEY) { console.error('BREVO_API_KEY is not set'); return send(res, 503, { ok: false, error: 'not_configured' }); }

  try {
    const listId = await resolveListId();
    if (!listId) return send(res, 503, { ok: false, error: 'list_not_found' });
    const r = await brevo('/contacts', {
      method: 'POST',
      body: JSON.stringify({ email, listIds: [listId], updateEnabled: true }),
    });
    if (r.ok) return send(res, 200, { ok: true, status: r.status === 201 ? 'created' : 'updated' });
    const code = (r.data && r.data.code) || '';
    console.error('brevo contact upsert failed', r.status, code);
    if (r.status === 400 && /email/i.test(String(r.data && r.data.message))) return send(res, 400, { ok: false, error: 'invalid_email' });
    return send(res, 502, { ok: false, error: 'provider_error' });
  } catch (e) {
    console.error('subscribe error', e && e.message);
    return send(res, 502, { ok: false, error: 'provider_error' });
  }
};
