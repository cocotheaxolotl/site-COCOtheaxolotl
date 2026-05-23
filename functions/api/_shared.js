const ipHits = new Map();

export const ALLOWED_ORIGINS = new Set([
  'https://cocotheaxolotl.org',
  'https://www.cocotheaxolotl.org',
  'http://localhost:3000',
  'http://127.0.0.1:3000',
]);

export function commonSecurityHeaders() {
  return {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Cache-Control': 'no-store',
  };
}

export function corsHeaders(request, methods = 'POST, OPTIONS') {
  const out = {
    'Access-Control-Allow-Methods': methods,
    'Access-Control-Allow-Headers': 'Content-Type',
  };
  const origin = request.headers.get('Origin') || '';
  if (origin && ALLOWED_ORIGINS.has(origin)) {
    out['Access-Control-Allow-Origin'] = origin;
    out['Vary'] = 'Origin';
  }
  return out;
}

export function getClientIp(request) {
  const fwd = request.headers.get('CF-Connecting-IP') || request.headers.get('X-Forwarded-For') || '';
  if (fwd) return fwd.split(',')[0].trim();
  return 'unknown';
}

export function rateLimit(request, keyPrefix, limit, windowMs) {
  const now = Date.now();
  for (const [k, v] of ipHits.entries()) {
    if (v.resetAt <= now) ipHits.delete(k);
  }
  const key = `${keyPrefix}:${getClientIp(request)}`;
  const cur = ipHits.get(key);
  if (!cur || cur.resetAt <= now) {
    ipHits.set(key, { count: 1, resetAt: now + windowMs });
    return { limited: false };
  }
  cur.count += 1;
  if (cur.count > limit) {
    const retryAfter = Math.max(1, Math.ceil((cur.resetAt - now) / 1000));
    return { limited: true, retryAfter };
  }
  return { limited: false };
}

export function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

export function normalizeText(value, maxLength) {
  if (typeof value !== 'string') return '';
  return value.trim().replace(/\s+/g, ' ').slice(0, maxLength);
}

export function safeCompare(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string') return false;
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

export function json(data, init = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...commonSecurityHeaders(),
    ...(init.headers || {}),
  };
  return new Response(JSON.stringify(data), { status: init.status || 200, headers });
}

export function preflight(request) {
  return new Response(null, {
    status: 204,
    headers: { ...commonSecurityHeaders(), ...corsHeaders(request) },
  });
}

export function forbiddenIfBadOrigin(request) {
  const origin = request.headers.get('Origin') || '';
  if (origin && !ALLOWED_ORIGINS.has(origin)) {
    return json({ error: 'Forbidden origin' }, { status: 403, headers: corsHeaders(request) });
  }
  return null;
}

async function hmacHex(secret, payload) {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    'raw',
    enc.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );
  const sig = await crypto.subtle.sign('HMAC', key, enc.encode(payload));
  return [...new Uint8Array(sig)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

export async function signSessionValue(secret, ttlSeconds) {
  const expiresAt = Date.now() + ttlSeconds * 1000;
  const nonceBytes = crypto.getRandomValues(new Uint8Array(16));
  const nonce = [...nonceBytes].map((b) => b.toString(16).padStart(2, '0')).join('');
  const payload = `${expiresAt}.${nonce}`;
  const signature = await hmacHex(secret, payload);
  return `${payload}.${signature}`;
}

export async function verifySessionValue(value, secret) {
  if (!value || !secret) return false;
  const parts = value.split('.');
  if (parts.length !== 3) return false;
  const [expiresAtRaw, nonce, signature] = parts;
  if (!/^\d+$/.test(expiresAtRaw) || !/^[a-f0-9]{32}$/i.test(nonce) || !/^[a-f0-9]{64}$/i.test(signature)) {
    return false;
  }
  const payload = `${expiresAtRaw}.${nonce}`;
  const expected = await hmacHex(secret, payload);
  if (!safeCompare(signature, expected)) return false;
  return Number(expiresAtRaw) > Date.now();
}
