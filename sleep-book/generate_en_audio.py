"""
Generate English narration audio for "Coco Doesn't Sleep Tonight"
using Edge TTS (Microsoft Neural voices).
"""
import asyncio, os, edge_tts

VOICE = "en-US-AnaNeural"   # Young, warm US female voice (good for children's books)
RATE = "-10%"                # Slightly slower for bedtime story feel
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio", "en")

# Each spread maps to narration text
SPREADS = {
    "spread_title": (
        "Coco Doesn't Sleep Tonight. A bedtime story."
    ),

    # Spread 00 = cover narration (title page)
    "spread_00": (
        "Coco Doesn't Sleep Tonight."
    ),

    # Spread 01 = Bedtime (slides 2-3)
    "spread_01": (
        "That night, it was time for bed. But Coco wasn't sleepy at all.\n"
        "Mom, I can't fall asleep!\n"
        "Count some sheep and...\n"
        "But Mom, sheep can't swim!\n"
        "Mom laughed.\n"
        "That's true! Just stay still and sleep will come."
    ),

    # Spread 02 = The Adventure Begins (slides 4-5)
    "spread_02": (
        "But Coco couldn't stay still. Not tonight.\n"
        "When Mom and Dad fell asleep, Coco quietly slipped out of the river.\n"
        "If I can't sleep, I'll find out what other animals do at night!"
    ),

    # Spread 03 = The Owl (slides 6-7)
    "spread_03": (
        "The Owl.\n"
        "Coco met an owl perched on a branch.\n"
        "Good evening, Owl! Why aren't you sleeping?\n"
        "Hoo hoo! I'm nocturnal! I work at night and sleep during the day. "
        "But even I need to sleep. Everyone needs to sleep!\n"
        "Did you know? Owls sleep during the day, hidden in trees. "
        "They can turn their heads almost all the way around, as if looking behind them!"
    ),

    # Spread 04 = The Dolphin (slides 8-9)
    "spread_04": (
        "The Dolphin.\n"
        "By the ocean, a dolphin was swimming peacefully.\n"
        "You're not sleeping either?\n"
        "Oh, I am! I only put half my brain to sleep at a time. "
        "The other half stays awake to swim and breathe!\n"
        "You sleep AND swim at the same time?!\n"
        "Sleep is so important that I found a way to never go without it!\n"
        "Did you know? Dolphins sleep with only one eye closed! "
        "The side of the brain that sleeps switches every two hours."
    ),

    # Spread 05 = The Otter (slides 10-11)
    "spread_05": (
        "The Otter.\n"
        "Two otters were floating on their backs, paw in paw.\n"
        "Why are you holding hands?\n"
        "So we don't drift apart while sleeping! "
        "Feeling safe is very important for a good night's sleep.\n"
        "Coco smiled.\n"
        "It's like when I snuggle up with my stuffed animal!\n"
        "Did you know? Sea otters really do hold hands while sleeping! "
        "They also wrap themselves in seaweed so they don't drift away."
    ),

    # Spread 06 = The Koala (slides 12-13)
    "spread_06": (
        "The Koala.\n"
        "In a eucalyptus tree, a koala was sleeping soundly.\n"
        "Koala! Are you sleeping?\n"
        "Zzz... yes... 22 hours a day...\n"
        "22 HOURS?! But why so much?\n"
        "My body needs energy to digest my leaves... "
        "Sleep recharges your body with energy!\n"
        "And he fell right back asleep.\n"
        "Did you know? Koalas sleep up to 22 hours a day! "
        "Eucalyptus leaves are very hard to digest and provide very little energy."
    ),

    # Spread 07 = The Bat (slides 14-15)
    "spread_07": (
        "The Bat.\n"
        "Under a bridge, bats were hanging upside down.\n"
        "You sleep upside down?!\n"
        "Of course! And while we sleep, our brain sorts everything we've learned — "
        "where the insects are, which paths to avoid...\n"
        "That's why you feel smarter after a good night's sleep!\n"
        "Did you know? During sleep, the brain sorts and organizes memories. "
        "That's why you remember your lessons better after a good night's sleep!"
    ),

    # Spread 08 = The Cat (slides 16-17)
    "spread_08": (
        "The Cat.\n"
        "Near a house, a cat was curled up on a low wall.\n"
        "Are you having a big nap?\n"
        "I take lots of little naps. They're called catnaps!\n"
        "For little axolotls, it's better to have one long sleep at night. "
        "During deep sleep, your body repairs itself!\n"
        "Did you know? Cats sleep between 12 and 16 hours a day! "
        "That's where the expression catnap comes from."
    ),

    # Spread 09 = The Horse (slides 18-19)
    "spread_09": (
        "The Horse.\n"
        "In a meadow, a horse stood still under the moon.\n"
        "You... you sleep standing up?\n"
        "Yes! That way I'm ready to run. But to dream, I have to lie down.\n"
        "Sleep has different stages: first light, then deep, then dreams! "
        "And it starts all over again throughout the night.\n"
        "Did you know? Horses only sleep deeply for 2 to 3 hours a day — "
        "and only when lying down!"
    ),

    # Spread 10 = The Flamingo (slides 20-21)
    "spread_10": (
        "The Flamingo.\n"
        "By a pond, a flamingo was sleeping on one leg!\n"
        "How don't you fall over?!\n"
        "Balance requires a well-rested body! When I'm tired...\n"
        "The flamingo wobbled.\n"
        "That's what happens!\n"
        "Coco laughed, but was starting to understand.\n"
        "Did you know? Flamingos often sleep on one leg! "
        "Scientists think it's to keep the other one warm."
    ),

    # Spread 11 = The Sloth (slides 22-23)
    "spread_11": (
        "The Sloth.\n"
        "Coco was starting to yawn. A sloth was hanging from a branch.\n"
        "I'm starting... to feel... tired...\n"
        "Welcomeee... to the cluuub... "
        "When you don't sleep enough... you become slow... grumpy... "
        "and everything is harder...\n"
        "Go on... go to bed... little axolotl... zzz...\n"
        "Did you know? Sloths sleep about 15 hours a day! "
        "Without enough sleep, our body feels heavy and our brain has trouble concentrating."
    ),

    # Spread 12 = Mama Axolotl (slides 24-25)
    "spread_12": (
        "Mama Axolotl.\n"
        "Coco?\n"
        "It was Mom, by the river.\n"
        "Mom! I discovered how all the animals sleep! Everyone needs it. Me too!\n"
        "And do you know how axolotls sleep? "
        "We settle at the bottom of the water, nice and quiet, rocked by the current...\n"
        "Did you know? Axolotls live in fresh water and breathe through "
        "their beautiful feather-shaped gills on their heads."
    ),

    # Spread 13 = The Superpower (slides 26-27)
    "spread_13": (
        "The Superpower.\n"
        "Mom carried Coco to his cozy spot at the bottom of the river.\n"
        "Sleep recharges your energy, organizes your brain, repairs your body... right?\n"
        "All of that at once, my Coco. And we axolotls can even regrow our legs! "
        "But for that, you need to sleep well.\n"
        "Did you know? Axolotls have a superpower: "
        "they can regenerate their legs, their tail, and even parts of their brain!"
    ),

    # Spread 14 = Good Night (slides 28-29)
    "spread_14": (
        "Good Night Coco!\n"
        "Coco snuggled into his little freshwater nest with his stuffed animal.\n"
        "He thought of all the animals sleeping right now — "
        "each in their own way, but all because sleep is magical.\n"
        "His gills turned rosy and fluffy again.\n"
        "And Coco fell asleep.\n"
        "Good Night!"
    ),

    "spread_credits": (
        "Coco Doesn't Sleep Tonight. A Coco the Axolotl adventure. "
        "By Doctor Anita Nirvena. Illustrations by Loopinky."
    ),
}


async def generate_audio(name, text):
    """Generate a single MP3 file from text."""
    filepath = os.path.join(OUTPUT_DIR, f"{name}.mp3")
    # Clean up text for speech: remove \n, normalize
    clean = text.replace("\n", " ").strip()
    communicate = edge_tts.Communicate(clean, VOICE, rate=RATE)
    await communicate.save(filepath)
    return filepath


async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    tasks = []
    for name, text in SPREADS.items():
        tasks.append((name, text))

    for name, text in tasks:
        print(f"Generating {name}...")
        path = await generate_audio(name, text)
        # Get file size
        size = os.path.getsize(path)
        print(f"  -> {path} ({size//1024} KB)")

    print(f"\nDone! {len(tasks)} audio files generated in {OUTPUT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
