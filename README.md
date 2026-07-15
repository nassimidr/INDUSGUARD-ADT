# INDUSGUARD-ADT

## Tableau de bord Phase 7

La phase 7 ajoute une API FastAPI versionnée, 15 tables SQLite/SQLAlchemy, des migrations Alembic, un flux WebSocket et une application React/TypeScript de 12 vues. Le système reste local et ne pilote aucun équipement réel.

```bash
pip install -r requirements-dashboard.txt
python import_dashboard_history.py
python run_dashboard.py
```

Dans un second terminal, lancer `cd frontend`, `npm install`, puis `npm run dev` et ouvrir `http://127.0.0.1:5173`. OpenAPI est disponible sur `http://127.0.0.1:8000/docs`. Pour la persistance SQLite pendant une exécution SPADE, définir `INDUSGUARD_DASHBOARD_ENABLED=1`. Voir [la documentation Phase 7](docs/phase_7_dashboard.md).

INDUSGUARD-ADT est un jumeau numérique Python destiné à expérimenter la surveillance d'une ligne industrielle et la détection automatique d'anomalies. Les données sont synthétiques : elles servent au développement et ne doivent pas piloter une installation réelle.

## Fonctionnalités

La phase 1 historique simule l'usure progressive d'un roulement sur 200 mesures. La phase 1B étend ce socle à une ligne couplée de quatre équipements :

| Équipement | Capteurs |
|---|---|
| Moteur | température, vibration, RPM, courant, charge |
| Roulement | température, vibration, RPM, score de santé |
| Convoyeur | température, vibration, charge, vitesse, glissement |
| Pompe | température, vibration, courant, pression, débit |

Chaque équipement évolue entre `normal`, `degradation` et `critical`. Les dépendances modélisent notamment l'effet de la surcharge du convoyeur sur le moteur, celui du roulement sur la vibration moteur, celui du régime moteur sur la vitesse du convoyeur et une panne de pompe sur le débit et la pression.

Les cinq scénarios YAML sont : fonctionnement normal, dégradation du roulement, surcharge du convoyeur, anomalie de pompe et défaillance en cascade. Le mode `all` génère 100 pas × 5 scénarios × 4 équipements, soit 2 000 lignes reproductibles.

La phase 2 fournit deux méthodes complémentaires :

- un détecteur par seuils, explicable par les capteurs responsables ;
- un pipeline Isolation Forest par type d'équipement avec imputation, standardisation et sauvegarde Joblib.

Les modèles non supervisés sont entraînés uniquement sur une fraction chronologique des données normales. `is_anomaly`, `operating_state`, `failure_type` et `anomaly_severity` ne sont jamais des variables d'entrée ; elles servent uniquement à l'évaluation.

La phase 3 transforme une anomalie en diagnostic : équipement concerné, panne probable, capteurs responsables, gravité, confiance et explication. Elle combine des règles métier configurables et quatre classificateurs `RandomForestClassifier`. Si les deux approches sont d'accord, la confiance augmente ; sinon la prédiction la plus fiable est retenue, ou `unknown_fault` si les preuves sont insuffisantes.

Les pannes cataloguées couvrent la surchauffe, surcharge, perte de vitesse et défaut électrique du moteur ; l'usure, surchauffe et dommage sévère du roulement ; la surcharge, le glissement, la vitesse et la surchauffe du convoyeur ; la cavitation, obstruction, fuite, surchauffe et défaut de roulement de la pompe ; ainsi que `cascade_failure`, `unknown_fault` et `normal`.

La phase 4 estime la durée de vie restante (`Remaining Useful Life`, RUL) en cycles et en heures. Elle génère des trajectoires indépendantes allant du fonctionnement normal à la panne, calcule des tendances utilisant seulement le passé, compare une baseline fondée sur la santé à quatre `RandomForestRegressor`, puis fournit un intervalle empirique, un risque, une confiance technique et une explication.

La phase 5 transforme les diagnostics et la RUL en décisions opérationnelles : stratégie, action, priorité, échéance, compétences, pièces, durée, coût synthétique et ordre de travail. Un planificateur heuristique réserve les pièces, attribue les premières ressources génériques disponibles et bloque explicitement les interventions impossibles.

La phase 6 distribue ce pipeline entre neuf agents SPADE. En développement, SPADE démarre automatiquement PyJabber en mémoire, auto-enregistre les JID `@localhost` et transporte de vrais messages XMPP. Les intentions suivent FIPA-ACL, les données métier sont des enveloppes JSON versionnées et l'allocation de maintenance suit le Contract Net Protocol. Heartbeats, idempotence, retries exponentiels, dead-letter queue, liste blanche des JID et traçabilité par `trace_id` complètent le dispositif.

## Architecture

