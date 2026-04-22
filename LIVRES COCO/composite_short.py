"""
Composite OpenArt animated Short over room background.
Replaces the black background from OpenArt with the illustrated room.
"""

import math
from pathlib import Path
from PIL import Image
import numpy as np

from moviepy import (
    VideoFileClip, ImageClip, CompositeVideoClip, VideoClip,
)

# ─── PATHS ──────────────────────────────────────────────────────────────────
BASE = Path(__file__).parent
OUTPUT_DIR = BASE / "animated-readaloud"

OPENART_VIDEO = Path(r"C:\Users\33612\Downloads\openart-video_97b7e716_1771012517359.mp4")
BG_PATH = OUTPUT_DIR / "kitten_background_v2.png"
FG_PNG = OUTPUT_DIR / "coco-kitten-no-background.png"  # Original PNG for silhouette mask

# ─── Load OpenArt clip ────────────────────────────────────────────────────
print("Loading OpenArt video...")
clip = VideoFileClip(str(OPENART_VIDEO))
VIDEO_W, VIDEO_H = clip.size
DURATION = clip.duration
FPS = clip.fps
print(f"  Size: {VIDEO_W}x{VIDEO_H}, Duration: {DURATION:.1f}s, FPS: {FPS}")

# ─── Load & prepare background ───────────────────────────────────────────
print("Loading background...")
bg_img = Image.open(BG_PATH).convert("RGB")

# Crop to match video aspect ratio
bg_orig_w, bg_orig_h = bg_img.size
target_ratio = VIDEO_W / VIDEO_H

bg_ratio = bg_orig_w / bg_orig_h
if bg_ratio > target_ratio:
    new_w = int(bg_orig_h * target_ratio)
    left = (bg_orig_w - new_w) // 2
    bg_img = bg_img.crop((left, 0, left + new_w, bg_orig_h))
else:
    new_h = int(bg_orig_w / target_ratio)
    top = (bg_orig_h - new_h) // 2
    bg_img = bg_img.crop((0, top, bg_orig_w, top + new_h))

# Scale up for Ken Burns
BG_SCALE = 1.15
bg_w = int(VIDEO_W * BG_SCALE)
bg_h = int(VIDEO_H * BG_SCALE)
bg_img = bg_img.resize((bg_w, bg_h), Image.LANCZOS)
bg_array = np.array(bg_img)
print(f"  BG: {bg_w}x{bg_h}")

# ─── Ken Burns background ────────────────────────────────────────────────
def make_ken_burns_frame(t):
    progress = t / DURATION
    zoom = 1.0 + 0.06 * progress
    cw = int(VIDEO_W / zoom)
    ch = int(VIDEO_H / zoom)
    pan_x = int(8 * math.sin(2 * math.pi * progress))
    pan_y = int(10 * progress)
    cx = (bg_w - cw) // 2 + pan_x
    cy = (bg_h - ch) // 2 + pan_y
    cx = max(0, min(cx, bg_w - cw))
    cy = max(0, min(cy, bg_h - ch))
    cropped = bg_array[cy:cy + ch, cx:cx + cw]
    pil_resized = Image.fromarray(cropped).resize((VIDEO_W, VIDEO_H), Image.LANCZOS)
    return np.array(pil_resized)

bg_clip = VideoClip(make_ken_burns_frame, duration=DURATION)

# ─── Create smart mask: silhouette from PNG + black-key outside ───────────
print("Building smart mask from PNG silhouette...")
from PIL import ImageFilter

# 1. Build character silhouette from first frame (bright pixels = character)
first_frame = clip.get_frame(0)
brightness_first = np.max(first_frame, axis=2)
char_mask = (brightness_first > 60).astype(np.uint8) * 255

# 2. Dilate generously to cover animation movement
char_mask_img = Image.fromarray(char_mask)
# Heavy dilation: MaxFilter multiple passes to cover movement range
for _ in range(8):
    char_mask_img = char_mask_img.filter(ImageFilter.MaxFilter(size=7))
# Smooth edges
char_mask_img = char_mask_img.filter(ImageFilter.GaussianBlur(radius=4))
silhouette = np.array(char_mask_img).astype(float) / 255.0  # (H, W) 0-1

print(f"  Silhouette covers {np.mean(silhouette > 0.5) * 100:.0f}% of frame")

# 3. Per-frame mask: inside silhouette = always visible, outside = black-key
BLACK_THRESHOLD = 50

def make_mask_frame(t):
    frame = clip.get_frame(t)
    brightness = np.max(frame, axis=2)

    # Black-key mask (for background area)
    low = BLACK_THRESHOLD - 20
    blackkey = np.clip((brightness.astype(float) - low) / (BLACK_THRESHOLD - low), 0.0, 1.0)

    # Combine: inside silhouette → keep everything, outside → use black-key
    mask = np.where(silhouette > 0.5, blackkey, 0.0)
    # But force: inside character silhouette, anything bright enough stays
    # This protects dark features (eyes, outlines) inside the character
    char_interior = silhouette > 0.5
    has_some_color = brightness > 15  # even very dark features have SOME value
    mask[char_interior & has_some_color] = 1.0

    # Only remove truly black pixels OUTSIDE the character
    mask[~char_interior] = blackkey[~char_interior]

    # Smooth
    mask_img = Image.fromarray((mask * 255).astype(np.uint8))
    mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=2))
    return np.array(mask_img).astype(float) / 255.0

mask_clip = VideoClip(make_mask_frame, is_mask=True, duration=DURATION)
clip_masked = clip.with_mask(mask_clip)

# ─── Composite ───────────────────────────────────────────────────────────
print("Compositing...")
final = CompositeVideoClip(
    [bg_clip, clip_masked],
    size=(VIDEO_W, VIDEO_H)
).with_duration(DURATION)

output_path = OUTPUT_DIR / "kitten_short_composited.mp4"
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
