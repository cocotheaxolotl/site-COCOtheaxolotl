const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const svgDir = path.join(__dirname, 'train');
const pngDir = path.join(__dirname, 'train-png');
if (!fs.existsSync(pngDir)) fs.mkdirSync(pngDir);

const files = fs.readdirSync(svgDir).filter(f => f.endsWith('.svg'));

async function convert() {
  for (const file of files) {
    const svgPath = path.join(svgDir, file);
    const pngName = file.replace('.svg', '.png');
    const pngPath = path.join(pngDir, pngName);

    await sharp(svgPath, { density: 300 })
      .resize(400, 440)
      .png()
      .toFile(pngPath);

    console.log('OK ' + pngName);
  }
  console.log('\nDone! ' + files.length + ' PNGs in ' + pngDir);
}

convert().catch(err => console.error(err));
