import {
  commonSecurityHeaders,
  corsHeaders,
  forbiddenIfBadOrigin,
  json,
  normalizeText,
  preflight,
  rateLimit,
} from './_shared.js';

export const onRequestOptions = ({ request }) => preflight(request);

async function readBrevoError(response) {
  const text = await response.text();
  let data = {};
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { message: text };
    }
  }

  return {
    status: response.status,
    code: data.code || String(response.status),
    message: data.message || response.statusText || 'Brevo request failed',
    details: data,
  };
}

function brevoErrorResponse(error, cors) {
  return json({ error: error.message, brevo: error }, { status: error.status || 502, headers: cors });
}

export async function onRequestPost({ request, env }) {
  const cors = corsHeaders(request);
  const forbidden = forbiddenIfBadOrigin(request);
  if (forbidden) return forbidden;

  const rl = rateLimit(request, 'subscribe', 10, 10 * 60 * 1000);
  if (rl.limited) {
    return json({ error: 'Too many requests' }, {
      status: 429,
      headers: { ...cors, 'Retry-After': String(rl.retryAfter) },
    });
  }

  let body;
  try {
    body = await request.json();
  } catch {
    body = {};
  }
  const name = normalizeText(body.name, 120);
  const email = typeof body.email === 'string' ? body.email.trim().toLowerCase() : '';
  const lang = normalizeText(body.lang, 10);
  const sourceUrl = typeof body.source_url === 'string' ? body.source_url.slice(0, 500) : '';
  const file = typeof body.file === 'string' ? body.file.slice(0, 300) : '';
  if (!email) return json({ error: 'Email required' }, { status: 400, headers: cors });
  if (email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return json({ error: 'Invalid email' }, { status: 400, headers: cors });
  }
  if (body.name && !name) return json({ error: 'Invalid name' }, { status: 400, headers: cors });
  if (body.lang && !lang) return json({ error: 'Invalid language' }, { status: 400, headers: cors });

  const listId = parseInt(env.BREVO_LIST_ID || '2');
  const apiKey = env.BREVO_API_KEY;

  try {
    const response = await fetch('https://api.brevo.com/v3/contacts', {
      method: 'POST',
      headers: { 'api-key': apiKey, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email,
        attributes: {
          FIRSTNAME: name || '',
          LANG: lang || 'en',
          SOURCE_URL: sourceUrl,
          SOURCE: 'site',
          ...(file ? { LAST_DOWNLOAD: file, LAST_DOWNLOAD_AT: new Date().toISOString() } : {}),
        },
        listIds: [listId],
        updateEnabled: true,
      }),
    });

    const isNew = response.ok || response.status === 204;
    let alreadyExists = false;
    if (!isNew) {
      const brevoError = await readBrevoError(response);
      if (brevoError.code === 'duplicate_parameter') alreadyExists = true;
      else return brevoErrorResponse(brevoError, cors);
    }

    return json({ success: true, already: alreadyExists }, { headers: cors });
  } catch {
    return json({ error: 'Server error' }, { status: 500, headers: cors });
  }
}

export function onRequest({ request }) {
  return new Response('Method not allowed', {
    status: 405,
    headers: { ...commonSecurityHeaders(), ...corsHeaders(request) },
  });
}
