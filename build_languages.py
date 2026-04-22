#!/usr/bin/env python3
"""
Coco the Axolotl - Multilingual Build Script
Generates /fr/ and /es/ versions of the static website for SEO.

Usage: python build_languages.py
"""

import os
import re
import copy
import shutil
import logging
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Tag

# ── Configuration ──────────────────────────────────────────────
SITE_ROOT = Path(__file__).parent
BASE_URL = "https://cocotheaxolotl.org"
TARGET_LANGS = ["fr", "es"]

BRAND_SUFFIX = {
    "en": " – Coco the Axolotl",
    "fr": " – Coco l'Axolotl",
    "es": " – Coco el Ajolote",
}

EXCLUDE_FILES = {
    "sleep-book/read/index.html",  # noindex, FR-only ebook reader
    "404.html",
    "admin/index.html",
    "admin/preview-valentine.html",
    "seo-tracker/seo-dashboard.html",
    "prototypes/book-insert.html",
    "prototypes/whose-egg-book.html",
    "_coloring_backup/index.html",
    "sleep-book/etsy-access-card.html",
}

EXCLUDE_PREFIXES = ("google",)

# Asset extensions and path prefixes that should NOT get /fr/ prefix
ASSET_EXTENSIONS = {
    ".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp",
    ".mp4", ".webm", ".ico", ".json", ".xml", ".pdf", ".woff", ".woff2",
}

ASSET_PATH_PREFIXES = (
    "/common.css", "/manifest.json", "/favicon.ico", "/icons/",
    "/api/", "/coco", "/axolotl", "/gills", "/poster-hero", "/hero-bg",
)

EXTERNAL_DOMAINS = (
    "amazon.com", "amazon.fr", "amazon.es", "amazon.de",
    "youtube.com", "youtu.be",
    "instagram.com", "tiktok.com", "pinterest.com", "facebook.com",
    "redbubble.com", "loopinky.com",
    "fonts.googleapis.com", "googletagmanager.com",
    "schema.org", "sitemaps.org",
    "google.com",
)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)-7s %(message)s",
)
log = logging.getLogger("build")


# ── Helpers ────────────────────────────────────────────────────

def discover_html_files():
    """Find all HTML files to process."""
    files = []
    for path in SITE_ROOT.rglob("*.html"):
        rel = path.relative_to(SITE_ROOT).as_posix()

        # Skip files in /fr/ or /es/ dirs (previous builds)
        if rel.startswith("fr/") or rel.startswith("es/"):
            continue

        # Skip excluded files
        if rel in EXCLUDE_FILES:
            continue

        # Skip google verification files
        basename = path.name
        if any(basename.startswith(p) for p in EXCLUDE_PREFIXES):
            continue

        files.append(rel)

    return sorted(files)


def is_external(href):
    if not href:
        return False
    for domain in EXTERNAL_DOMAINS:
        if domain in href:
            return True
    return False


def is_asset(href):
    if not href:
        return False
    # Check extension
    for ext in ASSET_EXTENSIONS:
        if href.lower().endswith(ext):
            return True
    # Check prefix
    for prefix in ASSET_PATH_PREFIXES:
        if href.startswith(prefix):
            return True
    return False


def is_internal_page_link(href):
    """Return True if href is an internal page link that should be prefixed."""
    if not href or href.startswith("#") or href.startswith("javascript:"):
        return False
    if is_external(href):
        return False
    if is_asset(href):
        return False
    # Must start with /
    if not href.startswith("/"):
        return False
    return True


def get_page_path(rel_file):
    """Convert file path to URL path. 'freebies/index.html' -> 'freebies/'"""
    if rel_file == "index.html":
        return ""
    return rel_file.replace("index.html", "").replace("\\", "/")


def extract_text_for_lang(container, lang):
    """Extract text from data-lang spans/divs inside a container."""
    if not container:
        return None
    el = container.find(attrs={"data-lang": lang})
    if el:
        return el.get_text(strip=True)
    return None


def get_page_dir(rel_file):
    """Get the directory URL prefix for a page file.
    'freebies/index.html' -> '/freebies/'
    'index.html' -> '/'
    'blog/post/index.html' -> '/blog/post/'
    """
    d = os.path.dirname(rel_file).replace("\\", "/")
    if d:
        return f"/{d}/"
    return "/"


def make_absolute_path(relative_ref, page_dir):
    """Convert a relative reference to an absolute path.
    relative_ref: 'turtle-coloring-page/image.png'
    page_dir: '/freebies/'
    -> '/freebies/turtle-coloring-page/image.png'
    """
    if relative_ref.startswith("/"):
        return relative_ref  # already absolute
    return page_dir + relative_ref


