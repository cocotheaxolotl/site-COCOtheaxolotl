module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const { name, email } = req.body;
  if (!email) return res.status(400).json({ error: 'Email required' });

  const listId = parseInt(process.env.BREVO_LIST_ID || '2');
  const apiKey = process.env.BREVO_API_KEY;
  const senderEmail = process.env.BREVO_SENDER_EMAIL || 'coco@cocotheaxolotl.org';
  const senderName = process.env.BREVO_SENDER_NAME || 'Coco the Axolotl';
  const firstName = name || 'friend';

  try {
    // 1. Add contact to list
    const response = await fetch('https://api.brevo.com/v3/contacts', {
      method: 'POST',
      headers: {
        'api-key': apiKey,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email: email,
        attributes: { FIRSTNAME: name || '' },
        listIds: [listId],
        updateEnabled: true
      })
    });

    const isNew = response.ok || response.status === 204;
    let alreadyExists = false;

    if (!isNew) {
      const data = await response.json();
      if (data.code === 'duplicate_parameter') {
        alreadyExists = true;
      } else {
        return res.status(500).json({ error: 'Subscription failed' });
      }
    }

    // 2. Send welcome email (only for new subscribers)
    if (!alreadyExists) {
      var welcomeHtml = '<!DOCTYPE html><html><head><meta charset="UTF-8"></head>'
        + '<body style="margin:0;padding:0;background:#f8f8f8;font-family:system-ui,-apple-system,Arial,sans-serif">'
        + '<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8f8f8;padding:30px 0"><tr><td align="center">'
        + '<table width="580" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:18px;overflow:hidden;box-shadow:0 4px 15px rgba(0,0,0,.06)">'
        // Header
        + '<tr><td style="background:#ff69b4;padding:28px 30px;text-align:center">'
        + '<img src="https://cocotheaxolotl.org/axolotl.png" width="80" alt="Coco" style="display:block;margin:0 auto 10px">'
        + '<h1 style="margin:0;color:#fff;font-size:22px">Welcome to Coco\'s world!</h1>'
        + '</td></tr>'
        // Body
        + '<tr><td style="padding:30px 32px">'
        + '<h2 style="margin:0 0 12px;font-size:20px;text-align:center">Hey ' + firstName + '! You\'re a hero now!</h2>'
        + '<p style="margin:0 0 8px;font-size:16px;line-height:1.6;color:#555;text-align:center">Coco was drawn by Loopinky... but Loopinky forgot to color him in! Now Coco needs <strong>your superpower</strong> to get his colors back.</p>'
        + '<p style="margin:0 0 22px;font-size:16px;line-height:1.6;color:#555;text-align:center">Grab your crayons and start coloring!</p>'
        // CTA buttons
        + '<table width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding-bottom:12px">'
        + '<a href="https://cocotheaxolotl.org/freebies/" style="display:inline-block;padding:14px 36px;background:#ff69b4;color:#fff;text-decoration:none;border-radius:30px;font-weight:800;font-size:16px">Download Free Coloring Pages</a>'
        + '</td></tr></table>'
        + '<table width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding-bottom:12px">'
        + '<a href="https://cocotheaxolotl.org/" style="display:inline-block;padding:12px 30px;background:#fff;color:#ff69b4;text-decoration:none;border-radius:30px;font-weight:800;font-size:14px;border:2px solid #ff69b4">Visit Coco\'s Website</a>'
        + '</td></tr></table>'
        // Social links
        + '<p style="margin:20px 0 0;font-size:13px;color:#999;text-align:center">'
        + 'Follow Coco: '
        + '<a href="https://www.youtube.com/channel/UCxSzBMea0cfiuJlrPCNG2UA" style="color:#ff69b4;text-decoration:none;font-weight:700">YouTube</a> | '
        + '<a href="https://www.instagram.com/cocotheaxolotl/" style="color:#ff69b4;text-decoration:none;font-weight:700">Instagram</a> | '
        + '<a href="https://www.tiktok.com/@cocotheaxolotl" style="color:#ff69b4;text-decoration:none;font-weight:700">TikTok</a>'
        + '</p>'
        + '</td></tr>'
        // Footer
        + '<tr><td style="padding:20px 30px;background:#fafafa;text-align:center;font-size:12px;color:#999">'
        + '<p style="margin:0 0 8px">&copy; Coco the Axolotl &ndash; <a href="https://cocotheaxolotl.org" style="color:#999">cocotheaxolotl.org</a></p>'
        + '<p style="margin:0"><a href="{{ unsubscribe }}" style="color:#999">Unsubscribe</a></p>'
        + '</td></tr>'
        + '</table></td></tr></table></body></html>';

      var emailRes = await fetch('https://api.brevo.com/v3/smtp/email', {
        method: 'POST',
        headers: {
          'api-key': apiKey,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          sender: { name: senderName, email: senderEmail },
          to: [{ email: email, name: name || '' }],
          subject: 'Welcome to Coco\'s world! Your free coloring pages are here',
          htmlContent: welcomeHtml
        })
      });

      if (!emailRes.ok) {
        var emailErr = await emailRes.json();
        return res.status(200).json({ success: true, already: false, welcomeError: emailErr });
      }
    }

    return res.status(200).json({ success: true, already: alreadyExists });
  } catch (err) {
    return res.status(500).json({ error: 'Server error' });
  }
};
