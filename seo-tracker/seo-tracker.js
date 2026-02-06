#!/usr/bin/env node
// ============================================================
// SEO TRACKER - Script de suivi de positionnement Google
// ============================================================
// Utilise SerpAPI (https://serpapi.com/) - 100 recherches/mois gratuites
//
// Usage :
//   node seo-tracker.js              → vérification complète
//   node seo-tracker.js --test       → teste 1 mot-clé (validation API)
//   node seo-tracker.js --group=coloring → vérifie un seul groupe
// ============================================================

const https = require('https');
const fs = require('fs');
const path = require('path');

// --- Load config ---
const configPath = path.join(__dirname, 'seo-config.js');
if (!fs.existsSync(configPath)) {
  console.error('ERREUR: seo-config.js introuvable.');
  process.exit(1);
}
const config = require(configPath);

const DATA_DIR = path.join(__dirname, 'data');
const DATA_FILE = path.join(DATA_DIR, 'seo-results.json');

// --- Parse CLI args ---
const args = process.argv.slice(2);
const isTest = args.includes('--test');
const groupArg = args.find(a => a.startsWith('--group='));
const groupFilter = groupArg ? groupArg.split('=')[1] : null;

// --- Validate config ---
function validateConfig() {
  if (!config.SERPAPI_KEY || config.SERPAPI_KEY === 'YOUR_SERPAPI_KEY_HERE') {
    console.error(`
╔══════════════════════════════════════════════════════════════╗
║  CLÉ SERPAPI MANQUANTE                                       ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  1. Va sur https://serpapi.com/                               ║
║  2. Crée un compte gratuit (100 recherches/mois)             ║
║  3. Copie ta clé API depuis le dashboard                     ║
║  4. Colle-la dans seo-config.js → SERPAPI_KEY                ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
`);
    process.exit(1);
  }
}

// --- Utilities ---
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function fetchJSON(url) {
  return new Promise((resolve, reject) => {
    https.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, body: JSON.parse(data) });
        } catch (e) {
          reject(new Error(`JSON parse error: ${e.message}`));
        }
      });
      res.on('error', reject);
    }).on('error', reject);
  });
}

async function fetchWithRetry(url, retries = 2) {
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const result = await fetchJSON(url);
      if (result.status === 429) {
        if (attempt < retries) {
          const wait = (attempt + 1) * 3000;
          console.log(`  Rate limit, attente ${wait}ms...`);
          await sleep(wait);
          continue;
        }
        return { status: 429, body: null };
      }
      if (result.status === 401) {
        console.error('ERREUR 401: Clé SerpAPI invalide.');
        return { status: 401, body: null };
      }
      return result;
    } catch (err) {
      if (attempt < retries) {
        await sleep((attempt + 1) * 1000);
        continue;
      }
      throw err;
    }
  }
}

// --- Core: check one keyword via SerpAPI ---
async function checkKeyword(keyword) {
  const allDomains = [config.TARGET_DOMAIN, ...config.COMPETITORS];
  const positions = {};
  allDomains.forEach(d => positions[d] = null);

  const maxResults = config.MAX_RESULTS || 30;
  const params = new URLSearchParams({
    api_key: config.SERPAPI_KEY,
    engine: 'google',
    q: keyword,
    num: maxResults.toString(),
    hl: 'en',
    gl: 'us',
  });

  const url = `https://serpapi.com/search.json?${params.toString()}`;
  const result = await fetchWithRetry(url);

  if (!result.body) {
    return { positions, partial: true };
  }

  if (result.body.error) {
    console.error(`  Erreur API: ${result.body.error}`);
    return { positions, partial: true };
  }

  const organicResults = result.body.organic_results || [];
  organicResults.forEach((item, index) => {
    try {
      const link = item.link || item.url || '';
      const resultDomain = new URL(link).hostname.replace(/^www\./, '');
      if (positions[resultDomain] !== undefined && positions[resultDomain] === null) {
        positions[resultDomain] = index + 1;
      }
    } catch (_) {
      // malformed URL, skip
    }
  });

  return { positions, partial: false };
}

// --- Data file management ---
function loadData() {
  if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
  }
  if (fs.existsSync(DATA_FILE)) {
    try {
      return JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
    } catch (_) {
      console.log('Fichier de données corrompu, création d\'un nouveau fichier.');
    }
  }
  return {
    metadata: {
      targetDomain: config.TARGET_DOMAIN,
      competitors: config.COMPETITORS,
      lastUpdated: null,
    },
    snapshots: [],
  };
}

