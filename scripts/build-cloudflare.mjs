import { cp, mkdir, rm, stat } from 'node:fs/promises';
import { join, relative } from 'node:path';
import { readdirSync } from 'node:fs';

const root = process.cwd();
const outDir = join(root, 'dist');

const excludedDirs = new Set([
  '.claude',
  '.git',
  '.github',
  '.vercel',
  '.vscode',
  '.well-known',
  '__pycache__',
  '_coloring_backup',
  'api',
  'cgi-bin',
  'coherence-app',
  'dist',
  'downloads',
  'emails',
  'functions',
  'LIVRES COCO',
  'Lettering COCO',
  'memory',
  'mosaic-api',
  'mosaic-examples',
  'node_modules',
  'planks_wood_letters',
  'scripts',
  'seo-tracker',
  'templates',
  'valentine_day',
  'youtube-pipeline',
]);

const allowedExtensions = new Set([
  '.avif',
  '.css',
  '.gif',
  '.html',
  '.ico',
  '.jpeg',
  '.jpg',
  '.js',
  '.json',
  '.map',
  '.mp3',
  '.mp4',
  '.ogg',
  '.pdf',
  '.png',
  '.svg',
  '.txt',
  '.webm',
  '.webp',
  '.xml',
]);

const allowedRootFiles = new Set([
  '_headers',
  '_redirects',
]);

function shouldSkipDir(name) {
  return excludedDirs.has(name) || name.startsWith('tmp') || name.startsWith('dist_stale_');
}

function shouldCopyFile(name) {
  if (allowedRootFiles.has(name)) return true;
  if (name.startsWith('test-')) return false;
  if (name.startsWith('cbn-')) return false;
  if (name.startsWith('mosaic-') && name.endsWith('.png')) return false;
  if (name.endsWith('.ps1')) return false;
  if (name.endsWith('.py')) return false;
  if (name.endsWith('.zip')) return false;
  if (name.endsWith('.pptx')) return false;
  if (name.endsWith('.psd')) return false;
  if (name.endsWith('.ai')) return false;
  if (name.endsWith('.mov')) return false;
  const dot = name.lastIndexOf('.');
  const ext = dot >= 0 ? name.slice(dot).toLowerCase() : '';
  return allowedExtensions.has(ext);
}

const MAX_FILE_BYTES = 25 * 1024 * 1024; // Cloudflare Pages per-file limit
const skippedOversized = [];

async function shouldCopy(path) {
  const rel = relative(root, path).replaceAll('\\', '/');
  if (!rel) return true;
  const parts = rel.split('/');
  if (parts.some((part) => shouldSkipDir(part))) return false;
  const name = parts.at(-1);
  const info = await stat(path).catch(() => null);
  if (!info) return false;
  if (info.isDirectory()) return true;
  if (!info.isFile() || !shouldCopyFile(name)) return false;
  if (info.size > MAX_FILE_BYTES) {
    skippedOversized.push(`${rel} (${(info.size / 1024 / 1024).toFixed(1)} MiB)`);
    return false;
  }
  return true;
}

await rm(outDir, { recursive: true, force: true });
await mkdir(outDir, { recursive: true });
for (const entry of readdirSync(root, { withFileTypes: true })) {
  if (entry.name === 'dist') continue;
  const from = join(root, entry.name);
  if (!(await shouldCopy(from))) continue;
  await cp(from, join(outDir, entry.name), {
    recursive: true,
    force: true,
    errorOnExist: false,
    filter: shouldCopy,
  });
}

const files = [];
async function collect(dir) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) {
      await collect(path);
    } else if (entry.isFile()) {
      files.push(relative(outDir, path).replaceAll('\\', '/'));
    }
  }
}
await collect(outDir);

const index = join(outDir, 'index.html');
await stat(index);
console.log(`Cloudflare build prepared ${files.length} public files in dist/`);
if (skippedOversized.length) {
  console.log(`Skipped ${skippedOversized.length} file(s) over 25 MiB (Cloudflare Pages limit):`);
  for (const item of skippedOversized) console.log(`  - ${item}`);
}
