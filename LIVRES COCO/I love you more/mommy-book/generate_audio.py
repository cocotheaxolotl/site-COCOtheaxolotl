"""
Generate English narration audio for "I Love You More, Mommy"
using Edge TTS with multiple voices. Same system as sleep book.
"""
import asyncio, os, tempfile, edge_tts
from pydub import AudioSegment

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio")

# ===== VOICE CASTING (same as sleep book EN) =====
# (voice_name, rate, volume_adjust_dB)
VOICES = {
    "NARRATOR": ("en-US-JennyNeural",  "-18%",  0),
    "COCO":     ("en-US-AnaNeural",    "-12%",  0),
    "MOMMY":    ("en-US-AriaNeural",   "-20%", -4),
    "TITLE":    ("en-US-JennyNeural",  "-25%",  0),
}

# Pause durations (ms)
SHORT_PAUSE  = 600
MEDIUM_PAUSE = 1200
LONG_PAUSE   = 1800

# ===== SPREADS =====
# Each spread = one page in the book (23 pages total = spreads 00-22)
# + spread_title (plays on cover entry) + spread_credits (plays at the end)
SPREADS = {

    "spread_title": [
        ("TITLE", "I Love You More, Mommy.", LONG_PAUSE),
        ("TITLE", "A Coco the Axolotl Adventure.", 0),
    ],

    # Page 0 — Cover
    "spread_00": [
        ("NARRATOR", "I Love You More, Mommy.", 0),
    ],

    # Page 1 — Copyright
    "spread_01": [
        ("NARRATOR", "A Coco the Axolotl Adventure.", MEDIUM_PAUSE),
        ("NARRATOR", "By Doctor Anita Nirvena. Illustrations by Loopinky.", 0),
    ],

    # Page 2 — Dedication
    "spread_02": [
        ("NARRATOR", "For every little heart that loves without measure...", MEDIUM_PAUSE),
        ("NARRATOR", "and every mama who loves you more.", 0),
    ],

    # Page 3 — Story page 1
    "spread_03": [
        ("NARRATOR", "Every night, Mommy tucked Coco in,", SHORT_PAUSE),
        ("NARRATOR", "just right.", MEDIUM_PAUSE),
        ("NARRATOR", "Not too tight.", SHORT_PAUSE),
        ("NARRATOR", "Not too loose.", SHORT_PAUSE),
        ("NARRATOR", "Just right.", 0),
    ],

    # Page 4 — Story page 2
    "spread_04": [
        ("NARRATOR", "Coco looked up and said:", MEDIUM_PAUSE),
        ("COCO",     "I love you, Mommy.", MEDIUM_PAUSE),
        ("NARRATOR", "Mommy smiled.", MEDIUM_PAUSE),
        ("MOMMY",    "I love you MORE.", 0),
    ],

    # Page 5 — Story page 3
    "spread_05": [
        ("NARRATOR", "Coco thought about this.", LONG_PAUSE),
        ("COCO",     "More?", MEDIUM_PAUSE),
        ("COCO",     "How much more?", 0),
    ],

    # Page 6 — Story page 4
    "spread_06": [
        ("NARRATOR", "The next morning, Coco hugged Mommy tight.", MEDIUM_PAUSE),
        ("COCO",     "I love you as big as my hug!", 0),
    ],

    # Page 7 — Story page 5
    "spread_07": [
        ("NARRATOR", "Mommy hugged back.", SHORT_PAUSE),
        ("NARRATOR", "Even tighter.", MEDIUM_PAUSE),
        ("MOMMY",    "I love you MORE than that.", 0),
    ],

    # Page 8 — Story page 6
    "spread_08": [
        ("NARRATOR", "At the park, Coco stretched arms out wide.", SHORT_PAUSE),
        ("NARRATOR", "As wide as they could go.", MEDIUM_PAUSE),
        ("COCO",     "I love you THIS much!", 0),
    ],

    # Page 9 — Story page 7
    "spread_09": [
        ("NARRATOR", "Mommy stretched her arms out wider.", SHORT_PAUSE),
        ("NARRATOR", "Much, much wider.", MEDIUM_PAUSE),
        ("MOMMY",    "I love you MORE than that.", 0),
    ],

    # Page 10 — Story page 8
    "spread_10": [
        ("NARRATOR", "That night, Coco pointed to the sky.", MEDIUM_PAUSE),
        ("COCO",     "I love you all the way to the stars!", 0),
    ],

    # Page 11 — Story page 9
    "spread_11": [
        ("NARRATOR", "Mommy pointed past the stars.", SHORT_PAUSE),
        ("NARRATOR", "Past the moon.", SHORT_PAUSE),
        ("NARRATOR", "Past everything.", MEDIUM_PAUSE),
        ("MOMMY",    "I love you MORE than all of that.", 0),
    ],

    # Page 12 — Story page 10
    "spread_12": [
        ("NARRATOR", "Coco was quiet for a moment.", LONG_PAUSE),
        ("COCO",     "How can you always love me more?", 0),
    ],

    # Page 13 — Story page 11
    "spread_13": [
        ("NARRATOR", "Mommy sat down.", MEDIUM_PAUSE),
        ("NARRATOR", "Pulled Coco close.", MEDIUM_PAUSE),
        ("NARRATOR", "And said nothing for a little while.", 0),
    ],

    # Page 14 — Story page 12
    "spread_14": [
        ("MOMMY", "Because before you were born...", LONG_PAUSE),
        ("MOMMY", "I already loved you.", 0),
    ],

    # Page 15 — Story page 13
    "spread_15": [
        ("NARRATOR", "Before your first smile.", MEDIUM_PAUSE),
        ("NARRATOR", "Before your first word.", MEDIUM_PAUSE),
        ("NARRATOR", "Before your first hug.", LONG_PAUSE),
        ("NARRATOR", "My love didn't start when I met you.", MEDIUM_PAUSE),
        ("NARRATOR", "It started before.", 0),
    ],

    # Page 16 — Story page 14
    "spread_16": [
        ("MOMMY", "So no matter how much you love me...", LONG_PAUSE),
        ("MOMMY", "I will always love you first.", MEDIUM_PAUSE),
        ("MOMMY", "And I will always love you more.", 0),
    ],

    # Page 17 — Story page 15
    "spread_17": [
        ("NARRATOR", "Coco thought about this for a long time.", MEDIUM_PAUSE),
        ("NARRATOR", "A very long time.", 0),
    ],

    # Page 18 — Story page 16
    "spread_18": [
        ("NARRATOR", "Then Coco smiled.", MEDIUM_PAUSE),
        ("NARRATOR", "The biggest smile.", 0),
    ],

    # Page 19 — Story page 17
    "spread_19": [
        ("COCO", "Well then...", LONG_PAUSE),
        ("COCO", "I love you MORE, Mommy!", 0),
    ],

    # Page 20 — Story page 18
    "spread_20": [
        ("NARRATOR", "Mommy laughed out loud.", MEDIUM_PAUSE),
        ("MOMMY",    "Okay.", MEDIUM_PAUSE),
        ("MOMMY",    "You win.", 0),
    ],

    # Page 21 — Story page 19
    "spread_21": [
        ("NARRATOR", "And they hugged.", LONG_PAUSE),
        ("NARRATOR", "Nobody loses...", MEDIUM_PAUSE),
        ("NARRATOR", "when love is the game.", 0),
    ],

    # Page 22 — Back cover
    "spread_22": [
        ("NARRATOR", "Discover more Coco the Axolotl adventures!", MEDIUM_PAUSE),
        ("NARRATOR", "How much does Mommy love you?", MEDIUM_PAUSE),
        ("NARRATOR", "More than hugs. More than stars. More than everything.", MEDIUM_PAUSE),
        ("NARRATOR", "She loved you before you even knew your name.", 0),
    ],

    "spread_credits": [
        ("NARRATOR", "I Love You More, Mommy. A Coco the Axolotl Adventure. By Doctor Anita Nirvena. Illustrations by Loopinky.", 0),
    ],
}


