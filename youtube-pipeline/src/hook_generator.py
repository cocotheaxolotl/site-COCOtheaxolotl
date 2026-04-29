"""Hook / B-roll generator: cinematic clips via Fal.ai.

Same as univers.studio pipeline — model-agnostic. For Coco, prompts should be
soft / storybook / pastel (not aggressive cinematic).
"""
import os
import sys
import time
from pathlib import Path
import requests
import fal_client
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / "config" / ".env")
os.environ["FAL_KEY"] = os.getenv("FAL_KEY", "")

OUTPUT_DIR = ROOT / "output" / "hooks"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MODELS = {
    "kling25": {
        "id": "fal-ai/kling-video/v2.5-turbo/pro/text-to-video",
        "allowed_durations": [5, 10],
        "duration_str": True,
    },
    "kling16": {
        "id": "fal-ai/kling-video/v1.6/standard/text-to-video",
        "allowed_durations": [5, 10],
        "duration_str": True,
    },
    "hailuo": {
        "id": "fal-ai/minimax/hailuo-02/standard/text-to-video",
        "allowed_durations": [6, 10],
        "duration_str": True,
    },
    "wan": {
        "id": "fal-ai/wan/v2.2-a14b/text-to-video",
        "allowed_durations": [5],
        "duration_str": False,
    },
}


def generate_hook(prompt: str, model: str = "kling25", duration: int = 5,
                  aspect_ratio: str = "9:16", out_name: str | None = None,
                  fallback_models: list[str] | None = None) -> Path:
    if model not in MODELS:
        raise ValueError(f"Unknown model {model}. Available: {list(MODELS)}")

    fallback_models = fallback_models or (["kling16", "wan"] if model == "hailuo" else [])
    models_to_try = [model] + [m for m in fallback_models if m in MODELS]

    last_err = None
    for current_model in models_to_try:
        try:
            return _generate_one(prompt, current_model, duration, aspect_ratio, out_name)
        except Exception as e:
            last_err = e
            print(f"[hook] model={current_model} exhausted retries: {type(e).__name__}: {str(e)[:120]}")
            if current_model != models_to_try[-1]:
                print(f"[hook] falling back to next model...")
    raise last_err


def _generate_one(prompt: str, model: str, duration: int,
                  aspect_ratio: str, out_name: str | None) -> Path:
    cfg = MODELS[model]
    model_id = cfg["id"]

    if duration not in cfg["allowed_durations"]:
        snapped = min(cfg["allowed_durations"], key=lambda d: abs(d - duration))
        print(f"[hook] duration {duration}s not supported by {model}, snapping to {snapped}s")
        duration = snapped

    print(f"[hook] model={model} duration={duration}s ratio={aspect_ratio}")
    print(f"[hook] prompt: {prompt[:120]}{'...' if len(prompt) > 120 else ''}")

    args = {
        "prompt": prompt,
        "duration": str(duration) if cfg["duration_str"] else duration,
        "aspect_ratio": aspect_ratio,
    }

    from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

    def _submit_and_wait():
        h = fal_client.submit(model_id, arguments=args)
        print(f"[hook] submitted, request_id={h.request_id}")
        for event in h.iter_events(with_logs=False):
            if hasattr(event, "logs") and event.logs:
                for log in event.logs:
                    print(f"  · {log.get('message', '')}")
        return h.get()

    last_err = None
    result = None
    for attempt in range(1, 5):
        try:
            t0 = time.time()
            print(f"[hook] {model} attempt {attempt}")
            with ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(_submit_and_wait)
                result = future.result(timeout=240)
            break
        except FuturesTimeout:
            last_err = TimeoutError(f"{model} timed out after 240s")
            print(f"[hook] {model} attempt {attempt} timed out (240s)")
        except Exception as e:
            last_err = e
            err_str = str(e)
            print(f"[hook] {model} attempt {attempt} failed: {type(e).__name__}: {err_str[:120]}")
            non_transient = any(s in err_str for s in [
                "Invalid", "not allowed", "literal_error", "Unauthorized",
            ])
            if non_transient:
                raise
        if attempt < 4:
            wait = [10, 30, 60][attempt - 1]
            print(f"[hook] retrying in {wait}s...")
            time.sleep(wait)
    if result is None:
        raise last_err
    elapsed = time.time() - t0

    video_url = result.get("video", {}).get("url")
    if not video_url:
        raise RuntimeError(f"No video in result: {result}")

    out_name = out_name or f"hook_{model}_{int(time.time())}.mp4"
    out_path = OUTPUT_DIR / out_name
    print(f"[hook] downloading {video_url} -> {out_path}")

    r = requests.get(video_url, timeout=120)
    r.raise_for_status()
    out_path.write_bytes(r.content)

    print(f"[hook] OK in {elapsed:.1f}s, {out_path.stat().st_size // 1024} KB")
    return out_path


if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else (
        "Soft watercolor children's book illustration of a small pink axolotl in pajamas "
        "peeking out of a bedroom window at a starry night sky, magical translucent dolphin "
        "floating gently outside, warm bedside lamp glow, pastel purple and soft blue palette, "
        "dreamy bokeh, calm slow camera push-in, Pixar-soft 3D animation aesthetic, vertical 9:16"
    )
    model = sys.argv[2] if len(sys.argv) > 2 else "kling25"
    generate_hook(prompt, model=model, duration=5, aspect_ratio="9:16")
