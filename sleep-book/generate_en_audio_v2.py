"""
Generate English narration audio for "Coco Doesn't Sleep Tonight"
using Edge TTS with MULTIPLE VOICES for each character.
Concatenates segments with pydub.
"""
import asyncio, os, tempfile, edge_tts
from pydub import AudioSegment

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio", "en")
SFX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio", "sfx")

# ===== ANIMAL SOUND EFFECTS =====
# (filename, max_duration_ms, volume_adjust_dB)
# Sounds are trimmed to max_duration and faded out
ANIMAL_SFX = {
    "OWL_SFX":      ("owl_hoot.mp3",      2000,  0),
    "DOLPHIN_SFX":  ("dolphin_chirp.mp3",  2500,  0),
    "OTTER_SFX":    ("otter_cry.mp3",       2000,  0),
    "BAT_SFX":      ("bat-sb.mp3",         2000, -5),
    "CAT_SFX":      ("cat_meow.mp3",       1000,  0),
    "HORSE_SFX":    ("horse_whinny.mp3",   2500,  0),
    "FLAMINGO_SFX": ("flamingo-sb.mp3",    2000, -3),
    "MOM_LAUGH":    ("maman_laugh.mp3",    2000,  0),
}

# ===== VOICE CASTING =====
# (voice_name, rate, volume_adjust_dB)
VOICES = {
    "NARRATOR":  ("en-US-JennyNeural",               "-18%", 0),
    "COCO":      ("en-US-AnaNeural",                  "-12%", 0),
    "MOM":       ("en-US-AriaNeural",                 "-20%", -4),
    "OWL":       ("en-GB-RyanNeural",                 "-15%", 0),
    "DOLPHIN":   ("en-US-AvaNeural",                   "-15%", 0),
    "OTTER":     ("en-US-EmmaNeural",                 "-15%", 0),
    "KOALA":     ("en-AU-WilliamMultilingualNeural",  "-20%", 0),
    "BAT":       ("en-GB-LibbyNeural",                 "-15%", 0),
    "CAT":       ("en-GB-SoniaNeural",                "-15%", 0),
    "HORSE":     ("en-US-ChristopherNeural",          "-22%", -3),
    "FLAMINGO":  ("en-US-MichelleNeural",             "-12%", 0),
    "SLOTH":     ("en-US-EricNeural",                 "-30%", 0),
    "FACT":      ("en-US-JennyNeural",                "-12%", 0),
}

# Pause durations (ms)
SHORT_PAUSE = 400
MEDIUM_PAUSE = 700
LONG_PAUSE = 1000

