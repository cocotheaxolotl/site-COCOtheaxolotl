# YouTube Pipeline — Coco the Axolotl (acquisition shorts)

Pipeline automatisé de **shorts d'acquisition** pour vendre les livres Coco the Axolotl sur Amazon / cocotheaxolotl.org.

**Même logique que le pipeline univers.studio** (shorts → trafic → conversion), mais cible parents 25-45 au lieu de créateurs KDP.

## Comparaison avec univers.studio

| Aspect | univers.studio | Coco |
|--------|----------------|------|
| Cible | Créateurs KDP, side-hustlers | Parents 25-45 |
| Pain point | "Je perds de l'argent / temps" | "Mon enfant dort pas / pose des questions difficiles" |
| Hook | Money/jealousy/anger | Validation de douleur parentale + curiosité |
| Reveal | Outil web univers.studio | Livre Coco |
| CTA | univers.studio/{tool} (free trial) | Amazon link / cocotheaxolotl.org (achat livre) |
| Voix | Punchy/agressive | Confiante mom-to-mom (Dorothy/Christine) |

## Stack

- **Scripts** : Claude API
- **Hook + B-roll par scène** : Fal.ai Kling 2.5 (parent fatigué, enfant qui dort, livre révélé)
- **Voix off** : ElevenLabs (Dorothy EN / Christine FR — settings expressifs, pas narrateur bedtime)
- **Assemblage** : FFmpeg (overlays texte + audio mix)
- **Publication** : YouTube Data API v3 (chaîne Coco)

## Workflow

```bash
pip install -r requirements.txt
cp config/.env.example config/.env  # remplir clés API
# Télécharger config/youtube_oauth.json depuis Google Cloud (Desktop OAuth)

python src/run.py coco-cant-sleep en bedtime
# → script (Claude) → hook clip → B-roll clips par scène → voix → mp4 final
# → output/videos/coco-cant-sleep_en_bedtime_<timestamp>.mp4

python src/youtube_upload.py output/videos/coco-cant-sleep_en_bedtime_*.mp4 "Title" "Description" "tag1,tag2"
```

## Angles disponibles

- **bedtime** — pain "kid won't sleep" → Coco Can't Sleep solves it
- **love** — pain "kid won't say I love you" / parent ne sait pas répondre → I Love You More
- **curiosity** — kid pose 1000 questions → Whose Egg Is This (livre interactif)
- **discovery** — framing "le livre que personne ne connaît mais qui marche"

## Books configurés

- `coco-cant-sleep` — Coco Can't Sleep Tonight!
- `i-love-you-more` — I Love You More
- `whose-egg-is-this` — Whose Egg Is This?

Pour ajouter un livre : créer `config/books/<slug>.json` avec `amazon_url` et `target_keywords`.

## Coût indicatif par short

- Claude script : ~0,02 $
- Fal.ai Kling : 1 hook (5s) + 3 B-roll scenes (5s) ≈ 4 × 0,15 $ = **0,60 $**
- ElevenLabs voice : ~0,03 $
- **Total : ~0,65 $/short**
