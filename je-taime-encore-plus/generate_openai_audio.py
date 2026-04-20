"""
Generate emotional French narration for "Je t'aime encore plus !"
using OpenAI's gpt-4o-mini-tts with per-character emotional instructions.
"""
import os, asyncio
from pathlib import Path
from openai import AsyncOpenAI
from pydub import AudioSegment
import io

# Load API key from LIVRES COCO/.env
ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT.parent / "LIVRES COCO" / ".env"
for line in ENV_FILE.read_text().splitlines():
    if line.startswith("OPENAI_API_KEY="):
        os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1].strip()
        break

OUTPUT_DIR = ROOT / "audio"
OUTPUT_DIR.mkdir(exist_ok=True)

client = AsyncOpenAI()

# ===== VOICE CASTING =====
# OpenAI gpt-4o-mini-tts voices: alloy, ash, ballad, coral, echo, fable, onyx, nova, sage, shimmer, verse
VOICES = {
    "NARRATOR": {
        "voice": "shimmer",
        "instructions": (
            "Speak in French with the warm, gentle tone of a bedtime storyteller. "
            "Soft, cozy, tender. Slow pace. Like reading to a sleepy child at night. "
            "Voice should feel like a warm blanket."
        ),
    },
    "COCO": {
        "voice": "nova",
        "instructions": (
            "Speak in French as a small, curious axolotl child — playful, innocent, "
            "full of wonder. High-pitched, sweet, excited, with childlike enthusiasm "
            "and a sprinkle of cheekiness. Sometimes thinking out loud."
        ),
    },
    "MOM": {
        "voice": "coral",
        "instructions": (
            "Speak in French as a loving, tender French mother talking to her little child. "
            "Warm, reassuring, soft. Full of love and affection. Slow, deep, sometimes "
            "playfully teasing, but always gentle. Like a hug in voice form."
        ),
    },
    "TITLE": {
        "voice": "shimmer",
        "instructions": (
            "Speak in French slowly and theatrically, like announcing the title of a "
            "magical bedtime storybook. Soft wonder, a touch of enchantment."
        ),
    },
}

SHORT_PAUSE = 500
MEDIUM_PAUSE = 1000
LONG_PAUSE = 1600

