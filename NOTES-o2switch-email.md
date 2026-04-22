# Notes o2switch / email Coco

Date: 2026-04-21

## Acces o2switch

- Espace client o2switch: `https://clients.o2switch.fr`
- Identifiant client espace o2switch: `Loopinky`
- Code client support: `B1H3 2563`

## Hebergement / cPanel

- Hebergement a utiliser pour `cocotheaxolotl.org`: `dayu0673`
- Serveur cPanel / SMTP: `printer.o2switch.net`
- URL cPanel directe: `https://printer.o2switch.net:2083`
- Identifiant cPanel probable: `dayu0673`

Dans l'espace client o2switch:

1. Aller dans `Gerer mes Services`.
2. Ouvrir `Tous mes services`.
3. Chercher la ligne `dayu0673` (`Offre Unique Grow`, `Sans Domaine`).
4. Cliquer sur le bouton `...` a droite.
5. Chercher `Acceder au cPanel`, `Administrer`, `Gerer l'hebergement` ou `Connexion cPanel`.

Important: `cocotheaxolotl.org` apparait comme `Domaine seul`, mais les emails doivent etre geres depuis l'hebergement `dayu0673`.

## Creer / gerer l'adresse email

Dans cPanel:

1. Aller dans `Mail`.
2. Ouvrir `Comptes de messagerie`.
3. Creer ou modifier `coco@cocotheaxolotl.org`.
4. Definir/reinitialiser le mot de passe de cette boite mail si besoin.

## Configurer Gmail pour envoyer depuis coco@cocotheaxolotl.org

Dans Gmail `annievannier@gmail.com`:

1. Aller dans `Parametres` > `Voir tous les parametres`.
2. Ouvrir `Comptes et importation`.
3. Dans `Envoyer des e-mails en tant que`, cliquer `Ajouter une autre adresse e-mail`.
4. Adresse: `coco@cocotheaxolotl.org`.
5. SMTP:
   - Serveur SMTP: `printer.o2switch.net`
   - Port: `465`
   - Securite: `SSL`
   - Nom d'utilisateur: `coco@cocotheaxolotl.org`
   - Mot de passe: mot de passe de la boite `coco@cocotheaxolotl.org`

Ne pas stocker le mot de passe dans ce fichier.
