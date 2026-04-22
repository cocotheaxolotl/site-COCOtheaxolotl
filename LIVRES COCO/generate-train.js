const fs = require('fs');
const path = require('path');

const outDir = path.join(__dirname, 'train');
if (!fs.existsSync(outDir)) fs.mkdirSync(outDir);

const colors = [
  { top: '#ff6b6b', bot: '#d63031', side: '#b71c1c', roof: '#c0392b' },
  { top: '#74b9ff', bot: '#0984e3', side: '#0652DD', roof: '#0769d4' },
  { top: '#55efc4', bot: '#00b894', side: '#00856a', roof: '#009b7d' },
  { top: '#ffeaa7', bot: '#fdcb6e', side: '#d4a843', roof: '#e6b84d' },
  { top: '#a29bfe', bot: '#6c5ce7', side: '#4834d4', roof: '#5a45e0' },
  { top: '#fab1a0', bot: '#e17055', side: '#c0392b', roof: '#d35043' },
  { top: '#fd79a8', bot: '#e84393', side: '#c0276e', roof: '#d43580' },
  { top: '#81ecec', bot: '#00cec9', side: '#009e9a', roof: '#00b5b0' },
  { top: '#f8a5c2', bot: '#f78fb3', side: '#d4668e', roof: '#e87aa0' },
  { top: '#63cdda', bot: '#3dc1d3', side: '#25a5b7', roof: '#30b1c3' },
];

const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'.split('');
const punctuation = [
  { char: ',', file: 'comma' },
  { char: '?', file: 'question' },
  { char: '.', file: 'period' },
  { char: '-', file: 'dash' },
  { char: '!', file: 'exclamation' },
];

function makeSvg(char, displayChar, c) {
  // Adjust font size for wider characters
  let fontSize = 110;
  let yPos = 148;
  if ('MW'.includes(char)) { fontSize = 95; }
  if ('WM'.includes(char)) { fontSize = 90; }
  if (char === '?' || char === '!') { fontSize = 105; }
  if (char === ',') { fontSize = 100; yPos = 140; }
  if (char === '.') { fontSize = 100; yPos = 135; }
  if (char === '-') { fontSize = 90; yPos = 130; }

  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 220" width="200" height="220">
  <defs>
    <linearGradient id="wb" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="${c.top}"/>
      <stop offset="100%" stop-color="${c.bot}"/>
    </linearGradient>
    <linearGradient id="ws" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="${c.bot}"/>
      <stop offset="100%" stop-color="${c.side}"/>
    </linearGradient>
    <linearGradient id="rg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#636e72"/>
      <stop offset="100%" stop-color="#2d3436"/>
    </linearGradient>
  </defs>
  <!-- 3D depth -->
  <path d="M20,45 L20,165 L28,172 L28,52 Z" fill="url(#ws)"/>
  <path d="M20,165 L180,165 L188,172 L28,172 Z" fill="${c.side}"/>
  <!-- Wagon body -->
  <rect x="20" y="45" width="160" height="120" rx="8" fill="url(#wb)" stroke="#2d3436" stroke-width="3"/>
  <!-- Roof -->
  <rect x="12" y="38" width="176" height="16" rx="6" fill="url(#rg)" stroke="#2d3436" stroke-width="2"/>
  <!-- Plank lines -->
  <line x1="20" y1="85" x2="180" y2="85" stroke="${c.side}" stroke-width="1.5" opacity="0.4"/>
  <line x1="20" y1="125" x2="180" y2="125" stroke="${c.side}" stroke-width="1.5" opacity="0.4"/>
  <!-- Letter -->
  <text x="100" y="${yPos}" text-anchor="middle" font-family="Arial Black, Impact, sans-serif" font-size="${fontSize}" font-weight="900" fill="#fff" stroke="#2d3436" stroke-width="3" paint-order="stroke">${displayChar}</text>
  <!-- Rivets -->
  <circle cx="32" cy="58" r="4" fill="#636e72" stroke="#2d3436" stroke-width="1"/>
  <circle cx="168" cy="58" r="4" fill="#636e72" stroke="#2d3436" stroke-width="1"/>
  <circle cx="32" cy="152" r="4" fill="#636e72" stroke="#2d3436" stroke-width="1"/>
  <circle cx="168" cy="152" r="4" fill="#636e72" stroke="#2d3436" stroke-width="1"/>
  <!-- Wheels -->
  <circle cx="55" cy="185" r="18" fill="#555" stroke="#2d3436" stroke-width="3"/>
  <circle cx="55" cy="185" r="8" fill="#888" stroke="#2d3436" stroke-width="2"/>
  <circle cx="55" cy="185" r="3" fill="#2d3436"/>
  <circle cx="145" cy="185" r="18" fill="#555" stroke="#2d3436" stroke-width="3"/>
  <circle cx="145" cy="185" r="8" fill="#888" stroke="#2d3436" stroke-width="2"/>
  <circle cx="145" cy="185" r="3" fill="#2d3436"/>
  <!-- Wheel connectors -->
  <rect x="38" y="168" width="6" height="14" rx="2" fill="#636e72" stroke="#2d3436" stroke-width="1.5"/>
  <rect x="156" y="168" width="6" height="14" rx="2" fill="#636e72" stroke="#2d3436" stroke-width="1.5"/>
  <!-- Couplings -->
  <rect x="0" y="155" width="20" height="8" rx="3" fill="#636e72" stroke="#2d3436" stroke-width="1.5"/>
  <rect x="180" y="155" width="20" height="8" rx="3" fill="#636e72" stroke="#2d3436" stroke-width="1.5"/>
</svg>`;
}

// Generate A-Z and 0-9
chars.forEach((ch, i) => {
  const c = colors[i % colors.length];
  const svg = makeSvg(ch, ch, c);
  fs.writeFileSync(path.join(outDir, ch + '.svg'), svg);
});

// Generate punctuation
punctuation.forEach((p, i) => {
  const c = colors[(chars.length + i) % colors.length];
  const displayChar = p.char === '&' ? '&amp;' : p.char;
  const svg = makeSvg(p.char, displayChar, c);
  fs.writeFileSync(path.join(outDir, p.file + '.svg'), svg);
});

console.log('Generated ' + (chars.length + punctuation.length) + ' train wagon SVGs in ' + outDir);
