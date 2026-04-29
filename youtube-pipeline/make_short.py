"""Convertit une scène animée du livre Coco en YouTube Short 30s.

Structure imposée :
  [0-3s]  HOOK (grosse phrase scroll-stopper)
  [3-10s] INFO 1 (fait du livre, retention)
  [10-20s] INFO 2 (fait + emotion)
  [20-27s] INFO 3 / closing beat
  [27-30s] CTA "Suivant : <nom animal> →"

Inputs :
  - une scène animée mp4 (ex: loutres_assemble.mp4)
  - une narration courte (voix Edge TTS Jenny -18%)
  - 4 beats de texte overlay (hook, info1, info2, cta)

Output :
  - <slug>_short.mp4 vertical 1080x1920, 30s, voix + musique
"""
import asyncio
import shutil
import subprocess
from pathlib import Path
from dataclasses import dataclass
import edge_tts


ROOT = Path(__file__).resolve().parent
LIVRES = ROOT.parent / "LIVRES COCO"
SLEEP_DIR = LIVRES / "Coco Can't Sleep Tonight!" / "Coco-ne-dort-pas-ce-soir-FR-8.5x11-spreads-V5" / "dessin animé coco-ne_dort_pas_ce_soir"
OUT = ROOT / "output" / "shorts"
OUT.mkdir(parents=True, exist_ok=True)
WORK = OUT / "_work"
WORK.mkdir(exist_ok=True)

VIDEO_W, VIDEO_H = 1080, 1920
FPS = 30
TARGET_DUR = 25.0  # visuel s'arrête à 25s même si voix plus courte

# Hey Comic = police kid-friendly demandée
FONT_HEY = "C\\:/Users/33612/AppData/Local/Microsoft/Windows/Fonts/Hey Comic.ttf"
FONT = FONT_HEY  # alias pour les overlays
MUSIC = Path("c:/Users/33612/Documents/site_COCOtheaxolotl/coherence/bgm.mp3")
SITE_URL = "www.cocotheaxolotl.org"


@dataclass
class Short:
    slug: str
    source_video: Path           # ex: loutres_assemble.mp4
    narration: str               # texte parlé full
    hook_text: str               # 0-3s overlay
    info1_text: str              # 3-10s overlay
    info2_text: str              # 10-20s overlay
    info3_text: str              # 20-27s overlay
    cta_text: str                # 27-30s : "Suivant : ... →"
    voice: str = "en-US-JennyNeural"
    rate: str = "-18%"


def esc(t: str) -> str:
    return (t.replace("\\", "\\\\")
             .replace("'", "")
             .replace(":", "\\:")
             .replace(",", "\\,"))


def drawtext_overlay(text: str, t_start: float, t_end: float,
                     y_pct: float = 0.10, fontsize: int = 56,
                     panel_color: str = "0xFFE9F2", text_color: str = "0x2C1845") -> str:
    """Build a drawtext filter expression that shows text only between t_start and t_end."""
    return (
        f"drawtext=fontfile='{FONT}':"
        f"text='{esc(text)}':"
        f"fontsize={fontsize}:fontcolor={text_color}:"
        f"x=(w-text_w)/2:y=h*{y_pct}:"
        f"box=1:boxcolor={panel_color}@0.85:boxborderw=24:"
        f"enable='between(t,{t_start},{t_end})'"
    )


async def gen_voice(text: str, voice: str, rate: str, out_path: Path) -> Path:
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(str(out_path))
    return out_path