# ── Transformation functions ───────────────────────────────────

def transform_html_lang(soup, lang):
    html_tag = soup.find("html")
    if html_tag:
        html_tag["lang"] = lang


def transform_title(soup, lang):
    """Extract title from H1 data-lang, fall back to H2, then existing title."""
    h1 = soup.find("h1")
    title_text = extract_text_for_lang(h1, lang) if h1 else None

    # Fallback to H2 if H1 has no data-lang content
    if not title_text:
        h2 = soup.find("h2")
        title_text = extract_text_for_lang(h2, lang) if h2 else None

    if title_text:
        # Clean up emojis at start/end and whitespace
        title_text = title_text.strip()
        # Add brand suffix if not already present
        if "coco" not in title_text.lower() or "axolotl" not in title_text.lower():
            title_text += BRAND_SUFFIX[lang]
    else:
        # Fallback: keep existing English title
        existing = soup.find("title")
        if existing:
            title_text = existing.get_text(strip=True)
            log.warning(f"  No {lang} H1/H2 found, keeping EN title: {title_text[:50]}")

    title_tag = soup.find("title")
    if title_tag and title_text:
        title_tag.string = title_text

    return title_text


def transform_meta_description(soup, lang):
    """Extract description from first paragraph with data-lang."""
    desc = None

    # Try .intro paragraph first
    intro = soup.find("p", class_="intro")
    if intro:
        desc = extract_text_for_lang(intro, lang)

    # Try first paragraph in .content or body
    if not desc:
        for p in soup.find_all("p"):
            candidate = extract_text_for_lang(p, lang)
            if candidate and len(candidate) > 30:
                desc = candidate
                break

    # Try any div with data-lang that has enough text
    if not desc:
        for div in soup.find_all(attrs={"data-lang": lang}):
            text = div.get_text(strip=True)
            if len(text) > 40:
                desc = text
                break

    if desc:
        # Truncate to ~155 chars for SEO
        if len(desc) > 155:
            desc = desc[:152].rsplit(" ", 1)[0] + "..."

    meta = soup.find("meta", attrs={"name": "description"})
    if meta and desc:
        meta["content"] = desc

    return desc


def transform_og_twitter(soup, lang, new_url, title, desc):
    """Update OG and Twitter meta tags."""
    # OG
    og_title = soup.find("meta", attrs={"property": "og:title"})
    if og_title and title:
        og_title["content"] = title

    og_desc = soup.find("meta", attrs={"property": "og:description"})
    if og_desc and desc:
        og_desc["content"] = desc

    og_url = soup.find("meta", attrs={"property": "og:url"})
    if og_url:
        og_url["content"] = new_url

    # OG locale
    og_locale = soup.find("meta", attrs={"property": "og:locale"})
    if og_locale:
        locale_map = {"fr": "fr_FR", "es": "es_ES", "en": "en_US"}
        og_locale["content"] = locale_map.get(lang, "en_US")

    # Twitter
    tw_title = soup.find("meta", attrs={"name": "twitter:title"})
    if tw_title and title:
        tw_title["content"] = title

    tw_desc = soup.find("meta", attrs={"name": "twitter:description"})
    if tw_desc and desc:
        tw_desc["content"] = desc


def transform_canonical(soup, new_url):
    canonical = soup.find("link", attrs={"rel": "canonical"})
    if canonical:
        canonical["href"] = new_url


def add_hreflang(soup, page_path):
    """Add hreflang tags to <head>."""
    head = soup.find("head")
    if not head:
        return

    # Remove existing hreflang
    for tag in soup.find_all("link", attrs={"rel": "alternate"}):
        if tag.get("hreflang"):
            tag.decompose()

    en_url = f"{BASE_URL}/{page_path}"
    fr_url = f"{BASE_URL}/fr/{page_path}"
    es_url = f"{BASE_URL}/es/{page_path}"

    for hreflang, href in [("en", en_url), ("fr", fr_url), ("es", es_url), ("x-default", en_url)]:
        tag = soup.new_tag("link", rel="alternate", hreflang=hreflang, href=href)
        head.append(tag)


def strip_other_languages(soup, keep_lang):
    """Remove data-lang elements of other languages, unwrap kept language."""
    other_langs = {"en", "fr", "es"} - {keep_lang}

    # Remove other languages
    for lang in other_langs:
        for el in soup.find_all(attrs={"data-lang": lang}):
            el.decompose()

    # Unwrap target language (remove wrapper tag, keep content)
    for el in soup.find_all(attrs={"data-lang": keep_lang}):
        el.unwrap()


