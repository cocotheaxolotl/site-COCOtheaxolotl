"""
Generate French narration audio for "Je t'aime encore plus !"
Uses Edge TTS with the same voices as sleep-book (Coco / Maman / Narrator).

NOTE: "axolotl" → "axolote" for better French TTS pronunciation.
"""
import asyncio, os, tempfile, edge_tts
from pydub import AudioSegment

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio")

# Same voice casting as sleep-book
VOICES = {
    "NARRATOR": ("fr-FR-DeniseNeural", "-18%", 0),
    "COCO":     ("fr-FR-EloiseNeural", "-12%", 0),
    "MOM":      ("fr-FR-DeniseNeural", "-20%", -4),
    "TITLE":    ("fr-FR-DeniseNeural", "-25%", 0),
}

SHORT_PAUSE = 500
MEDIUM_PAUSE = 1000
LONG_PAUSE = 1600

# Page index (0-based) → list of (tag, text, pause_ms)
# Pages are numbered as displayed: slide_01 = page 0, slide_29 = page 28
PAGES = {
    0: [  # slide_01 cover
        ("TITLE", "Je t'aime encore plus !", LONG_PAUSE),
        ("NARRATOR", "Une aventure de Coco l'axolote.", 0),
    ],
    1: [  # slide_02 title page
        ("NARRATOR", "Je t'aime encore plus. Par Docteur Anita Nirvéna.", 0),
    ],
    2: [  # slide_03 Cher parent — skip (adult note)
    ],
    3: [  # slide_04 dédicace
        ("NARRATOR", "Pour chaque petit cœur qui aime sans mesure, et chaque maman qui l'aime davantage.", 0),
    ],
    4: [  # slide_05 TOC — silent
    ],
    5: [  # slide_06
        ("NARRATOR", "Chaque nuit, Maman bordait Coco, juste comme il faut.", MEDIUM_PAUSE),
        ("NARRATOR", "Ni trop serré. Ni trop lâche.", SHORT_PAUSE),
        ("NARRATOR", "Juste comme il faut.", 0),
    ],
    6: [  # slide_07
        ("NARRATOR", "Coco leva les yeux et dit :", SHORT_PAUSE),
        ("COCO",     "Je t'aime, Maman.", MEDIUM_PAUSE),
        ("NARRATOR", "Maman sourit :", SHORT_PAUSE),
        ("MOM",      "Je t'aime encore plus !", 0),
    ],
    7: [  # slide_08
        ("NARRATOR", "Coco y pensa.", MEDIUM_PAUSE),
        ("COCO",     "Encore plus ? Combien encore plus ?", 0),
    ],
    8: [  # slide_09
        ("NARRATOR", "Le lendemain matin, Coco serra Maman dans ses bras.", MEDIUM_PAUSE),
        ("COCO",     "Je t'aime aussi grand que mon câlin !", 0),
    ],
    9: [  # slide_10
        ("NARRATOR", "Maman rendit l'étreinte, encore plus fort.", MEDIUM_PAUSE),
        ("MOM",      "Je t'aime encore plus que ça !", 0),
    ],
    10: [  # slide_11
        ("NARRATOR", "Au parc, Coco étendit les bras aussi larges qu'ils pouvaient l'être.", MEDIUM_PAUSE),
        ("COCO",     "Je t'aime autant !", 0),
    ],
    11: [  # slide_12
        ("NARRATOR", "Maman étendit ses bras plus largement. Beaucoup, beaucoup plus largement.", MEDIUM_PAUSE),
        ("MOM",      "Je t'aime encore plus !", 0),
    ],
    12: [  # slide_13
        ("NARRATOR", "Cette nuit-là, Coco pointa vers le ciel.", MEDIUM_PAUSE),
        ("COCO",     "Je t'aime jusqu'aux étoiles !", 0),
    ],
    13: [  # slide_14
        ("NARRATOR", "Maman pointa au-delà des étoiles. Au-delà de la lune. Au-delà de tout.", MEDIUM_PAUSE),
        ("MOM",      "Je t'aime plus que tout ça.", 0),
    ],
    14: [  # slide_15
        ("NARRATOR", "Coco resta silencieux un moment.", MEDIUM_PAUSE),
        ("COCO",     "Comment peux-tu toujours m'aimer plus ?", 0),
    ],
    15: [  # slide_16
        ("NARRATOR", "Maman s'assit. Prit Coco dans ses bras.", MEDIUM_PAUSE),
        ("NARRATOR", "Et ne dit rien pendant un long moment.", 0),
    ],
    16: [  # slide_17
        ("MOM",      "Parce qu'avant que tu ne sois né, je t'aimais déjà.", 0),
    ],
    17: [  # slide_18
        ("MOM",      "Avant ton premier sourire.", SHORT_PAUSE),
        ("MOM",      "Avant ton premier mot.", SHORT_PAUSE),
        ("MOM",      "Avant ton premier câlin.", MEDIUM_PAUSE),
        ("MOM",      "Mon amour n'a pas commencé quand tu es arrivé.", MEDIUM_PAUSE),
        ("MOM",      "Mon amour a commencé bien avant.", 0),
    ],
    18: [  # slide_19
        ("MOM",      "Donc peu importe combien tu m'aimes...", MEDIUM_PAUSE),
        ("MOM",      "je t'aimerai toujours en premier.", MEDIUM_PAUSE),
        ("MOM",      "Et je t'aimerai toujours plus.", 0),
    ],
    19: [  # slide_20
        ("NARRATOR", "Coco y pensa longtemps.", MEDIUM_PAUSE),
        ("NARRATOR", "Un très long moment.", 0),
    ],
    20: [  # slide_21
        ("NARRATOR", "Le lendemain matin, Coco sourit. Le plus grand des sourires.", 0),
    ],
    21: [  # slide_22
        ("COCO",     "Eh bien alors...", MEDIUM_PAUSE),
        ("COCO",     "...je t'aime encore plus plus, Maman !", 0),
    ],
    22: [  # slide_23
        ("NARRATOR", "Maman rit aux éclats.", MEDIUM_PAUSE),
        ("MOM",      "D'accord. Tu gagnes !", 0),
    ],
    23: [  # slide_24
        ("NARRATOR", "Et ils s'embrassèrent.", MEDIUM_PAUSE),
        ("NARRATOR", "Personne ne perd quand l'amour est le jeu.", 0),
    ],
    24: [  # slide_25 back matter
        ("NARRATOR", "Combien Maman t'aime ?", MEDIUM_PAUSE),
        ("NARRATOR", "Plus que tous les câlins.", SHORT_PAUSE),
        ("NARRATOR", "Plus que les étoiles.", SHORT_PAUSE),
        ("NARRATOR", "Plus que tout.", MEDIUM_PAUSE),
        ("NARRATOR", "Maman t'aime avant même que tu connaisses ton nom.", 0),
    ],
    25: [  # slide_26
        ("NARRATOR", "Bravo ! Tu as lu tout le livre !", 0),
    ],
    26: [  # slide_27
        ("NARRATOR", "Retrouve le monde de Coco sur cocotheaxolotl.org", 0),
    ],
    27: [  # slide_28
        ("NARRATOR", "Dessine ton plus beau cœur !", 0),
    ],
    28: [  # slide_29
        ("NARRATOR", "À bientôt ! Coco.", 0),
    ],
}


async def generate_segment(text, voice, rate):
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        await communicate.save(tmp_path)
        return AudioSegment.from_mp3(tmp_path)
    finally:
        try: os.unlink(tmp_path)
        except OSError: pass


async def generate_page(idx, segments):
    combined = AudioSegment.empty()
    if not segments:
        # Silent page (0.5s)
        combined = AudioSegment.silent(duration=500)
    else:
        for tag, text, pause_after in segments:
            voice, rate, vol_db = VOICES[tag]
            print(f"  [{tag}] {text[:60]}")
            seg = await generate_segment(text, voice, rate)
            if vol_db != 0:
                seg = seg + vol_db
            # Trim trailing silence
            chunk_ms = 50
            end = len(seg)
            while end > chunk_ms:
                chunk = seg[end - chunk_ms:end]
                if chunk.dBFS > -45:
                    break
                end -= chunk_ms
            if end < len(seg):
                seg = seg[:end + 100]
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

    print("\n===== DURATIONS (paste into read/index.html) =====")
    print("var durations = [" + ", ".join(f"{d:.2f}" for d in durations) + "];")


if __name__ == "__main__":
    asyncio.run(main())
