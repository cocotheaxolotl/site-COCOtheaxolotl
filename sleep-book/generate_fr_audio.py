"""
Generate French narration audio for "Coco ne dort pas ce soir !"
using Edge TTS with MULTIPLE VOICES for each character.
Concatenates segments with pydub.

NOTE: "axolotl" is spelled "axolote" for correct TTS pronunciation.
"""
import asyncio, os, tempfile, edge_tts
from pydub import AudioSegment

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio")
SFX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio", "sfx")

# ===== ANIMAL SOUND EFFECTS =====
ANIMAL_SFX = {
    "OWL_SFX":      ("owl_hoot.mp3",      2000,  0),
    "DOLPHIN_SFX":  ("dolphin_chirp.mp3",  2500,  0),
    "OTTER_SFX":    ("otter_cry.mp3",      2000,  0),
    "BAT_SFX":      ("bat-sb.mp3",         2000, -5),
    "CAT_SFX":      ("cat_meow.mp3",       1000,  0),
    "HORSE_SFX":    ("horse_whinny.mp3",   2500,  0),
    "FLAMINGO_SFX": ("flamingo-sb.mp3",    2000, -3),
    "MOM_LAUGH":    ("maman_laugh.mp3",    2000, -8),
    "COCO_LAUGH":   ("coco_laugh.mp3",     1500,  0),
    "SNORE_SFX":    ("snore.wav",          2000, -5),
}

# ===== VOICE CASTING (French voices) =====
VOICES = {
    "NARRATOR":  ("fr-FR-DeniseNeural",    "-18%", 0),
    "COCO":      ("fr-FR-EloiseNeural",    "-12%", 0),
    "MOM":       ("fr-FR-DeniseNeural",    "-20%", -4),
    "OWL":       ("fr-FR-HenriNeural",     "-15%", 0),
    "DOLPHIN":   ("fr-FR-VivienneMultilingualNeural", "-10%", 0),
    "OTTER":     ("fr-FR-DeniseNeural",    "-15%", -4),
    "KOALA":     ("fr-FR-HenriNeural",     "-20%", -4),
    "BAT":       ("fr-FR-DeniseNeural",    "-15%", 0),
    "CAT":       ("fr-FR-DeniseNeural",    "-15%", 0),
    "HORSE":     ("fr-FR-HenriNeural",     "-22%", -3),
    "FLAMINGO":  ("fr-FR-DeniseNeural",    "-12%", 0),
    "SLOTH":     ("fr-FR-HenriNeural",     "-30%", 0),
    "FACT":      ("fr-FR-DeniseNeural",    "-12%", 0),
    "TITLE":     ("fr-FR-DeniseNeural",    "-25%", 0),
}

# Pause durations (ms)
SHORT_PAUSE = 600
MEDIUM_PAUSE = 1200
LONG_PAUSE = 1800

