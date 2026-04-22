"""
Create ONE hero split thumbnail: left = original, right = ZOOMED + BOOSTED mosaic
Giraffe image (best contrast: orange/brown giraffe, blue sky, green grass, pink Coco).
"""
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import os

BASE = r"c:\Users\33612\Documents\site_COCOtheaxolotl\mosaic-examples"

orig_path = r"c:\Users\33612\Documents\site_COCOtheaxolotl\mosaic-examples\giraffe-temp\axolotl-giraffe-centered.png"
answer_path = os.path.join(BASE, "giraffe-temp", "giraffe-answer.png")
out_path = os.path.join(BASE, "hero-split.png")

orig = Image.open(orig_path).convert("RGB")
answer = Image.open(answer_path).convert("RGB")

# Target output = original size
w, h = orig.size

# ── Boost the mosaic answer: saturation + contrast + sharpness ──
boosted = answer.copy()
boosted = ImageEnhance.Color(boosted).enhance(1.6)       # +60% saturation
boosted = ImageEnhance.Contrast(boosted).enhance(1.4)     # +40% contrast
boosted = ImageEnhance.Brightness(boosted).enhance(1.05)   # slight brightness
boosted = ImageEnhance.Sharpness(boosted).enhance(1.3)     # sharpen hex edges

# ── Resize mosaic to match original dimensions (same scale, no zoom) ──
answer_zoomed = boosted.resize((w, h), Image.LANCZOS)

# ── Also boost original slightly for visual punch ──
orig_boosted = orig.copy()
orig_boosted = ImageEnhance.Color(orig_boosted).enhance(1.15)
orig_boosted = ImageEnhance.Contrast(orig_boosted).enhance(1.1)

# ── Create composite: left = original, right = zoomed mosaic ──
composite = orig_boosted.copy()

# Diagonal split
slant = int(w * 0.10)
mid = w // 2

# Mask for right side
mask = Image.new("L", (w, h), 0)
draw = ImageDraw.Draw(mask)
draw.polygon([
    (mid + slant, 0),
    (mid - slant, h),
    (w, h),
    (w, 0)
], fill=255)

composite.paste(answer_zoomed, mask=mask)

# ── White diagonal divider (thick) ──
draw_comp = ImageDraw.Draw(composite)
line_width = max(6, w // 80)
draw_comp.line([(mid + slant, 0), (mid - slant, h)], fill="white", width=line_width)

# ── Labels ──
try:
    font_size = max(24, h // 20)
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", font_size)
except:
    font = ImageFont.load_default()

pad = 14
for label, x_pos in [("Original", w // 4), ("Mosaic", w * 3 // 4)]:
    bbox = font.getbbox(label)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    lx = x_pos - tw // 2
    ly = h - th - pad * 5
    # Semi-transparent background
    overlay = Image.new("RGBA", composite.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rounded_rectangle(
        [lx - pad * 2, ly - pad, lx + tw + pad * 2, ly + th + pad],
        radius=14,
        fill=(0, 0, 0, 180)
    )
    composite = Image.alpha_composite(composite.convert("RGBA"), overlay).convert("RGB")
    draw_comp = ImageDraw.Draw(composite)
    draw_comp.text((lx, ly), label, fill="white", font=font)

composite.save(out_path, quality=95)
print(f"Created: {out_path} ({w}x{h})")
print("Done! One hero split preview with boosted contrast.")