# ===== SPREADS WITH CHARACTER TAGS =====
# Each spread is a list of (CHARACTER, text, pause_after_ms)
SPREADS = {
    "spread_title": [
        ("NARRATOR", "Coco Doesn't Sleep Tonight.", -1),
        ("NARRATOR", "A bedtime story.", 0),
    ],

    "spread_00": [
        ("NARRATOR", "Coco Doesn't Sleep Tonight.", 0),
    ],

    "spread_01": [
        ("NARRATOR", "Bedtime.", LONG_PAUSE),
        ("NARRATOR", "That night, it was time for bed. But Coco wasn't sleepy at all.", MEDIUM_PAUSE),
        ("COCO",     "Mom, I can't fall asleep!", MEDIUM_PAUSE),
        ("MOM",      "Count some sheep and...", -1),
        ("COCO",     "But Mom, sheep can't swim!", MEDIUM_PAUSE),
        ("SFX:MOM_LAUGH", "", SHORT_PAUSE),
        ("MOM",      "That's true! Just stay still and sleep will come.", 0),
    ],

    "spread_02": [
        ("NARRATOR", "But Coco couldn't stay still. Not tonight.", MEDIUM_PAUSE),
        ("NARRATOR", "When Mom and Dad fell asleep, Coco quietly slipped out of the river.", MEDIUM_PAUSE),
        ("COCO",     "If I can't sleep, I'll find out what other animals do at night!", 0),
    ],

    "spread_03": [
        ("NARRATOR", "The Owl.", LONG_PAUSE),
        ("NARRATOR", "Coco met an owl perched on a branch.", MEDIUM_PAUSE),
        ("SFX:OWL_SFX", "", SHORT_PAUSE),
        ("COCO",     "Good evening, Owl! Why aren't you sleeping?", MEDIUM_PAUSE),
        ("OWL",      "I'm nocturnal! I work at night and sleep during the day. But even I need to sleep. Everyone needs to sleep!", LONG_PAUSE),
        ("FACT",     "Did you know? Owls sleep during the day, hidden in trees. They can turn their heads almost all the way around, as if looking behind them!", 0),
    ],

    "spread_04": [
        ("NARRATOR", "The Dolphin.", LONG_PAUSE),
        ("NARRATOR", "By the ocean, a dolphin was swimming peacefully.", MEDIUM_PAUSE),
        ("SFX:DOLPHIN_SFX", "", SHORT_PAUSE),
        ("COCO",     "You're not sleeping either?", MEDIUM_PAUSE),
        ("DOLPHIN",  "Oh, I am! I only put half my brain to sleep at a time. The other half stays awake to swim and breathe!", MEDIUM_PAUSE),
        ("COCO",     "You sleep AND swim at the same time?!", MEDIUM_PAUSE),
        ("DOLPHIN",  "Sleep is so important that I found a way to never go without it!", LONG_PAUSE),
        ("FACT",     "Did you know? Dolphins sleep with only one eye closed! The side of the brain that sleeps switches every two hours.", 0),
    ],

    "spread_05": [
        ("NARRATOR", "The Otter.", LONG_PAUSE),
        ("NARRATOR", "Two otters were floating on their backs, paw in paw.", MEDIUM_PAUSE),
        ("SFX:OTTER_SFX", "", SHORT_PAUSE),
        ("COCO",     "Why are you holding hands?", MEDIUM_PAUSE),
        ("OTTER",    "So we don't drift apart while sleeping! Feeling safe is very important for a good night's sleep.", MEDIUM_PAUSE),
        ("NARRATOR", "Coco smiled.", SHORT_PAUSE),
        ("COCO",     "It's like when I snuggle up with my stuffed animal!", LONG_PAUSE),
        ("FACT",     "Did you know? Sea otters really do hold hands while sleeping! They also wrap themselves in seaweed so they don't drift away.", 0),
    ],

    "spread_06": [
        ("NARRATOR", "The Koala.", LONG_PAUSE),
        ("NARRATOR", "In a eucalyptus tree, a koala was sleeping soundly.", MEDIUM_PAUSE),
        ("COCO",     "Koala! Are you sleeping?", MEDIUM_PAUSE),
        ("KOALA",    "Mmm... yes... 22 hours a day...", MEDIUM_PAUSE),
        ("COCO",     "22 HOURS?! But why so much?", MEDIUM_PAUSE),
        ("KOALA",    "My body needs energy to digest my leaves... Sleep recharges your body with energy!", MEDIUM_PAUSE),
        ("NARRATOR", "And he fell right back asleep.", LONG_PAUSE),
        ("FACT",     "Did you know? Koalas sleep up to 22 hours a day! Eucalyptus leaves are very hard to digest and provide very little energy.", 0),
    ],

    "spread_07": [
        ("NARRATOR", "The Bat.", LONG_PAUSE),
        ("NARRATOR", "Under a bridge, bats were hanging upside down.", MEDIUM_PAUSE),
        ("SFX:BAT_SFX", "", SHORT_PAUSE),
        ("COCO",     "You sleep upside down?!", MEDIUM_PAUSE),
        ("BAT",      "Of course! And while we sleep, our brain sorts everything we've learned, where the insects are, which paths to avoid...", MEDIUM_PAUSE),
        ("BAT",      "That's why you feel smarter after a good night's sleep!", LONG_PAUSE),
        ("FACT",     "Did you know? During sleep, the brain sorts and organizes memories. That's why you remember your lessons better after a good night's sleep!", 0),
    ],

    "spread_08": [
        ("NARRATOR", "The Cat.", LONG_PAUSE),
        ("NARRATOR", "Near a house, a cat was curled up on a low wall.", MEDIUM_PAUSE),
        ("SFX:CAT_SFX", "", SHORT_PAUSE),
        ("COCO",     "Are you having a big nap?", MEDIUM_PAUSE),
        ("CAT",      "I take lots of little naps. They're called catnaps!", MEDIUM_PAUSE),
        ("CAT",      "For little axolotls, it's better to have one long sleep at night. During deep sleep, your body repairs itself!", LONG_PAUSE),
        ("FACT",     "Did you know? Cats sleep between 12 and 16 hours a day! That's where the expression catnap comes from.", 0),
    ],

    "spread_09": [
        ("NARRATOR", "The Horse.", LONG_PAUSE),
        ("NARRATOR", "In a meadow, a horse stood still under the moon.", MEDIUM_PAUSE),
        ("SFX:HORSE_SFX", "", SHORT_PAUSE),
        ("COCO",     "You... you sleep standing up?", MEDIUM_PAUSE),
        ("HORSE",    "Yes! That way I'm ready to run. But to dream, I have to lie down.", MEDIUM_PAUSE),
        ("HORSE",    "Sleep has different stages: first light, then deep, then dreams! And it starts all over again throughout the night.", LONG_PAUSE),
        ("FACT",     "Did you know? Horses only sleep deeply for 2 to 3 hours a day, and only when lying down!", 0),
    ],

    "spread_10": [
        ("NARRATOR", "The Flamingo.", LONG_PAUSE),
        ("NARRATOR", "By a pond, a flamingo was sleeping on one leg!", MEDIUM_PAUSE),
        ("SFX:FLAMINGO_SFX", "", SHORT_PAUSE),
        ("COCO",     "How don't you fall over?!", MEDIUM_PAUSE),
        ("FLAMINGO", "Balance requires a well-rested body! When I'm tired...", SHORT_PAUSE),
        ("NARRATOR", "The flamingo wobbled.", SHORT_PAUSE),
        ("FLAMINGO", "That's what happens!", MEDIUM_PAUSE),
        ("NARRATOR", "Coco laughed, but was starting to understand.", LONG_PAUSE),
        ("FACT",     "Did you know? Flamingos often sleep on one leg! Scientists think it's to keep the other one warm.", 0),
    ],

    "spread_11": [
        ("NARRATOR", "The Sloth.", LONG_PAUSE),
        ("NARRATOR", "Coco was starting to yawn. A sloth was hanging from a branch.", MEDIUM_PAUSE),
        ("COCO",     "I'm starting... to feel... tired...", MEDIUM_PAUSE),
        ("SLOTH",    "Welcomeee... to the cluuub... When you don't sleep enough... you become slow... grumpy... and everything is harder...", MEDIUM_PAUSE),
        ("SLOTH",    "Go on... go to bed... little axolotl...", LONG_PAUSE),
        ("FACT",     "Did you know? Sloths sleep about 15 hours a day! Without enough sleep, our body feels heavy and our brain has trouble concentrating.", 0),
    ],

    "spread_12": [
        ("NARRATOR", "Mama Axolotl.", LONG_PAUSE),
        ("MOM",      "Coco?", MEDIUM_PAUSE),
        ("NARRATOR", "It was Mom, by the river.", MEDIUM_PAUSE),
        ("COCO",     "Mom! I discovered how all the animals sleep! Everyone needs it. Me too!", MEDIUM_PAUSE),
        ("MOM",      "And do you know how axolotls sleep? We settle at the bottom of the water, nice and quiet, rocked by the current...", LONG_PAUSE),
        ("FACT",     "Did you know? Axolotls live in fresh water and breathe through their beautiful feather-shaped gills on their heads.", 0),
    ],

    "spread_13": [
        ("NARRATOR", "The Superpower.", LONG_PAUSE),
        ("NARRATOR", "Mom carried Coco to his cozy spot at the bottom of the river.", MEDIUM_PAUSE),
        ("COCO",     "Sleep recharges your energy, organizes your brain, repairs your body... right?", MEDIUM_PAUSE),
        ("MOM",      "All of that at once, my Coco. And we axolotls can even regrow our legs! But for that, you need to sleep well.", LONG_PAUSE),
        ("FACT",     "Did you know? Axolotls have a superpower: they can regenerate their legs, their tail, and even parts of their brain!", 0),
    ],

    "spread_14": [
        ("NARRATOR", "Good Night Coco!", LONG_PAUSE),
        ("NARRATOR", "Coco snuggled into his little freshwater nest with his stuffed animal.", MEDIUM_PAUSE),
        ("NARRATOR", "He thought of all the animals sleeping right now, each in their own way, but all because sleep is magical.", MEDIUM_PAUSE),
        ("NARRATOR", "His gills turned rosy and fluffy again.", MEDIUM_PAUSE),
        ("NARRATOR", "And Coco fell asleep.", LONG_PAUSE),
        ("NARRATOR", "Good Night!", 0),
    ],

    "spread_credits": [
        ("NARRATOR", "Coco Doesn't Sleep Tonight. A Coco the Axolotl adventure. By Doctor Anita Nirvena. Illustrations by Loopinky.", 0),
    ],
}


