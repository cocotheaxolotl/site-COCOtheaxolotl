# Carnet de bord — Flipbook "Coco ne dort pas ce soir !"

## Session 1 — Mise en place initiale

### 1. Centrage du flipbook
- **Probleme** : Le livre s'affichait a gauche de l'ecran au lieu du centre.
- **Cause** : La librairie page-flip utilise `position:absolute` sur `.stf__wrapper`, ce qui ignore `margin:0 auto`.
- **Tentatives echouees** :
  - `margin:0 auto` sur `.stf__wrapper`
  - `left:50%; transform:translateX(-50%)` sur `.stf__wrapper`
  - `showCover: false`
  - MutationObserver JS pour forcer le centrage
  - CSS `left:50%` sans changer `position` — page decalee
- **Solution** : `max-width:1060px; width:100%; margin:0 auto` sur `#flipbook-container` (le parent)

### 2. Son qui ne demarre pas (autoplay)
- **Probleme** : Le son ne demarrait pas pour les utilisateurs revenant via localStorage.
- **Cause** : Les navigateurs bloquent `audio.play()` sans geste utilisateur (clic). Les retours via localStorage n'ont pas de geste.
- **Solution** : Parametre `showReader(withAudio)` — `true` depuis le clic sur "Lire" (geste), `false` depuis localStorage.

### 3. Pages non synchronisees avec l'audio
- **Probleme** : Les pages ne tournaient pas au bon endroit lors de l'avance automatique.
- **Cause** : `flipNext()` appele deux fois etait peu fiable (timing, animation).
- **Solution** : `turnToPage(targetPage)` avec fonction `spreadToPage()` pour cibler la page exacte.

### 4. Sous-dossier imbrique dans l'export PPTX
- **Probleme** : L'export PPTX cree un sous-dossier `Coco-ne.../Coco-ne.../` avec les JPEGs.
- **Solution** : Deplacer les fichiers vers le dossier parent avec `mv`, supprimer le sous-dossier vide.
- **Note** : Ce probleme se reproduit a chaque re-export du PPTX.

---

## Session 2 — Audio, musique de fond, finalisation

### 5. Musique de fond (lullaby)
- **Demande** : Ajouter une musique douce en boucle.
- **Implementation** : `<audio id="bgMusic" loop>`, volume 0.15, demarre avec la narration.
- **Fadeout** : A la fin de l'histoire, volume descend progressivement sur ~3 secondes avant pause.

### 6. Auto-advance par defaut + skip titre Dr Nirvena
- **Demande** : Defilement automatique par defaut, ne pas lire la diapo titre (credits Dr Nirvena).
- **Solution** : `autoTurn = true` par defaut, `pageToSpread(0)` retourne -1, bouton AUTO actif visuellement.

---

## Session 3 — Version finale 31 pages

### 7. Passage de 35 a 31 pages
- **Changement** : Suppression page titre Dr Nirvena, 2e couverture, pages fin superflues.
- **Nouveau dossier** : `Coco-ne-dort-pas-ce-soir-FR-sleep-book/` (31 JPEGs)
- **Nouveau mapping** :
  - Page 0 (couverture) → spread_00
  - Pages 1-28 → spreads 1-14
  - Pages 29-30 → pas d'audio
- **Formule** : `Math.floor((pg - 1) / 2) + 1`

### 8. Begaiement audio sur les titres
- **Probleme** : L'audio begayait au debut de chaque chapitre (le titre se repetait).
- **Cause** : Double demarrage — `turnToPage()` declenche `onPageFlip` → `playSpread()`, puis le `setTimeout(1000)` relancait `playSpread()` une 2e fois, redemarrant l'audio depuis le debut.
- **Solution** : Ajout d'une garde `if(currentSpread !== nextSp)` dans le setTimeout pour eviter le double-play.

### 9. Credits audio joues au debut au lieu de la fin
- **Probleme** : spread_00 contient les credits ("Une aventure... Dr Nirvena... Loopinky"), pas le titre du livre. Il se jouait au debut sur la couverture.
- **Cause** : Confusion entre titre du livre et credits — `pageToSpread(0) = 0` lancait les credits des la couverture.
- **Solution** :
  - Couverture (page 0) → pas d'audio, seulement musique de fond
  - Apres spread_14 (dernier chapitre) → jouer spread_00 (credits)
  - Apres spread_00 → fadeout et stop
  - Logique dans `ended` : spreads 1-13 → avance, spread 14 → credits, spread 0 → fin

### 10. Separation titre / credits audio
- **Probleme** : spread_00 contenait le titre ET les credits dans un seul fichier. Impossible d'avoir le titre au debut et les credits a la fin.
- **Solution** : Couper spread_00 en deux fichiers via Premiere Pro :
  - `spread_title.mp3` → joue sur la couverture a l'entree du code
  - `spread_credits.mp3` → joue apres spread_14 (dernier chapitre)
  - Variable `playingSpecial` ('title', 'credits', '') pour gerer les etats hors spreads numerotes

### 11. Credits en boucle infinie + pages de fin non affichees
- **Probleme** : Apres l'histoire, les credits jouaient en boucle infinie. Les diapos 30-31 (A bientot / Cher Parent) ne s'affichaient pas.
- **Cause** : Quand les credits se terminent, `currentSpread` reste a 14 (TOTAL_SPREADS - 1). Le handler `ended` retombait dans la condition `currentSpread === 14` → relancait les credits.
- **Solution** :
  - Verifier `playingSpecial === 'credits'` AVANT la condition `currentSpread === 14`
  - Ajouter `turnToPage(29)` quand les credits demarrent pour afficher les pages de fin

### 12. Pas d'animation de page qui tourne
- **Probleme** : Les pages changeaient mais sans animation de flip visible.
- **Cause** : `turnToPage()` fait un saut instantane vers la page cible. Pas d'animation.
- **Solution** : Remplacer tous les `turnToPage()` par `flip()` qui declenche l'animation de page qui tourne.
