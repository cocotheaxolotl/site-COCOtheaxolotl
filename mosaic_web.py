"""
Mystery Mosaic Web App
======================
Flask web application that lets users upload an image and generate
a Mystery Mosaic Color by Number page.

Free tier: 3 HD downloads per day, then paywall.
Preview (watermarked) is always free.

Usage:
    pip install flask
    python mosaic_web.py

Then open http://localhost:5000
"""

import os
import uuid
import math
import time
import shutil
import zipfile
import sys
from pathlib import Path
from collections import defaultdict

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from flask import Flask, render_template, request, send_file, jsonify, url_for
from sklearn.cluster import KMeans

BASE_DIR = Path(__file__).resolve().parent
MOSAIC_API_DIR = BASE_DIR / "mosaic-api"
if str(MOSAIC_API_DIR) not in sys.path:
    sys.path.insert(0, str(MOSAIC_API_DIR))

from mosaic_engine import generate_cbn

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload

UPLOAD_DIR = Path("static/uploads")
OUTPUT_DIR = Path("static/output")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ─── Freemium usage tracking ───
FREE_DOWNLOADS_TOTAL = 3
USAGE_FILE = Path("usage_log.json")

# { "ip_address": count }
download_counts = {}

# Load persisted usage on startup
if USAGE_FILE.exists():
    import json
    try:
        download_counts = json.loads(USAGE_FILE.read_text())
    except Exception:
        download_counts = {}


def save_usage():
    """Persist usage to disk so it survives restarts."""
    import json
    USAGE_FILE.write_text(json.dumps(download_counts))


def get_client_ip():
    """Get the real client IP (handles proxies)."""
    if request.headers.get("X-Forwarded-For"):
        return request.headers["X-Forwarded-For"].split(",")[0].strip()
    return request.remote_addr or "unknown"


def count_downloads(ip):
    """Count total HD downloads for this IP."""
    return download_counts.get(ip, 0)


def record_download(ip):
    download_counts[ip] = download_counts.get(ip, 0) + 1
    save_usage()


# ─── Core mosaic functions ───

