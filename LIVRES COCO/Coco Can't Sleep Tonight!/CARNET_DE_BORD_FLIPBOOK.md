# Carnet de bord - Flipbook Audio "Coco ne dort pas ce soir !"

> Document de reference pour automatiser la production des prochains livres.
> Derniere mise a jour : 20 fevrier 2026

---

## REGLE ABSOLUE

> **NE JAMAIS ecraser les modifications manuelles faites dans PowerPoint.**
>
> Apres generation du PPTX par le script, l'utilisateur fait des ajustements manuels
> dans PowerPoint (taille des images, position, arriere-plans, etc.).
> Si le script doit etre modifie (ex: ajout des italiques), NE PAS regenerer le PPTX
> depuis zero. A la place :
> 1. Modifier le PPTX existant en place avec python-pptx (ouvrir, modifier, sauvegarder)
> 2. OU prevenir l'utilisateur que la regeneration ecrasera ses modifications manuelles
> 3. OU noter toutes les modifications manuelles dans ce carnet AVANT de regenerer
>
> Erreur commise : regeneration du PPTX pour ajouter les dialogues en italique,
> ce qui a ecrase les arriere-plans nuit etoilee et les tailles d'images ajustees manuellement.
>
> Erreur commise (bis) : lancement du script de generation SANS demander confirmation,
> ecrasant a nouveau le fichier PPTX. TOUJOURS demander confirmation avant toute action
> qui modifie ou ecrase un fichier existant.
>
> **VERSIONNEMENT OBLIGATOIRE** : Toujours generer les PPTX en V1, V2, V3, etc.
> Ne JAMAIS ecraser un fichier existant. Exemple :
> - `Coco-ne-dort-pas-V1.pptx`
> - `Coco-ne-dort-pas-V2.pptx`
> - `Coco-ne-dort-pas-V3.pptx`
>
> **NE TOUCHER QUE CE QUI EST DEMANDE** : Si l'utilisateur demande un changement de texte
> (ex: guillemets -> tirets), ne modifier QUE le texte dans le PPTX existant avec python-pptx.
> Ne PAS regenerer tout le fichier depuis le script. Ne PAS toucher aux images, positions,
> tailles, ou quoi que ce soit d'autre que ce qui a ete explicitement demande.
>
> **LIBERTE DE CREATION** : Ne JAMAIS verrouiller le formatage dans le PPTX genere.
> L'utilisateur doit pouvoir modifier librement couleurs, polices, tailles, positions
> dans PowerPoint apres generation. Le script doit definir les styles uniquement via
> `defRPr` (proprietes par defaut du paragraphe) et NE PAS forcer les proprietes
> dans `rPr` (proprietes de chaque run). Respecter la liberte de creation.

---

## Table des matieres

