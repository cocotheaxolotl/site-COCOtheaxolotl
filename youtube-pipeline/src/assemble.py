"""Assemble the final Coco YouTube Short.

Inputs:
  - hook_clip (Fal.ai 6s soft storybook intro)
  - main_video (book pages ken-burns OR concatenated clips)
  - voice_audio (mp3 from voice_generator)
  - outro_clip (optional)
  - text overlays (hook text, hook text 2, outro text, CTA)
  - music (soft lullaby track from assets/music/)

Outputs:
  - vertical 9:16 1080x1920 mp4, 30fps, h264 yuv420p
"""
import sys
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIDEOS_DIR = ROOT / "output" / "videos"
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR = ROOT / "assets"


def get_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip() or 0)


def _scale_to_vertical(in_path: Path, out_path: Path, dur: float | None = None) -> Path:
    """Scale any video to 1080x1920 with letterbox if needed."""
    cmd = [
        "ffmpeg", "-y", "-i", str(in_path),
        "-vf", "scale=w=1080:h=1920:force_original_aspect_ratio=decrease,"
               "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=#FCEEF5,format=yuv420p",
        "-r", "30", "-c:v", "libx264", "-crf", "20", "-an",
    ]
    if dur:
        cmd += ["-t", str(dur)]
    cmd.append(str(out_path))
    subprocess.run(cmd, check=True, capture_output=True)
    return out_path


def _concat_videos(clips: list[Path], out_path: Path) -> Path:
    """Concatenate videos via concat demuxer."""
    list_file = out_path.with_suffix(".txt")
    list_file.write_text("\n".join(f"file '{c.as_posix()}'" for c in clips), encoding="utf-8")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
           "-c", "copy", str(out_path)]
    subprocess.run(cmd, check=True, capture_output=True)
    list_file.unlink(missing_ok=True)
    return out_path


def assemble(out_name: str, hook_clip: Path, main_video: Path, voice_audio: Path,
             outro_clip: Path | None = None,
             hook_text: str = "", hook_text_2: str = "",
             outro_text: str = "", cta_url: str = "cocotheaxolotl.org",
             music_path: Path | None = None,
             lang: str = "en") -> Path:
    """Build a final 9:16 video.

    Layout:
      [0-3s]    hook_clip + hook_text overlay
      [3-6s]    hook_clip + hook_text_2 overlay
      [6-X]     main_video (book pages ken-burns) — voice plays over
      [X-end]   outro_clip + outro_text + CTA URL
    """
    print(f"\n[assemble] building {out_name}")
    work = VIDEOS_DIR / "_work"
    work.mkdir(exist_ok=True)

    # 1. Normalize all inputs to 1080x1920 vertical
    hook_norm = _scale_to_vertical(hook_clip, work / "hook_norm.mp4")
    main_norm = _scale_to_vertical(main_video, work / "main_norm.mp4")
    outro_norm = None
    if outro_clip and outro_clip.exists():
        outro_norm = _scale_to_vertical(outro_clip, work / "outro_norm.mp4")

    # 2. Concat hook + main (+ outro)
    parts = [hook_norm, main_norm]
    if outro_norm:
        parts.append(outro_norm)
    silent = work / "concat_silent.mp4"
    _concat_videos(parts, silent)

    silent_dur = get_duration(silent)
    voice_dur = get_duration(voice_audio)
    print(f"[assemble] silent={silent_dur:.1f}s voice={voice_dur:.1f}s")

    # 3. Build text overlay filter graph
    # Use FFmpeg drawtext with a soft white-on-pastel look. Fonts: use system default if no asset.
    font = ASSETS_DIR / "fonts" / "Quicksand-Bold.ttf"
    font_arg = f"fontfile='{font.as_posix()}':" if font.exists() else ""

    overlays = []
    if hook_text:
        overlays.append(
            f"drawtext={font_arg}text='{_esc(hook_text)}':"
            f"fontsize=72:fontcolor=white:bordercolor=#A65C82:borderw=4:"
            f"x=(w-text_w)/2:y=h*0.18:enable='between(t,0.2,3)'"
        )
    if hook_text_2:
        overlays.append(
            f"drawtext={font_arg}text='{_esc(hook_text_2)}':"
            f"fontsize=64:fontcolor=white:bordercolor=#A65C82:borderw=4:"
            f"x=(w-text_w)/2:y=h*0.18:enable='between(t,3,6)'"
        )
    # Outro text + CTA (last 5 seconds)
    final_dur = silent_dur
    if outro_text:
        overlays.append(
            f"drawtext={font_arg}text='{_esc(outro_text)}':"
            f"fontsize=64:fontcolor=white:bordercolor=#3A6B8C:borderw=4:"
            f"x=(w-text_w)/2:y=h*0.40:enable='gte(t,{final_dur - 5})'"
        )
    if cta_url:
        overlays.append(
            f"drawtext={font_arg}text='{_esc(cta_url)}':"
            f"fontsize=52:fontcolor=#FF6FA5:bordercolor=white:borderw=3:"
            f"x=(w-text_w)/2:y=h*0.55:enable='gte(t,{final_dur - 5})'"
        )

    vf = ",".join(overlays) if overlays else "null"

    # 4. Build the full command — combine video, voice, and music
    out_path = VIDEOS_DIR / out_name
    cmd = ["ffmpeg", "-y", "-i", str(silent), "-i", str(voice_audio)]
    if music_path and music_path.exists():
        cmd += ["-i", str(music_path)]
        # Music at low volume, voice louder, ducking via simple sidechaincompress would be cleaner
        filter_complex = (
            f"[0:v]{vf}[vout];"
            f"[1:a]volume=1.4[voice];"
            f"[2:a]volume=0.18,aloop=loop=-1:size=2e9[music];"
            f"[voice][music]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )
        cmd += [
            "-filter_complex", filter_complex,
            "-map", "[vout]", "-map", "[aout]",
        ]
    else:
        cmd += [
            "-filter_complex", f"[0:v]{vf}[vout]",
            "-map", "[vout]", "-map", "1:a",
        ]

    cmd += [
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(out_path),
    ]

    print(f"[assemble] running ffmpeg ({len(overlays)} overlays, music={'yes' if music_path else 'no'})")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[assemble] FFMPEG FAILED:\n{result.stderr[-2000:]}")
        raise RuntimeError("ffmpeg assembly failed")

    print(f"[assemble] OK -> {out_path} ({out_path.stat().st_size // 1024} KB)")
    return out_path


def _esc(text: str) -> str:
    """Escape text for FFmpeg drawtext."""
    return (text
            .replace("\\", "\\\\")
            .replace("'", "’")  # smart quote
            .replace(":", "\\:")
            .replace(",", "\\,")
            .replace("%", "\\%"))


if __name__ == "__main__":
    print("This module is called by run.py. See README.")
