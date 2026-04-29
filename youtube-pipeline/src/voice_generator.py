"""Generate gentle, child-friendly narration audio.

Two backends:
  - ElevenLabs (premium, best quality) — set ELEVENLABS_API_KEY + voice_id
  - Edge TTS (free fallback) — Microsoft neural voices, soft storybook style

For Coco the Axolotl, we use SOFT, GENTLE voices — NOT punchy/aggressive
(opposite of univers.studio).
"""
import os
import sys
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / "config" / ".env")

OUTPUT_DIR = ROOT / "output" / "audio"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ElevenLabs voice IDs — CONFIDENT PARENT-TO-PARENT (not bedtime narrator)
# These are acquisition shorts targeting parents 25-45, not kids' lullabies
EL_VOICES = {
    "en": "ThT5KcBeYPX3keUQqHPh",  # Dorothy — punchy, real, mom-coded
    "fr": "uFA9UGUhpwqGjVhz3lA2",  # Christine — confident FR (multilingual model)
    "es": "ThT5KcBeYPX3keUQqHPh",
}
EL_MODEL = "eleven_multilingual_v2"

# Edge TTS voices — free fallback (matches the Coco flipbook conventions per CLAUDE.md)
EDGE_VOICES = {
    "en": "en-US-AriaNeural",
    "fr": "fr-FR-VivienneMultilingualNeural",  # used for the dolphin in Coco flipbook
    "es": "es-ES-ElviraNeural",
}


def synth_elevenlabs(text: str, out_name: str, lang: str = "en",
                     voice_id: str | None = None) -> Path:
    """ElevenLabs synthesis with soft narrative settings."""
    from elevenlabs.client import ElevenLabs
    from elevenlabs import VoiceSettings

    api_key = os.getenv("ELEVENLABS_API_KEY", "")
    if not api_key or "COLLE" in api_key:
        raise RuntimeError("ELEVENLABS_API_KEY not set")

    voice_id = voice_id or os.getenv("ELEVENLABS_VOICE_ID", "") or EL_VOICES.get(lang, EL_VOICES["en"])
    print(f"[voice] ElevenLabs voice={voice_id} model={EL_MODEL} chars={len(text)}")

    client = ElevenLabs(api_key=api_key)
    audio = client.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
        model_id=EL_MODEL,
        output_format="mp3_44100_128",
        voice_settings=VoiceSettings(
            stability=0.45,        # mid = real conversational variation, not flat narrator
            similarity_boost=0.8,
            style=0.55,            # mid-high = expressive parent-to-parent storytelling
            use_speaker_boost=True,
        ),
    )

    out_path = OUTPUT_DIR / out_name
    with open(out_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)
    print(f"[voice] OK -> {out_path} ({out_path.stat().st_size // 1024} KB)")
    return out_path


def synth_edge_tts(text: str, out_name: str, lang: str = "en") -> Path:
    """Free fallback via Edge TTS — used for Coco flipbook narration already."""
    import edge_tts

    voice = EDGE_VOICES.get(lang, EDGE_VOICES["en"])
    out_path = OUTPUT_DIR / out_name

    async def _run():
        communicate = edge_tts.Communicate(text, voice, rate="+0%")  # natural pace, not slowed
        await communicate.save(str(out_path))

    asyncio.run(_run())
    print(f"[voice] EdgeTTS voice={voice} -> {out_path}")
    return out_path


def synth(text: str, out_name: str, lang: str = "en",
          backend: str = "auto", voice_id: str | None = None) -> Path:
    """Synthesize narration. backend: 'elevenlabs' | 'edge' | 'auto'."""
    if backend == "auto":
        backend = "elevenlabs" if os.getenv("ELEVENLABS_API_KEY", "") and "COLLE" not in os.getenv("ELEVENLABS_API_KEY", "") else "edge"

    if backend == "elevenlabs":
        return synth_elevenlabs(text, out_name, lang=lang, voice_id=voice_id)
    return synth_edge_tts(text, out_name, lang=lang)


def synth_from_script(script_path: Path, lang: str = "en",
                      backend: str = "auto", voice_id: str | None = None) -> Path:
    """Concatenate all voice lines from a script JSON into one audio file."""
    data = json.loads(script_path.read_text(encoding="utf-8"))
    lines = []
    for scene in data.get("scenes", []):
        v = scene.get("voice", "").strip()
        if v:
            lines.append(v)
    text = " ".join(lines)
    if not text:
        raise RuntimeError(f"No voice lines in {script_path}")

    out_name = script_path.stem + ".mp3"
    return synth(text, out_name, lang=lang, backend=backend, voice_id=voice_id)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].endswith(".json"):
        synth_from_script(Path(sys.argv[1]), lang=sys.argv[2] if len(sys.argv) > 2 else "en")
    else:
        text = "Once upon a time, a little pink axolotl named Coco couldn't sleep."
        synth(text, "test.mp3")