```text
configs/                         configurations YAML
data/synthetic/                  datasets générés
docs/phases_1b_2.md              choix techniques et limites
indusguard/digital_twin/         simulateurs et orchestration
indusguard/anomaly_detection/    préparation, détecteurs et évaluation
indusguard/fault_diagnosis/      catalogue, règles, ML et service hybride
indusguard/rul_prediction/       trajectoires, features, régression et RUL
indusguard/maintenance_planning/ catalogue, recommandations et planning
indusguard/multi_agent/          agents SPADE, protocoles, fiabilité et runtime
outputs/models/                  pipelines Isolation Forest
outputs/plots/                   graphiques des phases 1, 1B et 2
outputs/predictions/             prédictions et métriques
tests/                           tests unitaires
run_simulation.py                simulation historique du roulement
run_industrial_line_simulation.py simulation complète
train_anomaly_detector.py        entraînement et évaluation
predict_anomalies.py             inférence sur un CSV
train_fault_diagnosis.py         entraînement des classificateurs de panne
diagnose_faults.py               diagnostic hybride explicable
generate_rul_dataset.py          génération des trajectoires jusqu'à la panne
train_rul_models.py              entraînement des quatre modèles RUL
predict_rul.py                   prédiction, incertitude et risque
generate_maintenance_plan.py     recommandations, ordres et planning global
recommend_maintenance.py         recommandation pour un seul équipement
run_multi_agent_system.py        pipeline distribué SPADE/XMPP
run_multi_agent_demo.py          démonstration XMPP minimale
benchmark_multi_agent.py         stabilité sur 1 000 mesures
```

## Installation

Python 3.11 ou une version compatible est recommandé.

