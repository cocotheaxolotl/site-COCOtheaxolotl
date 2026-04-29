"""End-to-end orchestrator: produce one Coco the Axolotl ACQUISITION YouTube Short.

Goal: drive parents 25-45 to buy Coco books on Amazon / cocotheaxolotl.org.
NOT readalouds. Hook → pain → book reveal → outcome → CTA.

Usage:
    python src/run.py coco-cant-sleep en bedtime
    python src/run.py i-love-you-more fr love

Pipeline:
    1. Generate script (Claude)              -> output/scripts/<slug>_<lang>_<angle>.json
    2. Generate hook clip (Fal.ai Kling)     -> output/hooks/<slug>_hook.mp4
    3. Generate per-scene B-roll clips       -> output/brolls/<slug>_<i>.mp4
    4. Generate narration (ElevenLabs)       -> output/audio/<...>.mp3
    5. Assemble final video (FFmpeg)         -> output/videos/<...>.mp4

Each step caches its output. Use --force to regenerate everything.
"""
import sys
import json
import time
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from script_generator import generate_script, load_book
from hook_generator import generate_hook
from voice_generator import synth_from_script
from assemble import assemble


def _gen_clip(prompt: str, out_path: Path, duration: int = 5,
              aspect_ratio: str = "9:16", force: bool = False) -> Path:
    """Generate one Fal.ai clip if not cached."""
    if out_path.exists() and not force:
        print(f"[clip] cached: {out_path.name}")
        return out_path
    gen = generate_hook(prompt, model="kling25", duration=duration,
                        aspect_ratio=aspect_ratio, out_name=out_path.name)
    if gen != out_path:
        gen.rename(out_path)
    return out_path


def _concat_clips(clips: list[Path], out_path: Path) -> Path:
    """Concatenate B-roll clips for the main body."""
    list_file = out_path.with_suffix(".txt")
    list_file.write_text("\n".join(f"file '{c.as_posix()}'" for c in clips), encoding="utf-8")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
           "-c:v", "libx264", "-preset", "medium", "-crf", "20",
           "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
           "-r", "30", "-an", str(out_path)]
    subprocess.run(cmd, check=True, capture_output=True)
    list_file.unlink(missing_ok=True)
    return out_path


def run_pipeline(slug: str, lang: str = "en", angle: str = "bedtime",
                 force: bool = False) -> Path:
    print(f"\n{'=' * 60}\n[run] book={slug} lang={lang} angle={angle}\n{'=' * 60}\n")

    book = load_book(slug)

    # 1. Script
    script_path = ROOT / "output" / "scripts" / f"{slug}_short_{lang}_{angle}.json"
    if force or not script_path.exists():
        print("[1/5] script generation")
        generate_script(slug, "short", lang, hook_angle=angle)
    else:
        print(f"[1/5] script (cached): {script_path.name}")
    script = json.loads(script_path.read_text(encoding="utf-8"))

    # 2. Hook clip (parent-coded scroll-stopper, NOT the book)
    hook_visual = script.get("hook", {}).get("visual_prompt", "")
    hook_path = ROOT / "output" / "hooks" / f"{slug}_{angle}_hook.mp4"
    if force or not hook_path.exists():
        print("[2/5] hook clip (Kling 2.5)")
        _gen_clip(hook_visual, hook_path, duration=5, force=force)
    else:
        print(f"[2/5] hook (cached): {hook_path.name}")

    # 3. Per-scene B-roll clips
    print("[3/5] B-roll clips per scene")
    brolls_dir = ROOT / "output" / "brolls" / slug
    brolls_dir.mkdir(parents=True, exist_ok=True)
    scene_clips = []
    for i, scene in enumerate(script.get("scenes", [])):
        visual = scene.get("visual", "")
        if visual == "overlay":
            # Skip — handled as text overlay in assemble
            continue
        broll_prompt = scene.get("broll_prompt", "")
        if not broll_prompt:
            continue
        dur = max(5, int(scene.get("end_s", 0) - scene.get("start_s", 0)))
        clip_path = brolls_dir / f"scene_{i:02d}.mp4"
        try:
            _gen_clip(broll_prompt, clip_path, duration=min(dur, 10), force=force)
            scene_clips.append(clip_path)
        except Exception as e:
            print(f"[3/5] scene {i} FAILED: {type(e).__name__}: {e}")

    if not scene_clips:
        raise RuntimeError("No B-roll clips generated — cannot assemble video")

    # Concatenate scene clips into main body video
    main_body = ROOT / "output" / "brolls" / f"{slug}_{angle}_body.mp4"
    _concat_clips(scene_clips, main_body)

    # 4. Voice-over (confident parent voice)
    voice_path = ROOT / "output" / "audio" / f"{script_path.stem}.mp3"
    if force or not voice_path.exists():
        print("[4/5] voice-over (ElevenLabs)")
        synth_from_script(script_path, lang=lang)
    else:
        print(f"[4/5] voice (cached): {voice_path.name}")

    # 5. Assemble
    print("[5/5] assembling final video")
    out_name = f"{slug}_{lang}_{angle}_{int(time.time())}.mp4"
    final = assemble(
        out_name=out_name,
        hook_clip=hook_path,
        main_video=main_body,
        voice_audio=voice_path,
        hook_text=script.get("hook", {}).get("text_overlay", ""),
        hook_text_2=script.get("hook", {}).get("text_overlay_2", ""),
        outro_text=script.get("outro_text_overlay", ""),
        cta_url=book.get("amazon_url") or "cocotheaxolotl.org",
        music_path=None,  # acquisition shorts: voice over silence > music
        lang=lang,
    )

    print(f"\n{'=' * 60}\n[run] DONE -> {final}\n{'=' * 60}\n")
    print(f"Title : {script.get('title', '')}")
    print(f"Tags  : {', '.join(script.get('tags', [])[:8])}")
    print(f"Next  : python src/youtube_upload.py \"{final}\" \"{script.get('title', '')}\"")
    return final


if __name__ == "__main__":
    slug = sys.argv[1] if len(sys.argv) > 1 else "coco-cant-sleep"
    lang = sys.argv[2] if len(sys.argv) > 2 else "en"
    angle = sys.argv[3] if len(sys.argv) > 3 else "bedtime"
    force = "--force" in sys.argv
    run_pipeline(slug, lang, angle, force=force)
