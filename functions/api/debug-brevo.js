import {
  commonSecurityHeaders,
  corsHeaders,
  forbiddenIfBadOrigin,
  json,
} from './_shared.js';

export function onRequestOptions({ request }) {
  return new Response(null, {
    status: 204,
    headers: { ...commonSecurityHeaders(), ...corsHeaders(request, 'GET, OPTIONS') },
  });
}

export async function onRequestGet({ request, env }) {
  const cors = corsHeaders(request, 'GET, OPTIONS');
  const forbidden = forbiddenIfBadOrigin(request);
  if (forbidden) return forbidden;

  const apiKey = env.BREVO_API_KEY;
  if (!apiKey) {
    return json({ error: 'BREVO_API_KEY missing' }, { status: 500, headers: cors });
  }

  try {
    const response = await fetch('https://api.brevo.com/v3/account', {
      method: 'GET',
      headers: { 'api-key': apiKey, Accept: 'application/json' },
    });
    const body = await response.text();

    return new Response(body, {
      status: response.status,
      headers: {
        ...commonSecurityHeaders(),
        ...cors,
        'Content-Type': response.headers.get('Content-Type') || 'application/json; charset=utf-8',
      },
    });
  } catch (error) {
    return json({ error: error.message || 'Brevo debug request failed' }, { status: 500, headers: cors });
  }
}

export function onRequest({ request }) {
  return new Response('Method not allowed', {
    status: 405,
    headers: { ...commonSecurityHeaders(), ...corsHeaders(request, 'GET, OPTIONS') },
  });
}
