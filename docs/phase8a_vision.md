# Phase 8A — Vision industrielle

Date de validation : 20 juillet 2026

## Objectif et périmètre

La phase 8A ajoute une chaîne locale et appelable de détection d'anomalies visuelles sur convoyeur. Elle couvre les classes `belt_misalignment`, `obstacle` et `material_accumulation`, conserve `unknown_defect` dans le contrat de sortie, rattache chaque résultat à `equipment_id`, `camera_id` et `trace_id`, puis expose le résultat à SPADE, SQLAlchemy, FastAPI, WebSocket et React.

Cette phase ne commande aucun équipement. Son dataset de validation est petit et entièrement synthétique ; les résultats ne démontrent pas une performance sur des images industrielles réelles.

## Architecture

```text
image locale contrôlée / répertoire / requête VisionAgent
  → validation et normalisation RGB
  → VisionModelManager (poids custom, chargement paresseux, CPU/GPU auto)
  → YOLOv8n
  → conversion vers VisionDetection Pydantic
  → image annotée + JSON + table vision_detections
  → événements WebSocket
  → SupervisorAgent / HistorianAgent / AlertAgent
  → page React /vision
```

Le module `indusguard/vision/` sépare configuration, schémas, prétraitement, gestion du modèle, détection, service, persistance, visualisation, dataset et évaluation. Le modèle n'est pas chargé à l'import de l'application ; `/api/v1/vision/health` déclenche et rend observable son chargement. Si les poids custom manquent en mode `demo`, `yolov8n.pt` est un fallback technique COCO clairement signalé, et non un détecteur industriel valide. En mode hors démo, l'absence du modèle produit une erreur explicite.

## Dataset et reproductibilité

`generate_vision_dataset.py` crée 60 images 640×480 avec la seed 42 : 15 exemples par classe de défaut et 15 fonds normaux. La séparation déterministe donne 42 images train, 9 validation et 9 test. Les labels suivent YOLO et les SHA-256 du manifeste permettent à `validate_vision_dataset.py` de refuser les doublons entre splits.

La provenance détaillée est dans `data/vision/dataset_sources.md`. Aucun fichier `LICENSE` n'était présent dans le dépôt au moment de la génération ; la licence de redistribution doit être clarifiée avant publication.

Le module de vision est un prototype académique évalué principalement sur des données synthétiques ou publiques. Ses performances ne prouvent pas une validation sur un site industriel réel.

## Commandes

```bash
python generate_vision_dataset.py
python validate_vision_dataset.py
python train_vision_model.py
python evaluate_vision_model.py --split test
python run_vision_inference.py --image data/vision/demo/camera_01_sample_belt_misalignment.jpg --equipment-id CONVEYOR-001
python run_vision_agent_demo.py
python run_dashboard.py
```

Les réglages sont centralisés dans `configs/vision.yaml`. `train_vision_model.py --quick` valide techniquement le pipeline en une époque ; il ne remplace pas un entraînement. Le run conservé a demandé 20 époques et s'est arrêté tôt après 18, avec le meilleur checkpoint à l'époque 13. Le poids utilisé est `outputs/vision/models/best.pt`, tandis que l'historique, les courbes et matrices sont sous `outputs/vision/training/phase8a/`.

## API et contrats

Les routes sont `GET /api/v1/vision/health`, `POST /api/v1/vision/analyze`, `GET /api/v1/vision/detections`, `GET /api/v1/vision/detections/{detection_id}`, `GET /api/v1/assets/{equipment_id}/vision-detections` et `GET /api/v1/vision/detections/{detection_id}/image`.

L'analyse n'accepte que des chemins résolus sous les répertoires autorisés et impose une taille maximale. Les formats invalides, fichiers corrompus, chemins hors périmètre et modèles indisponibles produisent des erreurs explicites. L'événement `vision.detection.created` est diffusé par WebSocket. La table `vision_detections`, créée par la migration `0002_phase8a_vision`, conserve classe, confiance, bbox, chemins, modèle, provenance, identifiants et horodatage.

## Résultats réellement mesurés

Sur le split test synthétique indépendant (9 images, 6 annotations), l'évaluation réelle de `best.pt` a donné : précision 0,783, rappel 0,927, mAP@0.5 0,995 et mAP@0.5:0.95 0,949. La dernière revalidation a rapporté 37,7 ms/image sur une NVIDIA GeForce RTX 2060 ; cette mesure varie avec l'environnement et ne couvre pas tout le trajet API/SQL/WebSocket.

Avec le seuil configuré à 0,50, l'échantillon `camera_01_sample_belt_misalignment.jpg` produit une détection persistée de confiance 0,514. Les échantillons obstacle et accumulation ne franchissent pas systématiquement ce seuil : c'est une limite observable du modèle, pas un résultat masqué.

## Limites et prochaines étapes

- Le domaine synthétique est visuellement simple et le split test est trop petit pour conclure à une généralisation.
- Les métriques élevées sont donc descriptives de ce seul dataset.
- Aucune caméra physique n'a été utilisée ; la configuration prépare seulement un futur adaptateur.
- Le fallback COCO n'utilise pas le vocabulaire industriel custom.
- Il faut collecter un corpus terrain licencié, annoté et séparé par site/séquence, ajouter des cas difficiles, calibrer les confiances et établir des métriques par site avant tout pilote industriel.
- La phase 8B devra consommer les détections versionnées pour mettre à jour le belief state ; elle n'est pas implémentée ici.
