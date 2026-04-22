#!/usr/bin/env python3
"""
Generate YouTube video for: Coco-ne-dort-pas-ce-soir-FR-8.5x11-spreads-V5
Usage: python make_video.py
"""

import subprocess, os, sys, shutil

BASE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE, 'images')
AUDIO_DIR = os.path.join(BASE, 'audio')
OUT_DIR = os.path.join(BASE, 'youtube')
TMP = os.path.join(OUT_DIR, 'tmp')

BG = '0x1a1a4e'
VW, VH = 1920, 1080
FPS = 24
LULLABY_VOL = 0.15
FADE_S = 4
FADE_IN_S = 2

# (name, page_numbers, audio_file)
SCENES = [
    ('cover',     [1],      'spread_title.mp3'),
    ('spread_01', [2, 3],  'spread_01.mp3'),
    ('spread_02', [4, 5],  'spread_02.mp3'),
    ('spread_03', [6, 7],  'spread_03.mp3'),
    ('spread_04', [8, 9],  'spread_04.mp3'),
    ('spread_05', [10, 11],  'spread_05.mp3'),
    ('spread_06', [12, 13],  'spread_06.mp3'),
    ('spread_07', [14, 15],  'spread_07.mp3'),
    ('spread_08', [16, 17],  'spread_08.mp3'),
    ('spread_09', [18, 19],  'spread_09.mp3'),
    ('spread_10', [20, 21],  'spread_10.mp3'),
    ('spread_11', [22, 23],  'spread_11.mp3'),
    ('spread_12', [24, 25],  'spread_12.mp3'),
    ('spread_13', [26, 27],  'spread_13.mp3'),
    ('spread_14', [28, 29],  'spread_14.mp3'),
    ('spread_15', [30, 31],  'spread_15.mp3'),
    ('credits',   [32,33], 'spread_credits.mp3'),
]

LULLABY = os.path.join(AUDIO_DIR, 'lullaby.mp3')


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"ERREUR: {r.stderr[:500]}")
        sys.exit(1)
    return r


def duration(path):
    r = run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'csv=p=0', path])
    return float(r.stdout.strip())


def img(n):
    return os.path.join(IMG_DIR, f'page-{n}.jpg')


def make_spread(pages, out):
    if len(pages) == 1:
        run(['ffmpeg', '-y', '-i', img(pages[0]),
             '-vf', f'scale=-1:{VH},pad={VW}:{VH}:(ow-iw)/2:0:color={BG}',
             '-frames:v', '1', out])
    else:
        run(['ffmpeg', '-y', '-i', img(pages[0]), '-i', img(pages[1]),
             '-filter_complex',
             f'[0]scale=-1:{VH}[l];[1]scale=-1:{VH}[r];'
             f'color=c={BG}:s={VW}x{VH}:d=1[bg];'
             f'[bg][l]overlay=120:0[tmp];[tmp][r]overlay=960:0',
             '-frames:v', '1', out])


def make_segment(img_path, dur, out):
    run(['ffmpeg', '-y', '-loop', '1', '-i', img_path,
         '-t', str(dur),
         '-vf', f'fps={FPS},format=yuv420p',
         '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
         '-pix_fmt', 'yuv420p', out])


