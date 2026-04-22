"""
Color by Number Generator for Coco the Axolotl
================================================
Takes a B&W line art illustration and generates a color-by-number page.

Modes:
  --lineart (default): From B&W line art, detects zones and assigns colors
  --colored: From a colored illustration, reduces colors and numbers zones

Usage:
    python color_by_number.py input_image.png [--colors 6] [--min-zone 800] [--output-prefix coco-cbn]
    python color_by_number.py colored_image.png --colored [--colors 8]

Arguments:
    input_image.png     A B&W line art or colored illustration (PNG/JPG)
    --colored           Use colored-image mode (detect colors from image)
    --colors N          Number of colors in palette (default: 6)
    --min-zone N        Minimum zone size in pixels to number (default: 800)
    --blur N            Blur radius for colored mode (default: 3)
    --output-prefix     Prefix for output files
"""

import sys
import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage


# Kid-friendly color palette for Coco (axolotl colors + fun colors)
COCO_PALETTE = [
    ((255, 182, 193), "Rose / Pink"),          # 1 - Pink (Coco's body)
    ((135, 206, 250), "Bleu ciel / Sky Blue"), # 2 - Light blue (water)
    ((144, 238, 144), "Vert / Green"),         # 3 - Light green
    ((255, 218, 185), "Pêche / Peach"),        # 4 - Peach/salmon
    ((255, 255, 150), "Jaune / Yellow"),       # 5 - Yellow
    ((221, 160, 221), "Violet / Purple"),      # 6 - Plum/purple
    ((255, 160, 122), "Corail / Coral"),       # 7 - Light coral
    ((176, 224, 230), "Turquoise"),            # 8 - Powder blue
    ((255, 228, 181), "Orange clair / Light Orange"), # 9
    ((152, 251, 152), "Menthe / Mint"),        # 10
    ((240, 128, 128), "Rouge clair / Light Red"), # 11
    ((200, 200, 200), "Gris / Grey"),          # 12
]


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


# =============================================================================
# LINE ART MODE - From B&W coloring pages
# =============================================================================

def detect_zones_from_lineart(img, min_zone_size):
    """Detect enclosed white zones from B&W line art using flood fill."""
    # Convert to grayscale and threshold
    gray = np.array(img.convert("L"))

    # Threshold: pixels > 180 are "white" (zone), rest is "black" (outline)
    binary = (gray > 180).astype(np.uint8)

    print(f"Detecting zones from line art...")

    # Label connected white regions
    labeled_array, num_features = ndimage.label(binary)
    print(f"  Found {num_features} raw zones")

    # Filter by size and collect zone info
    zones = []  # (zone_id_in_labeled, centroid_y, centroid_x, size)
    for region_id in range(1, num_features + 1):
        region_mask = labeled_array == region_id
        size = region_mask.sum()

        if size < min_zone_size:
            continue

        cy, cx = ndimage.center_of_mass(region_mask)
        cy, cx = int(cy), int(cx)

        # Make sure centroid is inside the region
        if not region_mask[cy, cx]:
            ys, xs = np.where(region_mask)
            dists = (ys - cy) ** 2 + (xs - cx) ** 2
            nearest = np.argmin(dists)
            cy, cx = ys[nearest], xs[nearest]

        zones.append((region_id, cy, cx, size))

    print(f"  Kept {len(zones)} zones (min size: {min_zone_size}px)")
    return labeled_array, zones


