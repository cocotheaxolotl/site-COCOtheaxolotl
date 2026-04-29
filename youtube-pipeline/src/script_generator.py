"""Generate a Coco the Axolotl YouTube Short script using Claude.

Output: structured JSON with hook, scenes, voice-over text, B-roll prompts,
title, description, tags, thumbnail concept.
"""
import os
import sys
import json
import re
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / "config" / ".env")

PROMPTS_DIR = ROOT / "prompts"
BOOKS_DIR = ROOT / "config" / "books"
OUTPUT_DIR = ROOT / "output" / "scripts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL = "claude-opus-4-7"


def load_book(slug: str) -> dict:
    cfg_path = BOOKS_DIR / f"{slug}.json"
    if not cfg_path.exists():
        raise FileNotFoundError(f"No book config at {cfg_path}")
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def load_prompt(fmt: str) -> str:
    p = PROMPTS_DIR / f"script_{fmt}.md"
    if not p.exists():
        raise FileNotFoundError(f"No prompt template at {p}")
    return p.read_text(encoding="utf-8")


def load_narration(book: dict, lang: str) -> str:
    """Load the actual narration text from the book if available."""
    narr_files = book.get("narration_files", {})
    rel = narr_files.get(lang, "")
    if not rel:
        return ""
    p = (BOOKS_DIR / rel).resolve()
    if p.exists():
        return p.read_text(encoding="utf-8")
    return ""


def _call_claude(prompt: str, api_key: str) -> dict:
    client = Anthropic(api_key=api_key)
    msg = client.messages.create(
        model=MODEL, max_tokens=2500,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = msg.content[0].text
    raw_clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
    return json.loads(raw_clean)


def generate_script(slug: str, fmt: str = "short", lang: str = "en",
                    hook_angle: str | None = None) -> dict:
    """Generate a Coco YouTube script."""
    book = load_book(slug)
    template = load_prompt(fmt)

    angle_hint = ""
    if hook_angle:
        angle_hint = f"\n\nUse a '{hook_angle}' angle (one of bedtime/adventure/tendresse/fun)."

    narration = load_narration(book, lang)
    narration_hint = ""
    if narration:
        narration_hint = (
            f"\n\nACTUAL BOOK NARRATION ({lang}):\n```\n{narration[:3000]}\n```\n"
            "Use SHORT EXCERPTS from this when narrating scenes — preserve the book's "
            "exact gentle tone and phrasing where possible. Do not paraphrase the heart lines."
        )

    lang_hint = ""
    if lang == "fr":
        lang_hint = (
            "\n\nLANGUAGE: write EVERYTHING in FRENCH. "
            "Title, description, tags, hook text_overlay, hook text_overlay_2, "
            "outro_text_overlay, all scenes voice text. "
            "Use the url_fr from the book config (https://cocotheaxolotl.org/fr/). "
            "Tone: doux, chaleureux, narratif. Phrases courtes adaptées aux enfants 3-7 ans. "
            "FRENCH TYPOGRAPHY: espace avant ! ? : — "
            "(ex. 'Bonne nuit, Coco !' pas 'Bonne nuit, Coco!'). "
            "TTS: les nombres en lettres ('trois' pas '3'), pas de majuscules pour mots à épeler."
        )
    elif lang == "es":
        lang_hint = (
            "\n\nLANGUAGE: write EVERYTHING in SPANISH. "
            "Tone: cálido, dulce, narrativo. Frases cortas para niños 3-7 años."
        )

    prompt = (
        template.replace("{BOOK_JSON}", json.dumps(book, indent=2, ensure_ascii=False))
        + angle_hint + narration_hint + lang_hint
    )

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key or "COLLE" in api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set in config/.env")

    print(f"[script] generating {fmt} for {slug} (lang={lang}, angle={hook_angle or 'auto'})")

    data = _call_claude(prompt, api_key)

    out_path = OUTPUT_DIR / f"{slug}_{fmt}_{lang}_{hook_angle or 'auto'}.json"
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[script] OK -> {out_path}")
    print(f"[script] title: {data.get('title', '?')}")
    return data


if __name__ == "__main__":
    slug = sys.argv[1] if len(sys.argv) > 1 else "coco-cant-sleep"
    fmt = sys.argv[2] if len(sys.argv) > 2 else "short"
    lang = sys.argv[3] if len(sys.argv) > 3 else "en"
    angle = sys.argv[4] if len(sys.argv) > 4 else "bedtime"
    generate_script(slug, fmt, lang, hook_angle=angle)
