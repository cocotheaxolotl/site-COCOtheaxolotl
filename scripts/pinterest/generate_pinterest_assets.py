from __future__ import annotations

import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "pinterest-pins"
QUEUE_PATH = ROOT / "scripts" / "pinterest" / "pins-queue.json"

PINK = "#ff69b4"
DEEP = "#4b2e3f"
SOFT_BG = "#fff7fb"
TEXT_GRAY = "#5b5360"
SITE = "cocotheaxolotl.org"
CAMPAIGN = "launch"


ITEMS = [
    ("LIVRES COCO/Coco Can't Sleep Tonight!/coloring Coco can't sleep tonight/9-coloring-chat.png", "Coco and Cat Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("LIVRES COCO/Coco Can't Sleep Tonight!/coloring Coco can't sleep tonight/11-coloring-flamant-rose.png", "Coco and Flamingo Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("LIVRES COCO/I love you more/coloring _I_love_you_more/Walking under starry skies_coloring.png", "Walking Under Starry Skies Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("LIVRES COCO/I love you more/coloring _I_love_you_more/Bedtime warmth between axolotls_coloring.png", "Bedtime Axolotl Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("LIVRES COCO/I love you more/coloring _I_love_you_more/Axolotls in glowing orbs of joy_coloring.png", "Glowing Orbs Axolotl Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("LIVRES COCO/I love you more/coloring _I_love_you_more/Axolotls in a joyful meadow_coloring.png", "Joyful Meadow Axolotl Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("LIVRES COCO/I love you more/coloring _I_love_you_more/Under the starry embrace_coloring.png", "Starry Embrace Axolotl Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("LIVRES COCO/I love you more/coloring _I_love_you_more/Tender moment under the night sky_coloring.png", "Tender Night Sky Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("LIVRES COCO/I love you more/coloring _I_love_you_more/Axolotl mother and child in sunlight_coloring.png", "Sunlight Axolotl Family Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("LIVRES COCO/I love you more/coloring _I_love_you_more/A loving hug under the stars_coloring.png", "Loving Hug Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("LIVRES COCO/I love you more/coloring _I_love_you_more/Night under the stars with axolotls_coloring.png", "Axolotls Under the Stars Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("LIVRES COCO/I love you more/coloring _I_love_you_more/Mother and child axolotls in love_coloring.png", "Mother and Child Axolotls Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("LIVRES COCO/I love you more/coloring _I_love_you_more/Joyful axolotls in a meadow_coloring.png", "Happy Axolotls Meadow Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("LIVRES COCO/I love you more/coloring _I_love_you_more/Joyful axolotls in a sunlit meadow_coloring.png", "Sunlit Meadow Axolotl Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("LIVRES COCO/I love you more/coloring _I_love_you_more/Joyful axolotl under a glowing star_coloring.png", "Glowing Star Axolotl Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("LIVRES COCO/I love you more/coloring _I_love_you_more/Starry night with a cozy axolotl_coloring.png", "Cozy Starry Night Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("LIVRES COCO/I love you more/coloring _I_love_you_more/A joyful hug under the stars_coloring_.png", "Joyful Hug Under Stars Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("freebies/i-love-you-more-free-coloring-1.png", "Mother and Baby Axolotl Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("LIVRES COCO/I love you more/coloring _I_love_you_more/Mother and baby axolotl under the stars_coloring_.png", "Mother and Baby Stars Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("LIVRES COCO/I love you more/coloring _I_love_you_more/Cheerful axolotl on a sunny path_coloring_.png", "Sunny Path Axolotl Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("LIVRES COCO/I love you more/coloring _I_love_you_more/Dreaming under a starry sky_coloring_.png", "Dreaming Starry Sky Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("LIVRES COCO/I love you more/coloring _I_love_you_more/A mother's love under the stars_coloring_.png", "Mother's Love Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("LIVRES COCO/I love you more/coloring _I_love_you_more/Under the starry night sky_coloring_.png", "Starry Night Sky Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("LIVRES COCO/I love you more/coloring _I_love_you_more/Morning hug in the kitchen_coloring_.png", "Morning Hug Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("LIVRES COCO/Whose egg is this/whose-egg-colored/coloring_image de home page coco pâques_sans_fond.png", "Coco Easter Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("LIVRES COCO/Coco Can't Sleep Tonight!/coloring Coco can't sleep tonight/12-coloring-paresseux.png", "Coco and Sloth Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("LIVRES COCO/Coco Can't Sleep Tonight!/coloring Coco can't sleep tonight/6-coloring-loutre.png", "Coco and Otter Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("LIVRES COCO/Coco Can't Sleep Tonight!/coloring Coco can't sleep tonight/4-coloring-hibou.png", "Coco and Owl Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("LIVRES COCO/Coco Can't Sleep Tonight!/coloring Coco can't sleep tonight/5-coloring-dauphin.png", "Coco and Dolphin Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("LIVRES COCO/Coco Can't Sleep Tonight!/coloring Coco can't sleep tonight/7-coloriage-koala.png", "Coco and Koala Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/baloo2-bold.ttf" if bold else "C:/Windows/Fonts/baloo2-regular.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def wrap(draw: ImageDraw.ImageDraw, text: str, font_obj: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=font_obj)[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines[:3]


def slug_words(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def make_description(title: str, board_name: str) -> str:
    age = "ages 4-8" if "Color by Number" not in board_name else "ages 5-9"
    keyword = "free printable coloring page"
    if board_name == "Color by Number":
        keyword = "free color by number printable"
    elif board_name == "Kids Mazes Printable":
        keyword = "free printable maze"
        age = "ages 5-10"
    elif board_name == "Dot to Dot Activities":
        keyword = "free dot to dot printable"
        age = "ages 4-9"
    elif board_name == "Word Search for Kids":
        keyword = "free word search printable"
        age = "ages 6-10"
    subject = title
    for suffix in (" Coloring Page for Kids", " Coloring Page", " Printable Activity", " Page"):
        subject = subject.replace(suffix, "")
    return (
        f"Download this {keyword} featuring {subject.lower()}. "
        f"Perfect for kids {age} who love cute animals, simple art activities, and print-at-home fun. "
        f"Print on A4 or US Letter paper and discover more free kids activities at {SITE}."
    )


def make_title(title: str, board_name: str) -> str:
    subject = title
    for suffix in (" Coloring Page for Kids", " Coloring Page", " Printable Activity", " Page"):
        subject = subject.replace(suffix, "")
    if board_name == "Color by Number":
        text = f"{subject} - Free Color by Number Printable"
    elif board_name == "Kids Mazes Printable":
        text = f"{subject} - Free Maze Printable"
    elif board_name == "Dot to Dot Activities":
        text = f"{subject} - Free Dot to Dot Printable"
    elif board_name == "Word Search for Kids":
        text = f"{subject} - Free Word Search Printable"
    elif "Axolotl" in title or "Coco" in title:
        text = f"{subject} - Free Axolotl Coloring Page"
    else:
        text = f"{subject} - Free Printable Coloring Page"
    return text[:100]


def draw_centered(draw: ImageDraw.ImageDraw, y: int, text: str, font_obj: ImageFont.ImageFont, fill: str) -> int:
    bbox = draw.textbbox((0, 0), text, font=font_obj)
    x = (1000 - (bbox[2] - bbox[0])) // 2
    draw.text((x, y), text, font=font_obj, fill=fill)
    return bbox[3] - bbox[1]


def add_site_mark(image: Image.Image) -> Image.Image:
    marked = image.copy()
    draw = ImageDraw.Draw(marked)
    size = max(24, min(46, marked.width // 18))
    mark_font = font(size, bold=True)
    text = SITE
    bbox = draw.textbbox((0, 0), text, font=mark_font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (marked.width - text_w) // 2
    y = max(12, marked.height - text_h - max(18, marked.height // 35))
    draw.rounded_rectangle(
        (x - 18, y - 10, x + text_w + 18, y + text_h + 12),
        radius=14,
        fill=(255, 255, 255, 225),
    )
    draw.text((x, y), text, font=mark_font, fill=PINK, stroke_width=2, stroke_fill="white")
    return marked


def compose_pin(source: Path, title: str, target: Path) -> None:
    canvas = Image.new("RGB", (1000, 1500), SOFT_BG)
    draw = ImageDraw.Draw(canvas)

    draw.rectangle((0, 0, 1000, 190), fill=PINK)
    draw_centered(draw, 55, "FREE PRINTABLE", font(72, bold=True), "white")

    title_font = font(58, bold=True)
    lines = wrap(draw, title, title_font, 820)
    title_y = 245
    for line in lines:
        line_h = draw_centered(draw, title_y, line, title_font, DEEP)
        title_y += line_h + 8

    paper = Image.new("RGB", (790, 820), "white")
    src = Image.open(source).convert("RGBA")
    src = ImageOps.contain(src, (720, 735), Image.Resampling.LANCZOS)
    src_bg = Image.new("RGBA", src.size, "white")
    src_bg.alpha_composite(src)
    src_bg = add_site_mark(src_bg)

    paper_draw = ImageDraw.Draw(paper)
    paper_draw.rounded_rectangle((0, 0, 789, 819), radius=18, outline="#f3c4da", width=4)
    x = (790 - src_bg.width) // 2
    y = 42 + (735 - src_bg.height) // 2
    paper.paste(src_bg.convert("RGB"), (x, y))

    shadow = Image.new("RGBA", (830, 860), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle((24, 24, 824, 854), radius=22, fill=(92, 45, 72, 35))
    canvas.paste(shadow, (85, 510), shadow)
    canvas.paste(paper, (105, 500))

    draw.rectangle((0, 1398, 1000, 1500), fill=PINK)
    draw_centered(draw, 1426, SITE, font(46, bold=True), "white")
    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target, "PNG", optimize=True)


def compose_activity_pin(kind: str, title: str, target: Path) -> None:
    canvas = Image.new("RGB", (1000, 1500), SOFT_BG)
    draw = ImageDraw.Draw(canvas)

    draw.rectangle((0, 0, 1000, 190), fill=PINK)
    draw_centered(draw, 55, "FREE PRINTABLE", font(72, bold=True), "white")

    title_font = font(58, bold=True)
    lines = wrap(draw, title, title_font, 820)
    title_y = 245
    for line in lines:
        line_h = draw_centered(draw, title_y, line, title_font, DEEP)
        title_y += line_h + 8

    paper = Image.new("RGB", (790, 820), "white")
    pd = ImageDraw.Draw(paper)
    pd.rounded_rectangle((0, 0, 789, 819), radius=18, outline="#f3c4da", width=4)

    if kind.startswith("maze"):
        draw_maze_preview(pd)
    elif kind.startswith("dot"):
        draw_dot_preview(pd)
    else:
        draw_word_search_preview(pd)

    shadow = Image.new("RGBA", (830, 860), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((24, 24, 824, 854), radius=22, fill=(92, 45, 72, 35))
    canvas.paste(shadow, (85, 510), shadow)
    canvas.paste(paper, (105, 500))

    draw.rectangle((0, 1398, 1000, 1500), fill=PINK)
    draw_centered(draw, 1426, SITE, font(46, bold=True), "white")
    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target, "PNG", optimize=True)


def draw_maze_preview(draw: ImageDraw.ImageDraw) -> None:
    line = "#222222"
    cell = 58
    left = 78
    top = 80
    cols = 11
    rows = 10
    draw.text((98, 38), "START", font=font(28, bold=True), fill=TEXT_GRAY)
    draw.text((592, 720), "FINISH", font=font(28, bold=True), fill=TEXT_GRAY)
    for r in range(rows + 1):
        y = top + r * cell
        draw.line((left, y, left + cols * cell, y), fill=line, width=5)
    for c in range(cols + 1):
        x = left + c * cell
        draw.line((x, top, x, top + rows * cell), fill=line, width=5)
    openings = [
        (left, top, left, top + cell),
        (left + cols * cell, top + (rows - 1) * cell, left + cols * cell, top + rows * cell),
    ]
    for x1, y1, x2, y2 in openings:
        draw.line((x1, y1, x2, y2), fill="white", width=10)
    for c, r in [(1, 1), (2, 1), (2, 2), (4, 1), (5, 3), (7, 2), (8, 4), (3, 5), (6, 6), (9, 7)]:
        x = left + c * cell
        y = top + r * cell
        draw.line((x, y, x + cell, y), fill="white", width=10)
    path = [(105, 108), (165, 108), (165, 225), (282, 225), (282, 342), (455, 342), (455, 516), (630, 516), (630, 630), (710, 630)]
    draw.line(path, fill=PINK, width=8)


def draw_dot_preview(draw: ImageDraw.ImageDraw) -> None:
    pts = [(400, 155), (500, 175), (585, 240), (630, 350), (610, 475), (520, 565), (380, 585), (270, 520), (215, 400), (235, 285), (310, 200)]
    for index, (x, y) in enumerate(pts, start=1):
        draw.ellipse((x - 12, y - 12, x + 12, y + 12), fill="#222222")
        draw.text((x + 18, y - 16), str(index), font=font(24, bold=True), fill=TEXT_GRAY)
    for p1, p2 in zip(pts, pts[1:]):
        draw.line((p1, p2), fill="#dddddd", width=3)
    draw.text((235, 675), "Connect 1 to 11", font=font(40, bold=True), fill=DEEP)


def draw_word_search_preview(draw: ImageDraw.ImageDraw) -> None:
    letters = [
        "A X O L O T L S",
        "W A V E S E A H",
        "C O C O P I N K",
        "B U B B L E S I",
        "S M I L E F U N",
        "C R A Y O N S D",
        "O C E A N K I D",
        "P R I N T A B L",
    ]
    x0, y0 = 138, 120
    for r, row in enumerate(letters):
        for c, letter in enumerate(row.split()):
            x = x0 + c * 68
            y = y0 + r * 68
            draw.rectangle((x - 20, y - 16, x + 42, y + 46), outline="#f3c4da", width=2)
            draw.text((x, y), letter, font=font(34, bold=True), fill="#222222")
    draw.text((170, 705), "Find: COCO, OCEAN, AXOLOTL", font=font(32, bold=True), fill=DEEP)


def build_queue() -> list[dict[str, object]]:
    queue = []
    for index, (source, title, board_name, link_path) in enumerate(ITEMS, start=1):
        filename = f"pin-{index:03d}.png"
        link = f"https://{SITE}{link_path}?utm_source=pinterest&utm_medium=pin&utm_campaign={CAMPAIGN}"
        queue.append(
            {
                "id": f"pin-{index:03d}",
                "status": "pending",
                "title": make_title(title, board_name),
                "description": make_description(title, board_name),
                "link": link,
                "board_name": board_name,
                "media_url": f"https://{SITE}/pinterest-pins/{filename}",
                "alt_text": f"{title} with a pink Free Printable banner for kids.",
                "local_source": source,
                "local_pin": f"pinterest-pins/{filename}",
                "keywords": slug_words(title),
            }
        )
    return queue


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for index, (source, title, _board_name, _link_path) in enumerate(ITEMS, start=1):
        if source.startswith("activity:"):
            _prefix, kind, _variant = source.split(":", 2)
            compose_activity_pin(kind, title, OUTPUT_DIR / f"pin-{index:03d}.png")
        else:
            source_path = ROOT / source
            if not source_path.exists():
                raise FileNotFoundError(source_path)
            compose_pin(source_path, title, OUTPUT_DIR / f"pin-{index:03d}.png")

    queue = build_queue()
    QUEUE_PATH.write_text(json.dumps(queue, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {len(queue)} pins in {OUTPUT_DIR}")
    print(f"Wrote queue to {QUEUE_PATH}")


if __name__ == "__main__":
    main()