def transform_internal_links(soup, lang):
    """Prefix internal page links with /fr/ or /es/."""
    prefix = f"/{lang}"

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if is_internal_page_link(href):
            a["href"] = prefix + href

    # Also handle form actions if any
    for form in soup.find_all("form", action=True):
        action = form["action"]
        if is_internal_page_link(action):
            form["action"] = prefix + action


def transform_amazon_links(soup, lang):
    """Set Amazon links to the correct language version."""
    attr = f"data-href-{lang}"
    for a in soup.find_all("a", attrs={attr: True}):
        a["href"] = a[attr]


def transform_language_toggle(soup, lang, page_path):
    """Replace JS language buttons with static links."""
    toggle = soup.find(class_="lang-toggle")
    if not toggle:
        return

    toggle.clear()

    links = {
        "en": f"/{page_path}",
        "fr": f"/fr/{page_path}",
        "es": f"/es/{page_path}",
    }

    for code, url in links.items():
        a = soup.new_tag("a", href=url)
        a["class"] = ["lang-btn"]
        if code == lang:
            a["class"].append("active")
        a.string = code.upper()
        toggle.append(a)


def transform_home_link(soup, lang):
    """Update the home link (<a href="/">) to go to /fr/ or /es/."""
    for a in soup.find_all("a", class_="home-link"):
        if a.get("href") == "/":
            a["href"] = f"/{lang}/"


def clean_setlang_js(soup, lang):
    """Remove or simplify the setLang() JS function."""
    for script in soup.find_all("script"):
        if not script.string:
            continue
        content = script.string

        # If script contains setLang, simplify it
        if "function setLang" in content:
            # Keep analytics, cookie, and other non-language JS
            # Remove the setLang function and related code
            # Replace with minimal static language setup
            new_content = content

            # Remove the setLang function definition
            new_content = re.sub(
                r"function setLang\(.*?\n\s*\}",
                "",
                new_content,
                flags=re.DOTALL,
            )

            # Remove setLang calls
            new_content = re.sub(r"setLang\([^)]*\);?", "", new_content)

            # Remove placeholder setup that references setLang
            new_content = re.sub(
                r"document\.getElementById\('popupName'\)\.placeholder\s*=\s*'[^']*';",
                "",
                new_content,
            )
            new_content = re.sub(
                r"document\.getElementById\('popupEmail'\)\.placeholder\s*=\s*'[^']*';",
                "",
                new_content,
            )

            script.string = new_content


def clean_lang_css(soup):
    """Remove CSS language visibility rules (not needed in single-lang pages)."""
    for style in soup.find_all("style"):
        if not style.string:
            continue
        content = style.string

        # Remove data-lang visibility rules
        content = re.sub(r"span\[data-lang=\"[^\"]+\"\]\{[^}]+\}", "", content)
        content = re.sub(r"\[data-lang=\"[^\"]+\"\]\{[^}]+\}", "", content)
        content = re.sub(r"body\.\w+\s+span\[data-lang=\"[^\"]+\"\]\{[^}]+\}", "", content)
        content = re.sub(r"body\.\w+\s+\[data-lang=\"[^\"]+\"\]\{[^}]+\}", "", content)
        content = re.sub(
            r"body\.\w+\s+\[data-lang=\"[^\"]+\"\],\s*body\.\w+\s+\[data-lang=\"[^\"]+\"\]\{[^}]+\}",
            "",
            content,
        )
        content = re.sub(
            r"body\.\w+\s+span\[data-lang=\"[^\"]+\"\],\s*body\.\w+\s+span\[data-lang=\"[^\"]+\"\]\{[^}]+\}",
            "",
            content,
        )

        # Clean up extra blank lines
        content = re.sub(r"\n\s*\n\s*\n", "\n\n", content)

        style.string = content


def transform_form_placeholders(soup, lang):
    """Set form input placeholders to the target language."""
    placeholders = {
        "fr": {"name": "Ton prénom", "email": "Ton email"},
        "es": {"name": "Tu nombre", "email": "Tu email"},
        "en": {"name": "Your first name", "email": "Enter your email"},
    }
    p = placeholders.get(lang, placeholders["en"])

    name_input = soup.find("input", id="popupName")
    if name_input:
        name_input["placeholder"] = p["name"]

    email_input = soup.find("input", id="popupEmail")
    if email_input:
        email_input["placeholder"] = p["email"]

    # Also handle freebies page email gate
    for inp in soup.find_all("input", attrs={"type": "email"}):
        inp["placeholder"] = p["email"]
    for inp in soup.find_all("input", attrs={"type": "text"}):
        if inp.get("id") not in ("popupName",):
            current = (inp.get("placeholder") or "").lower()
            if "name" in current or "prénom" in current or "nombre" in current:
                inp["placeholder"] = p["name"]


