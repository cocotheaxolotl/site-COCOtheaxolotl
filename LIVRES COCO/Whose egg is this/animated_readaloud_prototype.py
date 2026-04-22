"""
Animated Read Aloud Prototype - "Whose Egg Is This?"
Style: LolliPop Animated Book (Pete the Cat) - cutout characters with parallax animation

Prototype page: Baby Kitten (Animal 1/29)
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageFilter, ImageDraw, ImageFont
import numpy as np

# ─── PATHS ──────────────────────────────────────────────────────────────────
BASE = Path(__file__).parent
COLORED_DIR = BASE / "whose-egg-colored"
OUTPUT_DIR = BASE / "animated-readaloud"
OUTPUT_DIR.mkdir(exist_ok=True)

KITTEN_IMG = COLORED_DIR / "axolotl-kitten-colored.png"

# ─── STEP 1: Background removal with rembg ─────────────────────────────────
print("=" * 60)
print("STEP 1: Extracting foreground with rembg...")
print("=" * 60)

from rembg import remove

img_original = Image.open(KITTEN_IMG).convert("RGBA")
print(f"  Original size: {img_original.size}")

# Remove background → transparent PNG
img_foreground = remove(img_original)
fg_path = OUTPUT_DIR / "kitten_foreground.png"
img_foreground.save(fg_path)
print(f"  Foreground saved: {fg_path}")

# ─── STEP 2: Create clean background ───────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 2: Creating clean background...")
print("=" * 60)

# Strategy: heavy gaussian blur on original to "remove" characters
# Then paste the blurred version where the foreground was
img_bg = img_original.copy().convert("RGB")

# Get the alpha mask from foreground (where characters are)
fg_alpha = img_foreground.split()[3]  # Alpha channel
# Dilate the mask a bit so we cover edges
fg_mask_dilated = fg_alpha.filter(ImageFilter.MaxFilter(size=25))

# Create heavily blurred version of original
img_blurred = img_bg.filter(ImageFilter.GaussianBlur(radius=40))

# Composite: use original where no characters, blurred where characters were
# This gives us a "clean" background
bg_clean = img_bg.copy()
# Convert mask to 0-1 for blending
mask_np = np.array(fg_mask_dilated).astype(float) / 255.0
bg_np = np.array(bg_clean).astype(float)
blur_np = np.array(img_blurred).astype(float)

# Blend: where mask is 1 (character area) use blurred, elsewhere keep original
for c in range(3):
    bg_np[:, :, c] = bg_np[:, :, c] * (1 - mask_np) + blur_np[:, :, c] * mask_np

bg_clean = Image.fromarray(bg_np.astype(np.uint8))
bg_path = OUTPUT_DIR / "kitten_background.png"
bg_clean.save(bg_path)
print(f"  Background saved: {bg_path}")

# ─── STEP 3: Build animated video with moviepy ─────────────────────────────
print("\n" + "=" * 60)
print("STEP 3: Building animated video...")
print("=" * 60)

from moviepy import (
    ImageClip, TextClip, CompositeVideoClip,
    ColorClip, concatenate_videoclips
)

# Video settings
VIDEO_W, VIDEO_H = 1920, 1080  # 16:9 HD
FPS = 30
DURATION = 15  # seconds for this page

# Colors
PINK_BG = (255, 230, 240)
TEXT_COLOR = (80, 40, 60)
ACCENT_COLOR = (220, 80, 140)

# ─── Background layer with Ken Burns (slow zoom in) ────────────────────────
bg_img = Image.open(bg_path).convert("RGB")
# Resize background to be larger than video (for zoom room)
bg_scale = 1.3
bg_w = int(VIDEO_W * bg_scale)
bg_h = int(VIDEO_H * bg_scale)
bg_img = bg_img.resize((bg_w, bg_h), Image.LANCZOS)
bg_array = np.array(bg_img)


def ken_burns_bg(get_frame, t):
    """Slow zoom in on background over time."""
    progress = t / DURATION
    # Zoom from 1.0 to 1.15 over the duration
    zoom = 1.0 + 0.15 * progress
    # Calculate crop region (zoom into center)
    cw = int(VIDEO_W / zoom)
    ch = int(VIDEO_H / zoom)
    cx = (bg_w - cw) // 2
    cy = (bg_h - ch) // 2
    cropped = bg_array[cy:cy+ch, cx:cx+cw]
    # Resize back to video dimensions
    from PIL import Image as PILImage
    pil_crop = PILImage.fromarray(cropped)
    pil_resized = pil_crop.resize((VIDEO_W, VIDEO_H), PILImage.LANCZOS)
    return np.array(pil_resized)


bg_clip = ImageClip(bg_array).with_duration(DURATION).resized((VIDEO_W, VIDEO_H))
bg_clip = bg_clip.transform(ken_burns_bg)

# ─── Foreground (Coco + Kitten) with gentle floating animation ─────────────
fg_img = Image.open(fg_path).convert("RGBA")
# Scale foreground to fit nicely in frame (about 60% of height)
fg_target_h = int(VIDEO_H * 0.75)
fg_ratio = fg_target_h / fg_img.height
fg_target_w = int(fg_img.width * fg_ratio)
fg_img = fg_img.resize((fg_target_w, fg_target_h), Image.LANCZOS)
fg_array = np.array(fg_img)

# Base position: center-right of frame
fg_base_x = VIDEO_W // 2 - fg_target_w // 2 + 100
fg_base_y = VIDEO_H - fg_target_h + 30


def floating_position(t):
    """Gentle floating up and down."""
    import math
    offset_y = int(8 * math.sin(2 * math.pi * t / 4))  # 4-second cycle, 8px amplitude
    offset_x = int(4 * math.sin(2 * math.pi * t / 6))  # 6-second cycle, 4px amplitude
    return (fg_base_x + offset_x, fg_base_y + offset_y)


fg_clip = (ImageClip(fg_array)
           .with_duration(DURATION)
           .with_position(floating_position))

# ─── Entrance animation: characters slide in from right ────────────────────
def entrance_position(t):
    """Slide in from right + floating once settled."""
    import math
    if t < 1.5:
        # Slide in from right over 1.5 seconds (ease-out)
        progress = t / 1.5
        ease = 1 - (1 - progress) ** 3  # cubic ease-out
        start_x = VIDEO_W + 50
        x = int(start_x + (fg_base_x - start_x) * ease)
        y = fg_base_y
    else:
        # Floating
        ft = t - 1.5
        x = fg_base_x + int(4 * math.sin(2 * math.pi * ft / 6))
        y = fg_base_y + int(8 * math.sin(2 * math.pi * ft / 4))
    return (x, y)


fg_clip = (ImageClip(fg_array)
           .with_duration(DURATION)
           .with_position(entrance_position))

# ─── Text overlays ─────────────────────────────────────────────────────────
# Narration text for kitten page
narration_lines = [
    ("Coco met a tiny kitten", 1.0, 4.0),
    ("playing with a ball of yarn.", 2.5, 5.5),
    ('"Is this your eggshell, little kitten?"', 5.0, 9.0),
    ("The kitten purred and shook its head.", 8.0, 11.5),
    ('"No, silly! Kittens don\'t hatch from eggs!"', 10.5, 14.0),
    ('"But keep looking!"', 12.5, 15.0),
]

# Did you know box
dyk_text = "Did you know?\nKittens are born with their eyes closed.\nThey can't see for the first 7-10 days!"

# Create text clips - use a system font
# Try to find a good font
import platform
font_candidates = [
    "C:/Windows/Fonts/comicbd.ttf",   # Comic Sans Bold
    "C:/Windows/Fonts/comic.ttf",      # Comic Sans
    "C:/Windows/Fonts/segoeuib.ttf",   # Segoe UI Bold
    "C:/Windows/Fonts/arialbd.ttf",    # Arial Bold
]

chosen_font = None
for f in font_candidates:
    if os.path.exists(f):
        chosen_font = f
        break

print(f"  Using font: {chosen_font}")

text_clips = []

# Create a semi-transparent text background bar at the bottom
text_bar = ColorClip(size=(VIDEO_W, 140), color=(255, 240, 248))
text_bar = (text_bar
            .with_opacity(0.85)
            .with_position(("center", VIDEO_H - 150))
            .with_duration(DURATION)
            .with_start(0.8))

text_clips.append(text_bar)

for line_text, start_t, end_t in narration_lines:
    try:
        txt = (TextClip(
            text=line_text,
            font_size=38,
            color="rgb(80, 40, 60)",
            font=chosen_font or "Arial",
            stroke_color="white",
            stroke_width=2,
            method="caption",
            size=(VIDEO_W - 200, None),
            text_align="center",
        )
        .with_position(("center", VIDEO_H - 130))
        .with_start(start_t)
        .with_duration(end_t - start_t))

        # Fade in effect
        txt = txt.with_effects([])  # placeholder - we'll use opacity

        text_clips.append(txt)
    except Exception as e:
        print(f"  Warning: Could not create text clip '{line_text[:30]}...': {e}")

# ─── "Did you know?" box at the end ────────────────────────────────────────
try:
    dyk_bg = ColorClip(size=(700, 180), color=(255, 250, 220))
    dyk_bg = (dyk_bg
              .with_opacity(0.9)
              .with_position(("center", 50))
              .with_start(12.0)
              .with_duration(3.0))
    text_clips.append(dyk_bg)

    dyk_clip = (TextClip(
        text=dyk_text,
        font_size=28,
        color="rgb(100, 60, 20)",
        font=chosen_font or "Arial",
        method="caption",
        size=(660, None),
        text_align="center",
    )
    .with_position(("center", 65))
    .with_start(12.0)
    .with_duration(3.0))
    text_clips.append(dyk_clip)
except Exception as e:
    print(f"  Warning: Could not create DYK clip: {e}")

# ─── Title card at start ───────────────────────────────────────────────────
try:
    title_text = "🐱 Baby Kitten"
    title_clip = (TextClip(
        text=title_text,
        font_size=56,
        color="rgb(220, 80, 140)",
        font=chosen_font or "Arial",
        stroke_color="white",
        stroke_width=3,
        method="caption",
        size=(VIDEO_W - 100, None),
        text_align="center",
    )
    .with_position(("center", 40))
    .with_start(0.0)
    .with_duration(3.5))
    text_clips.append(title_clip)
except Exception as e:
    print(f"  Warning: Could not create title: {e}")

# ─── Compose everything ────────────────────────────────────────────────────
print("  Compositing layers...")
final = CompositeVideoClip(
    [bg_clip, fg_clip] + text_clips,
    size=(VIDEO_W, VIDEO_H)
)
final = final.with_duration(DURATION)

# ─── Export ─────────────────────────────────────────────────────────────────
output_path = OUTPUT_DIR / "prototype_kitten_readaloud.mp4"
print(f"  Rendering to {output_path}...")
final.write_videofile(
    str(output_path),
    fps=FPS,
    codec="libx264",
    audio=False,  # No audio for now
    preset="medium",
    bitrate="5000k",
    logger="bar",
)

print("\n" + "=" * 60)
print(f"DONE! Video saved to: {output_path}")
print(f"Duration: {DURATION}s | Resolution: {VIDEO_W}x{VIDEO_H} | FPS: {FPS}")
print("=" * 60)
