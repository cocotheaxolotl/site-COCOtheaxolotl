"""
Automated illustration generator for "Whose Egg Is This?"
Uses OpenAI API (GPT-4o / gpt-image-1) to:
1. Generate colored illustrations from prompts
2. Convert each colored illustration to a coloring book page

Prerequisites:
- pip install openai (already installed)
- Set your API key: set OPENAI_API_KEY=sk-...
  Or create a file .env with OPENAI_API_KEY=sk-...
- API credits on https://platform.openai.com (separate from ChatGPT Pro subscription)

Usage:
  python generate-illustrations-api.py                  # Generate all missing illustrations
  python generate-illustrations-api.py --only-coloring  # Only convert colored → coloring
  python generate-illustrations-api.py --start 14       # Start from prompt 14 (giraffe)
  python generate-illustrations-api.py --only 5         # Generate only prompt 5 (unicorn)
"""

import os
import sys
import re
import base64
import time
import argparse
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("ERROR: openai package not installed. Run: pip install openai")
    sys.exit(1)

# --- Configuration ---
SCRIPT_DIR = Path(__file__).parent
COLORED_DIR = SCRIPT_DIR / "whose-egg-colored"
COLORING_DIR = SCRIPT_DIR / "whose-egg-coloring"
PROMPTS_FILE = SCRIPT_DIR / "chatgpt-prompts-whose-egg.md"

# Mapping prompt number → filename (without extension)
PROMPT_FILENAMES = {
    0: "axolotl-cover",
    1: "axolotl-intro-eggshell",
    2: "axolotl-kitten",
    3: "axolotl-puppy",
    4: "axolotl-rabbit",
    5: "axolotl-unicorn",
    6: "axolotl-panda",
    7: "axolotl-dolphin",
    8: "axolotl-foal",
    9: "axolotl-butterfly",
    10: "axolotl-dinosaur",
    11: "axolotl-lion",
    12: "axolotl-bear",
    13: "axolotl-elephant",
    14: "axolotl-giraffe",
    15: "axolotl-penguin",
    16: "axolotl-koala",
    17: "axolotl-fox",
    18: "axolotl-owl",
    19: "axolotl-turtle",
    20: "axolotl-frog",
    21: "axolotl-highland-cow",
    22: "axolotl-flamingo",
    23: "axolotl-sloth",
    24: "axolotl-otter",
    25: "axolotl-hedgehog",
    26: "axolotl-llama",
    27: "axolotl-duckling",
    28: "axolotl-chick",
    29: "axolotl-lamb",
    30: "axolotl-dragon",
    31: "axolotl-ending-mama-lili",
    32: "axolotl-back-cover",
}

COLORING_PROMPT = (
    "Convert this illustration into a clean coloring book page. "
    "Black outlines only on a pure white background. "
    "Thick, clear lines suitable for children to color in. "
    "Keep the same composition and characters. No shading, no colors, no gray areas. "
    "Portrait format, 3:4 ratio."
)


def parse_prompts(filepath):
    """Parse the markdown file and extract prompts by number."""
    content = filepath.read_text(encoding="utf-8")
    prompts = {}

    # Match ## Prompt N — ... followed by ``` code block
    pattern = r"## Prompt (\d+) —.*?\n```\n(.*?)\n```"
    matches = re.findall(pattern, content, re.DOTALL)

    for num_str, prompt_text in matches:
        num = int(num_str)
        prompts[num] = prompt_text.strip()

    return prompts


def generate_colored(client, prompt_text, output_path):
    """Generate a colored illustration from a text prompt."""
    print(f"  Generating colored illustration...")

    try:
        # Use GPT-4o image generation via the images API
        response = client.images.generate(
            model="gpt-image-1",
            prompt=prompt_text,
            size="1024x1536",  # Portrait 3:4 ratio
            quality="high",
            n=1,
        )

        # Save the image
        if response.data[0].b64_json:
            image_data = base64.b64decode(response.data[0].b64_json)
            output_path.write_bytes(image_data)
            print(f"  OK Saved: {output_path.name}")
            return True
        elif response.data[0].url:
            # If we get a URL instead of base64, download it
            import urllib.request
            urllib.request.urlretrieve(response.data[0].url, str(output_path))
            print(f"  OK Saved: {output_path.name}")
            return True

    except Exception as e:
        print(f"  FAIL Error: {e}")
        return False