def fix_relative_paths(soup, rel_file):
    """Convert relative asset paths to absolute so they work from /fr/ and /es/."""
    page_dir = get_page_dir(rel_file)

    # Fix <img src>, <source src>, <video poster>
    for tag in soup.find_all(["img", "source", "video", "audio"]):
        for attr in ["src", "poster"]:
            val = tag.get(attr)
            if val and not val.startswith(("/", "http://", "https://", "data:", "#")):
                tag[attr] = make_absolute_path(val, page_dir)

    # Fix <a href> for asset downloads (relative paths to files)
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith(("/", "http://", "https://", "mailto:", "tel:", "#", "javascript:")):
            continue
        # Relative path - check if it's an asset
        path_part = href.split("?")[0].split("#")[0]
        _, ext = os.path.splitext(path_part)
        if ext.lower() in ASSET_EXTENSIONS:
            a["href"] = make_absolute_path(href, page_dir)

    # Fix url() in <style> blocks
    for style in soup.find_all("style"):
        if not style.string:
            continue
        content = style.string

        def fix_css_url(match):
            url = match.group(1).strip("'\"")
            if url.startswith(("/", "http://", "https://", "data:")):
                return match.group(0)
            abs_url = make_absolute_path(url, page_dir)
            return f"url('{abs_url}')"

        new_content = re.sub(r"url\(([^)]+)\)", fix_css_url, content)
        if new_content != content:
            style.string = new_content

    # Fix <link href> for local stylesheets/fonts
    for link in soup.find_all("link", href=True):
        href = link["href"]
        if href.startswith(("/", "http://", "https://", "data:")):
            continue
        rel_attr = link.get("rel", [])
        if isinstance(rel_attr, list):
            rel_attr = " ".join(rel_attr)
        if "alternate" not in rel_attr:
            link["href"] = make_absolute_path(href, page_dir)

    # Fix <script src> for local scripts
    for script in soup.find_all("script", src=True):
        src = script["src"]
        if not src.startswith(("/", "http://", "https://", "data:")):
            script["src"] = make_absolute_path(src, page_dir)


# ── Main pipeline ──────────────────────────────────────────────

def process_file(rel_file, lang):
    """Process a single HTML file for a target language."""
    src = SITE_ROOT / rel_file
    page_path = get_page_path(rel_file)
    new_url = f"{BASE_URL}/{lang}/{page_path}"

    # Read and parse
    html = src.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    # Apply transformations
    transform_html_lang(soup, lang)
    title = transform_title(soup, lang)
    desc = transform_meta_description(soup, lang)
    transform_og_twitter(soup, lang, new_url, title, desc)
    transform_canonical(soup, new_url)
    add_hreflang(soup, page_path)
    transform_amazon_links(soup, lang)
    transform_home_link(soup, lang)
    transform_internal_links(soup, lang)
    transform_form_placeholders(soup, lang)

    # Fix relative paths BEFORE stripping (so they become absolute)
    fix_relative_paths(soup, rel_file)

    # Strip other languages (do this AFTER extracting title/desc)
    strip_other_languages(soup, lang)

    # Replace language toggle AFTER internal links + strip (so links don't get double-prefixed)
    transform_language_toggle(soup, lang, page_path)

    # Clean up JS/CSS
    clean_setlang_js(soup, lang)
    clean_lang_css(soup)

    # Write output
    out_path = SITE_ROOT / lang / rel_file
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Use str(soup) to preserve original formatting (not prettify which reformats)
    out_path.write_text(str(soup), encoding="utf-8")

    return True


