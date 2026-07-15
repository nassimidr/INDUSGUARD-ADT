# Phase 3 — diagnostic et classification des pannes

## Objectif

La phase 3 complète la détection binaire de la phase 2. Pour chaque mesure, elle indique l'équipement, une cause probable, les capteurs responsables, une gravité, une confiance et une explication basée sur les valeurs observées.

## Équipements et pannes

Le catalogue central se trouve dans `fault_catalog.py`.

- Moteur : surchauffe, surcharge, perte de vitesse, défaut électrique.
- Roulement : usure, surchauffe, dommage sévère.
- Convoyeur : surcharge, glissement, perte de vitesse, surchauffe moteur.
- Pompe : cavitation, obstruction, fuite, surchauffe, défaut de roulement.
- Ligne : défaillance en cascade, panne inconnue et fonctionnement normal.

Les pannes réellement simulées sont déterminées par le scénario, l'état et les capteurs. Une mesure normale porte toujours `failure_type=normal`. Par exemple, une vibration croissante et une santé décroissante indiquent une usure du roulement ; un débit bas avec pression et courant élevés indique une obstruction de pompe.

## Architecture

Le pipeline suit quatre étapes :

1. Les seuils et Isolation Forest de phase 2 détectent l'anomalie.
2. `RuleBasedDiagnoser` évalue les symptômes YAML pondérés.
3. Un Random Forest spécialisé prédit une panne par type d'équipement.
4. `DiagnosisService` fusionne les résultats, calcule la confiance et la gravité, puis construit l'explication.

Une mesure déjà en `degradation` ou `critical` est toujours diagnostiquée. Pour une mesure encore marquée normale, les deux détecteurs de phase 2 doivent être d'accord afin de limiter les faux positifs.

## Prétraitement et absence de fuite

Les variables `failure_type`, `is_anomaly`, `operating_state`, `anomaly_severity` et `scenario_id` sont explicitement interdites comme caractéristiques. Les capteurs sont sélectionnés par équipement. Une imputation médiane est intégrée à chaque pipeline.

La séparation train/test est stratifiée lorsque les effectifs le permettent, avec une graine fixe. Les index de test sont mémorisés et seuls ceux-ci servent au calcul des métriques. `class_weight="balanced"` réduit l'effet du déséquilibre.

## Diagnostic par règles

Les règles sont configurées dans `configs/fault_diagnosis.yaml`. Chaque panne définit des conditions, un poids et un nombre minimal de symptômes. La confiance dépend de la proportion pondérée de symptômes réellement vérifiés. Les capteurs correspondants sont conservés dans le CSV et dans l'explication.

## Classificateur Machine Learning

Quatre `RandomForestClassifier` sont entraînés, car les capteurs diffèrent entre moteur, roulement, convoyeur et pompe. Le modèle reste relativement interprétable, robuste aux relations non linéaires et compatible avec les classes déséquilibrées.

## Fusion hybride, confiance et gravité

Lorsque règles et ML sont d'accord, leur confiance moyenne reçoit un bonus. En cas de désaccord, le résultat le plus confiant est choisi. Sous le seuil configuré, le service retourne `unknown_fault`.

La gravité combine l'état, le score de santé, la confiance et le caractère en cascade : `none`, `low`, `medium`, `high` ou `critical`. Elle ne dépend donc pas uniquement du nom de la panne.

## Résultats de référence

L'évaluation comporte 500 mesures tenues à l'écart de l'entraînement.

| Approche | Accuracy | F1 macro | F1 pondéré |
|---|---:|---:|---:|
| Règles | 0,920 | 0,679 | 0,905 |
| Random Forest | 0,956 | 0,786 | 0,955 |
| Hybride | 0,942 | 0,742 | 0,940 |

Pour l'hybride, l'accuracy par équipement vaut 0,920 pour le moteur, 0,880 pour le roulement, 0,968 pour le convoyeur et 1,000 pour la pompe. Le F1 macro du roulement (0,584) montre que la distinction entre usure, surchauffe, dommage sévère et cascade reste la plus difficile.

## Limites et améliorations futures

- Les classes rares rendent certaines métriques instables.
- Plusieurs pannes progressives partagent les mêmes symptômes, surtout pour le roulement.
- Les données synthétiques sont plus régulières que des capteurs réels.
- La détection de cascade gagnerait à exploiter explicitement des fenêtres multi-équipements.
- La confiance est une heuristique et non une probabilité calibrée.

Les prochaines améliorations possibles sont l'ajout de scénarios dédiés aux classes absentes ou rares, une validation par groupes temporels, la calibration probabiliste, les caractéristiques glissantes et l'évaluation sur données terrain.
