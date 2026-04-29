"""Generate the missing 'chauve-souris' (bat) clip using Fal.ai Kling 2.5 image-to-video.

Animates the existing book illustration with subtle storybook motion that matches
the narration ('bats hanging upside down, brain sorting through memories').
"""
import os
import time
import requests
from pathlib import Path
from dotenv import load_dotenv
import fal_client

# Load FAL_KEY from univers.studio .env (Coco doesn't have one yet)
ENV = Path("C:/Users/33612/Documents/site_univers_studio/youtube-pipeline/config/.env")
load_dotenv(ENV)
os.environ["FAL_KEY"] = os.getenv("FAL_KEY", "")

if not os.environ["FAL_KEY"]:
    raise RuntimeError("FAL_KEY introuvable")

SLEEP_BOOK = Path("C:/Users/33612/Documents/site_COCOtheaxolotl/LIVRES COCO/Coco Can't Sleep Tonight!")
SRC_IMG = SLEEP_BOOK / "images des livres" / "chauve-souris.png"
OUT_DIR = SLEEP_BOOK / "Coco-ne-dort-pas-ce-soir-FR-8.5x11-spreads-V5" / "dessin animé coco-ne_dort_pas_ce_soir"
OUT_PATH = OUT_DIR / "chauve_souris_1.mp4"

assert SRC_IMG.exists(), f"Source missing: {SRC_IMG}"
print(f"[1/3] Upload illustration -> Fal.ai")
image_url = fal_client.upload_file(str(SRC_IMG))
print(f"      uploaded: {image_url[:80]}...")

# Animation prompt — matches the narration scene (bats sleeping upside down,
# the awake bat hovering near Coco, thought bubbles, candle flame flickering)
PROMPT = (
    "Soft children's storybook scene comes to life with very gentle motion. "
    "The small awake brown bat in the foreground hovers in place and slowly flaps "
    "its wings up and down. The sleeping bats hanging upside down on the cave roof "
    "sway slightly side to side as if breathing in their sleep. The thought bubbles "
    "above the bat drift gently and the small icons inside them shimmer faintly. "
    "The candle flame on Coco's candlestick flickers warmly. Tiny golden fireflies "
    "float slowly in the background. Coco's pink axolotl pajama hat sways slightly "
    "in the night breeze. Watercolor children's book illustration style, dreamy night "
    "atmosphere, very subtle calm motion, no camera movement, 24 fps."
)

print(f"[2/3] Génération Kling 2.5 image-to-video (5s)")
print(f"      prompt: {PROMPT[:120]}...")

t0 = time.time()
handler = fal_client.submit(
    "fal-ai/kling-video/v2.5-turbo/pro/image-to-video",
    arguments={
        "prompt": PROMPT,
        "image_url": image_url,
        "duration": "5",
        "negative_prompt": "blur, distortion, sudden movement, fast motion, scary, dark horror, glitch, deformed, extra limbs",
    },
)
print(f"      request_id={handler.request_id}")

for event in handler.iter_events(with_logs=False):
    if hasattr(event, "logs") and event.logs:
        for log in event.logs:
            print(f"      · {log.get('message', '')}")

result = handler.get()
elapsed = time.time() - t0
video_url = result.get("video", {}).get("url")
if not video_url:
    raise RuntimeError(f"No video in result: {result}")

print(f"[3/3] Téléchargement ({elapsed:.0f}s écoulés)")
r = requests.get(video_url, timeout=120)
r.raise_for_status()
OUT_PATH.write_bytes(r.content)
print(f"\n[DONE] -> {OUT_PATH} ({OUT_PATH.stat().st_size // 1024} KB)")
