import {
  commonSecurityHeaders,
  corsHeaders,
  escapeHtml,
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
  if (!email) return json({ error: 'Email required' }, { status: 400, headers: cors });
  if (email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return json({ error: 'Invalid email' }, { status: 400, headers: cors });
  }
  if (body.name && !name) return json({ error: 'Invalid name' }, { status: 400, headers: cors });
  if (body.lang && !lang) return json({ error: 'Invalid language' }, { status: 400, headers: cors });

  const listId = parseInt(env.BREVO_LIST_ID || '2');
  const apiKey = env.BREVO_API_KEY;
  const senderEmail = env.BREVO_SENDER_EMAIL || 'coco@cocotheaxolotl.org';
  const senderName = env.BREVO_SENDER_NAME || 'Coco the Axolotl';
  const firstName = escapeHtml(name || 'friend');

  try {
    const response = await fetch('https://api.brevo.com/v3/contacts', {
      method: 'POST',
      headers: { 'api-key': apiKey, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email,
        attributes: { FIRSTNAME: name || '', LANG: lang || 'en' },
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

    if (!alreadyExists) {
      const welcomeHtml = '<!DOCTYPE html><html><head><meta charset="UTF-8"></head>'
        + '<body style="margin:0;padding:0;background:#f8f8f8;font-family:system-ui,-apple-system,Arial,sans-serif">'
        + '<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8f8f8;padding:30px 0"><tr><td align="center">'
        + '<table width="580" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:18px;overflow:hidden;box-shadow:0 4px 15px rgba(0,0,0,.06)">'
        + '<tr><td style="background:#ff69b4;padding:28px 30px;text-align:center">'
        + '<img src="https://cocotheaxolotl.org/axolotl.png" width="80" alt="Coco" style="display:block;margin:0 auto 10px">'
        + '<h1 style="margin:0;color:#fff;font-size:22px">Welcome to Coco\'s world!</h1>'
        + '</td></tr>'
        + '<tr><td style="padding:30px 32px">'
        + '<h2 style="margin:0 0 12px;font-size:20px;text-align:center">Hey ' + firstName + '! You\'re a hero now!</h2>'
        + '<p style="margin:0 0 8px;font-size:16px;line-height:1.6;color:#555;text-align:center">Coco was drawn by Loopinky... but Loopinky forgot to color him in! Now Coco needs <strong>your superpower</strong> to get his colors back.</p>'
        + '<p style="margin:0 0 22px;font-size:16px;line-height:1.6;color:#555;text-align:center">Grab your crayons and start coloring!</p>'
        + '<table width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding-bottom:12px">'
        + '<a href="https://cocotheaxolotl.org/freebies/" style="display:inline-block;padding:14px 36px;background:#ff69b4;color:#fff;text-decoration:none;border-radius:30px;font-weight:800;font-size:16px">Download Free Coloring Pages</a>'
        + '</td></tr></table>'
        + '<table width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding-bottom:12px">'
        + '<a href="https://cocotheaxolotl.org/" style="display:inline-block;padding:12px 30px;background:#fff;color:#ff69b4;text-decoration:none;border-radius:30px;font-weight:800;font-size:14px;border:2px solid #ff69b4">Visit Coco\'s Website</a>'
        + '</td></tr></table>'
        + '<p style="margin:20px 0 0;font-size:13px;color:#999;text-align:center">'
        + 'Follow Coco: '
        + '<a href="https://www.youtube.com/channel/UCxSzBMea0cfiuJlrPCNG2UA" style="color:#ff69b4;text-decoration:none;font-weight:700">YouTube</a> | '
        + '<a href="https://www.instagram.com/cocotheaxolotl/" style="color:#ff69b4;text-decoration:none;font-weight:700">Instagram</a> | '
        + '<a href="https://www.tiktok.com/@cocotheaxolotl" style="color:#ff69b4;text-decoration:none;font-weight:700">TikTok</a>'
        + '</p>'
        + '</td></tr>'
        + '<tr><td style="padding:20px 30px;background:#fafafa;text-align:center;font-size:12px;color:#999">'
        + '<p style="margin:0 0 8px">&copy; Coco the Axolotl &ndash; <a href="https://cocotheaxolotl.org" style="color:#999">cocotheaxolotl.org</a></p>'
        + '<p style="margin:0"><a href="{{ unsubscribe }}" style="color:#999">Unsubscribe</a></p>'
        + '</td></tr>'
        + '</table></td></tr></table></body></html>';

      const emailRes = await fetch('https://api.brevo.com/v3/smtp/email', {
        method: 'POST',
        headers: { 'api-key': apiKey, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sender: { name: senderName, email: senderEmail },
          to: [{ email, name: name || '' }],
          subject: 'Welcome to Coco\'s world! Your free coloring pages are here',
          htmlContent: welcomeHtml,
        }),
      });
      if (!emailRes.ok) {
        const emailErr = await emailRes.json();
        return json({ success: true, already: false, welcomeError: emailErr }, { headers: cors });
      }
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