def convert_to_coloring(client, colored_path, output_path):
    """Convert a colored illustration to a coloring book page."""
    print(f"  Converting to coloring page...")

    try:
        # Read the colored image as base64
        image_data = colored_path.read_bytes()
        b64_image = base64.b64encode(image_data).decode("utf-8")

        # Determine mime type
        suffix = colored_path.suffix.lower()
        mime = "image/png" if suffix == ".png" else "image/jpeg"

        # Use chat completions with vision + image generation
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime};base64,{b64_image}"
                            },
                        },
                        {
                            "type": "text",
                            "text": COLORING_PROMPT,
                        },
                    ],
                }
            ],
            # Request image output if supported
        )

        # If the model returns an image in the response
        if hasattr(response.choices[0].message, 'image') and response.choices[0].message.image:
            img_data = base64.b64decode(response.choices[0].message.image.b64_json)
            output_path.write_bytes(img_data)
            print(f"  OK Saved: {output_path.name}")
            return True

        # Fallback: use images.edit endpoint
        print(f"  Trying images.edit fallback...")
        response = client.images.edit(
            model="gpt-image-1",
            image=open(colored_path, "rb"),
            prompt=COLORING_PROMPT,
            size="1024x1536",
            n=1,
        )

        if response.data[0].b64_json:
            img_data = base64.b64decode(response.data[0].b64_json)
            output_path.write_bytes(img_data)
            print(f"  OK Saved: {output_path.name}")
            return True
        elif response.data[0].url:
            import urllib.request
            urllib.request.urlretrieve(response.data[0].url, str(output_path))
            print(f"  OK Saved: {output_path.name}")
            return True

    except Exception as e:
        print(f"  FAIL Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Generate book illustrations via OpenAI API")
    parser.add_argument("--only-coloring", action="store_true",
                        help="Only convert existing colored images to coloring pages")
    parser.add_argument("--start", type=int, default=0,
                        help="Start from prompt number N")
    parser.add_argument("--end", type=int, default=32,
                        help="End at prompt number N (inclusive)")
    parser.add_argument("--only", type=int, default=None,
                        help="Generate only prompt number N")
    parser.add_argument("--no-coloring", action="store_true",
                        help="Skip coloring page conversion")
    parser.add_argument("--delay", type=int, default=5,
                        help="Delay in seconds between API calls (default: 5)")
    args = parser.parse_args()

    # Check API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        # Try .env file
        env_file = SCRIPT_DIR / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("OPENAI_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"').strip("'").strip()
                    break

    if not api_key:
        print("ERROR: No API key found!")
        print("Set it with: set OPENAI_API_KEY=sk-...")
        print(f"Or create: {SCRIPT_DIR / '.env'} with OPENAI_API_KEY=sk-...")
        sys.exit(1)

    client = OpenAI(api_key=api_key, timeout=180.0)

    # Parse prompts
    prompts = parse_prompts(PROMPTS_FILE)
    print(f"Found {len(prompts)} prompts in {PROMPTS_FILE.name}")

    # Create directories
    COLORED_DIR.mkdir(exist_ok=True)
    COLORING_DIR.mkdir(exist_ok=True)

    # Determine which prompts to process
    if args.only is not None:
        prompt_numbers = [args.only]
    else:
        prompt_numbers = list(range(args.start, args.end + 1))

    # Process each prompt
    stats = {"colored_ok": 0, "colored_skip": 0, "colored_fail": 0,
             "coloring_ok": 0, "coloring_skip": 0, "coloring_fail": 0}

    for num in prompt_numbers:
        if num not in PROMPT_FILENAMES:
            continue

        filename = PROMPT_FILENAMES[num]
        colored_path = COLORED_DIR / f"{filename}-colored.png"
        coloring_path = COLORING_DIR / f"{filename}-coloring.png"

        print(f"\n{'='*60}")
        print(f"Prompt {num}: {filename}")
        print(f"{'='*60}")

        # Step 1: Generate colored illustration
        if not args.only_coloring:
            if colored_path.exists():
                print(f"  SKIP Colored already exists, skipping")
                stats["colored_skip"] += 1
            elif num in prompts:
                if generate_colored(client, prompts[num], colored_path):
                    stats["colored_ok"] += 1
                else:
                    stats["colored_fail"] += 1
                time.sleep(args.delay)  # Rate limit protection
            else:
                print(f"  WARNING No prompt found for #{num}")

        # Step 2: Convert to coloring page
        if not args.no_coloring:
            if coloring_path.exists():
                print(f"  SKIP Coloring already exists, skipping")
                stats["coloring_skip"] += 1
            elif colored_path.exists():
                if convert_to_coloring(client, colored_path, coloring_path):
                    stats["coloring_ok"] += 1
                else:
                    stats["coloring_fail"] += 1
                time.sleep(args.delay)  # Rate limit protection
            else:
                print(f"  WARNING No colored image to convert")

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Colored:  {stats['colored_ok']} generated, {stats['colored_skip']} skipped, {stats['colored_fail']} failed")
    print(f"Coloring: {stats['coloring_ok']} converted, {stats['coloring_skip']} skipped, {stats['coloring_fail']} failed")


if __name__ == "__main__":
    main()