async def generate_segment(text, voice, rate):
    """Generate a single audio segment, return as AudioSegment."""
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


def load_sfx(sfx_key):
    """Load and prepare a sound effect clip."""
    filename, max_ms, vol_db = ANIMAL_SFX[sfx_key]
    path = os.path.join(SFX_DIR, filename)
    seg = AudioSegment.from_mp3(path)
    # Trim to max duration
    if len(seg) > max_ms:
        seg = seg[:max_ms].fade_out(300)
    # Adjust volume
    if vol_db != 0:
        seg = seg + vol_db
    return seg


async def generate_spread(name, segments):
    """Generate a full spread by concatenating character segments."""
    combined = AudioSegment.empty()

    for char_tag, text, pause_after in segments:
        if char_tag.startswith("SFX:"):
            sfx_key = char_tag.split(":")[1]
            print(f"  [SFX] {sfx_key}")
            seg = load_sfx(sfx_key)
        else:
            voice, rate, vol_db = VOICES[char_tag]
            print(f"  [{char_tag}] {text[:60]}...")
            seg = await generate_segment(text, voice, rate)
            if vol_db != 0:
                seg = seg + vol_db
        combined += seg
        if pause_after > 0:
            combined += AudioSegment.silent(duration=pause_after)
        elif pause_after < 0:
            # Negative pause = strip trailing silence (interrupt effect)
            stripped = seg.strip_silence(silence_len=50, silence_thresh=-45, padding=0)
            combined = combined[:-len(seg)] + stripped

    # Export
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

    # Print durations array for the reader
    print("\n\n===== DURATIONS FOR READER =====")
    ordered = ["spread_{:02d}".format(i) for i in range(15)]
    vals = [all_durations[k] for k in ordered]
    print(f"var durations = {vals};")
    print(f"spread_title: {all_durations['spread_title']}s")
    print(f"spread_credits: {all_durations['spread_credits']}s")
    print(f"\nTotal narration: {sum(all_durations.values()):.0f}s")


if __name__ == "__main__":
    asyncio.run(main())