```bash
python -m venv .venv
# Windows PowerShell : .venv\Scripts\Activate.ps1
# Linux/macOS : source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Utilisation

La simulation historique reste disponible :

```bash
python run_simulation.py
```

Exécuter ensuite le workflow des phases 1B et 2 :

```bash
python run_industrial_line_simulation.py
python train_anomaly_detector.py
python predict_anomalies.py
python train_fault_diagnosis.py
python diagnose_faults.py
python generate_rul_dataset.py
python train_rul_models.py
python predict_rul.py
python generate_maintenance_plan.py
python recommend_maintenance.py --equipment-id bearing_03
python run_multi_agent_system.py --scenario normal
python run_multi_agent_system.py --scenario bearing_wear --speed 20
python run_multi_agent_system.py --scenario pump_cavitation
python run_multi_agent_system.py --scenario emergency
python run_multi_agent_system.py --scenario resource_unavailable
python run_multi_agent_demo.py
python check_agent_health.py
python benchmark_multi_agent.py
python -m pytest -q -m "not integration"
python -m pytest -q -m integration
python -m pytest -q
```

## Phase 6 : configuration et sorties

Le mode `embedded`, par défaut, ne demande ni Prosody ni comptes manuels. Le mode `external` utilise un serveur XMPP configuré par `INDUSGUARD_XMPP_DOMAIN`, les JID configurables et `INDUSGUARD_AGENT_PASSWORD`; l'auto-enregistrement y est désactivé par défaut. Copier éventuellement `.env.example` vers un fichier `.env` ignoré par Git, puis exporter les variables dans le shell : le projet ne dépend pas de `python-dotenv`.

Les agents sont `SensorAgent`, `AnomalyDetectionAgent`, `FaultDiagnosisAgent`, `RULPredictionAgent`, `MaintenanceAgent`, `ResourceAgent`, `SupervisorAgent`, `AlertAgent` et `HistorianAgent`. Les modèles des phases 2 à 4 sont chargés une seule fois et les algorithmes validés sont invoqués par des adaptateurs fins. Seuls les canaux d'alerte console et fichier sont actifs; aucun e-mail, SMS, Slack ou équipement physique n'est commandé.

Les journaux sont écrits dans `outputs/multi_agent/` (`messages.jsonl`, événements, décisions, alertes, santé, DLQ et métriques). Douze graphiques sont produits dans `outputs/plots/multi_agent/`. Les limites actuelles sont académiques : PyJabber embarqué est local et en mémoire, le catalogue de ressources est synthétique, l'ordonnancement n'est pas un optimiseur industriel et les scénarios ne doivent piloter aucune installation réelle. Voir `docs/phase_6_multi_agent_spade.md`.

Un autre fichier compatible peut être analysé ainsi :

```bash
python predict_anomalies.py --input chemin/mesures.csv --output chemin/predictions.csv
```

Les paramètres se trouvent dans `configs/industrial_line.yaml`, `configs/anomaly_detection.yaml`, `configs/fault_diagnosis.yaml` et `configs/rul_prediction.yaml`. Pour exécuter un seul scénario industriel, remplacer `simulation.scenario: all` par son identifiant.

## Résultats de référence

Avec la graine `42`, le dataset industriel contient 2 000 mesures, dont 343 anomalies. L'évaluation de phase 2 exclut les lignes normales utilisées à l'entraînement.

| Détecteur | Accuracy | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| Seuils | 0,964 | 0,994 | 0,918 | 0,955 |
| Isolation Forest | 0,929 | 0,851 | 1,000 | 0,920 |

Les détails globaux et par équipement sont enregistrés dans `outputs/predictions/metrics.json`.

Le diagnostic de phase 3 est évalué sur 500 lignes de test stratifiées et jamais utilisées pour entraîner les classificateurs.

| Diagnostic | Accuracy | Precision macro | Recall macro | F1 macro | F1 pondéré |
|---|---:|---:|---:|---:|---:|
| Règles | 0,920 | 0,620 | 0,805 | 0,679 | 0,905 |
| Machine Learning | 0,956 | 0,782 | 0,791 | 0,786 | 0,955 |
| Hybride | 0,942 | 0,728 | 0,830 | 0,742 | 0,940 |

Les classes `motor_overheating`, `conveyor_overload` et `pump_overheating` ont moins de dix exemples ; leurs métriques doivent donc être interprétées prudemment.

La phase 4 sépare les données par `asset_run_id` : 60 trajectoires complètes servent à l'entraînement et 20 autres au test. Les 12 trajectoires incomplètes restent réservées à la prédiction.

| Estimateur RUL | MAE | RMSE | R² | Erreur médiane |
|---|---:|---:|---:|---:|
| Baseline santé | 33,293 | 38,283 | 0,194 | 32,983 |
| Random Forest | 5,020 | 8,945 | 0,956 | 2,044 |

Le modèle place 72,8 % des prédictions à moins de 5 cycles, 85,9 % à moins de 10 cycles et 93,9 % à moins de 20 cycles de la vraie RUL.

La phase 5 analyse les 12 trajectoires RUL incomplètes représentant le parc actuel. Elle produit 9 maintenances préventives, 2 arrêts d'urgence et 1 inspection. Les priorités comprennent 2 critiques, 6 élevées et 4 moyennes. Huit ordres sont planifiés et quatre sont bloqués ; toutes les échéances des ordres planifiés sont respectées.

Le score de priorité combine gravité, RUL, risque, cascade, sécurité, impact de production et confiance avec des poids configurables. Les coûts sont des estimations synthétiques fondées sur la durée, les techniciens, les pièces et le temps d'arrêt.

## Fichiers produits

- `data/synthetic/bearing_scenario_001.csv` : phase 1, 200 mesures ;
- `data/synthetic/industrial_line_scenario.csv` : phase 1B, 2 000 mesures ;
- `outputs/predictions/anomaly_predictions.csv` : résultats des deux détecteurs ;
- `outputs/models/*_isolation_forest.joblib` : quatre pipelines ;
- `outputs/plots/industrial_line/` : sept graphiques de simulation ;
- `outputs/plots/anomaly_detection/` : six graphiques d'évaluation.
- `outputs/diagnosis/fault_diagnosis_predictions.csv` : diagnostics explicables ;
- `outputs/diagnosis/diagnosis_metrics.json` : métriques règles, ML et hybride ;
- `outputs/models/fault_diagnosis/` : quatre classificateurs Random Forest ;
- `outputs/plots/fault_diagnosis/` : huit graphiques de diagnostic.
- `data/synthetic/industrial_rul_dataset.csv` : 13 156 mesures sur 92 trajectoires ;
- `outputs/models/rul_prediction/` : quatre modèles RUL et les groupes train/test ;
- `outputs/rul_predictions/rul_predictions.csv` : RUL, intervalles, risque et explications ;
- `outputs/rul_predictions/rul_metrics.json` : métriques baseline et ML ;
- `outputs/plots/rul_prediction/` : dix graphiques RUL.
- `outputs/maintenance/maintenance_recommendations.csv` : recommandations détaillées ;
- `outputs/maintenance/work_orders.csv` : douze ordres de travail ;
- `outputs/maintenance/maintenance_schedule.csv` : créneaux et ressources ;
- `outputs/maintenance/maintenance_metrics.json` : cohérence, coûts et conflits ;
- `outputs/plots/maintenance_planning/` : dix graphiques du plan.

## Tests et limites

```bash
python -m pytest -q
```

Le modèle reste une approximation pédagogique : plages et dépendances sont simplifiées, les scénarios synthétiques sont plus réguliers que des pannes réelles et les modèles doivent être recalibrés sur des données terrain avant tout usage industriel. Les percentiles des arbres ne sont pas un intervalle statistique calibré. Les coûts, stocks, ressources et consignes de sécurité de phase 5 sont synthétiques et ne remplacent ni un système de gestion de maintenance ni les procédures officielles. Voir [docs/phases_1b_2.md](docs/phases_1b_2.md), [docs/phase_3_fault_diagnosis.md](docs/phase_3_fault_diagnosis.md), [docs/phase_4_rul_prediction.md](docs/phase_4_rul_prediction.md) et [docs/phase_5_maintenance_planning.md](docs/phase_5_maintenance_planning.md).
