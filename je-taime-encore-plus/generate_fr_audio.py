"""
Generate emotional French narration for "Je t'aime encore plus !"
Uses Edge TTS (native French voices) with per-segment emotion modulation
via pitch/rate/volume.
"""
import asyncio, os, tempfile, edge_tts
from pydub import AudioSegment

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio")

# ===== VOICE BASES (rate %, pitch Hz, vol dB) =====
# Same voices as sleep-book: native French, no accent.
VOICES = {
    "NARRATOR": ("fr-FR-DeniseNeural",  -18, 0,    0),
    "COCO":     ("fr-FR-EloiseNeural",  -12, 0,    0),
    "MOM":      ("fr-FR-DeniseNeural",  -20, -2,  -4),
    "TITLE":    ("fr-FR-DeniseNeural",  -25, -2,   0),
}

# ===== EMOTIONS (delta on top of voice base: rate %, pitch Hz) =====
EMOTIONS = {
    "neutral":     (0,   0),
    "love":        (-8, -10),   # tender, soft, slower
    "joy":         (+10, +20),   # fast, high, bubbly
    "wonder":      (-4, +15),   # slower, higher (dreamy)
    "playful":     (+6, +18),   # cheeky, up
    "thoughtful":  (-10, -8),   # slower, slightly lower (pensive)
    "triumph":     (+10, +25),  # excited peak
    "tender":      (-12, -6),   # soft maman speaking
    "whisper":     (-8, -4),    # quiet
    "declarative": (-4, 0),     # serious, measured
}

SHORT_PAUSE = 500
MEDIUM_PAUSE = 1000
LONG_PAUSE = 1600

# (tag, text, emotion, pause_ms)
PAGES = {
    0: [
        ("TITLE", "Je t'aime encore plus !", "wonder", LONG_PAUSE),
        ("NARRATOR", "Une aventure de Coco l'axolote.", "neutral", 0),
    ],
    1: [
        ("NARRATOR", "Je t'aime encore plus. Par Docteur Anita Nirvéna.", "neutral", 0),
    ],
    2: [],
    3: [
        ("NARRATOR", "Pour chaque petit cœur qui aime sans mesure, et chaque maman qui l'aime davantage.", "love", 0),
    ],
    4: [],
    5: [
        ("NARRATOR", "Chaque nuit, Maman bordait Coco, juste comme il faut.", "tender", MEDIUM_PAUSE),
        ("NARRATOR", "Ni trop serré. Ni trop lâche.", "tender", SHORT_PAUSE),
        ("NARRATOR", "Juste comme il faut.", "tender", 0),
    ],
    6: [
        ("NARRATOR", "Coco leva les yeux et dit :", "neutral", SHORT_PAUSE),
        ("COCO",     "Je t'aime, Maman.", "love", MEDIUM_PAUSE),
        ("NARRATOR", "Maman sourit :", "tender", SHORT_PAUSE),
        ("MOM",      "Je t'aime encore plus !", "joy", 0),
    ],
    7: [
        ("NARRATOR", "Coco y pensa.", "thoughtful", MEDIUM_PAUSE),
        ("COCO",     "Encore plus ? Combien encore plus ?", "wonder", 0),
    ],
    8: [
        ("NARRATOR", "Le lendemain matin, Coco serra Maman dans ses bras.", "joy", MEDIUM_PAUSE),
        ("COCO",     "Je t'aime aussi grand que mon câlin !", "joy", 0),
    ],
    9: [
        ("NARRATOR", "Maman rendit l'étreinte, encore plus fort.", "joy", MEDIUM_PAUSE),
        ("MOM",      "Je t'aime encore plus que ça !", "joy", 0),
    ],
    10: [
        ("NARRATOR", "Au parc, Coco étendit les bras aussi larges qu'ils pouvaient l'être.", "playful", MEDIUM_PAUSE),
        ("COCO",     "Je t'aime autant !", "joy", 0),
    ],
    11: [
        ("NARRATOR", "Maman étendit ses bras plus largement. Beaucoup, beaucoup plus largement.", "playful", MEDIUM_PAUSE),
        ("MOM",      "Je t'aime encore plus !", "triumph", 0),
    ],
    12: [
        ("NARRATOR", "Cette nuit-là, Coco pointa vers le ciel.", "wonder", MEDIUM_PAUSE),
        ("COCO",     "Je t'aime jusqu'aux étoiles !", "wonder", 0),
    ],
    13: [
        ("NARRATOR", "Maman pointa au-delà des étoiles. Au-delà de la lune. Au-delà de tout.", "wonder", MEDIUM_PAUSE),
        ("MOM",      "Je t'aime plus que tout ça.", "love", 0),
    ],
    14: [
        ("NARRATOR", "Coco resta silencieux un moment.", "thoughtful", MEDIUM_PAUSE),
        ("COCO",     "Comment peux-tu toujours m'aimer plus ?", "wonder", 0),
    ],
    15: [
        ("NARRATOR", "Maman s'assit. Prit Coco dans ses bras.", "tender", MEDIUM_PAUSE),
        ("NARRATOR", "Et ne dit rien pendant un long moment.", "tender", 0),
    ],
    16: [
        ("MOM",      "Parce qu'avant que tu ne sois né, je t'aimais déjà.", "love", 0),
    ],
    17: [
        ("MOM",      "Avant ton premier sourire.", "love", SHORT_PAUSE),
        ("MOM",      "Avant ton premier mot.", "love", SHORT_PAUSE),
        ("MOM",      "Avant ton premier câlin.", "love", MEDIUM_PAUSE),
        ("MOM",      "Mon amour n'a pas commencé quand tu es arrivé.", "declarative", MEDIUM_PAUSE),
        ("MOM",      "Mon amour a commencé bien avant.", "love", 0),
    ],
    18: [
        ("MOM",      "Donc peu importe combien tu m'aimes...", "tender", MEDIUM_PAUSE),
        ("MOM",      "je t'aimerai toujours en premier.", "love", MEDIUM_PAUSE),
        ("MOM",      "Et je t'aimerai toujours plus.", "love", 0),
    ],
    19: [
        ("NARRATOR", "Coco y pensa longtemps.", "thoughtful", MEDIUM_PAUSE),
        ("NARRATOR", "Un très long moment.", "thoughtful", 0),
    ],
    20: [
        ("NARRATOR", "Le lendemain matin, Coco sourit. Le plus grand des sourires.", "joy", 0),
    ],
    21: [
        ("COCO",     "Eh bien alors...", "playful", MEDIUM_PAUSE),
        ("COCO",     "...je t'aime encore plus plus, Maman !", "triumph", 0),
    ],
    22: [
        ("NARRATOR", "Maman rit aux éclats.", "joy", MEDIUM_PAUSE),
        ("MOM",      "D'accord. Tu gagnes !", "joy", 0),
    ],
    23: [
        ("NARRATOR", "Et ils s'embrassèrent.", "love", MEDIUM_PAUSE),
        ("NARRATOR", "Personne ne perd quand l'amour est le jeu.", "tender", 0),
    ],
    24: [
        ("NARRATOR", "Combien Maman t'aime ?", "wonder", MEDIUM_PAUSE),
        ("NARRATOR", "Plus que tous les câlins.", "love", SHORT_PAUSE),
        ("NARRATOR", "Plus que les étoiles.", "wonder", SHORT_PAUSE),
        ("NARRATOR", "Plus que tout.", "love", MEDIUM_PAUSE),
        ("NARRATOR", "Maman t'aime avant même que tu connaisses ton nom.", "love", 0),
    ],
    25: [
        ("NARRATOR", "Bravo ! Tu as lu tout le livre !", "triumph", 0),
    ],
    26: [
        ("NARRATOR", "Retrouve le monde de Coco sur cocotheaxolotl.org", "joy", 0),
    ],
    27: [
        ("NARRATOR", "Dessine ton plus beau cœur !", "playful", 0),
    ],
    28: [
        ("NARRATOR", "À bientôt ! Coco.", "joy", 0),
    ],
}


