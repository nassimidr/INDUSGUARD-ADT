# Phase 4 — prédiction de la durée de vie restante

## Objectif et définition

La durée de vie restante, ou RUL (`Remaining Useful Life`), est le nombre de cycles avant la panne finale. Une trajectoire complète se termine par `failure_occurred=1`, `rul_steps=0` et `rul_hours=0`. La phase 4 complète ainsi la détection d'anomalie et le diagnostic par une estimation du temps restant.

## Création des trajectoires

Le générateur produit 20 trajectoires complètes et 3 trajectoires incomplètes pour chacun des quatre équipements. La longueur complète varie entre 120 et 180 cycles. Avec la configuration de référence, le dataset contient 13 156 lignes, 80 runs complets et 12 incomplets.

Chaque trajectoire possède une période quasi normale, puis une dégradation accélérée selon `progression = fraction_du_cycle^1,55`, une phase critique et une panne finale. La santé décroît tandis que les capteurs propres à la panne évoluent. Les trajectoires incomplètes sont tronquées avant la panne et leurs vraies RUL restent à `NaN` sur toutes leurs lignes.

## Types de panne

Les trajectoires représentent les 16 pannes propres aux équipements :

- moteur : surchauffe, surcharge, perte de vitesse, défaut électrique ;
- roulement : usure, surchauffe, dommage sévère ;
- convoyeur : surcharge, glissement, perte de vitesse, surchauffe moteur ;
- pompe : cavitation, obstruction, fuite, surchauffe, défaut de roulement.

Les quatre classes absentes du dataset de phase 3 (`motor_electrical_fault`, `conveyor_speed_fault`, `pump_leakage`, `pump_bearing_fault`) disposent ici de trajectoires et de signatures capteurs dédiées.

## Calcul de la vraie RUL

Pour une trajectoire complète de longueur `N`, la cible au cycle `c` vaut `N - 1 - c`. Elle diminue donc exactement d'un cycle à chaque ligne. `rul_hours` est cette valeur multipliée par l'intervalle configurable de 0,5 heure.

## Caractéristiques temporelles causales

Pour chaque capteur applicable, le pipeline calcule des moyennes et écarts-types glissants sur 5, 10 et 20 cycles, ainsi qu'une pente sur 10 cycles. `sensor_delta` résume les variations absolues courantes.

Les fenêtres ne sont jamais centrées. Chaque valeur utilise seulement les cycles précédents et le cycle courant, séparément pour chaque `asset_run_id`. Modifier une mesure future ne change donc aucune caractéristique passée, ce qui est couvert par un test automatique.

Les cibles, la progression, la panne finale, l'état, le diagnostic et toute information future sont explicitement interdits dans la liste des caractéristiques.

## Baseline

La baseline combine le score de santé relatif et sa vitesse récente de diminution, puis borne l'extrapolation par la RUL maximale observée. Elle sert de référence simple et obtient une MAE de 33,293 cycles.

## Modèle Machine Learning

Un `RandomForestRegressor` est entraîné par type d'équipement, avec imputation médiane. Ce modèle gère les relations non linéaires sans nécessiter un réseau de neurones. La MAE globale est de 5,020 cycles et le R² de 0,956 sur le test.

## Séparation par trajectoire

`GroupShuffleSplit` utilise `asset_run_id` comme groupe. Chaque équipement fournit 15 trajectoires d'entraînement et 5 de test. Aucun run ne peut apparaître des deux côtés. Les trajectoires incomplètes sont exclues de l'apprentissage supervisé.

Cette stratégie corrige le principal risque de fuite qu'aurait créé une séparation aléatoire ligne par ligne. Le calcul des caractéristiques avant la séparation est sûr ici, car il est strictement local et causal à chaque trajectoire ; aucune statistique n'est partagée entre runs.

## Incertitude et confiance

Chaque arbre du Random Forest fournit une prédiction. Les percentiles 10 et 90 forment `rul_lower_bound` et `rul_upper_bound`. Cet intervalle décrit la dispersion des arbres ; ce n'est pas un intervalle de confiance statistique calibré.

La confiance technique combine la largeur relative de cet intervalle, la quantité d'historique et la proportion de capteurs disponibles. Elle reste une heuristique entre 0 et 1.

## Niveau de risque et explication

Les seuils configurés sont : RUL ≤ 10 `critical`, ≤ 25 `high`, ≤ 50 `medium`, sinon `low`. L'explication mentionne la RUL, le risque et les pentes parmi les caractéristiques les plus importantes réellement observées.

## Métriques

L'évaluation contient 2 830 lignes issues de 20 trajectoires de test.

| Modèle | MAE | RMSE | R² | MAPE hors RUL=0 |
|---|---:|---:|---:|---:|
| Baseline | 33,293 | 38,283 | 0,194 | 52,853 % |
| Random Forest | 5,020 | 8,945 | 0,956 | 6,927 % |

MAE Random Forest par équipement : moteur 4,984 ; roulement 5,995 ; convoyeur 4,429 ; pompe 4,717 cycles. Les métriques complètes sont aussi calculées par panne et par niveau de RUL.

## Limites et améliorations futures

- Le score de santé synthétique est fortement informatif et rend le problème plus simple que sur données réelles.
- Les trajectoires partagent les mêmes familles d'équations malgré des longueurs et bruits différents.
- L'incertitude des arbres n'est pas calibrée sur une couverture réelle.
- Les trajectoires incomplètes n'ont pas de vérité terrain pour valider leur prédiction.
- La généralisation à un nouvel équipement physique n'est pas démontrée.

Les améliorations futures incluent davantage de régimes opérationnels, une validation `GroupKFold`, la calibration conformelle des intervalles, la détection du drift, des historiques irréguliers et l'évaluation sur des données de maintenance réelles.