function saveData(data) {
  data.metadata.targetDomain = config.TARGET_DOMAIN;
  data.metadata.competitors = config.COMPETITORS;
  data.metadata.lastUpdated = new Date().toISOString();

  const maxSnapshots = config.MAX_SNAPSHOTS || 52;
  if (data.snapshots.length > maxSnapshots) {
    data.snapshots = data.snapshots.slice(-maxSnapshots);
  }

  fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2), 'utf8');
}

// --- Console output ---
function printSummary(snapshot) {
  const allDomains = [config.TARGET_DOMAIN, ...config.COMPETITORS];
  const colWidth = 20;

  console.log('\n' + '='.repeat(80));
  console.log(`  SEO Position Check - ${new Date(snapshot.date).toLocaleDateString('fr-FR')}`);
  console.log('='.repeat(80));

  let header = 'Mot-clé'.padEnd(35);
  allDomains.forEach(d => {
    const short = d.replace('.com', '').replace('.org', '').replace('.ws', '');
    header += short.substring(0, colWidth).padStart(colWidth);
  });
  console.log(header);
  console.log('-'.repeat(header.length));

  const keywords = Object.keys(snapshot.results);
  let targetRanked = 0;
  let targetSum = 0;

  keywords.forEach(kw => {
    let row = kw.substring(0, 33).padEnd(35);
    allDomains.forEach(d => {
      const pos = snapshot.results[kw][d];
      const val = pos === null ? '-' : pos.toString();
      row += val.padStart(colWidth);
    });
    console.log(row);

    const targetPos = snapshot.results[kw][config.TARGET_DOMAIN];
    if (targetPos !== null) {
      targetRanked++;
      targetSum += targetPos;
    }
  });

  console.log('-'.repeat(header.length));
  console.log(`\nMots-clés suivis : ${keywords.length}`);
  console.log(`${config.TARGET_DOMAIN} classé : ${targetRanked}/${keywords.length}`);
  if (targetRanked > 0) {
    console.log(`Position moyenne : ${(targetSum / targetRanked).toFixed(1)}`);
  }
  console.log('');
}

// --- Main ---
async function main() {
  validateConfig();

  console.log('╔══════════════════════════════════════════════════╗');
  console.log('║        Coco SEO Tracker - Scan en cours         ║');
  console.log('╚══════════════════════════════════════════════════╝\n');

  // Filter keywords
  let keywords = config.KEYWORDS;
  if (groupFilter) {
    keywords = keywords.filter(k => k.group === groupFilter);
    if (keywords.length === 0) {
      const groups = [...new Set(config.KEYWORDS.map(k => k.group))];
      console.error(`Groupe "${groupFilter}" introuvable. Groupes : ${groups.join(', ')}`);
      process.exit(1);
    }
    console.log(`Groupe : ${groupFilter} (${keywords.length} mots-clés)\n`);
  }

  if (isTest) {
    keywords = [keywords[0]];
    console.log(`Mode test : 1 mot-clé ("${keywords[0].keyword}")\n`);
  }

  console.log(`Mots-clés : ${keywords.length} | 1 requête SerpAPI par mot-clé\n`);

  const data = loadData();
  const snapshot = { date: new Date().toISOString(), results: {} };
  let rateLimited = false;

  for (let i = 0; i < keywords.length; i++) {
    const kw = keywords[i];
    const progress = `[${i + 1}/${keywords.length}]`;
    process.stdout.write(`${progress} ${kw.keyword}...`);

    try {
      const result = await checkKeyword(kw.keyword);
      snapshot.results[kw.keyword] = result.positions;

      const targetPos = result.positions[config.TARGET_DOMAIN];
      const posStr = targetPos === null ? 'non classé' : `#${targetPos}`;
      console.log(` ${posStr}`);

      if (result.partial) {
        console.log('  ⚠ Résultats partiels (rate limit ou erreur)');
        rateLimited = true;
        break;
      }
    } catch (err) {
      console.log(` ERREUR: ${err.message}`);
      snapshot.results[kw.keyword] = {};
    }

    if (i < keywords.length - 1) {
      await sleep(config.DELAY_MS || 500);
    }
  }

  if (Object.keys(snapshot.results).length > 0) {
    data.snapshots.push(snapshot);
    saveData(data);
    console.log(`\nDonnées sauvegardées dans ${DATA_FILE}`);
  }

  if (rateLimited) {
    console.log('\n⚠ Scan interrompu. Résultats partiels sauvegardés.');
  }

  printSummary(snapshot);
}

main().catch(err => {
  console.error('Erreur fatale:', err.message);
  process.exit(1);
});
