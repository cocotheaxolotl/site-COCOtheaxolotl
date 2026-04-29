"""Mockup Short A1 — 'Axolotls can't close their eyes' — kids-friendly version.

Tout reste dans l'univers du livre : la couverture sert de fond pour toutes
les scènes, avec différents zooms (yeux de Coco / animaux endormis / vue large).
Pas de fond noir : c'est pour des enfants et des parents qui achètent un livre
pour enfants — l'esthétique doit rester douce.
"""
import asyncio
import shutil
import subprocess
from pathlib import Path
import edge_tts

ROOT = Path(__file__).resolve().parent
LIVRES = ROOT.parent / "LIVRES COCO"
SLEEP_BOOK = LIVRES / "Coco Can't Sleep Tonight!"
IMAGES = SLEEP_BOOK / "images des livres"
OUT = ROOT / "output" / "mockups"
OUT.mkdir(parents=True, exist_ok=True)

VIDEO_W, VIDEO_H = 1080, 1920
FPS = 30

# ---- Copy source images to clean filenames (no spaces/accents in FFmpeg paths) ----
ASSETS = OUT / "assets"
ASSETS.mkdir(exist_ok=True)
SRC_COVER = IMAGES / "couverture en FR coco ne dort pas ce soir.jpg"
COVER = ASSETS / "cover.jpg"
shutil.copy(SRC_COVER, COVER)

# ---- Voice over ----
VOICE_TEXT = (
    "Axolotls can't close their eyes. They have no eyelids. "
    "They sleep with their eyes wide open. "
    "So I wrote a children's book about a little axolotl who can't fall asleep. "
    "Coco the Axolotl. Find it on Amazon."
)
VOICE_FILE = OUT / "voice.mp3"


async def gen_voice():
    print("[1/4] Génération voix Edge TTS")
    communicate = edge_tts.Communicate(VOICE_TEXT, "en-US-JennyNeural", rate="-18%")
    await communicate.save(str(VOICE_FILE))


asyncio.run(gen_voice())

out = subprocess.run(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration",
     "-of", "default=noprint_wrappers=1:nokey=1", str(VOICE_FILE)],
    capture_output=True, text=True, check=True,
)
voice_dur = float(out.stdout.strip())
print(f"      voix = {voice_dur:.1f}s")


# ---- Helpers ----
FONT = None
for f in ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf"]:
    if Path(f).exists():
        FONT = f.replace("C:/", "C\\:/")
        break


def esc(t):
    return (t.replace("\\", "\\\\")
             .replace("'", "")
             .replace(":", "\\:")
             .replace(",", "\\,"))