async def generate_segment(text, voice, rate):
    """Generate a single audio segment."""
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        await communicate.save(tmp_path)
        return AudioSegment.from_mp3(tmp_path)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


async def generate_spread(name, segments):
    """Generate a full spread by concatenating character segments."""
    combined = AudioSegment.empty()

    for char_tag, text, pause_after in segments:
        voice, rate, vol_db = VOICES[char_tag]
        print(f"  [{char_tag}] {text[:70]}...")
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
        seg = seg[:end + 100]
        combined += seg
        if pause_after > 0:
            combined += AudioSegment.silent(duration=pause_after)

    filepath = os.path.join(OUTPUT_DIR, f"{name}.mp3")
    combined.export(filepath, format="mp3", bitrate="128k")
    duration = len(combined) / 1000.0
    size = os.path.getsize(filepath)
    print(f"  => {name}.mp3  ({duration:.1f}s, {size // 1024} KB)")
    return filepath, duration


async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_durations = {}
    for name, segments in SPREADS.items():
        print(f"\n=== {name} ===")
        _, dur = await generate_spread(name, segments)
        all_durations[name] = round(dur, 1)

    # Print durations array for the reader HTML
    print("\n\n===== DURATIONS FOR READER (copy into index.html) =====")
    ordered = ["spread_{:02d}".format(i) for i in range(23)]
    vals = [all_durations.get(k, 0.0) for k in ordered]
    print(f"var durations = {vals};")
    print(f"\nspread_title:   {all_durations.get('spread_title', 0)}s")
    print(f"spread_credits: {all_durations.get('spread_credits', 0)}s")
    print(f"\nTotal: {sum(all_durations.values()):.0f}s  ({sum(all_durations.values())/60:.1f} min)")


if __name__ == "__main__":
    asyncio.run(main())