def add_hreflang_to_en_files(html_files):
    """Add correct hreflang tags to the original EN files using text insertion (no BS4 reformat)."""
    log.info("Adding hreflang to EN files...")
    for rel_file in html_files:
        src = SITE_ROOT / rel_file
        page_path = get_page_path(rel_file)

        html = src.read_text(encoding="utf-8")

        # Remove any existing hreflang lines first
        html = re.sub(r'\s*<link[^>]*hreflang=[^>]*>', '', html)

        # Build hreflang tags
        en_url = f"{BASE_URL}/{page_path}"
        fr_url = f"{BASE_URL}/fr/{page_path}"
        es_url = f"{BASE_URL}/es/{page_path}"
        hreflang_block = (
            f'\n<link rel="alternate" hreflang="en" href="{en_url}">'
            f'\n<link rel="alternate" hreflang="fr" href="{fr_url}">'
            f'\n<link rel="alternate" hreflang="es" href="{es_url}">'
            f'\n<link rel="alternate" hreflang="x-default" href="{en_url}">'
        )

        # Insert before </head>
        html = html.replace('</head>', hreflang_block + '\n</head>', 1)

        src.write_text(html, encoding="utf-8")

    log.info(f"  Added hreflang to {len(html_files)} EN files")


def update_sitemap(html_files):
    """Update sitemap.xml to include /fr/ and /es/ URLs."""
    sitemap_path = SITE_ROOT / "sitemap.xml"
    if not sitemap_path.exists():
        log.warning("sitemap.xml not found, skipping")
        return

    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"')
    lines.append('        xmlns:xhtml="http://www.w3.org/1999/xhtml">')

    # Read existing sitemap to preserve priorities
    existing = sitemap_path.read_text(encoding="utf-8")
    priorities = {}
    for match in re.finditer(r"<loc>([^<]+)</loc>\s*<priority>([^<]+)</priority>", existing):
        url = match.group(1).replace(BASE_URL + "/", "")
        priorities[url] = match.group(2)

    for rel_file in html_files:
        page_path = get_page_path(rel_file)
        priority = priorities.get(page_path, "0.7")

        en_url = f"{BASE_URL}/{page_path}"
        fr_url = f"{BASE_URL}/fr/{page_path}"
        es_url = f"{BASE_URL}/es/{page_path}"

        # EN entry with hreflang
        lines.append(f"  <url>")
        lines.append(f"    <loc>{en_url}</loc>")
        lines.append(f"    <priority>{priority}</priority>")
        lines.append(f'    <xhtml:link rel="alternate" hreflang="en" href="{en_url}"/>')
        lines.append(f'    <xhtml:link rel="alternate" hreflang="fr" href="{fr_url}"/>')
        lines.append(f'    <xhtml:link rel="alternate" hreflang="es" href="{es_url}"/>')
        lines.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{en_url}"/>')
        lines.append(f"  </url>")

        # FR entry
        lines.append(f"  <url>")
        lines.append(f"    <loc>{fr_url}</loc>")
        lines.append(f"    <priority>{priority}</priority>")
        lines.append(f'    <xhtml:link rel="alternate" hreflang="en" href="{en_url}"/>')
        lines.append(f'    <xhtml:link rel="alternate" hreflang="fr" href="{fr_url}"/>')
        lines.append(f'    <xhtml:link rel="alternate" hreflang="es" href="{es_url}"/>')
        lines.append(f"  </url>")

        # ES entry
        lines.append(f"  <url>")
        lines.append(f"    <loc>{es_url}</loc>")
        lines.append(f"    <priority>{priority}</priority>")
        lines.append(f'    <xhtml:link rel="alternate" hreflang="en" href="{en_url}"/>')
        lines.append(f'    <xhtml:link rel="alternate" hreflang="fr" href="{fr_url}"/>')
        lines.append(f'    <xhtml:link rel="alternate" hreflang="es" href="{es_url}"/>')
        lines.append(f"  </url>")

    lines.append("</urlset>")

    sitemap_path.write_text("\n".join(lines), encoding="utf-8")
    log.info(f"  Sitemap updated with {len(html_files) * 3} URLs")


def main():
    log.info("=== Coco the Axolotl - Multilingual Build ===")

    # Discover files
    html_files = discover_html_files()
    log.info(f"Found {len(html_files)} HTML files to process")

    for lang in TARGET_LANGS:
        log.info(f"\n--- Generating /{lang}/ ---")

        # Clean output dir
        lang_dir = SITE_ROOT / lang
        if lang_dir.exists():
            shutil.rmtree(lang_dir)
        lang_dir.mkdir()

        # Process each file
        ok = 0
        errors = 0
        for rel_file in html_files:
            try:
                process_file(rel_file, lang)
                ok += 1
            except Exception as e:
                log.error(f"  FAILED {rel_file}: {e}")
                errors += 1

        log.info(f"  {ok} OK, {errors} errors")

    # Add hreflang to EN files
    add_hreflang_to_en_files(html_files)

    # Update sitemap
    update_sitemap(html_files)

    log.info("\n=== Build complete! ===")


if __name__ == "__main__":
    main()
