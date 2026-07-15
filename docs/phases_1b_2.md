# Phases 1B et 2 — choix techniques

## Simulation de la ligne

La ligne utilise un format long : chaque timestamp produit une ligne par équipement. Les capteurs non applicables restent à `NaN`. Ce choix garde un schéma CSV unique tout en permettant d'ajouter un équipement sans modifier les lignes existantes.

`BaseEquipment` centralise l'identifiant, l'état, la santé, la graine, le bruit et la validation. La classe historique `BearingSimulator` reste compatible ; `LineBearingSimulator` réutilise ses principes de vibration et température progressives dans l'orchestrateur multi-équipement.

### Plages nominales retenues

| Équipement | Hypothèses normales principales |
|---|---|
| Moteur | 48 °C, 1,8 mm/s, 1 500 RPM, 18 A, 55 % |
| Roulement | 40 °C, 2,0 mm/s, 1 500 RPM, santé proche de 100 |
| Convoyeur | 43 °C, 1,5 mm/s, charge 45 %, vitesse 1,8 m/s, glissement 1,5 % |
| Pompe | 46 °C, 1,6 mm/s, 14 A, 5 bar, 120 unités de débit |

Ces valeurs sont des hypothèses de démonstration configurables, pas des limites universelles. Un bruit gaussien faible et une graine indépendante par équipement rendent les séries réalistes et reproductibles.

### Scénarios de panne

Les scénarios démarrent par une période normale, puis appliquent une rampe de sévérité. La dégradation commence à une intensité de 0,25 et l'état critique à 0,75.

- `scenario_1_normal` : aucun défaut ;
- `scenario_2_bearing` : usure progressive du roulement ;
- `scenario_3_overload` : charge et glissement du convoyeur, puis courant et température moteur ;
- `scenario_4_pump` : baisse du débit et hausse de la pression, de la vibration et de la température ;
- `scenario_5_cascade` : roulement, moteur puis convoyeur avec des démarrages décalés.

### Dépendances

Les coefficients dans `configs/industrial_line.yaml` contrôlent quatre relations lisibles : vibration roulement vers moteur, dégradation roulement vers moteur, surcharge convoyeur vers charge moteur et baisse de régime moteur vers convoyeur. L'orchestrateur applique ces effets dans l'ordre roulement → moteur → convoyeur, puis simule la pompe.

## Détection d'anomalies

Le détecteur par seuils compare chaque capteur pertinent à un minimum ou maximum configuré. Il retourne les capteurs fautifs, une sévérité bornée entre 0 et 1 et une explication textuelle. Il est facile à auditer mais ne détecte pas bien les combinaisons inédites restant sous chaque seuil individuel.

Isolation Forest isole les observations rares à l'aide d'arbres aléatoires. Une observation isolée en peu de divisions reçoit un score plus anormal. Un pipeline par équipement applique :

1. une imputation médiane des valeurs manquantes ;
2. une standardisation ;
3. un modèle Isolation Forest.

Les quatre modèles utilisent seulement les capteurs applicables. Ils sont entraînés sur les 70 % premières mesures normales de chaque équipement, triées dans le temps. Ces index sont retirés du calcul des métriques. Les cibles synthétiques ne sont utilisées qu'après prédiction.

## Évaluation et reproductibilité

Les métriques comprennent accuracy, precision, recall, F1, vrais positifs, faux positifs, faux négatifs et vrais négatifs, globalement et par équipement. Les paramètres d'Isolation Forest, la contamination et la graine résident dans `configs/anomaly_detection.yaml`.

## Limites et améliorations futures

- Les équations ne remplacent pas un modèle physique validé.
- Les distributions synthétiques séparent assez nettement les pannes des états normaux.
- La contamination fixe provoque des faux positifs, surtout pour la pompe.
- Le système ne gère pas encore le drift, les données en flux ou le réentraînement automatique.
- Les seuils doivent être adaptés aux fiches constructeur et au contexte réel.

Les suites possibles sont l'étalonnage sur des mesures réelles, la validation temporelle sur plusieurs campagnes, des caractéristiques glissantes, une calibration des scores, la surveillance du drift et une API d'inférence temps réel.
