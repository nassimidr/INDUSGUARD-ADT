# Rapport de validation — Phase 8A Vision

Date : 20 juillet 2026  
Branche : `feature/vision`  
Environnement : Windows, Python 3.10.11, CUDA 12.4, NVIDIA GeForce RTX 2060

## Résultat

| Composant | Statut | Preuve exécutée |
| --- | --- | --- |
| Dataset | Fonctionnel avec limites | 60 images synthétiques, splits 42/9/9, manifeste SHA-256, validation sans fuite |
| Prétraitement | Validé | formats, RGB, redimensionnement, fichier corrompu et métadonnées testés |
| Entraînement | Fonctionnel avec limites | YOLOv8n custom, 20 époques demandées, arrêt anticipé après 18, poids `best.pt` conservé |
| Évaluation | Validée sur synthétique | précision 0,783 ; rappel 0,927 ; mAP50 0,995 ; mAP50-95 0,949 sur 9 images/6 objets |
| Inférence | Validée | image de démo → bbox/confiance/provenance → JSON et image annotée |
| VisionAgent | Validé | échange XMPP réel embarqué, même `trace_id`/`equipment_id`, supervision et historisation |
| Base de données | Validée | migration Alembic `0002`, insertion idempotente et lecture API |
| API/WebSocket | Validés | 6 routes OpenAPI, analyse HTTP 200, détail/image HTTP 200, événement temps réel reçu |
| Frontend | Validé | route `/vision`, santé, analyse, filtres, détails, images et états d'erreur ; 8 tests dédiés |
| Régression | Validée | 165 tests Python et 12 tests frontend réussis ; lint et build frontend réussis ; couverture globale 71 % |

## Scénario de bout en bout observé

L'image `data/vision/demo/camera_01_sample_belt_misalignment.jpg` a traversé le modèle custom. Une détection `belt_misalignment` à 0,514 a été créée avec sa bbox, son `trace_id`, `CONVEYOR-001` et `camera_01`, puis enregistrée en SQL. Le détail et l'image annotée ont été relus par API, et `vision.detection.created` a été reçu sur le WebSocket. Un second essai a fait transiter la même catégorie de résultat dans un message XMPP réel du `VisionAgent` vers le superviseur et l'historien.

## Incidents et observations

- Le premier essai CPU d'une époque puis un essai de cinq époques n'étaient pas suffisants ; ils ont été remplacés par le run GPU conservé. Aucun de leurs résultats n'est présenté comme métrique finale.
- L'arrêt anticipé a terminé 18 époques sur 20 demandées ; ce nombre est enregistré distinctement.
- Au seuil 0,50, certains échantillons synthétiques obstacle et accumulation restent sous le seuil. La classe bande désalignée fournit le scénario E2E démontré.
- Les avertissements existants concernent la compatibilité `TestClient/httpx` et la configuration Alembic ; ils ne font pas échouer les suites.
- Aucun dataset terrain, caméra réelle ou test de robustesse aux conditions industrielles n'a été exécuté.

La revalidation finale a donné `165 passed, 2 warnings` en Python et `12 passed` en frontend. La couverture globale est de 71 %. `npm run lint` et `npm run build` réussissent ; les bundles principaux mesurent 542,81 kB et 1 085,95 kB avant compression, ce dernier restant un point d'optimisation déjà identifié pour Plotly.

## Verdict

**Phase 8A : FONCTIONNEL AVEC LIMITES**

Le pipeline technique demandé existe, est intégré et a été exécuté réellement. Il n'est pas marqué « terminé et validé » au sens industriel, car les données sont synthétiques, le test est petit, deux démonstrations de classe sont fragiles au seuil nominal et aucune validation terrain n'existe.

Le module de vision est un prototype académique évalué principalement sur des données synthétiques ou publiques. Ses performances ne prouvent pas une validation sur un site industriel réel.
