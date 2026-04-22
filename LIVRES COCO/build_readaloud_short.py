"""
YouTube Short / TikTok / Reels - "Whose Egg Is This?" Kitten page
Format: 9:16 vertical (1080x1920), max 60s
Uses the new eyes-open foreground image
"""

import os
import math
from pathlib import Path
from PIL import Image
import numpy as np

from moviepy import (
    ImageClip, TextClip, CompositeVideoClip,
    ColorClip, VideoClip,
)
from moviepy.video.fx import CrossFadeIn

# ─── PATHS ──────────────────────────────────────────────────────────────────
BASE = Path(__file__).parent
OUTPUT_DIR = BASE / "animated-readaloud"
OUTPUT_DIR.mkdir(exist_ok=True)

FG_PATH = OUTPUT_DIR / "coco-kitten-no-background.png"
BG_PATH = OUTPUT_DIR / "kitten_background_v2.png"

# ─── Video settings (9:16 vertical Short) ─────────────────────────────────
VIDEO_W, VIDEO_H = 1080, 1920
FPS = 30
DURATION = 30  # 30s short

# ═══════════════════════════════════════════════════════════════════════════
# STEP 1: Load foreground
# ═══════════════════════════════════════════════════════════════════════════
print("STEP 1: Loading foreground...")
fg_clean = Image.open(FG_PATH).convert("RGBA")
print(f"  Foreground: {fg_clean.size}")

# ═══════════════════════════════════════════════════════════════════════════
# STEP 2: Load background + scale for Ken Burns
# ═══════════════════════════════════════════════════════════════════════════
print("STEP 2: Loading background...")
bg_img = Image.open(BG_PATH).convert("RGB")

# For vertical format, crop background to 9:16 center then scale up
bg_orig_w, bg_orig_h = bg_img.size
target_ratio = VIDEO_W / VIDEO_H  # 0.5625
bg_ratio = bg_orig_w / bg_orig_h

if bg_ratio > target_ratio:
    # Background is wider — crop sides
    new_w = int(bg_orig_h * target_ratio)
    left = (bg_orig_w - new_w) // 2
    bg_img = bg_img.crop((left, 0, left + new_w, bg_orig_h))
else:
    # Background is taller — crop top/bottom
    new_h = int(bg_orig_w / target_ratio)
    top = (bg_orig_h - new_h) // 2
    bg_img = bg_img.crop((0, top, bg_orig_w, top + new_h))

BG_SCALE = 1.25
bg_w = int(VIDEO_W * BG_SCALE)
bg_h = int(VIDEO_H * BG_SCALE)
bg_img = bg_img.resize((bg_w, bg_h), Image.LANCZOS)
bg_array = np.array(bg_img)
print(f"  Scaled BG: {bg_w}x{bg_h}")

# ═══════════════════════════════════════════════════════════════════════════
# STEP 3: Build animated short
# ═══════════════════════════════════════════════════════════════════════════
print("STEP 3: Building short...")

# Foreground — fill ~55% of width, centered in lower half
fg_target_w = int(VIDEO_W * 0.85)
fg_ratio = fg_target_w / fg_clean.width
fg_target_h = int(fg_clean.height * fg_ratio)
fg_resized = fg_clean.resize((fg_target_w, fg_target_h), Image.LANCZOS)
fg_array = np.array(fg_resized)

fg_base_x = VIDEO_W // 2 - fg_target_w // 2
fg_base_y = VIDEO_H // 2 - fg_target_h // 4  # lower center
print(f"  FG: {fg_target_w}x{fg_target_h}, pos: ({fg_base_x}, {fg_base_y})")

# Ken Burns background
def make_ken_burns_frame(t):
    progress = t / DURATION
    zoom = 1.0 + 0.08 * progress
    cw = int(VIDEO_W / zoom)
    ch = int(VIDEO_H / zoom)
    pan_x = int(10 * math.sin(2 * math.pi * progress))
    pan_y = int(15 * progress)
    cx = (bg_w - cw) // 2 + pan_x
    cy = (bg_h - ch) // 2 + pan_y
    cx = max(0, min(cx, bg_w - cw))
    cy = max(0, min(cy, bg_h - ch))
    cropped = bg_array[cy:cy + ch, cx:cx + cw]
    pil_resized = Image.fromarray(cropped).resize((VIDEO_W, VIDEO_H), Image.LANCZOS)
    return np.array(pil_resized)