def get_font(size):
    font_paths = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for fp in font_paths:
        try:
            return ImageFont.truetype(fp, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def rgb_to_color_name(r, g, b):
    r, g, b = int(r), int(g), int(b)
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    brightness = (r + g + b) / 3

    if max_c - min_c < 30:
        if brightness > 200:
            return "White"
        elif brightness > 140:
            return "Light Grey"
        elif brightness > 80:
            return "Grey"
        else:
            return "Black"

    if r >= g and r >= b:
        if g > b + 40:
            if r > 200 and g > 200:
                return "Yellow"
            return "Orange"
        elif b > g + 40:
            return "Purple"
        else:
            if r > 180 and g < 100 and b < 100:
                return "Red"
            elif r > 180 and g > 100:
                return "Salmon"
            return "Pink"
    elif g >= r and g >= b:
        if b > r + 40:
            return "Turquoise"
        elif r > b + 20 and r > 150:
            return "Yellow-Green"
        else:
            if g > 180:
                return "Light Green"
            return "Green"
    else:
        if r > g + 30 and r > 100:
            return "Purple"
        elif g > r + 10:
            return "Sky Blue"
        else:
            if b > 200:
                return "Light Blue"
            return "Blue"


def hexagon_vertices(cx, cy, size):
    angles = [math.radians(60 * i) for i in range(6)]
    return [(cx + size * math.cos(a), cy + size * math.sin(a)) for a in angles]


def generate_hex_grid(width, height, cell_size):
    centers = []
    hex_w = cell_size * 2
    hex_h = cell_size * math.sqrt(3)
    col_step = hex_w * 0.75
    row_step = hex_h

    cols = int(width / col_step) + 2
    rows = int(height / row_step) + 2

    for col in range(cols):
        for row in range(rows):
            cx = col * col_step
            cy = row * row_step
            if col % 2 == 1:
                cy += row_step / 2
            if -cell_size < cx < width + cell_size and -cell_size < cy < height + cell_size:
                centers.append((cx, cy))
    return centers


def quantize_image(img, n_colors):
    pixels = np.array(img).reshape(-1, 3).astype(np.float64)
    kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
    labels = kmeans.fit_predict(pixels)
    palette = kmeans.cluster_centers_.astype(np.uint8)

    rng = np.random.RandomState(12345)
    order = np.arange(n_colors)
    rng.shuffle(order)
    remap = np.zeros(n_colors, dtype=int)
    for new_idx, old_idx in enumerate(order):
        remap[old_idx] = new_idx
    labels = remap[labels]
    palette = palette[order]

    label_map = labels.reshape(img.size[1], img.size[0])
    return label_map, palette


def sample_hex_color(label_map, cx, cy, cell_size, width, height):
    r = max(2, int(cell_size * 0.4))
    y_start = max(0, int(cy) - r)
    y_end = min(height, int(cy) + r)
    x_start = max(0, int(cx) - r)
    x_end = min(width, int(cx) + r)
    if y_start >= y_end or x_start >= x_end:
        return 0
    region = label_map[y_start:y_end, x_start:x_end]
    if region.size == 0:
        return 0
    counts = np.bincount(region.flatten())
    return counts.argmax()


def add_watermark(img, text="PREVIEW - cocotheaxolotl.org"):
    """Add a diagonal watermark across the image."""
    watermarked = img.copy()
    draw = ImageDraw.Draw(watermarked, "RGBA")
    w, h = watermarked.size
    font_size = max(20, int(min(w, h) * 0.06))
    font = get_font(font_size)

    for y_offset in range(-h, h * 2, font_size * 4):
        for x_offset in range(-w, w * 2, font_size * 12):
            draw.text(
                (x_offset, y_offset),
                text,
                fill=(180, 180, 180, 100),
                font=font,
            )
    return watermarked


def create_legend_image(palette, img_width):
    n = len(palette)
    swatch_size = 40
    padding = 12
    text_width = 200
    cols = min(4, n)
    rows = (n + cols - 1) // cols

    legend_w = max(cols * (swatch_size + text_width + padding) + padding, img_width)
    legend_h = rows * (swatch_size + padding) + padding + 45

    legend = Image.new("RGB", (legend_w, legend_h), (255, 255, 255))
    draw = ImageDraw.Draw(legend)

    title_font = get_font(20)
    draw.text((padding, 8), "Mystery Mosaic - Color Legend",
              fill=(0, 0, 0), font=title_font)

    font = get_font(16)
    for i, color in enumerate(palette):
        col = i % cols
        row = i // cols
        x = padding + col * (swatch_size + text_width + padding)
        y = 45 + padding + row * (swatch_size + padding)

        name = rgb_to_color_name(color[0], color[1], color[2])
        draw.rectangle([x, y, x + swatch_size, y + swatch_size],
                        fill=tuple(color), outline=(0, 0, 0), width=2)
        draw.text((x + swatch_size + 5, y + 10),
                  f"  {i+1} = {name}", fill=(0, 0, 0), font=font)
    return legend


def stack_images(top, bottom, gap=10):
    w = max(top.size[0], bottom.size[0])
    h = top.size[1] + bottom.size[1] + gap
    combined = Image.new("RGB", (w, h), (255, 255, 255))
    combined.paste(top, ((w - top.size[0]) // 2, 0))
    combined.paste(bottom, ((w - bottom.size[0]) // 2, top.size[1] + gap))
    return combined


def generate_mosaic(img, n_colors, cell_size, crop=None, blur=0, page=None, landscape=False):
    """Generate classic CBN output using the shared production CBN engine."""
    crop_str = None
    if crop:
        left_pct, top_pct, right_pct, bottom_pct = crop
        crop_str = f"{left_pct},{top_pct},{right_pct},{bottom_pct}"

    result = generate_cbn(
        img,
        colors=n_colors,
        page=page or "letter",
        landscape=landscape,
        crop=crop_str,
        blur=blur,
        min_zone_pixels=150,
    )
    return (
        result.mystery_png,
        result.answer_png,
        result.legend_png,
        result.palette,
        result.zone_count,
    )


# ─── Flask routes ───

@app.route("/")
def index():
    return render_template("mosaic.html")


@app.route("/usage")
def usage():
    """Check remaining free downloads for this user."""
    ip = get_client_ip()
    used = count_downloads(ip)
    remaining = max(0, FREE_DOWNLOADS_TOTAL - used)
    return jsonify({
        "free_remaining": remaining,
        "free_total": FREE_DOWNLOADS_TOTAL,
        "used_today": used,
    })


@app.route("/generate", methods=["POST"])
def generate():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    # Parse parameters
    n_colors = int(request.form.get("colors", 10))
    cell_size = int(request.form.get("cell_size", 60))
    blur = int(request.form.get("blur", 0))
    page = request.form.get("page", "letter")
    landscape = request.form.get("landscape", "false") == "true"

    crop_left = float(request.form.get("crop_left", 0))
    crop_top = float(request.form.get("crop_top", 0))
    crop_right = float(request.form.get("crop_right", 0))
    crop_bottom = float(request.form.get("crop_bottom", 0))

    crop = None
    if any(v > 0 for v in [crop_left, crop_top, crop_right, crop_bottom]):
        crop = (crop_left, crop_top, crop_right, crop_bottom)

    # Clamp values
    n_colors = max(4, min(20, n_colors))
    cell_size = max(30, min(100, cell_size))
    blur = max(0, min(20, blur))

    # Save uploaded file
    job_id = str(uuid.uuid4())[:8]
    ext = Path(file.filename).suffix or ".png"
    upload_path = UPLOAD_DIR / f"{job_id}{ext}"
    file.save(str(upload_path))

    try:
        img = Image.open(str(upload_path))
        img = ImageOps.exif_transpose(img)

        # Generate mosaic
        mystery, answer, legend, palette, hex_count = generate_mosaic(
            img, n_colors, cell_size, crop=crop, blur=blur,
            page=page, landscape=landscape
        )

        # Save HD versions
        job_dir = OUTPUT_DIR / job_id
        job_dir.mkdir(exist_ok=True)

        mystery_path = job_dir / "mystery-mosaic.png"
        answer_path = job_dir / "answer-key.png"
        legend_path = job_dir / "legend.png"
        combined_path = job_dir / "mystery-mosaic-full.png"

        mystery.save(str(mystery_path), dpi=(300, 300))
        answer.save(str(answer_path), dpi=(300, 300))
        legend.save(str(legend_path), dpi=(300, 300))
        combined = stack_images(mystery, legend)
        combined.save(str(combined_path), dpi=(300, 300))

        # Create preview (smaller, watermarked)
        preview_size = (800, int(800 * mystery.size[1] / mystery.size[0]))
        preview_mystery = mystery.resize(preview_size, Image.LANCZOS)
        preview_answer = answer.resize(preview_size, Image.LANCZOS)

        preview_mystery = add_watermark(preview_mystery)
        preview_answer = add_watermark(preview_answer)

        preview_mystery.save(str(job_dir / "preview-mystery.png"))
        preview_answer.save(str(job_dir / "preview-answer.png"))

        # Create ZIP for download
        zip_path = job_dir / "mystery-mosaic-pack.zip"
        with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(str(mystery_path), "mystery-mosaic.png")
            zf.write(str(answer_path), "answer-key.png")
            zf.write(str(legend_path), "legend.png")
            zf.write(str(combined_path), "mystery-mosaic-full.png")

        # Check free tier
        ip = get_client_ip()
        used = count_downloads(ip)
        remaining = max(0, FREE_DOWNLOADS_TOTAL - used)

        # Build palette info
        palette_info = []
        for i, c in enumerate(palette):
            palette_info.append({
                "number": i + 1,
                "r": int(c[0]), "g": int(c[1]), "b": int(c[2]),
                "name": rgb_to_color_name(c[0], c[1], c[2]),
            })

        return jsonify({
            "success": True,
            "job_id": job_id,
            "hex_count": hex_count,
            "colors": len(palette),
            "palette": palette_info,
            "preview_mystery": f"/static/output/{job_id}/preview-mystery.png",
            "preview_answer": f"/static/output/{job_id}/preview-answer.png",
            "download_url": f"/download/{job_id}",
            "image_size": f"{mystery.size[0]}x{mystery.size[1]}",
            "free_remaining": remaining,
            "free_total": FREE_DOWNLOADS_TOTAL,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/download/<job_id>")
def download(job_id):
    zip_path = OUTPUT_DIR / job_id / "mystery-mosaic-pack.zip"
    if not zip_path.exists():
        return "File not found", 404

    ip = get_client_ip()
    used = count_downloads(ip)

    if used >= FREE_DOWNLOADS_TOTAL:
        return jsonify({
            "error": "free_limit_reached",
            "message": f"You've used all {FREE_DOWNLOADS_TOTAL} free downloads.",
            "used": used,
        }), 402  # 402 = Payment Required

    # Record this download
    record_download(ip)

    return send_file(str(zip_path.resolve()), as_attachment=True,
                     download_name=f"mystery-mosaic-{job_id}.zip")


if __name__ == "__main__":
    print("Mystery Mosaic Generator - Web App")
    print("Open http://localhost:5000")
    print(f"Free tier: {FREE_DOWNLOADS_TOTAL} HD downloads total")
    app.run(debug=True, port=5000)
