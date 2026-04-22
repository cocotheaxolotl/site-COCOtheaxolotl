"""
Animated Read Aloud Video Builder - "Whose Egg Is This?"
Style: LolliPop Animated Book - cutout characters with parallax animation

Prototype page: Baby Kitten (Animal 1/29)
v5: Use foreground as-is, no floating animation, fix text & ear cropping
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
COLORED_DIR = BASE / "whose-egg-colored"
OUTPUT_DIR = BASE / "animated-readaloud"
OUTPUT_DIR.mkdir(exist_ok=True)

FG_PATH = OUTPUT_DIR / "kitten_foreground.png"
BG_PATH = OUTPUT_DIR / "kitten_background_v2.png"  # ChatGPT-generated clean background

# ─── Video settings ─────────────────────────────────────────────────────────
VIDEO_W, VIDEO_H = 1920, 1080
FPS = 30
DURATION = 16

# ═══════════════════════════════════════════════════════════════════════════
# STEP 1: Load foreground as-is (image is already good)
# ═══════════════════════════════════════════════════════════════════════════
print("STEP 1: Loading foreground as-is...")

fg_clean = Image.open(FG_PATH).convert("RGBA")
print(f"  Foreground loaded: {fg_clean.size}")

# ═══════════════════════════════════════════════════════════════════════════
# STEP 2: Load ChatGPT background + scale for Ken Burns
# ═══════════════════════════════════════════════════════════════════════════
print("STEP 2: Loading ChatGPT background...")

bg_img = Image.open(BG_PATH).convert("RGB")
print(f"  Original BG size: {bg_img.size}")

# Scale up 25% for Ken Burns headroom
BG_SCALE = 1.25
bg_w = int(VIDEO_W * BG_SCALE)
bg_h = int(VIDEO_H * BG_SCALE)
bg_img = bg_img.resize((bg_w, bg_h), Image.LANCZOS)
bg_array = np.array(bg_img)
print(f"  Scaled BG: {bg_w}x{bg_h}")

# ═══════════════════════════════════════════════════════════════════════════
# STEP 3: Build animated video
# ═══════════════════════════════════════════════════════════════════════════
print("STEP 3: Building animated video...")

# Prepare foreground — scale to 75% height with padding above for ears
fg_target_h = int(VIDEO_H * 0.75)
fg_ratio = fg_target_h / fg_clean.height
fg_target_w = int(fg_clean.width * fg_ratio)
fg_resized = fg_clean.resize((fg_target_w, fg_target_h), Image.LANCZOS)
fg_array = np.array(fg_resized)

# Center horizontally, anchor to bottom with margin
fg_base_x = VIDEO_W // 2 - fg_target_w // 2 + 60
fg_base_y = VIDEO_H - fg_target_h - 10  # -10 margin from bottom (ears safe at top)
print(f"  FG: {fg_target_w}x{fg_target_h}, pos: ({fg_base_x}, {fg_base_y})")

# Ken Burns background
def make_ken_burns_frame(t):
    progress = t / DURATION
    zoom = 1.0 + 0.10 * progress
    cw = int(VIDEO_W / zoom)
    ch = int(VIDEO_H / zoom)
    pan_x = int(15 * progress)
    pan_y = int(8 * progress)
    cx = (bg_w - cw) // 2 + pan_x
    cy = (bg_h - ch) // 2 + pan_y
    cx = max(0, min(cx, bg_w - cw))
    cy = max(0, min(cy, bg_h - ch))
    cropped = bg_array[cy:cy + ch, cx:cx + cw]
    pil_resized = Image.fromarray(cropped).resize((VIDEO_W, VIDEO_H), Image.LANCZOS)
    return np.array(pil_resized)

bg_clip = VideoClip(make_ken_burns_frame, duration=DURATION)

# Foreground: slide in from right edge, then very gentle sway (alive but no sea sickness)
def entrance_position(t):
    if t < 1.5:
        # Slide in from right edge of frame (stay within bounds to avoid mask bug)
        progress = t / 1.5
        ease = 1 - (1 - progress) ** 3  # cubic ease-out
        start_x = VIDEO_W - 50  # start just inside right edge
        x = int(start_x + (fg_base_x - start_x) * ease)
        y = fg_base_y
    else:
        # Very gentle sway: 2px amplitude, 8s period — barely perceptible but alive
        ft = t - 1.5
        x = fg_base_x + int(2 * math.sin(2 * math.pi * ft / 8))
        y = fg_base_y + int(1 * math.sin(2 * math.pi * ft / 6))
    return (x, y)

fg_clip = (ImageClip(fg_array)
           .with_duration(DURATION)
           .with_position(entrance_position)
           .with_effects([CrossFadeIn(1.0)]))

# Font
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

# ─── Text overlays ─────────────────────────────────────────────────────────
print("  Building text overlays...")

narration_lines = [
    ("Coco met a tiny kitten playing with a ball of yarn.", 1.0, 5.0),
    ('"Is this your eggshell, little kitten?"', 5.0, 9.0),
    ('The kitten purred and shook its head.', 8.5, 11.5),
    ('"No, silly! Kittens don\'t hatch from eggs!\nBut keep looking!"', 11.0, 15.0),
]

dyk_text = ("Did you know?\nKittens are born with their eyes closed.\n"
            "They can't see for the first 7-10 days!")

text_clips = []

# Text bar - taller (160px) to fit 2-line text without cropping
TEXT_BAR_Y = 900
TEXT_BAR_H = 160
text_bar = (ColorClip(size=(VIDEO_W, TEXT_BAR_H), color=(255, 240, 248))
            .with_opacity(0.85)
            .with_position(("center", TEXT_BAR_Y))
            .with_duration(DURATION - 1.0)
            .with_start(0.8))
text_clips.append(text_bar)

TEXT_Y = TEXT_BAR_Y + 15
for line_text, start_t, end_t in narration_lines:
    try:
        txt = (TextClip(
            text=line_text,
            font_size=36,
            color="rgb(80, 40, 60)",
            font=chosen_font,
            stroke_color="white",
            stroke_width=2,
            method="caption",
            size=(VIDEO_W - 160, None),
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
        text="Baby Kitten",
        font_size=60,
        color="rgb(220, 80, 140)",
        font=chosen_font,
        stroke_color="white",
        stroke_width=3,
    )
    .with_position(("center", 40))
    .with_start(0.2)
    .with_duration(3.0))
    text_clips.append(title_clip)
except Exception as e:
    print(f"  WARN title: {e}")

# "Did you know?" box
try:
    dyk_bg = (ColorClip(size=(800, 200), color=(255, 250, 220))
              .with_opacity(0.9)
              .with_position(("center", 30))
              .with_start(13.0)
              .with_duration(3.0))
    text_clips.append(dyk_bg)

    dyk_clip = (TextClip(
        text=dyk_text,
        font_size=30,
        color="rgb(100, 60, 20)",
        font=chosen_font,
        method="caption",
        size=(760, None),
        text_align="center",
    )
    .with_position(("center", 45))
    .with_start(13.0)
    .with_duration(3.0))
    text_clips.append(dyk_clip)
except Exception as e:
    print(f"  WARN dyk: {e}")

# ─── Compose & render ──────────────────────────────────────────────────────
print("Compositing...")
final = CompositeVideoClip(
    [bg_clip, fg_clip] + text_clips,
    size=(VIDEO_W, VIDEO_H)
).with_duration(DURATION)

output_path = OUTPUT_DIR / "prototype_kitten_readaloud_v5.mp4"
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
