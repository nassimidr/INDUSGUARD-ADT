# Provenance du dataset vision

Les images de `data/vision/` sont entièrement synthétiques. Elles sont produites hors ligne par
`generate_vision_dataset.py` avec Pillow et représentent un convoyeur stylisé, une bande
désalignée, un obstacle ou une accumulation de matière. Aucune photographie industrielle,
personne ou donnée tierce n'est incluse.

- Dataset : `indusguard-vision-synthetic`
- Seed : 42
- Générateur : code INDUSGUARD-ADT ; aucun fichier `LICENSE` n'était présent dans le dépôt au moment de la génération, la licence de redistribution doit donc être clarifiée avant toute publication
- Taille générée pour la validation : 60 images
- Distribution : 15 images par classe de défaut et 15 images normales
- Séparation : 70 % train, 15 % validation, 15 % test, après mélange déterministe
- Contrôle : SHA-256 de chaque image pour refuser tout doublon entre splits

Les formes, textures, éclairages et défauts sont volontairement simplifiés. Les performances
mesurées ne représentent pas un site industriel réel. Le manifeste conserve le split et les
paramètres de chaque image. Un futur importeur pourra ajouter un dataset public ou terrain dans
`data/vision/raw/`, à condition d'enregistrer sa source, sa licence et un split indépendant.

Le module de vision est un prototype académique évalué principalement sur des
données synthétiques ou publiques. Ses performances ne prouvent pas une
validation sur un site industriel réel.
