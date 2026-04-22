"""
Mystery Mosaic Color by Number Generator
==========================================
Takes a colored image and creates a "mystery mosaic" where the image
is hidden in a grid of hexagonal cells with numbers.

Usage:
    python mystery_mosaic.py input_image.png [--colors 12] [--cell-size 20] [--output-prefix coco-mosaic]

The result is a page of numbered hexagons. Only when colored does the image appear.
"""

import sys
import math
import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from sklearn.cluster import KMeans


def get_font(size):
    """Try to get a nice font, fall back to default."""
    font_paths = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for fp in font_paths:
        try:
            return ImageFont.truetype(fp, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def rgb_to_color_name(r, g, b):
    """Convert RGB to a human-readable color name (FR/EN)."""
    r, g, b = int(r), int(g), int(b)
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    brightness = (r + g + b) / 3

    if max_c - min_c < 30:
        if brightness > 200:
            return "Blanc / White"
        elif brightness > 140:
            return "Gris clair / Light Grey"
        elif brightness > 80:
            return "Gris / Grey"
        else:
            return "Noir / Black"

    if r >= g and r >= b:
        if g > b + 40:
            if r > 200 and g > 200:
                return "Jaune / Yellow"
            return "Orange"
        elif b > g + 40:
            return "Violet / Purple"
        else:
            if r > 180 and g < 100 and b < 100:
                return "Rouge / Red"
            elif r > 180 and g > 100:
                return "Rose saumon / Salmon"
            return "Rose / Pink"
    elif g >= r and g >= b:
        if b > r + 40:
            return "Turquoise"
        elif r > b + 20 and r > 150:
            return "Jaune-vert / Yellow-Green"
        else:
            if g > 180:
                return "Vert clair / Light Green"
            return "Vert / Green"
    else:
        if r > g + 30 and r > 100:
            return "Violet / Purple"
        elif g > r + 10:
            return "Bleu ciel / Sky Blue"
        else:
            if b > 200:
                return "Bleu clair / Light Blue"
            return "Bleu / Blue"


def autocrop_to_subject(img, margin_pct=5):
    """Auto-crop image to the main subject by removing background.

    Detects the background color from image edges, then finds the bounding
    box of all non-background pixels and crops with a margin.
    """
    arr = np.array(img)
    h, w = arr.shape[:2]

    # Sample background color from the edges (top/bottom rows, left/right cols)
    edge_pixels = np.concatenate([
        arr[0, :, :],           # top row
        arr[-1, :, :],          # bottom row
        arr[:, 0, :],           # left column
        arr[:, -1, :],          # right column
    ])
    # Background = median of edge pixels (robust to small foreground at edges)
    bg_color = np.median(edge_pixels, axis=0).astype(np.float64)

    print(f"  Detected background color: RGB({int(bg_color[0])},{int(bg_color[1])},{int(bg_color[2])})")

    # Compute color distance from background for each pixel
    diff = np.sqrt(np.sum((arr.astype(np.float64) - bg_color) ** 2, axis=2))

    # Threshold: pixels that differ significantly from background
    threshold = 40  # color distance threshold
    foreground = diff > threshold

    # Find bounding box of foreground
    rows_with_fg = np.any(foreground, axis=1)
    cols_with_fg = np.any(foreground, axis=0)

    if not np.any(rows_with_fg) or not np.any(cols_with_fg):
        print("  Warning: no foreground detected, keeping original image")
        return img

    y_min = np.argmax(rows_with_fg)
    y_max = h - 1 - np.argmax(rows_with_fg[::-1])
    x_min = np.argmax(cols_with_fg)
    x_max = w - 1 - np.argmax(cols_with_fg[::-1])

    # Add margin
    margin_x = int((x_max - x_min) * margin_pct / 100)
    margin_y = int((y_max - y_min) * margin_pct / 100)

    x_min = max(0, x_min - margin_x)
    y_min = max(0, y_min - margin_y)
    x_max = min(w - 1, x_max + margin_x)
    y_max = min(h - 1, y_max + margin_y)

    cropped = img.crop((x_min, y_min, x_max + 1, y_max + 1))
    print(f"  Cropped: {w}x{h} -> {cropped.size[0]}x{cropped.size[1]}")
    print(f"  Box: ({x_min},{y_min}) to ({x_max},{y_max})")

    return cropped


def hexagon_vertices(cx, cy, size):
    """Return vertices of a flat-top hexagon centered at (cx, cy)."""
    angles = [math.radians(60 * i) for i in range(6)]
    return [(cx + size * math.cos(a), cy + size * math.sin(a)) for a in angles]


def generate_hex_grid(width, height, cell_size):
    """Generate a grid of hexagon centers (flat-top orientation).
    Returns list of (cx, cy) for each hex center."""
    centers = []

    # Flat-top hex dimensions
    hex_w = cell_size * 2          # width of one hex
    hex_h = cell_size * math.sqrt(3)  # height of one hex

    col_step = hex_w * 0.75   # horizontal distance between columns
    row_step = hex_h          # vertical distance between rows

    cols = int(width / col_step) + 2
    rows = int(height / row_step) + 2

    for col in range(cols):
        for row in range(rows):
            cx = col * col_step
            cy = row * row_step
            # Offset odd columns
            if col % 2 == 1:
                cy += row_step / 2

            if -cell_size < cx < width + cell_size and -cell_size < cy < height + cell_size:
                centers.append((cx, cy))

    return centers


def quantize_image(img, n_colors):
    """Reduce image to n_colors using KMeans."""
    pixels = np.array(img).reshape(-1, 3).astype(np.float64)

    print(f"Clustering into {n_colors} colors...")
    kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
    labels = kmeans.fit_predict(pixels)
    palette = kmeans.cluster_centers_.astype(np.uint8)

    # Shuffle palette randomly so number order doesn't reveal the image
    # (if sorted by brightness, dark=low numbers would outline the shapes)
    rng = np.random.RandomState(12345)  # Fixed seed for reproducibility
    order = np.arange(n_colors)
    rng.shuffle(order)
    remap = np.zeros(n_colors, dtype=int)
    for new_idx, old_idx in enumerate(order):
        remap[old_idx] = new_idx
    labels = remap[labels]
    palette = palette[order]

    label_map = labels.reshape(img.size[1], img.size[0])

    print("Palette:")
    for i, c in enumerate(palette):
        name = rgb_to_color_name(c[0], c[1], c[2])
        pct = (labels == i).sum() / len(labels) * 100
        print(f"  #{i+1}: RGB({c[0]},{c[1]},{c[2]}) = {name} ({pct:.1f}%)")

    return label_map, palette


def sample_hex_color(label_map, cx, cy, cell_size, width, height):
    """Sample the dominant color label at a hex center region."""
    # Sample a small area around the center
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

    # Most common label in the region
    counts = np.bincount(region.flatten())
    return counts.argmax()


def create_mystery_mosaic(img, n_colors, cell_size, prefix):
    """Main pipeline to create mystery mosaic pages."""
    w, h = img.size

    # Step 1: Quantize colors
    label_map, palette = quantize_image(img, n_colors)

    # Step 2: Generate hex grid
    print(f"Generating hexagonal grid (cell size: {cell_size}px)...")
    centers = generate_hex_grid(w, h, cell_size)
    print(f"  {len(centers)} hexagons")

    # Step 3: Assign color to each hex
    hex_data = []  # (cx, cy, color_label)
    for cx, cy in centers:
        color_label = sample_hex_color(label_map, cx, cy, cell_size, w, h)
        hex_data.append((cx, cy, color_label))

    # Step 4: Create the mystery page (numbered hexagons, no color)
    print("Drawing mystery mosaic page...")
    # Use high-res for print quality
    scale = 1
    page_w, page_h = w * scale, h * scale

    mystery = Image.new("RGB", (page_w, page_h), (255, 255, 255))
    draw_mystery = ImageDraw.Draw(mystery)

    # Determine font size based on cell size
    font_size = max(6, int(cell_size * 0.45))
    font = get_font(font_size)

    for cx, cy, color_label in hex_data:
        sx, sy = cx * scale, cy * scale
        s = cell_size * scale

        vertices = hexagon_vertices(sx, sy, s)

        # Draw hex outline
        draw_mystery.polygon(vertices, outline=(0, 0, 0), fill=None, width=1)

        # Draw number
        number = str(color_label + 1)
        bbox = draw_mystery.textbbox((0, 0), number, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = sx - tw / 2
        ty = sy - th / 2
        draw_mystery.text((tx, ty), number, fill=(80, 80, 80), font=font)

    # Step 5: Create the answer key (colored hexagons)
    print("Drawing answer key...")
    answer = Image.new("RGB", (page_w, page_h), (255, 255, 255))
    draw_answer = ImageDraw.Draw(answer)

    for cx, cy, color_label in hex_data:
        sx, sy = cx * scale, cy * scale
        s = cell_size * scale

        vertices = hexagon_vertices(sx, sy, s)
        rgb = tuple(palette[color_label])

        draw_answer.polygon(vertices, outline=(40, 40, 40), fill=rgb, width=1)

    # Step 6: Create legend
    print("Creating legend...")
    legend = create_mosaic_legend(palette, page_w)

    # Step 7: Save everything
    mystery.save(f"{prefix}-mystery.png", dpi=(300, 300))
    print(f"Saved: {prefix}-mystery.png (the page to print & color)")

    combined = stack_images(mystery, legend)
    combined.save(f"{prefix}-mystery-full.png", dpi=(300, 300))
    print(f"Saved: {prefix}-mystery-full.png (page + legend)")

    answer.save(f"{prefix}-answer.png", dpi=(300, 300))
    print(f"Saved: {prefix}-answer.png (colored answer key)")

    legend.save(f"{prefix}-legend.png", dpi=(300, 300))
    print(f"Saved: {prefix}-legend.png")

    print(f"\nDone! {len(hex_data)} hexagons, {n_colors} colors.")
    print(f"The image is hidden in the mosaic - only visible once colored!")


def create_mosaic_legend(palette, img_width):
    """Create a legend for the mosaic."""
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
    draw.text((padding, 8), "Mystery Mosaic - Color Legend / Légende des couleurs",
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
    """Stack two images vertically."""
    w = max(top.size[0], bottom.size[0])
    h = top.size[1] + bottom.size[1] + gap
    combined = Image.new("RGB", (w, h), (255, 255, 255))
    combined.paste(top, ((w - top.size[0]) // 2, 0))
    combined.paste(bottom, ((w - bottom.size[0]) // 2, top.size[1] + gap))
    return combined


def main():
    parser = argparse.ArgumentParser(description="Generate Mystery Mosaic Color by Number")
    parser.add_argument("input", help="Path to a colored illustration (PNG/JPG)")
    parser.add_argument("--colors", type=int, default=12,
                        help="Number of colors (default: 12, typical: 8-20)")
    parser.add_argument("--cell-size", type=int, default=18,
                        help="Hex cell size in pixels (default: 18, smaller=more detail)")
    parser.add_argument("--upscale", type=int, default=2,
                        help="Upscale image by this factor before processing (default: 2)")
    parser.add_argument("--blur", type=int, default=0,
                        help="Blur radius to smooth small details (default: 0, try 5-15)")
    parser.add_argument("--autocrop", action="store_true",
                        help="Auto-crop to main subject (removes background)")
    parser.add_argument("--crop-margin", type=int, default=5,
                        help="Margin around subject in %% (default: 5)")
    parser.add_argument("--crop", type=str, default=None,
                        help="Manual crop: LEFT,TOP,RIGHT,BOTTOM as %% to remove from each side (e.g. 15,5,15,5)")
    parser.add_argument("--page", type=str, default=None,
                        help="Output page size: 'letter' or 'a4' (adjusts image to fill page at 300dpi)")
    parser.add_argument("--landscape", action="store_true",
                        help="Use landscape orientation (with --page)")
    parser.add_argument("--output-prefix", help="Prefix for output files")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} not found")
        sys.exit(1)

    prefix = args.output_prefix or input_path.stem + "-mosaic"
    img = Image.open(input_path).convert("RGB")
    print(f"Image loaded: {img.size[0]}x{img.size[1]} pixels")

    if args.crop:
        parts = [float(x) for x in args.crop.split(",")]
        if len(parts) != 4:
            print("Error: --crop needs 4 values: LEFT,TOP,RIGHT,BOTTOM (percentages)")
            sys.exit(1)
        left_pct, top_pct, right_pct, bottom_pct = parts
        w, h = img.size
        x1 = int(w * left_pct / 100)
        y1 = int(h * top_pct / 100)
        x2 = int(w * (100 - right_pct) / 100)
        y2 = int(h * (100 - bottom_pct) / 100)
        img = img.crop((x1, y1, x2, y2))
        print(f"Manual crop: removed {left_pct}%L {top_pct}%T {right_pct}%R {bottom_pct}%B -> {img.size[0]}x{img.size[1]}")
    elif args.autocrop:
        print("Auto-cropping to main subject...")
        img = autocrop_to_subject(img, margin_pct=args.crop_margin)

    if args.blur > 0:
        img = img.filter(ImageFilter.GaussianBlur(radius=args.blur))
        print(f"Applied blur (radius={args.blur}) to smooth details")

    if args.page:
        # Standard page sizes at 300 DPI
        pages = {
            "letter": (2550, 3300),  # 8.5 x 11 inches
            "a4": (2480, 3508),      # 210 x 297 mm
        }
        page_name = args.page.lower()
        if page_name not in pages:
            print(f"Error: unknown page size '{args.page}'. Use 'letter' or 'a4'.")
            sys.exit(1)
        pw, ph = pages[page_name]
        if args.landscape:
            pw, ph = ph, pw
        # Fit image to page with margin
        margin = 50  # pixels margin on each side
        target_w = pw - 2 * margin
        target_h = ph - 2 * margin
        scale = min(target_w / img.size[0], target_h / img.size[1])
        new_w = int(img.size[0] * scale)
        new_h = int(img.size[1] * scale)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        print(f"Fitted to {page_name} page: {new_w}x{new_h} pixels ({new_w/300:.1f}x{new_h/300:.1f} inches at 300dpi)")
        cell_px = args.cell_size / 300 * 25.4  # cell size in mm
        print(f"  Cell size: {args.cell_size}px = {cell_px:.1f}mm (font ~{cell_px*0.45:.1f}mm)")
    elif args.upscale > 1:
        new_w = img.size[0] * args.upscale
        new_h = img.size[1] * args.upscale
        img = img.resize((new_w, new_h), Image.LANCZOS)
        print(f"Upscaled to: {new_w}x{new_h} pixels")

    create_mystery_mosaic(img, args.colors, args.cell_size, prefix)


if __name__ == "__main__":
    main()