def cover_clip(text: str, dur: float, out_path: Path,
               crop_focus: str = "full",
               text_pos: str = "top",
               fontsize: int = 60) -> Path:
    """Render a clip from the book cover with a specific zoom focus + soft pink text panel.

    crop_focus :
      - 'full' = vue entière de la couverture
      - 'eyes' = zoom sur les yeux grands ouverts de Coco (centre haut)
      - 'sleeping' = zoom sur les animaux qui dorment (haut-droite : koala+hibou)
      - 'dolphin' = zoom sur le dauphin endormi (gauche-milieu)

    text_pos : 'top' | 'bottom' — emplacement du panneau texte
    """
    # ImageMagick-ish ken-burns by ffmpeg's zoompan, anchored on the focus point.
    # Source image is portrait ~514x768. Scale up first, then crop+zoom around point.
    # We'll first scale the source to a much bigger canvas, then animate a zoom.
    base_scale_w = 2160  # 2x final width
    base_scale_h = 3072  # ~9:16 of base_scale_w * (768/514) but we crop later

    # Focus offsets (fraction of scaled image)
    focus_map = {
        "full":     {"zoom_start": 1.00, "zoom_end": 1.06, "x": "(iw-iw/zoom)/2", "y": "(ih-ih/zoom)/2"},
        "eyes":     {"zoom_start": 1.50, "zoom_end": 1.40, "x": "iw*0.50-(iw/zoom)/2",  "y": "ih*0.40-(ih/zoom)/2"},
        "sleeping": {"zoom_start": 1.55, "zoom_end": 1.45, "x": "iw*0.78-(iw/zoom)/2", "y": "ih*0.27-(ih/zoom)/2"},
        "dolphin":  {"zoom_start": 1.60, "zoom_end": 1.45, "x": "iw*0.18-(iw/zoom)/2", "y": "ih*0.50-(ih/zoom)/2"},
    }
    f = focus_map[crop_focus]
    total_frames = int(dur * FPS)
    zoom_expr = f"if(lte(on,1),{f['zoom_start']},max({f['zoom_end']},zoom-{(f['zoom_start']-f['zoom_end'])/total_frames:.6f}))"
    if f["zoom_start"] < f["zoom_end"]:
        zoom_expr = f"min({f['zoom_end']},zoom+{(f['zoom_end']-f['zoom_start'])/total_frames:.6f})"

    # Pre-scale the input to a large canvas so zoom doesn't pixelate
    pre = (
        f"scale=w={base_scale_w}:h={base_scale_h}:force_original_aspect_ratio=increase,"
        f"crop={base_scale_w}:{base_scale_h}"
    )
    zp = (
        f"zoompan=z='{zoom_expr}':"
        f"x='{f['x']}':y='{f['y']}':"
        f"d={total_frames}:s={VIDEO_W}x{VIDEO_H}:fps={FPS}"
    )

    # Soft pink text panel (semi-transparent), Comic-style font, multiline-friendly
    # Use boxed text for readability over busy illustration
    if text_pos == "top":
        y_expr = "h*0.06"
    elif text_pos == "bottom":
        y_expr = "h*0.78"
    else:  # center
        y_expr = "(h-text_h)/2"

    # Box background = soft creamy pink with low alpha; text = deep navy for contrast on pastel
    drawtext = (
        f"drawtext=fontfile='{FONT}':"
        f"text='{esc(text)}':"
        f"fontsize={fontsize}:"
        f"fontcolor=0x2C1845:"  # deep night-purple — readable on pastel
        f"x=(w-text_w)/2:y={y_expr}:"
        f"box=1:boxcolor=0xFFE9F2@0.86:"  # soft pink panel
        f"boxborderw=28"
    )

    vf = f"{pre},{zp},{drawtext},format=yuv420p"
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", str(COVER),
        "-t", str(dur), "-vf", vf, "-r", str(FPS),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
        str(out_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return out_path


# ---- Build scenes (all from book cover, different zooms) ----
print("[2/4] Création des scènes (toutes sur couverture livre, zooms différents)")

# Scene 1 — hook : zoom sur les yeux grands ouverts de Coco
s1 = cover_clip("Axolotls can't close their eyes.", 3.5,
                OUT / "s1.mp4", crop_focus="eyes", text_pos="bottom", fontsize=58)
print("  [ok] scene 1 - eyes zoom")

# Scene 2 — fait : zoom sur le koala/hibou endormis (les autres dorment, Coco non)
s2 = cover_clip("They have no eyelids.", 3.5,
                OUT / "s2.mp4", crop_focus="sleeping", text_pos="bottom", fontsize=64)
print("  [ok] scene 2 - sleeping animals zoom")

# Scene 3 — révélation : zoom sur le dauphin qui dort (un seul oeil fermé)
s3 = cover_clip("They sleep with eyes wide open.", 4.0,
                OUT / "s3.mp4", crop_focus="dolphin", text_pos="top", fontsize=58)
print("  [ok] scene 3 - dolphin zoom")

# Scene 4 — vue large couverture entière (le livre apparaît)
s4 = cover_clip("So I wrote a book about it.", 6.5,
                OUT / "s4.mp4", crop_focus="full", text_pos="top", fontsize=58)
print("  [ok] scene 4 - full cover reveal")

# Scene 5 — CTA, vue large + texte action
remaining = max(4.0, voice_dur - (3.5 + 3.5 + 4.0 + 6.5) + 1.0)
s5 = cover_clip("Coco the Axolotl on Amazon", remaining,
                OUT / "s5.mp4", crop_focus="full", text_pos="bottom", fontsize=56)
print(f"  [ok] scene 5 - CTA ({remaining:.1f}s)")


# ---- Concat ----
print("[3/4] Concaténation")
list_file = OUT / "concat.txt"
list_file.write_text(
    "\n".join(f"file '{c.as_posix()}'" for c in [s1, s2, s3, s4, s5]),
    encoding="utf-8",
)
silent = OUT / "silent.mp4"
subprocess.run(
    ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
     "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", str(silent)],
    check=True, capture_output=True,
)


# ---- Mix voice + music ----
print("[4/4] Mix voix + musique")
MUSIC = Path("c:/Users/33612/Documents/site_COCOtheaxolotl/coherence/bgm.mp3")
final = OUT / "A1_no_eyelids_v5.mp4"

if MUSIC.exists():
    cmd = [
        "ffmpeg", "-y",
        "-i", str(silent),
        "-i", str(VOICE_FILE),
        "-i", str(MUSIC),
        "-filter_complex",
        "[1:a]volume=1.4[voice];"
        "[2:a]volume=0.18,aloop=loop=-1:size=2e9[music];"
        "[voice][music]amix=inputs=2:duration=first:dropout_transition=2[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
        str(final),
    ]
else:
    cmd = ["ffmpeg", "-y", "-i", str(silent), "-i", str(VOICE_FILE),
           "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(final)]

subprocess.run(cmd, check=True, capture_output=True)
print(f"\n[DONE] -> {final}")
