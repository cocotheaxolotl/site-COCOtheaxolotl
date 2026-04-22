"""
Create split thumbnails: left half = original image, right half = ZOOMED mosaic answer key
Crop the center of the mosaic at full resolution so hexagons look detailed and impressive.
"""
from PIL import Image, ImageDraw, ImageFont
import os

BASE = r"c:\Users\33612\Documents\site_COCOtheaxolotl\mosaic-examples"

examples = [
    ("unicorn-mystery-mosaic", "unicorn-answer.png"),
    ("dragon-mystery-mosaic", "dragon-answer.png"),
    ("dinosaur-mystery-mosaic", "dinosaur-answer.png"),
    ("cat-color-by-number", "cat-answer.png"),
    ("turtle-color-by-number", "turtle-answer.png"),
    ("rabbit-mystery-mosaic", "rabbit-answer.png"),
]

for folder, answer_file in examples:
    orig_path = os.path.join(BASE, folder, "original.png")
    answer_path = os.path.join(BASE, folder, answer_file)
    out_path = os.path.join(BASE, folder, "split-preview.png")

    orig = Image.open(orig_path).convert("RGB")
    answer = Image.open(answer_path).convert("RGB")

    # Target output size = original size
    w, h = orig.size

    # ZOOM into the center of the mosaic answer (crop ~40% of center area)
    aw, ah = answer.size
    zoom = 0.4  # crop 40% of the center
    crop_w = int(aw * zoom)
    crop_h = int(ah * zoom)
    cx, cy = aw // 2, ah // 2
    # Offset slightly up to show more interesting area (character faces tend to be in upper-center)
    cy = int(ah * 0.4)
    crop_box = (cx - crop_w // 2, cy - crop_h // 2, cx + crop_w // 2, cy + crop_h // 2)
    answer_cropped = answer.crop(crop_box)

    # Resize cropped mosaic to match the original image dimensions
    answer_zoomed = answer_cropped.resize((w, h), Image.LANCZOS)

    # Create composite: left = original, right = zoomed mosaic
    composite = orig.copy()

    # Diagonal split
    slant = int(w * 0.12)
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

    # White diagonal divider
    draw_comp = ImageDraw.Draw(composite)
    line_width = max(4, w // 120)
    draw_comp.line([(mid + slant, 0), (mid - slant, h)], fill="white", width=line_width)

    # Labels
    try:
        font_size = max(20, h // 25)
        font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", font_size)
    except:
        font = ImageFont.load_default()

    pad = 10
    for label, x_pos in [("Original", w // 4), ("Mosaic", w * 3 // 4)]:
        bbox = font.getbbox(label)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        lx = x_pos - tw // 2
        ly = h - th - pad * 4
        # Semi-transparent background
        overlay = Image.new("RGBA", composite.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rounded_rectangle(
            [lx - pad * 2, ly - pad, lx + tw + pad * 2, ly + th + pad],
            radius=12,
            fill=(0, 0, 0, 160)
        )
        composite = Image.alpha_composite(composite.convert("RGBA"), overlay).convert("RGB")
        draw_comp = ImageDraw.Draw(composite)
        draw_comp.text((lx, ly), label, fill="white", font=font)

    composite.save(out_path, quality=90)
    print(f"Created: {out_path} ({w}x{h})")

print("\nDone! 6 split previews with zoomed mosaics created.")