def fmt_rate(pct):
    return f"{'+' if pct >= 0 else ''}{pct}%"


def fmt_pitch(hz):
    return f"{'+' if hz >= 0 else ''}{hz}Hz"


async def generate_segment(text, tag, emotion):
    voice, rate_base, pitch_base, vol_db = VOICES[tag]
    rate_delta, pitch_delta = EMOTIONS[emotion]
    rate = fmt_rate(rate_base + rate_delta)
    pitch = fmt_pitch(pitch_base + pitch_delta)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        c = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        await c.save(tmp_path)
        seg = AudioSegment.from_mp3(tmp_path)
        if vol_db != 0:
            seg = seg + vol_db
        return seg
    finally:
        try: os.unlink(tmp_path)
        except OSError: pass


def trim_silence(seg, silence_thresh=-45, chunk_ms=50):
    end = len(seg)
    while end > chunk_ms:
        if seg[end - chunk_ms:end].dBFS > silence_thresh:
            break
        end -= chunk_ms
    return seg[:end + 100] if end < len(seg) else seg


async def generate_page(idx, segments):
    if not segments:
        combined = AudioSegment.silent(duration=500)
    else:
        combined = AudioSegment.empty()
        for tag, text, emotion, pause_after in segments:
            print(f"  [{tag}/{emotion}] {text[:60]}")
            seg = await generate_segment(text, tag, emotion)
            seg = trim_silence(seg)
            combined += seg
            if pause_after > 0:
                combined += AudioSegment.silent(duration=pause_after)

    out = os.path.join(OUTPUT_DIR, f"page_{idx:02d}.mp3")
    combined.export(out, format="mp3", bitrate="128k")
    dur = len(combined) / 1000
    print(f"  -> page_{idx:02d}.mp3 ({dur:.2f}s)")
    return dur


async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    durations = []
    for i in range(29):
        print(f"=== page {i} (slide_{i+1:02d}) ===")
        dur = await generate_page(i, PAGES.get(i, []))
        durations.append(dur)

    print("\n===== DURATIONS =====")
    print("var durations = [" + ", ".join(f"{d:.2f}" for d in durations) + "];")


if __name__ == "__main__":
    asyncio.run(main())