def assign_colors_graph_coloring(labeled_array, zones, n_colors):
    """Assign colors to zones so adjacent zones have different colors.
    Uses a greedy graph coloring approach."""

    # Build adjacency: which zones touch each other?
    zone_ids = {z[0] for z in zones}

    # Find adjacencies by checking borders
    adjacency = {z[0]: set() for z in zones}

    # Dilate each zone by 10+ pixels to jump over black outlines
    # (outlines can be 3-8 pixels wide in typical coloring pages)
    h, w = labeled_array.shape
    for z_id, _, _, _ in zones:
        mask = (labeled_array == z_id)
        dilated = ndimage.binary_dilation(mask, iterations=12)
        # Find which other zone IDs are in the dilated border
        border = dilated & ~mask
        neighbor_ids = np.unique(labeled_array[border])
        for nid in neighbor_ids:
            if nid != z_id and nid in zone_ids:
                adjacency[z_id].add(nid)
                adjacency[nid].add(z_id)

    # Greedy graph coloring
    # Sort zones by number of neighbors (most constrained first)
    sorted_zones = sorted(zones, key=lambda z: len(adjacency[z[0]]), reverse=True)

    color_assignment = {}  # zone_id -> color_index (0-based)

    for z_id, cy, cx, size in sorted_zones:
        # Find colors used by neighbors
        neighbor_colors = {color_assignment[nid] for nid in adjacency[z_id] if nid in color_assignment}

        # Pick the first available color
        for c in range(n_colors):
            if c not in neighbor_colors:
                color_assignment[z_id] = c
                break
        else:
            # All colors used by neighbors, just pick least-used among neighbors
            color_assignment[z_id] = 0

    # Report
    color_counts = {}
    for z_id, c in color_assignment.items():
        color_counts[c] = color_counts.get(c, 0) + 1
    colors_used = len(color_counts)
    print(f"  Assigned {colors_used} colors to {len(zones)} zones")

    return color_assignment


