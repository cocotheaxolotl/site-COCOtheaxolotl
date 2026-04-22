#!/usr/bin/env python3
"""
Generate a KDP-ready cover PDF for "Coco ne dort pas ce soir !"
Assembles front cover + back cover (with text) + spine into a single PDF.

Usage:  python make_kdp_cover.py
Output: sleep-book/kdp-cover/cover.pdf + cover-preview.png
"""

import os, textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE, 'kdp-cover')
os.makedirs(OUT_DIR, exist_ok=True)

# ── KDP Specs ────────────────────────────────────
TRIM_W = 8.5        # inches
TRIM_H = 11.0
BLEED = 0.125
DPI = 300
# ── Binding type ──────────────────────────────────
BINDING = 'paperback'   # 'paperback' or 'hardcover'
PAGE_COUNT = 30          # interior pages
PAPER = 'white'          # 'white' or 'cream'

SPINE_PER_PAGE = {'white': 0.002252, 'cream': 0.0025}[PAPER]
SPINE_W = PAGE_COUNT * SPINE_PER_PAGE

# Hardcover wrap: 0.625" de chaque côté (couverture rigide qui se replie)
WRAP = 0.625 if BINDING == 'hardcover' else 0.0

TOTAL_W = WRAP + BLEED + TRIM_W + SPINE_W + TRIM_W + BLEED + WRAP
TOTAL_H = WRAP + BLEED + TRIM_H + BLEED + WRAP

PX_W = round(TOTAL_W * DPI)  # 5195
PX_H = round(TOTAL_H * DPI)  # 3375

# Zone boundaries (in pixels)
WRAP_PX = round(WRAP * DPI)
BLEED_PX = round(BLEED * DPI)
MARGIN_LEFT = WRAP_PX + BLEED_PX                        # wrap + bleed
BACK_RIGHT = MARGIN_LEFT + round(TRIM_W * DPI)          # end of back cover trim
SPINE_RIGHT = BACK_RIGHT + round(SPINE_W * DPI)         # end of spine
FRONT_LEFT = SPINE_RIGHT                                 # start of front cover

# ── Source files ─────────────────────────────────
AXOLOTL = os.path.join(os.path.expanduser('~'), 'Documents', 'AXOLOTL',
                       "Coco Can't Sleep Tonight!")
FRONT_IMG = os.path.join(AXOLOTL,
    'Coco-ne-dort-pas-ce-soir-FR-8.5x11-spreads-V5', 'Diapositive1.JPG')
BACK_BG = os.path.join(AXOLOTL, 'nuit-étoilée-noire.png')
DARKEN_BACK = 0.55  # darken back cover (0=black, 1=original)

# ── Back cover text ──────────────────────────────
HOOK = "Votre enfant ne veut pas dormir ?"
HOOK2 = "Coco non plus !"
DESCRIPTION = (
    "Avec Coco, votre enfant d\u00e9couvre que tous "
    "les animaux ont besoin de dormir \u2014 mais "
    "chacun \u00e0 sa fa\u00e7on ! Saviez-vous que le "
    "dauphin dort avec un \u0153il ouvert ?\n\n"
    "Une histoire rassurante qui aide votre "
    "enfant \u00e0 s\u2019endormir en douceur, "
    "en transformant le coucher en un voyage "
    "extraordinaire dans le monde animal."
)
BULLETS = "9 animaux \u00b7 9 secrets du sommeil \u00b7 1 c\u00e2lin garanti"
AUTHOR = "Dr. Anita NIRVENA"
ILLUSTRATOR = "Illustrations : Loopinky"
AGE_INFO = "3\u20138 ans  \u00b7  30 pages"

# ── Fonts (minimum 14pt = 59px @ 300 DPI) ────────
def load_font(name, size):
    try:
        return ImageFont.truetype(name, size)
    except OSError:
        return ImageFont.truetype('arial.ttf', size)

FONT_HOOK = load_font('georgiab.ttf', 88)
FONT_HOOK2 = load_font('georgiab.ttf', 80)
FONT_DESC = load_font('calibri.ttf', 62)
FONT_TAGLINE = load_font('calibrib.ttf', 60)  # kept for potential use
FONT_BULLETS = load_font('calibrib.ttf', 60)
FONT_AUTHOR = load_font('calibrib.ttf', 60)
FONT_INFO = load_font('calibri.ttf', 60)
FONT_ILLUST = load_font('calibri.ttf', 60)


