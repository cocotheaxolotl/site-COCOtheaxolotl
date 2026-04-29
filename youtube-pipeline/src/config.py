"""Centralized config — loads .env and exposes paths/keys."""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / "config" / ".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
FAL_KEY = os.getenv("FAL_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")
YOUTUBE_CLIENT_SECRETS_FILE = ROOT / os.getenv(
    "YOUTUBE_CLIENT_SECRETS_FILE", "config/youtube_oauth.json"
)
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID", "")

ASSETS_DIR = ROOT / "assets"
OUTPUT_DIR = ROOT / "output"
PROMPTS_DIR = ROOT / "prompts"
BOOKS_CONFIG_DIR = ROOT / "config" / "books"

OUTPUT_DIR.mkdir(exist_ok=True)
BOOKS_CONFIG_DIR.mkdir(parents=True, exist_ok=True)

SITE_BASE_URL = "https://cocotheaxolotl.org"
