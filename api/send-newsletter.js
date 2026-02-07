module.exports = async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const { secret, title, emoji, description, url, color } = req.body;

  if (secret !== process.env.NEWSLETTER_SECRET) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  const listId = parseInt(process.env.BREVO_LIST_ID || '2');
  const senderEmail = process.env.BREVO_SENDER_EMAIL || 'coco@cocotheaxolotl.org';
  const senderName = process.env.BREVO_SENDER_NAME || 'Coco the Axolotl';
  const siteUrl = 'https://cocotheaxolotl.org';
  const fullUrl = siteUrl + url;
  var bgColor = color || '#ff69b4';

  var htmlContent = '<!DOCTYPE html><html><head><meta charset="UTF-8"></head>'
    + '<body style="margin:0;padding:0;background:#f8f8f8;font-family:system-ui,-apple-system,Arial,sans-serif">'
    + '<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8f8f8;padding:30px 0"><tr><td align="center">'
    + '<table width="580" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:18px;overflow:hidden;box-shadow:0 4px 15px rgba(0,0,0,.06)">'
    // Header
    + '<tr><td style="background:' + bgColor + ';padding:28px 30px;text-align:center">'
    + '<img src="' + siteUrl + '/axolotl.png" width="80" alt="Coco" style="display:block;margin:0 auto 10px">'
    + '<h1 style="margin:0;color:#fff;font-size:22px">Coco the Axolotl</h1>'
    + '</td></tr>'
    // Body
    + '<tr><td style="padding:30px 32px">'
    + '<h2 style="margin:0 0 12px;font-size:24px;text-align:center">' + (emoji || '') + ' ' + title + '</h2>'
    + '<p style="margin:0 0 22px;font-size:16px;line-height:1.5;color:#555;text-align:center">' + description + '</p>'
    + '<table width="100%" cellpadding="0" cellspacing="0"><tr><td align="center">'
    + '<a href="' + fullUrl + '" style="display:inline-block;padding:14px 36px;background:' + bgColor + ';color:#fff;text-decoration:none;border-radius:30px;font-weight:800;font-size:16px">Try it now!</a>'
    + '</td></tr></table>'
    + '</td></tr>'
    // Footer
    + '<tr><td style="padding:20px 30px;background:#fafafa;text-align:center;font-size:12px;color:#999">'
    + '<p style="margin:0 0 8px">&copy; Coco the Axolotl &ndash; <a href="' + siteUrl + '" style="color:#999">cocotheaxolotl.org</a></p>'
    + '<p style="margin:0"><a href="{{ unsubscribe }}" style="color:#999">Unsubscribe</a></p>'
    + '</td></tr>'
    + '</table></td></tr></table></body></html>';

  try {
    // Create campaign
    var createRes = await fetch('https://api.brevo.com/v3/emailCampaigns', {
      method: 'POST',
      headers: {
        'api-key': process.env.BREVO_API_KEY,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: 'New: ' + title,
        subject: emoji + ' New on Coco the Axolotl: ' + title + '!',
        sender: { name: senderName, email: senderEmail },
        recipients: { listIds: [listId] },
        htmlContent: htmlContent
      })
    });

    if (!createRes.ok) {
      var err = await createRes.json();
      return res.status(500).json({ error: 'Campaign creation failed', details: err });
    }

    var campaign = await createRes.json();

    // Send now
    var sendRes = await fetch('https://api.brevo.com/v3/emailCampaigns/' + campaign.id + '/sendNow', {
      method: 'POST',
      headers: { 'api-key': process.env.BREVO_API_KEY }
    });

    if (sendRes.ok || sendRes.status === 204) {
      return res.status(200).json({ success: true, campaignId: campaign.id });
    }

    var sendErr = await sendRes.json();
    return res.status(500).json({ error: 'Campaign send failed', details: sendErr });
  } catch (err) {
    return res.status(500).json({ error: 'Server error' });
  }
};
