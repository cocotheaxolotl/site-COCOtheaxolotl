"""
Build final YouTube Short from Kling video + text overlays + CTA
Kitten page - "Whose Egg Is This?"
"""

import os
from pathlib import Path
from PIL import Image
import numpy as np

from moviepy import (
    VideoFileClip, TextClip, CompositeVideoClip, ColorClip, ImageClip,
)
from moviepy.video.fx import CrossFadeIn, CrossFadeOut

# ─── PATHS ──────────────────────────────────────────────────────────────────
BASE = Path(__file__).parent
OUTPUT_DIR = BASE / "animated-readaloud"
OUTPUT_DIR.mkdir(exist_ok=True)

KLING_VIDEO = OUTPUT_DIR / "coco-kitten_EN.mp4"
COLORING_IMG = Path(r"C:\Users\33612\Documents\site_COCOtheaxolotl\freebies\coco-kitten_coloring-video.png")

# ─── Load Kling clip ─────────────────────────────────────────────────────
print("Loading Kling video...")
clip = VideoFileClip(str(KLING_VIDEO))
VIDEO_W, VIDEO_H = clip.size
DURATION = clip.duration
FPS = clip.fps
print(f"  Size: {VIDEO_W}x{VIDEO_H}, Duration: {DURATION:.1f}s, FPS: {FPS}")

# ─── Font ─────────────────────────────────────────────────────────────────
font_candidates = [
    "C:/Windows/Fonts/comicbd.ttf",
    "C:/Windows/Fonts/comic.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]
chosen_font = "Arial"
for f in font_candidates:
    if os.path.exists(f):
        chosen_font = f
        break
print(f"  Font: {chosen_font}")

# ─── Text overlays ────────────────────────────────────────────────────────
print("Building text overlays...")
text_clips = []

# --- Narration texts (top of screen) ---
narration = [
    ("Coco met a tiny kitten\nplaying with a ball of yarn.", 1.0, 5.5),
    ('"Is this your eggshell,\nlittle kitten?"', 5.5, 9.5),
    ("The kitten purred\nand shook its head.", 9.5, 13.0),
    ('"No, silly!\nKittens don\'t hatch from eggs!\nBut keep looking!"', 13.0, 17.5),
]

# Semi-transparent bar behind narration text
for line_text, start_t, end_t in narration:
    # Background bar
    bar_h = 140
    bar = (ColorClip(size=(VIDEO_W - 40, bar_h), color=(255, 240, 248))
           .with_opacity(0.80)
           .with_position(("center", 60))
           .with_start(start_t)
           .with_duration(end_t - start_t))
    text_clips.append(bar)

    # Text
    try:
        txt = (TextClip(
            text=line_text,
            font_size=36,
            color="rgb(80, 40, 60)",
            font=chosen_font,
            stroke_color="white",
            stroke_width=2,
            method="caption",
            size=(VIDEO_W - 100, None),
            text_align="center",
        )
        .with_position(("center", 75))
        .with_start(start_t)
        .with_duration(end_t - start_t))
        text_clips.append(txt)
    except Exception as e:
        print(f"  WARN: {e}")

# --- "Did you know?" box (replaces narration near end) ---
DYK_START = 17.5
DYK_END = DURATION
dyk_text = "Did you know?\nKittens are born with their\neyes closed. They can't see\nfor the first 7-10 days!"

try:
    dyk_bar = (ColorClip(size=(VIDEO_W - 40, 200), color=(255, 250, 220))
               .with_opacity(0.90)
               .with_position(("center", 50))
               .with_start(DYK_START)
               .with_duration(DYK_END - DYK_START))
    text_clips.append(dyk_bar)

    dyk_clip = (TextClip(
        text=dyk_text,
        font_size=32,
        color="rgb(100, 60, 20)",
        font=chosen_font,
        method="caption",
        size=(VIDEO_W - 100, None),
        text_align="center",
    )
    .with_position(("center", 65))
    .with_start(DYK_START)
    .with_duration(DYK_END - DYK_START))
    text_clips.append(dyk_clip)
except Exception as e:
    print(f"  WARN dyk: {e}")

# --- CTA: Free coloring pages (bottom of screen, always visible from ~3s) ---
CTA_START = 3.0
CTA_TEXT = "FREE coloring pages!\ncocotheaxolotl.org/freebies"

try:
    cta_bar = (ColorClip(size=(VIDEO_W - 40, 110), color=(220, 80, 140))
               .with_opacity(0.90)
               .with_position(("center", VIDEO_H - 180))
               .with_start(CTA_START)
               .with_duration(DURATION - CTA_START)
               .with_effects([CrossFadeIn(0.5)]))
    text_clips.append(cta_bar)

    cta_clip = (TextClip(
        text=CTA_TEXT,
        font_size=32,
        color="white",
        font=chosen_font,
        stroke_color="rgb(150, 40, 80)",
        stroke_width=2,
        method="caption",
        size=(VIDEO_W - 100, None),
        text_align="center",
    )
    .with_position(("center", VIDEO_H - 170))
    .with_start(CTA_START)
    .with_duration(DURATION - CTA_START)
    .with_effects([CrossFadeIn(0.5)]))
    text_clips.append(cta_clip)
except Exception as e:
    print(f"  WARN cta: {e}")

# --- Coloring page preview (appears with CTA in last 5 seconds) ---
COLORING_START = DURATION - 5.0
print("  Adding coloring page preview...")

try:
    col_img = Image.open(COLORING_IMG).convert("RGBA")
    # Scale to fit ~40% of video width
    col_target_w = int(VIDEO_W * 0.45)
    col_ratio = col_target_w / col_img.width
    col_target_h = int(col_img.height * col_ratio)
    col_img = col_img.resize((col_target_w, col_target_h), Image.LANCZOS)

    # White border / card effect
    border = 8
    card = Image.new("RGBA", (col_target_w + border * 2, col_target_h + border * 2), (255, 255, 255, 240))
    card.paste(col_img, (border, border), col_img)
    col_array = np.array(card)

    # Position: center, above CTA bar
    col_x = VIDEO_W // 2 - card.width // 2
    col_y = VIDEO_H - 180 - card.height - 20

    col_clip = (ImageClip(col_array)
                .with_duration(5.0)
                .with_position((col_x, col_y))
                .with_start(COLORING_START)
                .with_effects([CrossFadeIn(0.5)]))
    text_clips.append(col_clip)

    # Label above image
    col_label = (TextClip(
        text="Get this FREE coloring page!",
        font_size=30,
        color="rgb(220, 80, 140)",
        font=chosen_font,
        stroke_color="white",
        stroke_width=2,
    )
    .with_position(("center", col_y - 45))
    .with_start(COLORING_START)
    .with_duration(5.0)
    .with_effects([CrossFadeIn(0.5)]))
    text_clips.append(col_label)
except Exception as e:
    print(f"  WARN coloring: {e}")

# ─── Compose & render ────────────────────────────────────────────────────
print("Compositing...")
final = CompositeVideoClip(
    [clip] + text_clips,
    size=(VIDEO_W, VIDEO_H)
).with_duration(DURATION)

output_path = OUTPUT_DIR / "kitten_short_final_EN.mp4"
print(f"Rendering {output_path}...")

final.write_videofile(
    str(output_path),
    fps=FPS,
    codec="libx264",
    audio=False,
    preset="medium",
    bitrate="8000k",
    logger="bar",
)

print(f"\nDONE! {output_path}")
print(f"Size: {output_path.stat().st_size / 1024 / 1024:.1f} MB")