1. [Pipeline generale](#1-pipeline-generale)
2. [Du PPTX aux images](#2-du-pptx-aux-images)
3. [Voix et TTS (edge-tts)](#3-voix-et-tts-edge-tts)
4. [Pitch des animaux](#4-pitch-des-animaux)
5. [Effets sonores (SFX)](#5-effets-sonores-sfx)
6. [Assemblage audio par spread](#6-assemblage-audio-par-spread)
7. [Le player HTML/JS](#7-le-player-htmljs)
8. [Problemes rencontres et solutions](#8-problemes-rencontres-et-solutions)
9. [Checklist pour le prochain livre](#9-checklist-pour-le-prochain-livre)
10. [Fichiers et structure](#10-fichiers-et-structure)

---

## 1. Pipeline generale

```
PPTX (python-pptx)
  |
  v
Export JPG (32 pages : 30 + 1 intro + 1 page site internet)
  |
  v
narrations_multi.json (texte segmente par personnage)
  |
  v
TTS edge-tts (1 fichier MP3 par segment, par voix)
  |
  v
Pitch shift ffmpeg (segments animaux uniquement)
  |
  v
Insertion SFX (bruits d'animaux avant la 1ere replique)
  |
  v
Concatenation segments -> spread_XX.mp3
  |
  v
Ralentissement global atempo=0.9
  |
  v
index.html (flipbook avec player audio synchronise)
```

---

## 2. Du PPTX aux images

### Script de generation PPTX

- **Script** : `generate-sleep-book-pptx.py`
- **Librairie** : `python-pptx` + `lxml`
- **Dimensions** : 8.75" x 11.25" (8.5x11 + 0.125" bleed)
- **Version courante** : V5 (32 pages)
- **Pages ajoutees manuellement** : 1 page d'intro + 1 page site internet (fin)

### Polices et couleurs

| Element          | Police              | Taille | Couleur              |
|------------------|---------------------|--------|----------------------|
| Titre couverture | Berlin Sans FB Demi | 48pt   | #D6006E (rose fonce) |
| Titres chapitres | Berlin Sans FB Demi | 36pt   | #3D3D8E (bleu doux)  |
| Texte corps      | Berlin Sans FB Demi | 28pt   | #000000 (noir)       |
| Credits/pages    | Berlin Sans FB Demi | 12pt   | #AAAAAA (gris)       |
| Boite "Le savais-tu?" | Berlin Sans FB Demi | 24pt | #000080 (bleu marine) sur fond #E8EAF6, bordure #7B7FC4 |
| Dialogues (tiret cadratin —) | Berlin Sans FB Demi | meme taille | meme couleur, style normal |

### Formatage des dialogues

- Les dialogues utilisent le **tiret cadratin** — (pas de guillemets « »)
- Pas d'italique sur les dialogues, tout est en style normal
- Chaque replique commence par — **suivi d'un espace** (ex: `— Maman`, pas `—Maman`)
- La fonction `tbox()` affiche le texte tel quel, sans formatage special

### Arriere-plans

| Type de page     | Arriere-plan                                    |
|------------------|-------------------------------------------------|
| Pages de texte   | `fond_nuit_étoilee.png` (843x1264, lavande clair avec etoiles) |
| Pages illustration | Image pleine page (etirée pour remplir la page) |
| Page copyright   | Fond uni blanc (pas de bg image)                |

- Le fond `fond_nuit_étoilee.png` est assez clair pour que le texte noir soit lisible dessus
- Le fond `nuit-étoilée-noire.png` (1024x1536, violet saturé) est trop foncé pour du texte
- Les illustrations 1024x1536 (ratio 2:3) sont étirées pour remplir la page 8.75x11.25 (ratio ~7:9)
- L'utilisateur ajuste manuellement les tailles d'images dans PowerPoint apres generation

### ATTENTION - Police Berlin Sans FB Demi
- Doit etre installee sur le systeme pour que le PPTX s'affiche correctement
- Si elle manque, PowerPoint la remplace par une police par defaut (Arial)
- Police Windows native (incluse avec Microsoft Office)

### Export des images

- Export depuis PowerPoint : Fichier > Exporter > Images JPEG
- Nommage : `page_01.jpg` a `page_30.jpg`
- Taille : 175-288 KB par image (bonne compression web)
- 30 pages = 15 spreads (2 pages par spread)
- Spread N = `page_(2N+1).jpg` (gauche) + `page_(2N+2).jpg` (droite)

### Illustrations sources (DALL-E via ChatGPT)

- Prompts stockes dans `chatgpt-prompts-sleep.md`
- Format : PNG, ~2.8-3 MB chacune
- 15 illustrations + couverture avant/arriere + fond texte
- Style : cartoon doux, couleurs pastels, fond nuit etoilee

---

## 3. Voix et TTS (edge-tts)

### Moteur TTS

- **Outil** : `edge-tts` (Microsoft Edge TTS, gratuit, hors-ligne)
- **Commande** : `python -m edge_tts --voice VOIX --text "texte" --write-media output.mp3`
- **ATTENTION** : `edge-tts` en ligne de commande directe (`edge-tts ...`) ne fonctionne PAS sous Windows, utiliser `python -m edge_tts`
- **Format sortie** : MP3, 24000 Hz, mono (IMPORTANT pour le pitch shift !)

### Assignation des voix

| Personnage | Code | Voix edge-tts                        | Notes                          |
|------------|------|--------------------------------------|--------------------------------|
| Narratrice | N    | fr-FR-VivienneMultilingualNeural     | Belle voix, MAIS probleme de langue sur phrases courtes |
| Coco       | C    | fr-FR-EloiseNeural                   | Voix d'enfant, parfaite        |
| Maman      | M    | fr-FR-DeniseNeural                   | Voix douce, maternelle         |
| Animaux    | A    | fr-CA-SylvieNeural                   | Canadienne, differencie des FR |

### PROBLEME CRITIQUE : VivienneMultilingualNeural et l'italien

VivienneMultilingualNeural est **multilingue** et confond le francais avec l'italien sur les phrases courtes :

| Phrase problematique        | Spread | Ce qu'elle dit                |
|-----------------------------|--------|-------------------------------|
| "La Loutre."                | 05     | Prononce a l'italienne        |
| "La Chauve-Souris."         | 07     | Prononce a l'italienne        |
| "Maman ria."                | 01     | "ria" = mot italien           |
| "Coco sourit."              | 05     | Accent bizarre                |
| "Maman Axolotl."            | 12     | Prononce a l'italienne        |
| "Illustrations de Loupineki"| 00     | "de" sonne comme "zene"       |
| "Le flamant vacilla."       | 10     | "vacilla" = mot italien       |

### SOLUTION : Forcer DeniseNeural pour ces segments

```python
FORCE_DENISE = {
    (0, 1),   # "Une aventure de Coco l'Axolotl..."
    (1, 5),   # "Maman ria."
    (5, 0),   # "La Loutre."
    (5, 4),   # "Coco sourit."
    (7, 0),   # "La Chauve-Souris."
    (10, 5),  # "Le flamant vacilla."
    (12, 0),  # "Maman Axolotl."
}
```

### REGLE POUR LES PROCHAINS LIVRES

> Toute phrase de narrateur de moins de ~5 mots, ou contenant des mots
> qui existent en italien/espagnol/portugais, DOIT etre generee avec
> DeniseNeural au lieu de VivienneMultilingualNeural.
>
> Mots a surveiller : ria, sourit, vacilla, et tout nom propre inventé.

### Prononciation des noms propres

- "Loupinneki" -> "Loupineki" (avec accent aigu) pour forcer la prononciation francaise
- Les noms inventés sont souvent prononces avec un accent italien par Vivienne
- "Loupinéki" (accent aigu) -> prononce "loopi-NE-ki" au lieu de "loopi-ne-ky"
- "Loupineky" (sans accent, y final) -> prononce correctement "loopi-ne-ky"
- Solution : adapter l'orthographe dans le JSON de narration (pas dans le texte du livre) jusqu'a obtenir la bonne prononciation

### Vitesse de parole (atempo)

| Element            | atempo | Effet                        |
|--------------------|--------|------------------------------|
| Titre du livre     | 0.825  | Legerement ralenti (majestueux) |
| Sous-titre         | 0.9    | Legerement ralenti           |
| Tout le reste      | 0.9    | Global, applique au spread final |

- atempo < 1 = plus lent, atempo > 1 = plus rapide
- On applique 0.9 globalement a chaque spread pour un rythme de lecture enfantine

---

## 4. Pitch des animaux

### Objectif
Differencier la voix de chaque animal par le pitch (tonalité) pour que l'enfant reconnaisse qui parle, tout en gardant la meme voix TTS (SylvieNeural).

### Configuration pitch (en demi-tons)

```python
ANIMAL_PITCH = {
    3:  -1.5,   # Hibou     : grave, sage
    4:  +2.0,   # Dauphin   : aigu, enjoue
    5:  +1.0,   # Loutre    : douce, legere
    6:  -1.0,   # Koala     : lent, endormi
    7:  +1.5,   # Chauve-S. : vive, rapide
    8:   0.0,   # Chat      : normal (pas de pitch)
    9:  -0.5,   # Cheval    : pose, calme
    10: +1.0,   # Flamant   : leger, elegant
    11: -2.0,   # Paresseux : grave et lent
}
```

### PROBLEME CRITIQUE : Taux d'echantillonnage pour le pitch shift

Le pitch shift utilise `ffmpeg asetrate + aresample + atempo`. La formule doit utiliser le **taux d'echantillonnage reel du fichier source** :

```
edge-tts sort a 24000 Hz  (PAS 44100 Hz !)
```

### Formule CORRECTE

```python
orig_sr = 24000  # Taux reel de edge-tts
rate_factor = 2 ** (semitones / 12.0)
new_rate = int(orig_sr * rate_factor)
atempo_comp = 1.0 / rate_factor

ffmpeg -i input.mp3 \
  -af "asetrate={new_rate},aresample={orig_sr},atempo={atempo_comp}" \
  -codec:a libmp3lame -b:a 192k output.mp3
```

### ERREUR FATALE A NE JAMAIS REFAIRE

Si on utilise `asetrate=44100*factor` alors que le fichier est a 24000 Hz :
- Le pitch est DOUBLE (ex: -1.5st devient -3st)
- La duree est DIVISEE PAR DEUX
- Les animaux parlent en accelere, inintelligibles

### Verification
Apres pitch shift, la duree du fichier doit etre ~identique a l'original (ecart < 2%).
Si l'ecart est > 5%, le taux d'echantillonnage est probablement faux.

```python
# TOUJOURS verifier le sample rate avant de pitcher
def get_sample_rate(path):
    r = subprocess.run(['ffprobe','-v','quiet',
        '-show_entries','stream=sample_rate','-of','csv=p=0', path],
        capture_output=True, text=True)
    return int(r.stdout.strip())
```

---

## 5. Effets sonores (SFX)

### Source
- Compte Envato Elements (sons d'animaux royalty-free)
- Format source : WAV ou MP3 haute qualite

### Fichiers SFX utilises

| Animal   | Spread | Fichier source (Envato)                         | Extraction      |
|----------|--------|--------------------------------------------------|-----------------|
| Hibou    | 03     | `OwlGreatHornedHoot AT083001.wav`                | 1.9s - 3.65s (2 derniers houlements sur 3) |
| Dauphin  | 04     | `DolphinChirpsVocal PE024601.wav`                | 1.1s - 3.1s (chirps) |
| Chat     | 08     | `Cat 4.mp3`                                      | 0s - 0.85s (miaulement court) |
| Cheval   | 09     | `ANML_HorsesMillWhinny_SDLX.wav`                | 8.3s - 10.5s (hennissement) |
| Rire Maman | 01   | `young woman laugh 3.wav`                        | Fichier complet (~2s) |

### Pipeline de normalisation SFX

Les sons bruts Envato sont souvent BEAUCOUP trop faibles par rapport au TTS.

#### Methode qui FONCTIONNE : `loudnorm` (EBU R128)

```bash
# 1. Extraire le clip
ffmpeg -i source.wav -ss 8.3 -to 10.5 -ac 1 clip.wav

# 2. Normaliser avec loudnorm
ffmpeg -i clip.wav \
  -af "loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=in:d=0.05,afade=t=out:st=1.9:d=0.3" \
  normalized.wav

# 3. Convertir en MP3
ffmpeg -i normalized.wav -codec:a libmp3lame -b:a 192k sfx.mp3
```

- Cible : `-16 LUFS` (standard pour la parole)
- Volume resultant : ~-19 dB mean, ~-4 dB max (bien audible)
- Ajouter fade in/out pour eviter les clics

#### Methode qui a ECHOUE : `dynaudnorm`

```bash
# NE PAS UTILISER pour les SFX !
ffmpeg -i source.wav -af dynaudnorm normalized.wav
```

- `dynaudnorm` a produit -91 dB pour le cheval (completement silencieux)
- Fonctionne parfois (hibou, dauphin, chat) mais pas fiable
- Probleme : dynaudnorm est concu pour normaliser de longs fichiers, pas des clips courts

#### Methode qui a partiellement echoue : boost de volume

```bash
# Resultat : son "boop" deforme
ffmpeg -i clip.wav -af "volume=35dB" boosted.wav
```

- Trop de boost = distorsion
- Pas assez = toujours inaudible
- `loudnorm` est la meilleure solution universelle

### REGLE POUR LES PROCHAINS LIVRES

> Toujours utiliser `loudnorm=I=-16:TP=-1.5:LRA=11` pour normaliser les SFX.
> Toujours verifier le volume avec `volumedetect` : mean doit etre entre -25 et -15 dB.
> Si mean < -30 dB, le son sera inaudible mele au TTS.

### Placement des SFX

Le SFX est insere **avant** la premiere replique de l'animal dans le spread :

```
[Narrateur: titre] [Narrateur: description] [Coco: question] [SFX] [Animal: reponse] ...
```

Pas de SFX pour : loutre, koala, chauve-souris, flamant, paresseux (pas de son caracteristique court).

### IMPORTANT : Supprimer l'onomatopee du texte TTS quand il y a un SFX

Si un SFX remplace une onomatopee (ex: "Hou, hou !" pour le hibou), il faut
SUPPRIMER l'onomatopee du texte dans narrations_multi.json. Sinon le TTS dit
"Hou hou" ET le SFX joue le vrai hululement = doublon bizarre.

Exemple hibou : "Hou, hou ! Je suis nocturne..." -> "Je suis nocturne..."

### Remplacer une narration par un SFX

Quand un narrateur decrit une reaction (ex: "Maman ria."), on peut remplacer le
segment TTS par un vrai son (ex: rire de femme). Cela rend l'histoire plus vivante.

- Normaliser le SFX avec loudnorm comme les bruits d'animaux
- Le placer a la position du segment narrateur qu'il remplace
- Supprimer le segment narrateur de l'assemblage

### Interruptions (couper la parole)

Pour qu'un personnage coupe la parole a un autre :
1. Generer le segment du 1er personnage normalement
2. Couper le silence a la fin avec `silenceremove` (technique reverse) :
```bash
ffmpeg -i maman.mp3 \
  -af "areverse,silenceremove=start_periods=1:start_silence=0.05:start_threshold=-35dB,areverse" \
  maman_trimmed.mp3
```
3. Concatener directement avec le segment suivant (pas de silence entre les deux)
- Resultat : le 2e personnage "enchaine" immediatement, effet d'interruption naturel
- Spread 01 : Maman dit "Compte les moutons et..." (trimme 840ms) -> Coco enchaine "Mais Maman..."

### Expression par pitch shift

Pour rendre une replique plus expressive (sans SSML, qui ne marche pas avec edge-tts) :
- Pitch up de +0.5 a +1.0 st = ton incredule/joueur (enfant qui retorque)
- Pitch down de -0.5 a -1.0 st = ton calme/sage
- Toujours utiliser le bon sample rate (24000 Hz pour edge-tts)

Exemple : Coco retorque "les moutons ne savent pas nager !" -> pitch +0.8st

---

## 6. Assemblage audio par spread

### Architecture : un MP3 par spread (PAS un seul MP3 global)

Le flipbook utilise **15 fichiers MP3 independants** (`spread_00.mp3` a `spread_14.mp3`).

#### Pourquoi pas un seul MP3 ?
- Un MP3 concatene de 15 spreads avait un **drift temporel cumulatif** de ~0.8s
- Les pages tournaient avant la fin de la narration
- Impossible de corriger avec des timestamps car le drift augmente au fil du fichier

### Etapes d'assemblage par spread

```python
# 1. Lister les segments dans l'ordre
segments = []
for seg_idx, (role, text) in enumerate(spread['segments']):
    if role == 'A' and first_animal and spread in SFX_MAP:
        segments.append(SFX_FILE)        # Inserer SFX avant 1er animal

    if role == 'A' and pitch != 0:
        segments.append(f"{seg_name}_fx.mp3")   # Version pitchee
    else:
        segments.append(f"{seg_name}.mp3")       # Version normale

# 2. Concatener avec ffmpeg filter_complex
# NE PAS utiliser le concat demuxer si le chemin contient une apostrophe !
ffmpeg -i seg1.mp3 -i seg2.mp3 -i seg3.mp3 \
  -filter_complex "[0:a][1:a][2:a]concat=n=3:v=0:a=1[out]" \
  -map "[out]" -codec:a libmp3lame -b:a 192k spread_raw.mp3

# 3. Appliquer ralentissement global
ffmpeg -i spread_raw.mp3 -af "atempo=0.9" \
  -codec:a libmp3lame -b:a 192k spread_XX.mp3
```

### Cas special : spread_00 (couverture)

Le titre et le sous-titre ont des vitesses differentes :

```python
# Titre "Coco ne dort pas ce soir !" -> atempo 0.825 (lent, majestueux)
# Sous-titre "Une aventure de..." -> atempo 0.9 (normal ralenti)
# Concatener les deux apres application individuelle
```

### Cas special : spread_01 (Maman interrompue par Coco)

Maman dit "Compte les moutons et..." et Coco l'interrompt avec "Mais Maman, les moutons ne savent pas nager !"
- Le silence a la fin du segment de Maman a ete coupe (trimmed) pour que l'interruption soit naturelle

### PROBLEME : Concatenation binaire vs filter_complex

```bash
# NE PAS FAIRE - concatenation binaire
copy /b seg1.mp3+seg2.mp3+seg3.mp3 spread.mp3
# ou
cat seg1.mp3 seg2.mp3 > spread.mp3
```

Cela fonctionne avec les MP3 bruts d'edge-tts, mais **echoue** avec les MP3 traites par ffmpeg (headers VBR differents). Toujours utiliser `filter_complex concat`.

### PROBLEME : Apostrophe dans les chemins

Le chemin `Coco Can't Sleep Tonight!` contient une apostrophe ET un point d'exclamation :
- L'apostrophe casse le **concat demuxer** de ffmpeg (fichier de liste .txt)
- Le `!` casse l'**expansion d'historique bash**
- Solution : utiliser des scripts Python avec subprocess au lieu de commandes bash directes
- Solution alternative : utiliser `filter_complex concat` au lieu du concat demuxer

---

## 7. Le player HTML/JS

### Architecture

- **Fichier unique** : `index.html` (tout le HTML + CSS + JS)
- **Pas de dependances externes** (pas de React, pas de jQuery)
- **Responsive** : 800x540px desktop, 95vw mobile

### Animation de page

- CSS 3D avec `transform-style: preserve-3d` + `rotateY`
- Duree : 0.7s avec `cubic-bezier(0.645, 0.045, 0.355, 1)`
- Overlay `.turn-overlay` cree dynamiquement, supprime apres `transitionend`
- Direction : `flip-right` (next) ou `flip-left` (prev)

### Synchronisation audio

```javascript
const durations = [11.16, 23.74, ...];  // 15 durees en secondes

function spreadAudioSrc(sp) {
    return `audio/spread_${String(sp).padStart(2, '0')}.mp3`;
}
```

- Chaque spread charge son propre MP3
- A la fin de l'audio (`ended`), delai de 800ms puis page suivante
- La barre de progression affiche le temps global (somme cumulative)

### Navigation

| Action              | Effet                                         |
|---------------------|-----------------------------------------------|
| Clic fleche droite  | Page suivante + charge audio du nouveau spread |
| Clic fleche gauche  | Page precedente + charge audio                |
| Barre espace        | Play/pause                                     |
| Clic barre progress | Seek dans le spread correspondant             |
| Swipe gauche        | Page suivante (tactile, seuil 50px)           |
| Swipe droite        | Page precedente                               |
| Bouton AUTO         | Active/desactive l'avance automatique          |

### PROBLEME RESOLU : Navigation arriere

Le bug : quand on revenait en arriere, le son ne se synchronisait pas car `currentSpread` n'etait pas encore mis a jour pendant l'animation de 700ms.

Solution : calculer le spread cible AVANT de lancer l'animation :

```javascript
function goPrev() {
    const target = currentSpread - 1;  // Calculer AVANT
    prevPage();                         // Lancer animation
    syncAudioToSpread(target);          // Sync avec le bon spread
}
```

---

## 8. Problemes rencontres et solutions

### Tableau recapitulatif

| # | Probleme | Cause | Solution | Impact |
|---|----------|-------|----------|--------|
| 1 | Pages tournent avant fin narration | Drift cumulatif dans MP3 unique | Architecture per-spread (15 MP3) | CRITIQUE |
| 2 | Vivienne parle italien | Voix multilingue confond phrases courtes | Utiliser DeniseNeural pour segments courts | CRITIQUE |
| 3 | Animaux parlent en accelere | asetrate utilise 44100 au lieu de 24000 | Detecter le sample rate reel du fichier | CRITIQUE |
| 4 | Hennissement inaudible | dynaudnorm produit -91 dB | Utiliser loudnorm (EBU R128) | MAJEUR |
| 5 | Hibou inaudible | Volume source trop faible | loudnorm normalisation | MAJEUR |
| 6 | Hibou fait "boop" | Boost volume +35 dB = distorsion | loudnorm au lieu de volume brut | MINEUR |
| 7 | "Loupinneki" accent italien | Vivienne multilingue | Ecrire "Loupineki" avec accent | MINEUR |
| 8 | Navigation arriere desynchronisee | currentSpread pas a jour pendant animation | Calculer target avant animation | MAJEUR |
| 9 | SSML avec edge-tts | edge-tts lit les tags XML comme du texte | Utiliser ffmpeg pour post-traiter | CRITIQUE |
| 10 | Concatenation binaire echoue | Headers VBR differents apres ffmpeg | Utiliser filter_complex concat | MAJEUR |
| 11 | `!` dans chemin bash | Expansion historique bash | Scripts Python avec subprocess | MINEUR |
| 12 | Double ralentissement animaux | Per-animal rate + global atempo | Supprimer per-animal rate, garder pitch seul | MAJEUR |
| 13 | ElevenLabs trop cher/complex | API payante, voix pas adaptees | Abandonner pour edge-tts gratuit | DECISION |
| 14 | Fonds nuit etoilee et tailles images perdus | Regeneration PPTX depuis le script | NE JAMAIS regenerer sans preserver les modifs manuelles | CRITIQUE |

### Detail des problemes critiques

#### SSML ne fonctionne PAS avec edge-tts

```bash
# CATASTROPHE : edge-tts lit les balises comme du texte !
edge-tts --text '<speak><prosody pitch="+2st">Bonjour</prosody></speak>'
# Resultat : il dit "speak prosody pitch equals plus two st Bonjour /prosody /speak"
# Duree multipliee par 3x
```

**Solution definitive** : NE JAMAIS utiliser de SSML avec edge-tts. Toute modification de pitch/rate doit etre faite en post-traitement avec ffmpeg.

#### Architecture audio : per-spread vs MP3 unique

L'approche initiale (un seul `narration.mp3` avec des timestamps) avait un drift de ~0.8s a la fin du livre car :
- Les timestamps etaient calcules a partir des durees individuelles
- Mais la concatenation MP3 ajoute des micro-silences entre les frames
- Ces micro-silences s'accumulent sur 15 spreads

L'architecture per-spread elimine ce probleme car chaque audio demarre a 0:00.

---

## 9. Checklist pour le prochain livre

### Preparation

- [ ] Illustrations generees (DALL-E ou autre) en PNG haute resolution
- [ ] Texte du livre ecrit et relu
- [ ] Texte segmente par personnage dans `narrations_multi.json`
- [ ] Police Baloo 2 installee sur le systeme

### Generation PPTX

- [ ] Adapter `generate-sleep-book-pptx.py` avec le nouveau contenu
- [ ] Verifier les couleurs et tailles de police
- [ ] Exporter en JPEG (30 pages, `page_01.jpg` a `page_30.jpg`)
- [ ] Verifier que les images font < 300 KB chacune

### Generation audio

- [ ] Identifier les segments courts de narrateur (< 5 mots)
- [ ] Marquer ces segments comme FORCE_DENISE dans le script
- [ ] Verifier les noms propres inventes (ajouter accents si necessaire)
- [ ] Generer tous les segments TTS avec `python -m edge_tts`
- [ ] Verifier le sample rate des fichiers TTS (`ffprobe`)
- [ ] Appliquer pitch shift avec le BON sample rate (24000 Hz pour edge-tts)
- [ ] Verifier que la duree post-pitch est identique a la duree pre-pitch (+/- 2%)

### Effets sonores

- [ ] Chercher les SFX sur Envato Elements
- [ ] Ecouter le fichier complet, reperer la section a extraire (noter ss et to)
- [ ] Extraire avec `ffmpeg -ss X -to Y -ac 1`
- [ ] Normaliser avec `loudnorm=I=-16:TP=-1.5:LRA=11`
- [ ] Verifier avec `volumedetect` : mean entre -25 et -15 dB
- [ ] Ajouter fade in (0.05s) et fade out (0.3s)

### Assemblage

- [ ] Concatener segments avec `filter_complex concat` (PAS binaire)
- [ ] Inserer SFX avant la premiere replique de chaque animal concerne
- [ ] Appliquer atempo=0.9 global (sauf titre : 0.825)
- [ ] Mesurer durees finales avec `ffprobe`
- [ ] Mettre a jour le tableau `durations` dans `index.html`

### Test du flipbook

- [ ] Ecouter CHAQUE spread du debut a la fin
- [ ] Verifier que les pages ne tournent PAS avant la fin de l'audio
- [ ] Verifier la navigation arriere (le son doit se re-synchroniser)
- [ ] Verifier le mode auto-avance
- [ ] Verifier la barre de progression (clic pour seek)
- [ ] Tester sur mobile (swipe, taille responsive)
- [ ] Verifier qu'aucune phrase ne sonne italienne/espagnole
- [ ] Si un SFX remplace une onomatopee, SUPPRIMER l'onomatopee du texte TTS
- [ ] Tester la prononciation des noms propres inventes (ajuster orthographe JSON si besoin)

### Points de vigilance specifiques

- [ ] **NE JAMAIS regenerer le PPTX sans preserver les modifications manuelles**
- [ ] Si modif du script necessaire, modifier le PPTX existant en place (python-pptx open/save)
- [ ] Pas d'apostrophe ni de `!` dans les chemins de fichiers (ou utiliser Python)
- [ ] Ne JAMAIS utiliser SSML avec edge-tts
- [ ] Ne JAMAIS utiliser dynaudnorm pour normaliser des clips courts
- [ ] Toujours utiliser `filter_complex concat`, jamais concatenation binaire
- [ ] Toujours verifier le sample rate avant pitch shift
- [ ] Toujours generer les segments avec le BON executable : `python -m edge_tts` (pas `edge-tts` direct sous Windows)

---

## 10. Fichiers et structure

### Arborescence du projet

```
Coco Can't Sleep Tonight!/
|
|-- generate-sleep-book-pptx.py          Script de generation PPTX
|-- Coco-ne-dort-pas-ce-soir-FR-8.5x11-spreads.pptx   PPTX genere (49 MB)
|-- Coco-ne-dort-pas-ce-soir.epub        EPUB (96 MB)
|-- narration-FR.txt                     Texte brut FR
|-- narration-EN.txt                     Texte brut EN
|-- chatgpt-prompts-sleep.md             Prompts DALL-E pour illustrations
|-- couverture en FR.png                 Couverture (DALL-E)
|-- le-hibou.png, le_dauphin.png, ...    15 illustrations PNG (~3 MB chacune)
|-- CARNET_DE_BORD_FLIPBOOK.md           CE FICHIER
|
|-- flipbook/
    |-- index.html                       Flipbook complet (HTML+CSS+JS)
    |-- narrations_multi.json            Narration segmentee par personnage
    |-- narrations.json                  Narration v1 (texte brut, legacy)
    |-- timestamps.json                  Timestamps legacy (plus utilise)
    |-- page_01.jpg ... page_30.jpg      30 images JPEG du livre
    |
    |-- audio/
        |-- spread_00.mp3 ... spread_14.mp3    15 MP3 finaux (un par spread)
        |-- concat_list.txt                    Liste pour concat legacy
        |-- narration.mp3                      MP3 unique legacy (plus utilise)
        |
        |-- segments/
        |   |-- spread_XX_segYY_V.mp3          Segments TTS bruts
        |   |-- spread_XX_segYY_V_fx.mp3       Segments avec pitch shift
        |   |-- spread_XX_segYY_V_raw.mp3      Versions pre-traitement
        |   |-- spread_XX_segYY_V_tts.mp3.ssml Fichiers SSML (legacy, inutiles)
        |
        |-- sfx/
            |-- owl_hoot.mp3                   Hibou (normalise)
            |-- dolphin_chirp.mp3              Dauphin (normalise)
            |-- cat_meow.mp3                   Chat (normalise)
            |-- horse_whinny.mp3               Cheval (normalise)
            |-- owl_hoot.wav, etc.             Sources WAV normalisees
```

### Format du narrations_multi.json

```json
[
  {
    "name": "spread_00",
    "segments": [
      ["N", "Coco ne dort pas ce soir !"],
      ["N", "Une aventure de Coco l'Axolotl. Par Docteur Anita Nirvena. Illustrations de Loupineki."]
    ]
  },
  {
    "name": "spread_01",
    "segments": [
      ["N", "L'heure de dormir."],
      ["N", "Ce soir, c'etait l'heure de dormir..."],
      ["C", "Maman, je n'arrive pas a dormir !"],
      ["M", "Compte les moutons et..."],
      ["C", "Mais Maman, les moutons ne savent pas nager !"],
      ["N", "Maman ria."],
      ["M", "C'est vrai ! Alors reste tranquille et le sommeil viendra."]
    ]
  }
]
```

Codes voix : `N` = Narrateur, `C` = Coco, `M` = Maman, `A` = Animal

### Tableau des durations par spread

| Spread | Contenu              | Duree   | SFX      | Pitch  |
|--------|----------------------|---------|----------|--------|
| 00     | Couverture           | 11.09s  | -        | -      |
| 01     | L'heure de dormir    | 23.74s  | -        | -      |
| 02     | L'aventure commence  | 16.94s  | -        | -      |
| 03     | Le Hibou             | 32.69s  | Hibou    | -1.5st |
| 04     | Le Dauphin           | 34.66s  | Dauphin  | +2.0st |
| 05     | La Loutre            | 30.00s  | -        | +1.0st |
| 06     | Le Koala             | 35.86s  | -        | -1.0st |
| 07     | La Chauve-Souris     | 31.44s  | -        | +1.5st |
| 08     | Le Chat              | 30.38s  | Chat     | 0st    |
| 09     | Le Cheval            | 33.86s  | Cheval   | -0.5st |
| 10     | Le Flamant Rose      | 30.29s  | -        | +1.0st |
| 11     | Le Paresseux         | 32.54s  | -        | -2.0st |
| 12     | Maman Axolotl        | 32.57s  | -        | -      |
| 13     | Le super-pouvoir     | 32.88s  | -        | -      |
| 14     | Bonne nuit Coco      | 18.84s  | -        | -      |
| **Total** |                   | **~7min 10s** |    |        |

---

## Annexe : Services testes et abandonnes

| Service        | Resultat | Raison de l'abandon                    |
|----------------|----------|----------------------------------------|
| ElevenLabs     | Teste    | Trop cher, voix pas assez enfantines   |
| MicMonster     | Pas teste | -                                     |
| Ideogram       | Pas teste | Pour les images, pas le son           |
| ChatGPT TTS    | Pas teste | -                                     |
| Azure SSML     | Echoue   | edge-tts lit le SSML comme du texte   |

### Cle API ElevenLabs (si besoin futur)
`sk_92f5614ecf487391a45cbf06a4559ff89a5a1952360ca0f4`

---

## Commandes utiles (copier-coller)

### Generer un segment TTS
```bash
C:/Python313/python.exe -m edge_tts --voice fr-FR-VivienneMultilingualNeural --text "Texte ici" --write-media output.mp3
```

### Verifier le sample rate
```bash
ffprobe -v quiet -show_entries stream=sample_rate -of csv=p=0 fichier.mp3
```

### Verifier le volume
```bash
ffmpeg -v info -i fichier.mp3 -af volumedetect -f null -
```

### Pitch shift (24000 Hz)
```bash
# Exemple : +2 demi-tons
ffmpeg -y -i input.mp3 -af "asetrate=26934,aresample=24000,atempo=0.890899" -codec:a libmp3lame -b:a 192k output.mp3
# 26934 = 24000 * 2^(2/12)
# 0.890899 = 1 / 2^(2/12)
```

### Normaliser un SFX
```bash
ffmpeg -y -i clip.wav -af "loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=in:d=0.05,afade=t=out:st=1.9:d=0.3" normalized.wav
```

### Concatener des segments
```bash
ffmpeg -y -i seg1.mp3 -i seg2.mp3 -i seg3.mp3 -filter_complex "[0:a][1:a][2:a]concat=n=3:v=0:a=1[out]" -map "[out]" -codec:a libmp3lame -b:a 192k spread.mp3
```

### Ralentir un spread
```bash
ffmpeg -y -i spread_raw.mp3 -af "atempo=0.9" -codec:a libmp3lame -b:a 192k spread_final.mp3
```