# ===== SPREADS WITH CHARACTER TAGS =====
SPREADS = {
    "spread_title": [
        ("TITLE", "Coco ne dort pas ce soir !", LONG_PAUSE),
        ("TITLE", "Une histoire du soir.", 0),
    ],

    "spread_00": [
        ("NARRATOR", "Coco ne dort pas ce soir ! Une aventure de Coco l'axolote. Par Docteur Anita Nirvéna. Illustrations de Loupine-ki.", 0),
    ],

    "spread_01": [
        ("NARRATOR", "L'heure de dormir.", LONG_PAUSE),
        ("NARRATOR", "Ce soir, c'était l'heure de dormir. Mais Coco n'avait pas du tout sommeil.", MEDIUM_PAUSE),
        ("COCO",     "Maman, je n'arrive pas à dormir !", MEDIUM_PAUSE),
        ("MOM",      "Compte les moutons,", 200),
        ("MOM",      "et...", 0),
        ("COCO",     "Mais Maman, les moutons ne savent pas nager !", MEDIUM_PAUSE),
        ("NARRATOR", "Maman ria.", SHORT_PAUSE),
        ("SFX:MOM_LAUGH", "", SHORT_PAUSE),
        ("MOM",      "C'est vrai ! Alors reste tranquille et le sommeil viendra.", 0),
    ],

    "spread_02": [
        ("NARRATOR", "L'aventure commence.", LONG_PAUSE),
        ("NARRATOR", "Mais Coco ne pouvait pas rester tranquille. Pas ce soir.", MEDIUM_PAUSE),
        ("NARRATOR", "Quand Maman et Papa se furent endormis, Coco se faufila doucement hors de la rivière.", MEDIUM_PAUSE),
        ("COCO",     "Si je ne dors pas, je vais découvrir ce que font les autres animaux la nuit !", 0),
    ],

    "spread_03": [
        ("NARRATOR", "Le Hibou.", LONG_PAUSE),
        ("NARRATOR", "Coco rencontra un hibou perché sur une branche.", MEDIUM_PAUSE),
        ("COCO",     "Bonsoir, Hibou ! Pourquoi tu ne dors pas ?", MEDIUM_PAUSE),
        ("SFX:OWL_SFX", "", SHORT_PAUSE),
        ("OWL",      "Hou hou ! Je suis nocturne ! Je travaille la nuit et je dors le jour. Mais même moi, j'ai besoin de dormir. Tout le monde a besoin de dormir !", LONG_PAUSE),
        ("FACT",     "Le savais-tu ? Les hiboux dorment le jour, cachés dans les arbres. Ils peuvent tourner la tête presque tout autour, comme pour regarder derrière eux !", 0),
    ],

    "spread_04": [
        ("NARRATOR", "Le Dauphin.", LONG_PAUSE),
        ("NARRATOR", "Au bord de l'océan, un dauphin nageait tranquillement.", MEDIUM_PAUSE),
        ("SFX:DOLPHIN_SFX", "", SHORT_PAUSE),
        ("COCO",     "Tu ne dors pas non plus ?", MEDIUM_PAUSE),
        ("DOLPHIN",  "Oh si ! Je n'endors qu'une moitié de mon cerveau à la fois. L'autre reste éveillée pour nager et respirer !", MEDIUM_PAUSE),
        ("COCO",     "Tu dors ET tu nages en même temps ?!", MEDIUM_PAUSE),
        ("DOLPHIN",  "Le sommeil est si important que j'ai trouvé un moyen de ne jamais m'en passer !", LONG_PAUSE),
        ("FACT",     "Le savais-tu ? Les dauphins dorment avec un seul œil fermé ! Le côté du cerveau qui dort change toutes les deux heures.", 0),
    ],

    "spread_05": [
        ("NARRATOR", "La Loutre.", LONG_PAUSE),
        ("NARRATOR", "Deux loutres flottaient sur le dos, patte dans la patte.", MEDIUM_PAUSE),
        ("SFX:OTTER_SFX", "", SHORT_PAUSE),
        ("COCO",     "Pourquoi vous vous tenez la main ?", MEDIUM_PAUSE),
        ("OTTER",    "Pour ne pas s'éloigner en dormant ! Se sentir en sécurité, c'est très important pour bien dormir.", MEDIUM_PAUSE),
        ("NARRATOR", "Coco sourit.", SHORT_PAUSE),
        ("COCO",     "C'est comme quand je me blottis contre ma peluche !", LONG_PAUSE),
        ("FACT",     "Le savais-tu ? Les loutres de mer se tiennent vraiment par la main en dormant ! Elles s'enroulent aussi dans des algues pour ne pas dériver.", 0),
    ],

    "spread_06": [
        ("NARRATOR", "Le Koala.", LONG_PAUSE),
        ("NARRATOR", "Dans un eucalyptus, un koala dormait profondément.", MEDIUM_PAUSE),
        ("COCO",     "Koala ! Tu dors ?", MEDIUM_PAUSE),
        ("SFX:SNORE_SFX", None, 0),
        ("KOALA",    "oui... 22 heures par jour...", MEDIUM_PAUSE),
        ("COCO",     "vingt-deux heures ?! Mais pourquoi autant ?", MEDIUM_PAUSE),
        ("KOALA",    "Mon corps a besoin d'énergie pour digérer mes feuilles... Le sommeil, ça recharge ton corps en énergie !", MEDIUM_PAUSE),
        ("NARRATOR", "Et il se rendormit aussitôt.", LONG_PAUSE),
        ("FACT",     "Le savais-tu ? Les koalas dorment jusqu'à 22 heures par jour ! Les feuilles d'eucalyptus sont très dures à digérer et donnent très peu d'énergie.", 0),
    ],

    "spread_07": [
        ("NARRATOR", "La Chauve-Souris.", LONG_PAUSE),
        ("NARRATOR", "Sous un pont, des chauves-souris étaient suspendues la tête en bas.", MEDIUM_PAUSE),
        ("SFX:BAT_SFX", "", SHORT_PAUSE),
        ("COCO",     "Vous dormez à l'envers ?!", MEDIUM_PAUSE),
        ("BAT",      "Bien sûr ! Et pendant qu'on dort, notre cerveau trie tout ce qu'on a appris, où sont les insectes, quels chemins éviter...", MEDIUM_PAUSE),
        ("COCO",     "C'est pour ça qu'on se sent plus malin après une bonne nuit !", LONG_PAUSE),
        ("FACT",     "Le savais-tu ? Pendant le sommeil, le cerveau trie et range les souvenirs. C'est pour ça qu'on retient mieux ses leçons après avoir bien dormi !", 0),
    ],

    "spread_08": [
        ("NARRATOR", "Le Chat.", LONG_PAUSE),
        ("NARRATOR", "Près d'une maison, un chat était roulé en boule sur un muret.", MEDIUM_PAUSE),
        ("SFX:CAT_SFX", "", SHORT_PAUSE),
        ("COCO",     "Tu fais un gros dodo ?", MEDIUM_PAUSE),
        ("CAT",      "Je fais plein de petits dodos. On appelle ça des micro-siestes !", MEDIUM_PAUSE),
        ("CAT",      "Pour les petits axolotes, c'est mieux de faire un long sommeil la nuit. Pendant le sommeil profond, ton corps se répare !", LONG_PAUSE),
        ("FACT",     "Le savais-tu ? Les chats dorment entre 12 et 16 heures par jour ! C'est de là que vient l'expression micro-sieste.", 0),
    ],

    "spread_09": [
        ("NARRATOR", "Le Cheval.", LONG_PAUSE),
        ("NARRATOR", "Dans un pré, un cheval se tenait immobile sous la lune.", MEDIUM_PAUSE),
        ("SFX:HORSE_SFX", "", SHORT_PAUSE),
        ("COCO",     "Tu... tu dors debout ?", MEDIUM_PAUSE),
        ("HORSE",    "Oui ! Comme ça je suis prêt à courir. Mais pour rêver, je dois m'allonger.", MEDIUM_PAUSE),
        ("HORSE",    "Le sommeil a différentes étapes : d'abord léger, puis profond, puis les rêves ! Et ça recommence toute la nuit.", LONG_PAUSE),
        ("FACT",     "Le savais-tu ? Les chevaux ne dorment profondément que 2 à 3 heures par jour, et seulement allongés !", 0),
    ],

    "spread_10": [
        ("NARRATOR", "Le Flamant Rose.", LONG_PAUSE),
        ("NARRATOR", "Au bord d'un étang, un flamant rose dormait sur une seule patte !", MEDIUM_PAUSE),
        ("SFX:FLAMINGO_SFX", "", SHORT_PAUSE),
        ("COCO",     "Comment tu ne tombes pas ?!", MEDIUM_PAUSE),
        ("FLAMINGO", "L'équilibre, ça demande un corps bien reposé ! Quand je suis fatigué...", SHORT_PAUSE),
        ("NARRATOR", "Le flamant vacilla.", SHORT_PAUSE),
        ("FLAMINGO", "Voilà ce qui arrive !", MEDIUM_PAUSE),
        ("SFX:COCO_LAUGH", "", SHORT_PAUSE),
        ("NARRATOR", "Coco rigola, mais commençait à comprendre.", LONG_PAUSE),
        ("FACT",     "Le savais-tu ? Les flamants dorment souvent sur une seule patte ! Les scientifiques pensent que c'est pour garder l'autre au chaud.", 0),
    ],

    "spread_11": [
        ("NARRATOR", "Le Paresseux.", LONG_PAUSE),
        ("NARRATOR", "Coco commençait à bâiller. Un paresseux pendait d'une branche.", MEDIUM_PAUSE),
        ("COCO",     "Je commence... à être... fatigué...", MEDIUM_PAUSE),
        ("SLOTH",    "Bienvenuuuue... au cluuuub... Quand on ne dort pas assez... on devient lent... grognon... et tout est plus difficile...", MEDIUM_PAUSE),
        ("SLOTH",    "Allez... va te coucher... petit axolote...", LONG_PAUSE),
        ("FACT",     "Le savais-tu ? Les paresseux dorment environ 15 heures par jour ! Sans assez de sommeil, notre corps se sent lourd et notre cerveau a du mal à se concentrer.", 0),
    ],

    "spread_12": [
        ("NARRATOR", "Maman Axolote.", LONG_PAUSE),
        ("MOM",      "Coco ?", MEDIUM_PAUSE),
        ("NARRATOR", "C'était Maman, au bord de la rivière.", MEDIUM_PAUSE),
        ("COCO",     "Maman ! J'ai découvert comment tous les animaux dorment ! Tout le monde en a besoin. Moi aussi !", MEDIUM_PAUSE),
        ("MOM",      "Et sais-tu comment dorment les axolotes ? On se pose au fond de l'eau, bien tranquilles, bercés par le courant...", LONG_PAUSE),
        ("FACT",     "Le savais-tu ? Les axolotes vivent dans l'eau douce et respirent grâce à leurs jolies branchies en forme de plume sur leur tête.", 0),
    ],

    "spread_13": [
        ("NARRATOR", "Le super-pouvoir.", LONG_PAUSE),
        ("NARRATOR", "Maman porta Coco jusqu'à son coin douillet au fond de la rivière.", MEDIUM_PAUSE),
        ("COCO",     "Le sommeil, ça recharge l'énergie, ça range le cerveau, ça répare le corps... pas vrai ?", MEDIUM_PAUSE),
        ("MOM",      "Tout ça à la fois, mon Coco. Et nous, les axolotes, on peut même faire repousser nos pattes ! Mais pour ça, il faut bien dormir.", LONG_PAUSE),
        ("FACT",     "Le savais-tu ? Les axolotes ont un super-pouvoir : ils peuvent régénérer leurs pattes, leur queue et même des parties de leur cerveau !", 0),
    ],

    "spread_14": [
        ("NARRATOR", "Bonne nuit Coco !", LONG_PAUSE),
        ("NARRATOR", "Coco se blottit dans son petit nid d'eau douce avec sa peluche.", MEDIUM_PAUSE),
        ("NARRATOR", "Il pensa à tous les animaux qui dormaient en ce moment, chacun à sa façon, mais tous parce que le sommeil est magique.", MEDIUM_PAUSE),
        ("NARRATOR", "Ses branchies redevinrent toutes roses et touffues.", MEDIUM_PAUSE),
        ("NARRATOR", "Et Coco s'endormit.", LONG_PAUSE),
        ("NARRATOR", "Bonne nuit !", 0),
    ],

    "spread_credits": [
        ("NARRATOR", "Coco ne dort pas ce soir ! Une aventure de Coco l'axolote. Par Docteur Anita Nirvéna. Illustrations de Loupine-ki.", 0),
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
    if path.endswith('.wav'):
        seg = AudioSegment.from_wav(path)
    else:
        seg = AudioSegment.from_mp3(path)
    if len(seg) > max_ms:
        seg = seg[:max_ms].fade_out(300)
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

    # Export
    out_path = os.path.join(OUTPUT_DIR, f"{name}.mp3")
    combined.export(out_path, format="mp3", bitrate="128k")
    dur = len(combined) / 1000
    print(f"  -> {out_path} ({dur:.2f}s)\n")
    return dur


async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    durations = {}
    for name, segments in SPREADS.items():
        print(f"=== {name} ===")
        dur = await generate_spread(name, segments)
        durations[name] = dur

    print("\n===== DURATIONS (for reader JS) =====")
    ordered = ["spread_title"] + [f"spread_{i:02d}" for i in range(15)] + ["spread_credits"]
    for name in ordered:
        if name in durations:
            print(f"  {name}: {durations[name]:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())
