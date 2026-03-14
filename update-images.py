"""
update-images.py
----------------
Lance ce script après avoir ajouté des images dans puzzle/images/
Il met à jour puzzle/images/index.json automatiquement.

Usage : double-clique dessus, ou dans un terminal :
    python update-images.py
"""
import os, json, sys

sys.stdout.reconfigure(encoding='utf-8')

BASE   = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.join(BASE, 'puzzle', 'images')
EXTS   = {'.jpg', '.jpeg', '.png', '.webp'}

images = sorted([
    f for f in os.listdir(FOLDER)
    if os.path.splitext(f)[1].lower() in EXTS
])

out = os.path.join(FOLDER, 'index.json')
with open(out, 'w', encoding='utf-8') as f:
    json.dump(images, f, ensure_ascii=False, indent=2)

print(f'✅ {len(images)} images dans puzzle/images/index.json')
for img in images:
    print(f'   • {img}')

print('\nN\'oublie pas de faire un git add + commit + push !')
input('\nAppuie sur Entrée pour fermer...')
