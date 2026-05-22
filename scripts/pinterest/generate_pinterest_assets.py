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
    ("freebies/i-love-you-more-free-coloring-1.png", "Mother and Baby Axolotl Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("freebies/coco-kitten_coloring-video.png", "Coco and Kitten Yarn Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("freebies/coco-puppy-coloring.png", "Coco and Puppy Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("freebies/coco-kitten_coloring.png", "Coco and Kitten Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("freebies/coco-christmas.png", "Christmas Axolotl Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("freebies/coco-and-girl.png", "Coco and Girl Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("freebies/coco-and-boy.png", "Coco and Boy Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("freebies/coco et le chaton.png", "Coco and Little Cat Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("freebies/underwater-scene.png", "Underwater Coloring Page for Kids", "Free Coloring Pages for Kids", "/freebies/"),
    ("freebies/axolotl-emotions.png", "Axolotl Emotions Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("freebies/coco_puppy.png", "Cute Puppy Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("freebies/coco_rabbit-coloring.png", "Coco Rabbit Coloring Page", "Axolotl Coloring & Crafts", "/freebies/"),
    ("freebies/dolphin-coloring-page.png", "Dolphin Coloring Page for Kids", "Free Coloring Pages for Kids", "/freebies/"),
    ("freebies/dragon-coloring-page/dragon_and_axolotl_freebie.png", "Dragon and Axolotl Coloring Page", "Axolotl Coloring & Crafts", "/freebies/dragon-coloring-page/"),
    ("freebies/unicorn-coloring-page/unicorn_axolotl_freebie_colorin_page.png", "Unicorn and Axolotl Coloring Page", "Axolotl Coloring & Crafts", "/freebies/unicorn-coloring-page/"),
    ("freebies/dinosaur-coloring-page/dinosaur_and_axolotl_coloring_page.png", "Dinosaur and Axolotl Coloring Page", "Axolotl Coloring & Crafts", "/freebies/dinosaur-coloring-page/"),
    ("freebies/dog-coloring-page/dog_and_axolotl-freebie.png", "Dog and Axolotl Coloring Page", "Axolotl Coloring & Crafts", "/freebies/dog-coloring-page/"),
    ("freebies/dolphin-coloring-page/dolphin-coloring-page_freebie.png", "Coco Dolphin Coloring Page", "Axolotl Coloring & Crafts", "/freebies/dolphin-coloring-page/"),
    ("freebies/bear-coloring-page/bear_freebie.png", "Bear Coloring Page for Kids", "Free Coloring Pages for Kids", "/freebies/bear-coloring-page/"),
    ("freebies/turtle-coloring-page/turtle_and_axolotl_freebie.png", "Turtle and Axolotl Coloring Page", "Axolotl Coloring & Crafts", "/freebies/turtle-coloring-page/"),
    ("freebies/cat-coloring-page/cat_and_axolotl-freebie.png", "Cat and Axolotl Coloring Page", "Axolotl Coloring & Crafts", "/freebies/cat-coloring-page/"),
    ("freebies/coco-rabbit-cbn-v2.png", "Coco Rabbit Color by Number", "Color by Number", "/freebies/"),
    ("freebies/coco-rabbit-cbn-v2-full.png", "Rabbit Color by Number Printable", "Color by Number", "/freebies/"),
    ("freebies/coco-rabbit-cbn.png", "Easy Color by Number for Kids", "Color by Number", "/freebies/"),
    ("freebies/coco-rabbit-cbn-full.png", "Free Color by Number Activity", "Color by Number", "/freebies/"),
    ("activity:maze:easy", "Easy Kids Maze Printable", "Kids Mazes Printable", "/maze/"),
    ("activity:maze:dragon", "Dragon Maze Printable for Kids", "Kids Mazes Printable", "/maze/"),
    ("activity:dot:axolotl", "Axolotl Dot to Dot Printable", "Dot to Dot Activities", "/dot-to-dot/"),
    ("activity:dot:ocean", "Ocean Dot to Dot Activity", "Dot to Dot Activities", "/dot-to-dot/"),
    ("activity:word:ocean", "Ocean Word Search for Kids", "Word Search for Kids", "/word-search/"),
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