PAGES = {
    0: [
        ("TITLE", "Je t'aime encore plus !", LONG_PAUSE),
        ("NARRATOR", "Une aventure de Coco l'axolote.", 0),
    ],
    1: [
        ("NARRATOR", "Je t'aime encore plus. Par Docteur Anita Nirvéna.", 0),
    ],
    2: [],
    3: [
        ("NARRATOR", "Pour chaque petit cœur qui aime sans mesure, et chaque maman qui l'aime davantage.", 0),
    ],
    4: [],
    5: [
        ("NARRATOR", "Chaque nuit, Maman bordait Coco, juste comme il faut.", MEDIUM_PAUSE),
        ("NARRATOR", "Ni trop serré. Ni trop lâche.", SHORT_PAUSE),
        ("NARRATOR", "Juste comme il faut.", 0),
    ],
    6: [
        ("NARRATOR", "Coco leva les yeux et dit :", SHORT_PAUSE),
        ("COCO",     "Je t'aime, Maman.", MEDIUM_PAUSE),
        ("NARRATOR", "Maman sourit :", SHORT_PAUSE),
        ("MOM",      "Je t'aime encore plus !", 0),
    ],
    7: [
        ("NARRATOR", "Coco y pensa.", MEDIUM_PAUSE),
        ("COCO",     "Encore plus ? Combien encore plus ?", 0),
    ],
    8: [
        ("NARRATOR", "Le lendemain matin, Coco serra Maman dans ses bras.", MEDIUM_PAUSE),
        ("COCO",     "Je t'aime aussi grand que mon câlin !", 0),
    ],
    9: [
        ("NARRATOR", "Maman rendit l'étreinte, encore plus fort.", MEDIUM_PAUSE),
        ("MOM",      "Je t'aime encore plus que ça !", 0),
    ],
    10: [
        ("NARRATOR", "Au parc, Coco étendit les bras aussi larges qu'ils pouvaient l'être.", MEDIUM_PAUSE),
        ("COCO",     "Je t'aime autant !", 0),
    ],
    11: [
        ("NARRATOR", "Maman étendit ses bras plus largement. Beaucoup, beaucoup plus largement.", MEDIUM_PAUSE),
        ("MOM",      "Je t'aime encore plus !", 0),
    ],
    12: [
        ("NARRATOR", "Cette nuit-là, Coco pointa vers le ciel.", MEDIUM_PAUSE),
        ("COCO",     "Je t'aime jusqu'aux étoiles !", 0),
    ],
    13: [
        ("NARRATOR", "Maman pointa au-delà des étoiles. Au-delà de la lune. Au-delà de tout.", MEDIUM_PAUSE),
        ("MOM",      "Je t'aime plus que tout ça.", 0),
    ],
    14: [
        ("NARRATOR", "Coco resta silencieux un moment.", MEDIUM_PAUSE),
        ("COCO",     "Comment peux-tu toujours m'aimer plus ?", 0),
    ],
    15: [
        ("NARRATOR", "Maman s'assit. Prit Coco dans ses bras.", MEDIUM_PAUSE),
        ("NARRATOR", "Et ne dit rien pendant un long moment.", 0),
    ],
    16: [
        ("MOM",      "Parce qu'avant que tu ne sois né, je t'aimais déjà.", 0),
    ],
    17: [
        ("MOM",      "Avant ton premier sourire.", SHORT_PAUSE),
        ("MOM",      "Avant ton premier mot.", SHORT_PAUSE),
        ("MOM",      "Avant ton premier câlin.", MEDIUM_PAUSE),
        ("MOM",      "Mon amour n'a pas commencé quand tu es arrivé.", MEDIUM_PAUSE),
        ("MOM",      "Mon amour a commencé bien avant.", 0),
    ],
    18: [
        ("MOM",      "Donc peu importe combien tu m'aimes...", MEDIUM_PAUSE),
        ("MOM",      "je t'aimerai toujours en premier.", MEDIUM_PAUSE),
        ("MOM",      "Et je t'aimerai toujours plus.", 0),
    ],
    19: [
        ("NARRATOR", "Coco y pensa longtemps.", MEDIUM_PAUSE),
        ("NARRATOR", "Un très long moment.", 0),
    ],
    20: [
        ("NARRATOR", "Le lendemain matin, Coco sourit. Le plus grand des sourires.", 0),
    ],
    21: [
        ("COCO",     "Eh bien alors...", MEDIUM_PAUSE),
        ("COCO",     "...je t'aime encore plus plus, Maman !", 0),
    ],
    22: [
        ("NARRATOR", "Maman rit aux éclats.", MEDIUM_PAUSE),
        ("MOM",      "D'accord. Tu gagnes !", 0),
    ],
    23: [
        ("NARRATOR", "Et ils s'embrassèrent.", MEDIUM_PAUSE),
        ("NARRATOR", "Personne ne perd quand l'amour est le jeu.", 0),
    ],
    24: [
        ("NARRATOR", "Combien Maman t'aime ?", MEDIUM_PAUSE),
        ("NARRATOR", "Plus que tous les câlins.", SHORT_PAUSE),
        ("NARRATOR", "Plus que les étoiles.", SHORT_PAUSE),
        ("NARRATOR", "Plus que tout.", MEDIUM_PAUSE),
        ("NARRATOR", "Maman t'aime avant même que tu connaisses ton nom.", 0),
    ],
    25: [
        ("NARRATOR", "Bravo ! Tu as lu tout le livre !", 0),
    ],
    26: [
        ("NARRATOR", "Retrouve le monde de Coco sur cocotheaxolotl.org", 0),
    ],
    27: [
        ("NARRATOR", "Dessine ton plus beau cœur !", 0),
    ],
    28: [
        ("NARRATOR", "À bientôt ! Coco.", 0),
    ],
}


async def tts(text: str, tag: str) -> AudioSegment:
    cfg = VOICES[tag]
    resp = await client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice=cfg["voice"],
        input=text,
        instructions=cfg["instructions"],
        response_format="mp3",
    )
    return AudioSegment.from_file(io.BytesIO(resp.content), format="mp3")


def trim_silence(seg: AudioSegment, silence_thresh=-45, chunk_ms=50) -> AudioSegment:
    end = len(seg)
    while end > chunk_ms:
        if seg[end - chunk_ms:end].dBFS > silence_thresh:
            break
        end -= chunk_ms
    return seg[:end + 100] if end < len(seg) else seg


async def generate_page(idx: int, segments) -> float:
    if not segments:
        combined = AudioSegment.silent(duration=500)
    else:
        combined = AudioSegment.empty()
        for tag, text, pause_after in segments:
            print(f"  [{tag}] {text[:60]}")
            seg = await tts(text, tag)
            seg = trim_silence(seg)
            combined += seg
            if pause_after > 0:
                combined += AudioSegment.silent(duration=pause_after)

    out = OUTPUT_DIR / f"page_{idx:02d}.mp3"
    combined.export(out, format="mp3", bitrate="128k")
    dur = len(combined) / 1000
    print(f"  -> {out.name} ({dur:.2f}s)")
    return dur


async def main():
    durations = []
    for i in range(29):
        print(f"=== page {i} (slide_{i+1:02d}) ===")
        dur = await generate_page(i, PAGES.get(i, []))
        durations.append(dur)
    print("\n===== DURATIONS =====")
    print("var durations = [" + ", ".join(f"{d:.2f}" for d in durations) + "];")


if __name__ == "__main__":
    asyncio.run(main())