def main():
    os.makedirs(TMP, exist_ok=True)
    print("=" * 50)
    print("  Coco-ne-dort-pas-ce-soir-FR-8.5x11-spreads-V5 - YouTube Video")
    print("=" * 50, "\n")

    # 1. Audio durations
    print("[1/6] Durees audio...")
    durs = []
    audio_files = []
    for name, pages, af in SCENES:
        p = os.path.join(AUDIO_DIR, af)
        if not os.path.exists(p):
            print(f"  MANQUANT: {p}")
            sys.exit(1)
        d = duration(p)
        durs.append(d)
        audio_files.append(p)
        print(f"  {name:12s} {d:6.1f}s")

    total_narr = sum(durs)
    total_vid = total_narr + FADE_S
    print(f"  Total: {total_vid:.0f}s ({total_vid/60:.1f} min)\n")

    # 2. Spread images
    print("[2/6] Images des spreads...")
    spread_imgs = []
    for i, (name, pages, _) in enumerate(SCENES):
        out = os.path.join(TMP, f'spread_{i:02d}.png')
        make_spread(pages, out)
        spread_imgs.append(out)
        print(f"  {name}")
    print()

    # 3. Video segments
    print("[3/6] Segments video...")
    segments = []
    for i, ((name, pages, af), d) in enumerate(zip(SCENES, durs)):
        seg = os.path.join(TMP, f'seg_{i:02d}.mp4')
        make_segment(spread_imgs[i], d, seg)
        segments.append(seg)
        print(f"  seg_{i:02d}.mp4  ({d:.1f}s)")

    seg_fade = os.path.join(TMP, 'seg_fade.mp4')
    make_segment(spread_imgs[-1], FADE_S, seg_fade)
    segments.append(seg_fade)
    print(f"  seg_fade.mp4 ({FADE_S}s)\n")

    # 4. Concatenate video
    print("[4/6] Assemblage video...")
    seg_list = os.path.join(TMP, 'segments.txt')
    with open(seg_list, 'w') as f:
        for s in segments:
            f.write(f"file '{s.replace(os.sep, '/')}'\n")

    raw_vid = os.path.join(TMP, 'raw_video.mp4')
    run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', seg_list,
         '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
         '-pix_fmt', 'yuv420p', raw_vid])

    vid = os.path.join(TMP, 'video.mp4')
    run(['ffmpeg', '-y', '-i', raw_vid,
         '-vf', f'fade=t=in:d={FADE_IN_S},fade=t=out:st={total_vid - FADE_S}:d={FADE_S}',
         '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
         '-pix_fmt', 'yuv420p', vid])
    print("  OK\n")

    # 5. Audio mix
    print("[5/6] Audio (narration + musique)...")
    alist = os.path.join(TMP, 'audio_list.txt')
    with open(alist, 'w') as f:
        for p in audio_files:
            f.write(f"file '{p.replace(os.sep, '/')}'\n")

    narr = os.path.join(TMP, 'narration.wav')
    run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', alist,
         '-ar', '44100', '-ac', '2', narr])

    mixed = os.path.join(TMP, 'mixed.aac')
    narr_dur = duration(narr)
    mix_dur = narr_dur + FADE_S
    run(['ffmpeg', '-y',
         '-i', narr,
         '-stream_loop', '-1', '-i', LULLABY,
         '-filter_complex',
         f'[1]volume={LULLABY_VOL}[bg];'
         f'[0]apad=pad_dur={FADE_S}[nr];'
         f'[nr][bg]amix=inputs=2:duration=first:normalize=0[mx];'
         f'[mx]afade=t=out:st={narr_dur}:d={FADE_S}',
         '-t', str(mix_dur),
         '-c:a', 'aac', '-b:a', '192k', mixed])
    print("  OK\n")

    # 6. Final
    print("[6/6] Export final...")
    final = os.path.join(OUT_DIR, 'coco-ne-dort-pas-ce-soir-fr-8-5x11-spreads-v5.mp4')
    run(['ffmpeg', '-y',
         '-i', vid, '-i', mixed,
         '-c:v', 'copy', '-c:a', 'copy',
         '-shortest', final])

    sz = os.path.getsize(final) / (1024 * 1024)
    print(f'\n{"=" * 50}')
    print(f'  TERMINE !')
    print(f'  Fichier : {final}')
    print(f'  Taille  : {sz:.0f} MB')
    print(f'  Duree   : ~{total_vid / 60:.1f} min')
    print(f'{"=" * 50}')

    shutil.rmtree(TMP)
    print("Fichiers temporaires supprimes.")


if __name__ == '__main__':
    main()