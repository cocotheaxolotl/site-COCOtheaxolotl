"""Swap PNG/JPG -> WebP refs in HTML/CSS where a .webp file exists alongside.

Only updates src="..." attributes (img/video/source) and url(...) in CSS.
Never touches href="..." (download links / PDFs / page links).
Originals stay on disk — pure additive WebP swap.
"""
from pathlib import Path
import re
import sys

ROOT = Path(r"c:\Users\33612\Documents\site_COCOtheaxolotl")

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

# Build set of available .webp paths (relative + by basename for quick lookup)
webp_files = set()
for p in ROOT.rglob("*.webp"):
    if not is_excluded(p):
        webp_files.add(str(p.relative_to(ROOT)).replace("\\", "/").lower())

def webp_exists_for(ref: str, current_file: Path) -> bool:
    """Given an image ref like '/freebies/x.png' or 'pages/x.jpg', check that
    a corresponding .webp exists on disk."""
    candidate = re.sub(r"\.(png|jpe?g)(\?[^\"']*)?$", ".webp", ref, flags=re.I)
    # Strip query string
    candidate_path = candidate.split("?")[0].split("#")[0]

    if candidate_path.startswith("/"):
        # Site-absolute
        rel = candidate_path.lstrip("/")
    elif candidate_path.startswith(("http://", "https://", "//")):
        return False  # external
    else:
        # Relative to current file
        rel = str((current_file.parent / candidate_path).resolve().relative_to(ROOT)).replace("\\", "/")
    return rel.lower() in webp_files

# Patterns to swap:
#   src="...png" / src='...jpg'
#   <source srcset="...png">
#   url("...png") / url(...png) in CSS / inline styles
SRC_RE = re.compile(r'''((?:src|srcset)\s*=\s*['"])([^'"]+?\.(?:png|jpe?g))((?:\?[^'"]*)?['"])''', re.IGNORECASE)
URL_RE = re.compile(r'''(url\(\s*['"]?)([^'")]+?\.(?:png|jpe?g))((?:\?[^'")]*)?['"]?\s*\))''', re.IGNORECASE)

def to_webp(match_ref: str) -> str:
    return re.sub(r"\.(png|jpe?g)(\?|$)", lambda m: ".webp" + (m.group(2) if m.group(2) != "$" else ""), match_ref, count=1, flags=re.I)

# Actually simpler: just replace .png/.jpg/.jpeg with .webp at end (before ? or end)
EXT_RE = re.compile(r"\.(png|jpe?g)(?=\?|$)", re.IGNORECASE)
def swap_ext(ref: str) -> str:
    return EXT_RE.sub(".webp", ref)

EXTENSIONS_TO_SCAN = (".html", ".css", ".js")

total_files = 0
changed_files = 0
total_replacements = 0
skipped_no_webp = 0

for ext in EXTENSIONS_TO_SCAN:
    for path in ROOT.rglob(f"*{ext}"):
        if is_excluded(path):
            continue
        total_files += 1
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                text = path.read_text(encoding="latin-1")
            except Exception as e:
                print(f"skip {path}: {e}", file=sys.stderr)
                continue

        original = text
        counts = {"swapped": 0, "skipped": 0}

        def process(m, file=path, counts=counts):
            prefix, ref, suffix = m.group(1), m.group(2), m.group(3)
            if webp_exists_for(ref, file):
                counts["swapped"] += 1
                return prefix + swap_ext(ref) + suffix
            counts["skipped"] += 1
            return m.group(0)

        text = SRC_RE.sub(process, text)
        text = URL_RE.sub(process, text)
        local_replacements = counts["swapped"]
        local_skipped = counts["skipped"]

        if text != original:
            path.write_text(text, encoding="utf-8")
            changed_files += 1
            total_replacements += local_replacements
            rel = path.relative_to(ROOT)
            print(f"  {rel}: {local_replacements} refs swapped" + (f", {local_skipped} skipped (no .webp)" if local_skipped else ""))
        else:
            skipped_no_webp += local_skipped

print()
print(f"Scanned {total_files} files. Changed {changed_files} files. Total refs swapped: {total_replacements}")
print(f"Refs skipped because no .webp exists: {skipped_no_webp}")