def fit_cover(img, target_w, target_h):
    """Resize and crop image to fill target area (cover fit)."""
    iw, ih = img.size
    scale = max(target_w / iw, target_h / ih)
    new_w = round(iw * scale)
    new_h = round(ih * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    # Center crop
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


def draw_text_centered(draw, text, y, font, fill='white', max_width=None,
                       center_x=None):
    """Draw text centered horizontally, with word-wrapping if max_width set."""
    if center_x is None:
        center_x = (MARGIN_LEFT + BACK_RIGHT) // 2

    if max_width:
        # Word wrap
        lines = []
        for paragraph in text.split('\n'):
            words = paragraph.split()
            line = ''
            for word in words:
                test = (line + ' ' + word).strip()
                bbox = font.getbbox(test)
                if bbox[2] > max_width and line:
                    lines.append(line)
                    line = word
                else:
                    line = test
            if line:
                lines.append(line)
    else:
        lines = text.split('\n')

    for line in lines:
        bbox = font.getbbox(line)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = center_x - tw // 2
        draw.text((x, y), line, font=font, fill=fill)
        y += th + 16
    return y


def draw_isbn_zone(draw):
    """Draw white rectangle for KDP barcode placement."""
    # 2" x 1.2" in bottom-right of back cover
    zone_w = round(2.0 * DPI)   # 600 px
    zone_h = round(1.2 * DPI)   # 360 px
    margin = round(0.375 * DPI)  # from trim edge

    x1 = BACK_RIGHT - margin - zone_w
    y1 = PX_H - MARGIN_LEFT - margin - zone_h
    x2 = x1 + zone_w
    y2 = y1 + zone_h

    # White rectangle with subtle rounded corners
    draw.rounded_rectangle([x1, y1, x2, y2], radius=20, fill='white')


def main():
    print("=" * 50)
    print("  KDP Cover Generator - Coco ne dort pas ce soir")
    print("=" * 50)
    print(f"  Binding      : {BINDING}")
    print(f"  Format       : {TRIM_W} x {TRIM_H} inches")
    print(f"  Paper        : {PAPER}")
    print(f"  Spine        : {SPINE_W:.3f} inches ({SPINE_W*25.4:.1f} mm)")
    if WRAP > 0:
        print(f"  Wrap         : {WRAP} inches (hardcover)")
    print(f"  Total cover  : {TOTAL_W:.3f} x {TOTAL_H:.3f} inches")
    print(f"  Pixels       : {PX_W} x {PX_H} @ {DPI} DPI")
    print()

    # ── 1. Create canvas ────────────────────────
    print("[1/5] Canvas...")
    canvas = Image.new('RGB', (PX_W, PX_H), (26, 26, 78))  # #1a1a4e

    # ── 2. Place back cover background ──────────
    print("[2/5] Fond 4eme de couverture...")
    back_bg = Image.open(BACK_BG).convert('RGB')
    # Cover the entire left side (bleed + back + spine), darkened
    back_fitted = fit_cover(back_bg, SPINE_RIGHT, PX_H)
    from PIL import ImageEnhance
    back_fitted = ImageEnhance.Brightness(back_fitted).enhance(DARKEN_BACK)
    canvas.paste(back_fitted, (0, 0))

    # ── 3. Place front cover ────────────────────
    print("[3/5] 1ere de couverture...")
    front = Image.open(FRONT_IMG).convert('RGB')
    front_w = PX_W - FRONT_LEFT  # from spine to right edge (incl bleed)
    front_fitted = fit_cover(front, front_w, PX_H)
    canvas.paste(front_fitted, (FRONT_LEFT, 0))

    # ── 4. Add back cover text (vertically centered) ──
    print("[4/5] Texte 4eme de couverture...")
    draw = ImageDraw.Draw(canvas)

    # Center of back cover (between bleed and back_right)
    cx = (MARGIN_LEFT + BACK_RIGHT) // 2
    text_max_w = round(6.5 * DPI)  # 6.5 inches max text width

    # Calculate total text block height for vertical centering
    def text_block_height(text, font, max_width=None):
        if max_width:
            lines = []
            for paragraph in text.split('\n'):
                words = paragraph.split()
                line = ''
                for word in words:
                    test = (line + ' ' + word).strip()
                    bbox = font.getbbox(test)
                    if bbox[2] > max_width and line:
                        lines.append(line)
                        line = word
                    else:
                        line = test
                if line:
                    lines.append(line)
        else:
            lines = text.split('\n')
        h = 0
        for line in lines:
            bbox = font.getbbox(line)
            h += (bbox[3] - bbox[1]) + 16
        return h

    GAP_SMALL = 30
    GAP_MED = 50
    GAP_LARGE = 60
    SEP_H = 50

    total_h = (
        text_block_height(HOOK, FONT_HOOK)
        + GAP_SMALL
        + text_block_height(HOOK2, FONT_HOOK2)
        + GAP_MED + SEP_H
        + text_block_height(DESCRIPTION, FONT_DESC, text_max_w)
        + GAP_LARGE
        + text_block_height(BULLETS, FONT_BULLETS)
        + GAP_LARGE
        + text_block_height(AUTHOR, FONT_AUTHOR)
        + GAP_SMALL
        + text_block_height(ILLUSTRATOR, FONT_ILLUST)
        + GAP_SMALL
        + text_block_height(AGE_INFO, FONT_INFO)
    )

    # Vertically center (leave space for ISBN zone at bottom)
    isbn_reserve = round(2.0 * DPI)  # reserve bottom area for barcode
    available_h = PX_H - isbn_reserve
    y = max(BLEED_PX + 40, (available_h - total_h) // 2)

    # Hook
    y = draw_text_centered(draw, HOOK, y, FONT_HOOK, fill='white',
                           center_x=cx)
    y += GAP_SMALL

    # Hook2
    y = draw_text_centered(draw, HOOK2, y, FONT_HOOK2,
                           fill=(200, 180, 255),  # soft lavender
                           center_x=cx)

    # Separator
    y += GAP_MED
    sep_w = round(1.5 * DPI)
    draw.line([(cx - sep_w//2, y), (cx + sep_w//2, y)],
              fill=(255, 255, 255, 150), width=3)
    y += SEP_H

    # Description
    y = draw_text_centered(draw, DESCRIPTION, y, FONT_DESC,
                           fill=(255, 255, 255, 230),
                           max_width=text_max_w, center_x=cx)

    # Bullets (soft lavender)
    y += GAP_LARGE
    y = draw_text_centered(draw, BULLETS, y, FONT_BULLETS,
                           fill=(200, 180, 255), center_x=cx)

    # Author + illustrator
    y += GAP_LARGE
    y = draw_text_centered(draw, AUTHOR, y, FONT_AUTHOR, fill='white',
                           center_x=cx)
    y += GAP_SMALL
    y = draw_text_centered(draw, ILLUSTRATOR, y, FONT_ILLUST,
                           fill=(255, 255, 255, 200), center_x=cx)

    # Age info
    y += GAP_SMALL
    draw_text_centered(draw, AGE_INFO, y, FONT_INFO,
                       fill=(255, 255, 255, 180), center_x=cx)

    # ── 5. ISBN barcode zone ────────────────────
    # Ne pas dessiner de rectangle blanc : KDP place son propre code-barres.
    # On garde juste isbn_reserve dans le calcul vertical pour ne rien mettre
    # dans cette zone.

    # ── Export ──────────────────────────────────
    print("[5/5] Export...")

    # PNG preview
    png_path = os.path.join(OUT_DIR, 'cover-preview.png')
    canvas.save(png_path, 'PNG')
    print(f"  PNG : {png_path}")

    # PDF at 300 DPI
    pdf_path = os.path.join(OUT_DIR, 'cover.pdf')
    canvas.save(pdf_path, 'PDF', resolution=DPI)
    print(f"  PDF : {pdf_path}")

    sz = os.path.getsize(pdf_path) / (1024 * 1024)

    # ── 6. Ebook cover (front only, 1600x2560) ───
    print("[6/6] Couverture ebook...")
    EBOOK_W, EBOOK_H = 1600, 2560  # KDP Kindle recommended
    ebook = Image.open(FRONT_IMG).convert('RGB')
    ebook = fit_cover(ebook, EBOOK_W, EBOOK_H)
    ebook_path = os.path.join(OUT_DIR, 'ebook-cover.jpg')
    ebook.save(ebook_path, 'JPEG', quality=95)
    ebook_sz = os.path.getsize(ebook_path) / 1024
    print(f"  JPG : {ebook_path} ({ebook_sz:.0f} KB)")

    print(f"\n{'=' * 50}")
    print(f"  TERMINE !")
    print(f"  Paperback  : {PX_W} x {PX_H} px ({TOTAL_W:.3f} x {TOTAL_H:.3f} in)")
    print(f"  PDF        : {sz:.1f} MB")
    print(f"  Ebook      : {EBOOK_W} x {EBOOK_H} px")
    print(f"{'=' * 50}")


if __name__ == '__main__':
    main()