bg_clip = VideoClip(make_ken_burns_frame, duration=DURATION)

# Foreground: fade in, gentle sway
def fg_position(t):
    if t < 1.0:
        progress = t / 1.0
        ease = 1 - (1 - progress) ** 3
        start_y = fg_base_y + 80
        x = fg_base_x
        y = int(start_y + (fg_base_y - start_y) * ease)
    else:
        ft = t - 1.0
        x = fg_base_x + int(2 * math.sin(2 * math.pi * ft / 8))
        y = fg_base_y + int(1 * math.sin(2 * math.pi * ft / 6))
    return (x, y)

fg_clip = (ImageClip(fg_array)
           .with_duration(DURATION)
           .with_position(fg_position)
           .with_effects([CrossFadeIn(1.0)]))

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
print("  Building text overlays...")

narration_lines = [
    ("Coco met a tiny kitten\nplaying with a ball of yarn.", 1.5, 6.0),
    ('"Is this your eggshell,\nlittle kitten?"', 6.5, 11.0),
    ("The kitten purred\nand shook its head.", 11.5, 16.0),
    ('"No, silly!\nKittens don\'t hatch from eggs!"', 16.5, 22.0),
    ('"But keep looking!"', 22.5, 26.0),
]

dyk_text = ("Did you know?\nKittens are born with\ntheir eyes closed.\nThey can't see for\nthe first 7-10 days!")

text_clips = []

# Text bar at top
TEXT_BAR_Y = 60
TEXT_BAR_H = 180
text_bar = (ColorClip(size=(VIDEO_W - 80, TEXT_BAR_H), color=(255, 240, 248))
            .with_opacity(0.85)
            .with_position(("center", TEXT_BAR_Y))
            .with_duration(DURATION - 1.0)
            .with_start(1.0))
text_clips.append(text_bar)

TEXT_Y = TEXT_BAR_Y + 20
for line_text, start_t, end_t in narration_lines:
    try:
        txt = (TextClip(
            text=line_text,
            font_size=42,
            color="rgb(80, 40, 60)",
            font=chosen_font,
            stroke_color="white",
            stroke_width=2,
            method="caption",
            size=(VIDEO_W - 140, None),
            text_align="center",
        )
        .with_position(("center", TEXT_Y))
        .with_start(start_t)
        .with_duration(end_t - start_t))
        text_clips.append(txt)
    except Exception as e:
        print(f"  WARN text: {e}")

# Title
try:
    title_clip = (TextClip(
        text="Whose Egg Is This?",
        font_size=52,
        color="rgb(220, 80, 140)",
        font=chosen_font,
        stroke_color="white",
        stroke_width=3,
    )
    .with_position(("center", 10))
    .with_start(0.2)
    .with_duration(4.0))
    text_clips.append(title_clip)
except Exception as e:
    print(f"  WARN title: {e}")

# "Did you know?" box at the end
try:
    dyk_bg = (ColorClip(size=(VIDEO_W - 80, 280), color=(255, 250, 220))
              .with_opacity(0.9)
              .with_position(("center", 60))
              .with_start(26.0)
              .with_duration(4.0))
    text_clips.append(dyk_bg)

    dyk_clip = (TextClip(
        text=dyk_text,
        font_size=34,
        color="rgb(100, 60, 20)",
        font=chosen_font,
        method="caption",
        size=(VIDEO_W - 160, None),
        text_align="center",
    )
    .with_position(("center", 80))
    .with_start(26.0)
    .with_duration(4.0))
    text_clips.append(dyk_clip)
except Exception as e:
    print(f"  WARN dyk: {e}")

# ─── Compose & render ────────────────────────────────────────────────────
print("Compositing...")
final = CompositeVideoClip(
    [bg_clip, fg_clip] + text_clips,
    size=(VIDEO_W, VIDEO_H)
).with_duration(DURATION)

output_path = OUTPUT_DIR / "kitten_short_9x16.mp4"
print(f"Rendering {output_path}...")

final.write_videofile(
    str(output_path),
    fps=FPS,
    codec="libx264",
    audio=False,
    preset="medium",
    bitrate="5000k",
    logger="bar",
)

print(f"\nDONE! {output_path}")
print(f"Size: {output_path.stat().st_size / 1024 / 1024:.1f} MB")