def create_cbn_from_lineart(img, n_colors, min_zone_size, prefix):
    """Full pipeline for line art mode."""
    w, h = img.size

    # Step 1: Detect zones
    labeled_array, zones = detect_zones_from_lineart(img, min_zone_size)

    if not zones:
        print("ERROR: No zones detected! Try lowering --min-zone")
        sys.exit(1)

    # Sort zones by size (largest first)
    zones.sort(key=lambda z: z[3], reverse=True)

    # Skip the largest zone if it's likely the background (>30% of image)
    total_pixels = w * h
    if zones[0][3] > total_pixels * 0.30:
        print(f"  Skipping background zone ({zones[0][3] / total_pixels * 100:.0f}% of image)")
        bg_zone_id = zones[0][0]
        zones = zones[1:]
    else:
        bg_zone_id = None

    # Step 2: Assign colors using graph coloring
    n_colors = min(n_colors, len(COCO_PALETTE))
    color_assignment = assign_colors_graph_coloring(labeled_array, zones, n_colors)

    # Step 3: Build the numbered image
    print("Creating numbered image...")

    # Start with the original line art (keeps the black outlines)
    result = img.convert("RGB").copy()
    draw = ImageDraw.Draw(result)

    # Make everything that's white stay white (the zones)
    # and keep black outlines

    # Determine font size
    base_font_size = max(14, min(w, h) // 50)

    for zone_id, cy, cx, size in zones:
        color_idx = color_assignment.get(zone_id, 0)
        number = str(color_idx + 1)  # 1-indexed

        # Adjust font based on zone size
        zone_font_size = base_font_size
        if size < 3000:
            zone_font_size = max(10, base_font_size * 2 // 3)
        elif size < 1500:
            zone_font_size = max(8, base_font_size // 2)

        font = get_font(zone_font_size)

        # Get text size
        bbox = draw.textbbox((0, 0), number, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        tx = cx - tw // 2
        ty = cy - th // 2

        # Keep within bounds
        tx = max(2, min(tx, w - tw - 2))
        ty = max(2, min(ty, h - th - 2))

        # Small white circle behind number for readability
        pad = 3
        draw.ellipse(
            [tx - pad, ty - pad, tx + tw + pad, ty + th + pad],
            fill=(255, 255, 255),
            outline=(180, 180, 180),
        )
        draw.text((tx, ty), number, fill=(0, 0, 0), font=font)

    # Step 4: Create legend
    print("Creating legend...")
    colors_used = sorted(set(color_assignment.values()))
    legend = create_legend_palette(colors_used, w)

    # Step 5: Create colored reference (so user knows what it should look like)
    print("Creating colored reference...")
    reference = create_colored_reference(img, labeled_array, zones, color_assignment, bg_zone_id)

    # Step 6: Save
    result.save(f"{prefix}.png", dpi=(300, 300))
    print(f"Saved: {prefix}.png (numbered page)")

    legend.save(f"{prefix}-legend.png", dpi=(300, 300))
    print(f"Saved: {prefix}-legend.png")

    # Combined: numbered + legend
    combined = stack_images(result, legend)
    combined.save(f"{prefix}-full.png", dpi=(300, 300))
    print(f"Saved: {prefix}-full.png (page + legend)")

    reference.save(f"{prefix}-reference.png", dpi=(300, 300))
    print(f"Saved: {prefix}-reference.png (colored answer key)")

    print(f"\nDone! {len(zones)} zones with {len(colors_used)} colors.")
    return


def create_colored_reference(img, labeled_array, zones, color_assignment, bg_zone_id):
    """Create a colored version showing what the finished result should look like."""
    result = np.array(img.convert("RGB")).copy()
    gray = np.array(img.convert("L"))

    # Only color white areas (not the black outlines)
    white_mask = gray > 180

    for zone_id, _, _, _ in zones:
        color_idx = color_assignment.get(zone_id, 0)
        rgb = COCO_PALETTE[color_idx][0]

        zone_mask = (labeled_array == zone_id) & white_mask
        result[zone_mask] = rgb

    return Image.fromarray(result)


def create_legend_palette(colors_used, img_width):
    """Create legend using the COCO_PALETTE."""
    n = len(colors_used)
    swatch_size = 50
    padding = 15
    text_width = 200
    cols = min(3, n)
    rows = (n + cols - 1) // cols

    legend_w = cols * (swatch_size + text_width + padding) + padding
    legend_w = max(legend_w, img_width)
    legend_h = rows * (swatch_size + padding) + padding + 45

    legend = Image.new("RGB", (legend_w, legend_h), (255, 255, 255))
    draw = ImageDraw.Draw(legend)

    # Title
    title_font = get_font(22)
    draw.text((padding, 8), "Color by Number / Coloriage par numéros", fill=(0, 0, 0), font=title_font)

    font = get_font(18)
    for i, color_idx in enumerate(colors_used):
        col = i % cols
        row = i // cols

        x = padding + col * (swatch_size + text_width + padding)
        y = 45 + padding + row * (swatch_size + padding)

        rgb, name = COCO_PALETTE[color_idx]

        # Swatch
        draw.rectangle([x, y, x + swatch_size, y + swatch_size],
                        fill=rgb, outline=(0, 0, 0), width=2)

        # Number and name
        label = f"  {color_idx + 1} = {name}"
        draw.text((x + swatch_size + 5, y + 12), label, fill=(0, 0, 0), font=font)

    return legend


# =============================================================================
# COLORED IMAGE MODE - From colored illustrations
# =============================================================================

def create_cbn_from_colored(img, n_colors, min_zone_size, blur_radius, prefix):
    """Full pipeline for colored image mode.
    Extracts black outlines from the colored image, detects zones,
    then samples colors from the original to assign correct colors."""
    from sklearn.cluster import KMeans

    w, h = img.size
    img_array = np.array(img)
    gray = np.array(img.convert("L"))

    # Step 1: Extract black outlines from the colored image
    # Dark pixels (< 60 brightness) are outlines
    print("Extracting outlines from colored image...")
    outline_mask = gray < 60
    # Clean up: dilate outlines slightly to close small gaps
    outline_mask = ndimage.binary_dilation(outline_mask, iterations=1)

    # Step 2: Detect zones (non-outline connected regions)
    zone_binary = (~outline_mask).astype(np.uint8)
    labeled_array, num_features = ndimage.label(zone_binary)
    print(f"  Found {num_features} raw zones")

    # Step 3: Collect zones with their sampled color
    zones_raw = []  # (region_id, cy, cx, size, avg_color_rgb)
    for region_id in range(1, num_features + 1):
        region_mask = labeled_array == region_id
        size = region_mask.sum()
        if size < min_zone_size:
            continue

        cy, cx = ndimage.center_of_mass(region_mask)
        cy, cx = int(cy), int(cx)
        if not region_mask[cy, cx]:
            ys, xs = np.where(region_mask)
            dists = (ys - cy) ** 2 + (xs - cx) ** 2
            nearest = np.argmin(dists)
            cy, cx = ys[nearest], xs[nearest]

        # Sample the average color from the original image in this zone
        zone_pixels = img_array[region_mask]
        avg_color = zone_pixels.mean(axis=0).astype(np.uint8)
        zones_raw.append((region_id, cy, cx, size, avg_color))

    print(f"  Kept {len(zones_raw)} zones (min size: {min_zone_size}px)")

    if not zones_raw:
        print("ERROR: No zones detected! Try lowering --min-zone")
        sys.exit(1)

    # Step 4: Cluster the sampled colors into n_colors groups
    zone_colors = np.array([z[4] for z in zones_raw], dtype=np.float64)
    actual_n = min(n_colors, len(zones_raw))
    print(f"Clustering zone colors into {actual_n} groups...")
    kmeans = KMeans(n_clusters=actual_n, random_state=42, n_init=10)
    color_labels = kmeans.fit_predict(zone_colors)
    palette = kmeans.cluster_centers_.astype(np.uint8)

    # Sort palette by brightness (lightest first, so background-like colors get low numbers)
    brightness_order = np.argsort(-palette.sum(axis=1))
    remap = np.zeros(actual_n, dtype=int)
    for new_idx, old_idx in enumerate(brightness_order):
        remap[old_idx] = new_idx
    color_labels = remap[color_labels]
    palette = palette[brightness_order]

    print("Color palette:")
    for i, c in enumerate(palette):
        name = rgb_to_color_name(c[0], c[1], c[2])
        count = (color_labels == i).sum()
        print(f"  #{i+1}: RGB({c[0]},{c[1]},{c[2]}) = {name} ({count} zones)")

    # Note: we do NOT skip the background for colored images
    # because the background color (e.g. cyan water) is important

    # Step 6: Build the numbered page using ORIGINAL outlines
    print("Creating numbered page...")
    result = Image.new("RGB", (w, h), (255, 255, 255))
    result_array = np.array(result)
    # Draw original outlines in black
    result_array[outline_mask] = [0, 0, 0]
    result = Image.fromarray(result_array)
    draw = ImageDraw.Draw(result)

    base_font_size = max(14, min(w, h) // 45)

    for i, (region_id, cy, cx, size, avg_color) in enumerate(zones_raw):
        color_idx = color_labels[i]
        number = str(color_idx + 1)

        zone_font_size = base_font_size
        if size < 5000:
            zone_font_size = max(10, base_font_size * 2 // 3)
        if size < 2000:
            zone_font_size = max(8, base_font_size // 2)

        font = get_font(zone_font_size)
        bbox = draw.textbbox((0, 0), number, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        tx = max(2, min(cx - tw // 2, w - tw - 2))
        ty = max(2, min(cy - th // 2, h - th - 2))

        pad = 3
        draw.ellipse([tx - pad, ty - pad, tx + tw + pad, ty + th + pad],
                     fill=(255, 255, 255), outline=(180, 180, 180))
        draw.text((tx, ty), number, fill=(0, 0, 0), font=font)

    # Step 7: Create colored reference
    print("Creating colored reference...")
    ref_array = np.array(result.copy())
    for i, (region_id, cy, cx, size, avg_color) in enumerate(zones_raw):
        color_idx = color_labels[i]
        rgb = tuple(palette[color_idx])
        zone_mask = (labeled_array == region_id) & ~outline_mask
        ref_array[zone_mask] = rgb
    reference = Image.fromarray(ref_array)

    # Step 8: Legend & save
    print("Creating legend...")
    legend = create_legend_rgb(palette, w)

    result.save(f"{prefix}.png", dpi=(300, 300))
    print(f"Saved: {prefix}.png (numbered page)")
    legend.save(f"{prefix}-legend.png", dpi=(300, 300))
    print(f"Saved: {prefix}-legend.png")
    combined = stack_images(result, legend)
    combined.save(f"{prefix}-full.png", dpi=(300, 300))
    print(f"Saved: {prefix}-full.png")
    reference.save(f"{prefix}-reference.png", dpi=(300, 300))
    print(f"Saved: {prefix}-reference.png (answer key)")
    print(f"\nDone! {len(zones_raw)} zones with {actual_n} colors.")


def rgb_to_color_name(r, g, b):
    """Convert RGB to a human-readable color name (FR/EN)."""
    r, g, b = int(r), int(g), int(b)  # Convert from uint8 to avoid overflow
    # Determine dominant characteristics
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    brightness = (r + g + b) / 3

    if max_c - min_c < 30:  # Very low saturation = grey/white/black
        if brightness > 200:
            return "Blanc / White"
        elif brightness > 140:
            return "Gris clair / Light Grey"
        elif brightness > 80:
            return "Gris / Grey"
        else:
            return "Noir / Black"

    # Find the hue
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
    else:  # Blue dominant
        if r > g + 30 and r > 100:
            return "Violet / Purple"
        elif g > r + 10:
            return "Bleu ciel / Sky Blue"
        else:
            if b > 200:
                return "Bleu clair / Light Blue"
            return "Bleu / Blue"


def create_legend_rgb(colors, img_width):
    """Create legend from RGB color array with human-readable color names."""
    n = len(colors)
    swatch_size = 50
    padding = 15
    text_width = 220
    cols = min(3, n)
    rows = (n + cols - 1) // cols

    legend_w = max(cols * (swatch_size + text_width + padding) + padding, img_width)
    legend_h = rows * (swatch_size + padding) + padding + 45

    legend = Image.new("RGB", (legend_w, legend_h), (255, 255, 255))
    draw = ImageDraw.Draw(legend)

    title_font = get_font(22)
    draw.text((padding, 8), "Color by Number / Coloriage par numéros", fill=(0, 0, 0), font=title_font)

    font = get_font(18)
    for i, color in enumerate(colors):
        col = i % cols
        row = i // cols
        x = padding + col * (swatch_size + text_width + padding)
        y = 45 + padding + row * (swatch_size + padding)

        name = rgb_to_color_name(color[0], color[1], color[2])

        draw.rectangle([x, y, x + swatch_size, y + swatch_size],
                        fill=tuple(color), outline=(0, 0, 0), width=2)
        draw.text((x + swatch_size + 5, y + 12),
                  f"  {i+1} = {name}", fill=(0, 0, 0), font=font)

    return legend


# =============================================================================
# SHARED UTILITIES
# =============================================================================

def stack_images(top, bottom, gap=10):
    """Stack two images vertically with a gap."""
    w = max(top.size[0], bottom.size[0])
    h = top.size[1] + bottom.size[1] + gap
    combined = Image.new("RGB", (w, h), (255, 255, 255))
    combined.paste(top, ((w - top.size[0]) // 2, 0))
    combined.paste(bottom, ((w - bottom.size[0]) // 2, top.size[1] + gap))
    return combined


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Generate Color by Number pages")
    parser.add_argument("input", help="Path to the illustration (PNG/JPG)")
    parser.add_argument("--colored", action="store_true",
                        help="Use colored-image mode (default: line art mode)")
    parser.add_argument("--colors", type=int, default=6,
                        help="Number of colors (default: 6)")
    parser.add_argument("--min-zone", type=int, default=800,
                        help="Minimum zone size in pixels (default: 800)")
    parser.add_argument("--blur", type=int, default=3,
                        help="Blur radius for colored mode (default: 3)")
    parser.add_argument("--output-prefix", help="Prefix for output files")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} not found")
        sys.exit(1)

    prefix = args.output_prefix or input_path.stem + "-color-by-number"
    img = Image.open(input_path).convert("RGB")
    print(f"Image loaded: {img.size[0]}x{img.size[1]} pixels")

    if args.colored:
        create_cbn_from_colored(img, args.colors, args.min_zone, args.blur, prefix)
    else:
        create_cbn_from_lineart(img, args.colors, args.min_zone, prefix)


if __name__ == "__main__":
    main()
