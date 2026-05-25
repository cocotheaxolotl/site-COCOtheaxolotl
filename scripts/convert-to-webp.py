"""Convert large PNG/JPG to WebP alongside originals.

Originals are NEVER deleted or overwritten — WebP is additive.
Skips files in dirs that are excluded from the Cloudflare build,
and skips files already converted (unless source is newer).
"""
from pathlib import Path
from PIL import Image
import sys

ROOT = Path(r"c:\Users\33612\Documents\site_COCOtheaxolotl")
MIN_BYTES = 500 * 1024  # only convert images larger than 500KB
QUALITY = 82  # WebP quality (visually lossless ~80-85)

# Match build-cloudflare.mjs exclusions
EXCLUDED_DIRS = {
    ".claude", ".git", ".github", ".vercel", ".vscode", ".well-known",
    "__pycache__", "_coloring_backup", "api", "cgi-bin", "coherence-app",
    "dist", "downloads", "emails", "functions", "LIVRES COCO",
    "Lettering COCO", "memory", "mosaic-api", "mosaic-examples",
    "node_modules", "planks_wood_letters", "scripts", "seo-tracker",
    "templates", "valentine_day", "youtube-pipeline",
}

def is_excluded(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    return any(p in EXCLUDED_DIRS or p.startswith("tmp") or p.startswith("dist_stale_")
               for p in rel.parts)

candidates = []
for ext in ("*.png", "*.jpg", "*.jpeg"):
    for p in ROOT.rglob(ext):
        if is_excluded(p):
            continue
        try:
            if p.stat().st_size < MIN_BYTES:
                continue
        except OSError:
            continue
        candidates.append(p)

candidates.sort(key=lambda p: p.stat().st_size, reverse=True)
print(f"Found {len(candidates)} images >500KB to convert")

total_in = total_out = converted = skipped = errors = 0

for i, src in enumerate(candidates, 1):
    dst = src.with_suffix(".webp")
    src_size = src.stat().st_size
    total_in += src_size

    if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
        total_out += dst.stat().st_size
        skipped += 1
        continue

    try:
        with Image.open(src) as im:
            # WebP supports RGB and RGBA; convert palette/CMYK
            if im.mode in ("P", "CMYK"):
                im = im.convert("RGBA" if im.mode == "P" else "RGB")
            im.save(dst, format="WEBP", quality=QUALITY, method=6)
        out_size = dst.stat().st_size
        total_out += out_size
        converted += 1
        saved_pct = 100 * (1 - out_size / src_size)
        rel = src.relative_to(ROOT)
        print(f"  [{i}/{len(candidates)}] {rel}: {src_size//1024}KB -> {out_size//1024}KB ({saved_pct:.0f}% saved)")
    except Exception as e:
        errors += 1
        print(f"  ERROR {src.relative_to(ROOT)}: {e}", file=sys.stderr)

print()
print(f"Converted: {converted}, skipped (up-to-date): {skipped}, errors: {errors}")
print(f"Originals total: {total_in/1024/1024:.1f} MB")
print(f"WebP total:      {total_out/1024/1024:.1f} MB")
if total_in:
    print(f"Saved:           {(total_in - total_out)/1024/1024:.1f} MB ({100*(1-total_out/total_in):.0f}%)")
