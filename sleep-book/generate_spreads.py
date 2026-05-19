#!/usr/bin/env python3
"""
Genere les images de spreads (couverture seule + paires de pages cote a cote)
pour le flipbook web, identiques a celles utilisees dans la video YouTube.

Output:
  sleep-book/spreads-fr/cover.jpg, spread_01.jpg, ..., credits.jpg
  sleep-book/spreads-en/cover.jpg, spread_01.jpg, ..., credits.jpg
"""

import subprocess, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))

BG = '0x1a1a4e'
VW, VH = 1920, 1080
PW = 840

SCENES = [
    ('cover',     [1]),
    ('spread_01', [2, 3]),
    ('spread_02', [4, 5]),
    ('spread_03', [6, 7]),
    ('spread_04', [8, 9]),
    ('spread_05', [10, 11]),
    ('spread_06', [12, 13]),
    ('spread_07', [14, 15]),
    ('spread_08', [16, 17]),
    ('spread_09', [18, 19]),
    ('spread_10', [20, 21]),
    ('spread_11', [22, 23]),
    ('spread_12', [24, 25]),
    ('spread_13', [26, 27]),
    ('spread_14', [28, 29]),
    ('credits',   [30, 31]),
]

VARIANTS = {
    'fr': {
        'img_dir': os.path.join(BASE, 'Coco-ne-dort-pas-ce-soir-FR-sleep-book'),
        'cover':   os.path.join(BASE, '..', 'LIVRES COCO', "Coco Can't Sleep Tonight!",
                                'FR Coco-ne-dort-pas-ce-soir-FR-8.5x11-spreads-V5',
                                'FR 1ere de couv coco ne dort pas ce soir 4K.jpeg'),
        'out':     os.path.join(BASE, 'spreads-fr'),
    },
    'en': {
        'img_dir': os.path.join(BASE, 'Coco-doesnt-sleep-tonight-EN-sleep-book'),
        'cover':   os.path.join(BASE, '..', 'LIVRES COCO', "Coco Can't Sleep Tonight!",
                                "EN Coco can't sleep tonight",
                                'EN 1ere couv coco cant sleep tonight 4K.png'),
        'out':     os.path.join(BASE, 'spreads-en'),
    },
}


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"ERREUR: {r.stderr[-800:]}")
        sys.exit(1)


def img(variant, n):
    v = VARIANTS[variant]
    if n == 1:
        return v['cover']
    return os.path.join(v['img_dir'], f'Diapositive{n}.JPG')


def make_spread(variant, pages, out_path):
    if len(pages) == 1:
        run(['ffmpeg', '-y', '-i', img(variant, pages[0]),
             '-vf', f'scale={PW}:{VH},pad={VW}:{VH}:(ow-iw)/2:0:color={BG}',
             '-q:v', '2', '-frames:v', '1', out_path])
    else:
        run(['ffmpeg', '-y', '-i', img(variant, pages[0]), '-i', img(variant, pages[1]),
             '-filter_complex',
             f'[0]scale={PW}:{VH}[l];[1]scale={PW}:{VH}[r];'
             f'color=c={BG}:s={VW}x{VH}:d=1[bg];'
             f'[bg][l]overlay=120:0[tmp];'
             f'[tmp][r]overlay=960:0',
             '-q:v', '2', '-frames:v', '1', out_path])


def main():
    for variant in ('fr', 'en'):
        out_dir = VARIANTS[variant]['out']
        os.makedirs(out_dir, exist_ok=True)
        print(f"\n[{variant.upper()}] -> {out_dir}")
        for name, pages in SCENES:
            out_path = os.path.join(out_dir, f'{name}.jpg')
            print(f"  {name}: pages {pages}")
            make_spread(variant, pages, out_path)
    print("\nFAIT.")


if __name__ == '__main__':
    main()
