const sharp = require('sharp');
const path = require('path');
const fs = require('fs');

const src = path.join(__dirname, 'www', 'coco.png');
const androidRes = path.join(__dirname, 'android', 'app', 'src', 'main', 'res');

const sizes = {
  'mipmap-mdpi': 48,
  'mipmap-hdpi': 72,
  'mipmap-xhdpi': 96,
  'mipmap-xxhdpi': 144,
  'mipmap-xxxhdpi': 192,
};

async function generate() {
  // Read the source image
  const img = sharp(src);
  const meta = await img.metadata();

  // Determine crop to make it square (center crop)
  const size = Math.min(meta.width, meta.height);

  for (const [folder, px] of Object.entries(sizes)) {
    const dir = path.join(androidRes, folder);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

    // Standard icon (square with padding, pink background)
    await sharp(src)
      .resize(px, px, { fit: 'contain', background: { r: 26, g: 26, b: 46, alpha: 1 } })
      .png()
      .toFile(path.join(dir, 'ic_launcher.png'));

    // Round icon (circular)
    const roundMask = Buffer.from(
      `<svg width="${px}" height="${px}">
        <circle cx="${px/2}" cy="${px/2}" r="${px/2}" fill="white"/>
      </svg>`
    );

    const resized = await sharp(src)
      .resize(px, px, { fit: 'contain', background: { r: 26, g: 26, b: 46, alpha: 1 } })
      .png()
      .toBuffer();

    await sharp(resized)
      .composite([{ input: roundMask, blend: 'dest-in' }])
      .png()
      .toFile(path.join(dir, 'ic_launcher_round.png'));

    console.log(`${folder}: ${px}x${px} done`);
  }

  // Also generate foreground for adaptive icons
  const fgDir = path.join(androidRes, 'mipmap-xxxhdpi');
  await sharp(src)
    .resize(288, 288, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })
    .png()
    .toFile(path.join(fgDir, 'ic_launcher_foreground.png'));
  console.log('Foreground icon done');

  console.log('All icons generated!');
}

generate().catch(console.error);