def get_dur(p: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(p)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def build_short(spec: Short) -> Path:
    print(f"\n=== Building short : {spec.slug} ===")

    # 1. Voice
    print("[1/4] Voice (Edge TTS)")
    voice_path = WORK / f"{spec.slug}_voice.mp3"
    asyncio.run(gen_voice(spec.narration, spec.voice, spec.rate, voice_path))
    voice_dur = get_dur(voice_path)
    print(f"      voice = {voice_dur:.1f}s")

    # 2. Trim/extend source video to TARGET_DUR
    src_dur = get_dur(spec.source_video)
    print(f"[2/4] Source video : {src_dur:.1f}s -> target {TARGET_DUR:.0f}s")

    # Copy source with clean filename (no spaces) to avoid ffmpeg path issues
    clean_src = WORK / f"{spec.slug}_src.mp4"
    shutil.copy(spec.source_video, clean_src)

    # If source longer than target, trim. If shorter, freeze last frame.
    base_norm = WORK / f"{spec.slug}_base.mp4"
    if src_dur >= TARGET_DUR:
        # trim + scale to vertical 9:16
        cmd = ["ffmpeg", "-y", "-i", str(clean_src),
               "-t", str(TARGET_DUR),
               "-vf", f"scale=w={VIDEO_W}:h={VIDEO_H}:force_original_aspect_ratio=increase,"
                      f"crop={VIDEO_W}:{VIDEO_H}",
               "-r", str(FPS), "-an",
               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
               str(base_norm)]
    else:
        # Loop or pad — for now we tpad (extend last frame)
        pad_dur = TARGET_DUR - src_dur
        cmd = ["ffmpeg", "-y", "-i", str(clean_src),
               "-vf", f"scale=w={VIDEO_W}:h={VIDEO_H}:force_original_aspect_ratio=increase,"
                      f"crop={VIDEO_W}:{VIDEO_H},"
                      f"tpad=stop_mode=clone:stop_duration={pad_dur}",
               "-r", str(FPS), "-an",
               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
               str(base_norm)]
    subprocess.run(cmd, check=True, capture_output=True)

    # 3. Text overlays — bandes recalibrées pour 25s + URL footer permanent
    # 0-3 hook | 3-9 info1 | 9-17 info2 | 17-22 info3 | 22-25 CTA | 0-25 URL footer
    print("[3/4] Text overlays + URL footer")
    overlays = [
        drawtext_overlay(spec.hook_text,   0.0,  3.0, y_pct=0.10, fontsize=72,
                         panel_color="0xFFE9F2", text_color="0xC23B7E"),
        drawtext_overlay(spec.info1_text,  3.0,  9.0, y_pct=0.10, fontsize=58),
        drawtext_overlay(spec.info2_text,  9.0, 17.0, y_pct=0.10, fontsize=58),
        drawtext_overlay(spec.info3_text, 17.0, 22.0, y_pct=0.10, fontsize=58),
        drawtext_overlay(spec.cta_text,   22.0, 25.0, y_pct=0.78, fontsize=54,
                         panel_color="0x2C1845", text_color="0xFFFFFF"),
        # URL footer permanent (toute la durée)
        drawtext_overlay(SITE_URL,         0.0, 25.0, y_pct=0.94, fontsize=42,
                         panel_color="0xFFFFFF", text_color="0xC23B7E"),
    ]
    vf = ",".join(overlays)

    overlaid = WORK / f"{spec.slug}_overlaid.mp4"
    cmd = ["ffmpeg", "-y", "-i", str(base_norm), "-vf", vf,
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-r", str(FPS),
           "-an", str(overlaid)]
    subprocess.run(cmd, check=True, capture_output=True)

    # 4. Mix voice + bgm music
    print("[4/4] Mix audio")
    final = OUT / f"{spec.slug}_short_v3.mp4"
    # On force la sortie à TARGET_DUR (25s) — voix paddée avec silence si plus courte
    if MUSIC.exists():
        cmd = [
            "ffmpeg", "-y",
            "-i", str(overlaid),
            "-i", str(voice_path),
            "-i", str(MUSIC),
            "-filter_complex",
            f"[1:a]volume=1.4,apad=whole_dur={TARGET_DUR}[voice];"
            f"[2:a]volume=0.18,aloop=loop=-1:size=2e9,atrim=0:{TARGET_DUR}[music];"
            "[voice][music]amix=inputs=2:duration=longest:dropout_transition=2[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-t", str(TARGET_DUR),
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            str(final),
        ]
    else:
        cmd = ["ffmpeg", "-y", "-i", str(overlaid), "-i", str(voice_path),
               "-filter_complex", f"[1:a]apad=whole_dur={TARGET_DUR}[a]",
               "-map", "0:v", "-map", "[a]",
               "-t", str(TARGET_DUR),
               "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", str(final)]
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"\n[DONE] {final}")
    return final


# ============== APPLICATION : Loutres ==============

LOUTRES = Short(
    slug="loutres",
    source_video=SLEEP_DIR / "loutres_assemble.mp4",
    narration=(
        "Sea otters hold hands while they sleep. "
        "Why? So they dont drift apart in the ocean current. "
        "They sometimes wrap themselves in seaweed for the same reason. "
        "Feeling safe is the secret to good sleep. "
        "Coco understood: just like cuddling a plushie."
    ),
    hook_text="Otters hold hands to sleep.",
    info1_text="So they dont drift apart at sea.",
    info2_text="They wrap up in seaweed too.",
    info3_text="Feeling safe = better sleep.",
    cta_text="Next : the koala sleeps 22h a day -->",
)


if __name__ == "__main__":
    build_short(LOUTRES)
    import os
    os.startfile(str(OUT / "loutres_short_v3.mp4"))
