# Audit des phases 8A à 8G — INDUSGUARD-ADT

Date de l'audit : 20 juillet 2026  
Environnement : Windows, Python 3.10.11, Node.js 24.14.1, npm 11.11.0  
Révision auditée : branche `main`, alignée sur `origin/main` au début de l'audit  
État Git initial : propre, aucun fichier modifié ou non suivi

## Conclusion exécutive

Le projet est **non conforme aux phases 8A à 8G**. Le socle des phases 0 à 7 est réel et largement testé, mais aucune chaîne Vision → Belief state → Fusion multimodale → RAG → Simulation comparative → Validation humaine n'existe dans le code. La phase 8G ne peut donc pas expérimenter cette chaîne.

Les 136 tests Python et les 4 tests frontend existants passent. Ils valident principalement les phases 0 à 7 et ne constituent pas une preuve pour les phases 8A à 8G. Un lancement SPADE réel sur 400 mesures de dégradation retourne le code 0, mais produit 1 timeout, 15 traces échouées, 449 messages perdus et une latence P95 de 59,283 s. La cible de 10 s n'est pas atteinte.

| Phase | Statut | Code présent | Intégration | Tests | Démonstration | Problèmes bloquants |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 8A Vision | ABSENTE | Non | Non | Non | Non | Aucun module, dataset image, poids, script ou agent vision |
| 8B Belief state | ABSENTE | Non | Non | Non | Non | Aucun schéma probabiliste, historique ou table de beliefs |
| 8C Fusion | ABSENTE | Non | Non | Non | Non | Aucune modalité commune ni fusion probabiliste multimodale |
| 8D LLM/RAG | ABSENTE | Non | Non | Non | Non | Aucun corpus, ingestion, index, modèle local ou KnowledgeAgent |
| 8E Simulation actions | COMMENCÉE | Pré requis seulement | Non | Non | Non | Une recommandation unique ; aucune simulation de trois actions |
| 8F Validation humaine | COMMENCÉE | Pré requis seulement | Non | Non | Non | Aucun cycle opérateur ; transition critique directe autorisée |
| 8G Expérimentation | COMMENCÉE | Phase 0–7 seulement | Non | Non | Non | Aucune matrice baselines/ablations/robustesse des phases 8 |

Les statuts ci-dessus sont ceux du diagnostic initial. Les corrections limitées réalisées après ce diagnostic sont consignées dans la section « Corrections post-audit » ; elles ne changent aucun statut de phase.

## 1. Périmètre et méthode

L'audit a combiné :

- inventaire de tous les fichiers suivis et de l'état Git ;
- lecture du README, des sept documents présents et des dix configurations YAML ;
- recherche transversale des concepts phase 8, routes, modèles, schémas, agents, composants, stubs et exceptions ignorées ;
- inspection des contrats Python, de la migration SQLAlchemy/Alembic, de l'API et du frontend ;
- collecte et exécution des tests ;
- vérification Alembic, OpenAPI, API et WebSocket ;
- lancement réel du runtime SPADE/PyJabber dans une copie temporaire pour protéger les sorties versionnées ;
- vérification des sorties, types de messages, `trace_id`, identifiants d'équipement et métriques de latence.

Une fonctionnalité n'a été considérée présente que lorsqu'un code appelable et intégré a été trouvé. Les bibliothèques installées globalement sur la machine ne sont pas considérées comme des dépendances du projet lorsqu'elles ne sont ni déclarées ni utilisées.

## 2. Cartographie du projet

### 2.1 Structure et artefacts

| Catégorie | Emplacement | Constat |
| --- | --- | --- |
| Simulation | `indusguard/digital_twin/` | 5 modules de simulation, scénarios synthétiques |
| Anomalies | `indusguard/anomaly_detection/` | Seuils et Isolation Forest |
| Diagnostic | `indusguard/fault_diagnosis/` | Règles, Random Forest et service hybride |
| RUL | `indusguard/rul_prediction/` | Baseline, Random Forest, intervalle empirique |
| Maintenance | `indusguard/maintenance_planning/` | Recommandation unique, coûts, ressources, planning |
| Multi-agents | `indusguard/multi_agent/` | 9 agents SPADE, protocoles, adaptateurs, persistance |
| API/dashboard | `indusguard/dashboard/` | FastAPI, WebSocket, SQLAlchemy, 42 chemins OpenAPI |
| Frontend | `frontend/src/` | React/TypeScript, 12 routes/pages phase 7 |
| Configuration | `configs/*.yaml` | 10 fichiers, uniquement phases 0 à 7 |
| Données | `data/synthetic/` | 3 CSV synthétiques, aucune image/vidéo/PDF |
| Modèles | `outputs/models/` | 4 Isolation Forest, 4 classificateurs, 4 modèles RUL |
| Tests | `tests/`, `frontend/src/**/*.test.tsx` | 136 tests Python, 4 tests frontend |
| Documentation | `README.md`, `docs/phase*.md` | Phases 1B à 7, aucune documentation phase 8 |
| Rapports/sorties | `outputs/` | CSV, JSON, JSONL et PNG des phases 0 à 7 |
| Migrations | `migrations/versions/0001_phase7_dashboard.py` | Une révision, 15 tables phase 7 |
| Lancements | Scripts `run_*`, `train_*`, `predict_*`, `generate_*` | Aucun script phase 8 ou expérience globale |

Le dépôt contient 208 fichiers Python, 56 PNG, 13 CSV, 12 Joblib, 10 JSON, 10 YAML, 8 TSX et 7 fichiers Markdown hors caches/dépendances. Les seuls fichiers quasi vides sont des marqueurs ou sorties attendues : `data/dashboard/.gitkeep` et une DLQ vide.

### 2.2 Agents SPADE réellement exportés

`SensorAgent`, `AnomalyDetectionAgent`, `FaultDiagnosisAgent`, `RULPredictionAgent`, `MaintenanceAgent`, `ResourceAgent`, `SupervisorAgent`, `AlertAgent` et `HistorianAgent` sont exportés et instanciés par `MultiAgentRuntime`.

Il n'existe ni `VisionAgent`, ni `CameraAgent`, ni `KnowledgeAgent`, ni agent de fusion, de simulation comparative ou de validation opérateur. Les vocabulaires `MESSAGE_TYPES`, `ONTOLOGIES` et `CASE_STATES` ne contiennent aucun événement phase 8.

### 2.3 Routes FastAPI et pages React

OpenAPI contient 42 chemins couvrant santé, configuration, actifs, mesures, anomalies, diagnostics, RUL, recommandations de maintenance, ordres de travail, agents, alertes, traces et exécutions.

Les contrôles explicites suivants sont négatifs :

- `/api/v1/vision` : absent ;
- `/api/v1/beliefs` : absent ;
- `/api/v1/knowledge` : absent ;
- `/api/v1/recommendations/{id}/accept` : absent ;
- routes modify/reject/request-observation : absentes.

Les 12 pages React correspondent au dashboard phase 7 : vue générale, ligne, actifs, détail actif, anomalies, RUL, maintenance, agents, alertes, traces, runs et paramètres. Aucun composant vision, belief, contribution multimodale, citation RAG, alternatives ou validation humaine n'est monté.

### 2.4 Modèles SQLAlchemy et schémas Pydantic

Les 15 tables sont : assets, mesures, anomalies, diagnostics, RUL, recommandations, ordres, planning, santé agent, messages agent, événements, décisions, alertes, traces et runs.

Il manque toutes les persistances requises pour :

- image/frame et détection vision ;
- belief courant, versions, distribution et preuves ;
- observations multimodales et contributions ;
- documents, chunks, embeddings, citations et connaissances structurées ;
- alternatives simulées et classement ;
- décision humaine, ancienne/nouvelle recommandation, opérateur et journal d'audit.

Les seuls schémas Pydantic dashboard sont une mise à jour de statut d'ordre, le lancement d'un run, les événements WebSocket et leur enveloppe. Le contrat agent est une `dataclass`, sans payload métier Pydantic par type de message.

### 2.5 Flux réellement présent

```text
CSV capteurs synthétiques
→ SensorAgent
→ AnomalyDetectionAgent
→ FaultDiagnosisAgent
→ RULPredictionAgent
→ MaintenanceAgent
→ ResourceAgent / SupervisorAgent
→ HistorianAgent / AlertAgent
→ CSV/JSONL et, optionnellement, SQLite
→ API FastAPI / dashboard React
```

Le flux demandé n'existe pas :

```text
RUL -X→ Vision -X→ Belief state -X→ Fusion multimodale
    -X→ RAG -X→ Simulation comparative -X→ Validation humaine
    -X→ Expérimentation phase 8
```

## 3. Phase 8A — Vision industrielle

**Statut : ABSENTE**

1. **Fichiers analysés** : inventaire complet, `requirements*.txt`, configs, agents, constantes, API, modèles, frontend, données et sorties.
2. **Fonctionnalités trouvées** : aucune fonctionnalité vision. Les PNG sous `outputs/plots/` sont des graphiques Matplotlib, pas des images industrielles d'entrée.
3. **Fonctionnalités utilisées** : aucune.
4. **Tests présents** : aucun test image, vidéo, prétraitement, modèle, métrique, inférence ou agent vision.
5. **Tests exécutés** : collecte complète de 136 tests Python et 4 frontend ; aucun ne cible 8A.
6. **Résultats des commandes** : recherche `vision|camera|image|frame` sans module métier ; aucun chemin API ou type de message vision.
7. **Erreurs trouvées** : aucun dossier vision, dataset/annotation/licence/split, poids, entraînement, évaluation, inférence, mode caméra indisponible ou conservation de frame.
8. **Risques** : impossible de vérifier fuite de données, authenticité des métriques, confiance ou rattachement équipement.
9. **Tâches manquantes** : l'intégralité des éléments obligatoires 8A.
10. **Priorité** : P0, car 8A bloque le scénario complet et 8C/8G.
11. **Preuve du statut** : aucun fichier, import, route, table, composant, dépendance déclarée ou message vision. OpenCV/Torch installés globalement ne sont ni déclarés ni utilisés par le dépôt.

Le critère « une image de test traverse le pipeline jusqu'au dashboard ou au belief state » est impossible à exécuter.

## 4. Phase 8B — Belief state probabiliste

**Statut : ABSENTE**

1. **Fichiers analysés** : modèles et schémas dashboard, schéma agent, constantes, agents, adaptateurs, API, migration et frontend.
2. **Fonctionnalités trouvées** : des confiances scalaires de diagnostic/RUL et un score de santé ; ce ne sont pas un belief state.
3. **Fonctionnalités utilisées** : aucune distribution multi-hypothèses n'est lue ou mise à jour.
4. **Tests présents** : aucun test de normalisation, update, contradiction, provenance ou historique.
5. **Tests exécutés** : aucun test collecté ne mentionne un belief.
6. **Résultats des commandes** : aucune occurrence métier `belief`; aucune table ou route associée.
7. **Erreurs trouvées** : absence de distribution sommant à 1, état inconnu, incertitude consolidée, RUL interval typé, preuves, provenance, contraintes, actions et versions.
8. **Risques** : les confiances isolées peuvent être prises à tort pour une représentation probabiliste ; aucune évolution temporelle n'est auditée.
9. **Tâches manquantes** : schéma central, moteur d'update, persistance versionnée, API, agent, frontend et tests.
10. **Priorité** : P0, prérequis de 8C, 8E et 8G.
11. **Preuve du statut** : `FaultDiagnosis.confidence` et `RULPrediction.prediction_confidence` sont des scalaires ; aucune structure ne conserve plusieurs hypothèses.

## 5. Phase 8C — Fusion multimodale

**Statut : ABSENTE**

1. **Fichiers analysés** : service de diagnostic, prétraitement maintenance, adaptateurs agents, configurations et tests associés.
2. **Fonctionnalités trouvées** : la phase 3 combine règles et ML sur la même modalité capteur ; la phase 5 joint des CSV anomalies/diagnostic/RUL. Ce n'est pas une fusion multimodale probabiliste.
3. **Fonctionnalités utilisées** : aucune modalité vision, document ou opérateur n'entre dans le diagnostic final.
4. **Tests présents** : aucun des six scénarios obligatoires de fusion.
5. **Tests exécutés** : les tests du diagnostic hybride et du merge phase 5 passent, mais ne couvrent pas 8C.
6. **Résultats des commandes** : aucun poids multimodal configurable, contribution, calibration, gestion de contradiction ou modalité manquante.
7. **Erreurs trouvées** : pas de schéma commun, distribution par modalité, incertitude par modalité ou méthode documentée.
8. **Risques** : le mot « fusion » dans les docs phases 3/5 crée un faux positif de réalisation.
9. **Tâches manquantes** : moteur complet de fusion, explications, configuration, intégration belief et tests comparatifs.
10. **Priorité** : P0 après 8A/8B/8D.
11. **Preuve du statut** : seuls les capteurs alimentent la chaîne SPADE ; aucun type de message phase 8 n'a été observé parmi 3 027 messages du run réel.

## 6. Phase 8D — LLM local et RAG

**Statut : ABSENTE**

1. **Fichiers analysés** : données, requirements, configs, agents, API, modèles, frontend et tests.
2. **Fonctionnalités trouvées** : aucune.
3. **Fonctionnalités utilisées** : aucune.
4. **Tests présents** : aucun test ingestion/chunk/index/recherche/citation/JSON/fallback.
5. **Tests exécutés** : aucun test RAG ou LLM collecté.
6. **Résultats des commandes** : aucun PDF ou corpus technique ; Chroma, FAISS, sentence-transformers et Ollama ne sont pas installés ; Transformers global n'est pas déclaré ni utilisé.
7. **Erreurs trouvées** : absence de corpus/licence, extraction, chunks, embeddings, index, retrieval, prompt contextualisé, modèle local, validation de sortie et vocabulaire contrôlé.
8. **Risques** : aucune défense contre hallucination ou action inconnue ; aucun mode sans LLM puisqu'il n'existe pas de mode avec LLM.
9. **Tâches manquantes** : l'intégralité des éléments 8D, y compris `KnowledgeAgent` et preuves documentaires.
10. **Priorité** : P0 pour le périmètre phase 8, P1 si un mode dégradé sans RAG est accepté temporairement.
11. **Preuve du statut** : aucun artefact documentaire/vectoriel, route, table, agent, configuration ou dépendance RAG.

## 7. Phase 8E — Simulation comparative des actions

**Statut : COMMENCÉE**

1. **Fichiers analysés** : `maintenance_planning/`, configs maintenance, `MaintenanceAgent`, Contract Net, modèles/API/frontend maintenance et tests.
2. **Fonctionnalités trouvées** : coût synthétique, priorité, durée, ressources, pièces, stratégie et recommandation unique.
3. **Fonctionnalités utilisées** : la recommandation unique alimente la négociation de ressources et peut créer un ordre.
4. **Tests présents** : tests du coût, de la priorité, du catalogue, du planning et du Contract Net ; aucun test de simulation comparative.
5. **Tests exécutés** : les tests existants passent.
6. **Résultats des commandes** : 116 recommandations et 8 ordres ont été produits sur le run réel, mais sans alternatives ni utilité comparative.
7. **Erreurs trouvées** : moins de trois actions candidates, aucune projection de risque/RUL par action, aucune fonction d'utilité, aucun classement ou risque résiduel.
8. **Risques** : une heuristique unique peut être présentée à tort comme une décision prescriptive optimisée.
9. **Tâches manquantes** : modèle d'action, simulateur, paramètres de coût/production/sécurité/incertitude, persistance des alternatives, API, frontend et tests.
10. **Priorité** : P0 pour le critère 8E ; P1 après stabilisation des beliefs/fusion.
11. **Preuve du statut** : `MaintenanceRecommendation` ne possède qu'un `recommended_action`; aucune table alternative/utility et aucune route de classement.

Le critère « trois actions simulées, classées et consultables dans l'API et le dashboard » échoue.

## 8. Phase 8F — Validation humaine

**Statut : COMMENCÉE**

1. **Fichiers analysés** : modèles recommandation/ordre/décision, schémas, routes API, page Maintenance, SupervisorAgent, tests API/frontend.
2. **Fonctionnalités trouvées** : lecture des recommandations, modification directe du statut d'un ordre et acquittement d'alertes.
3. **Fonctionnalités utilisées** : la page Maintenance appelle `PATCH /work-orders/{id}/status` sans confirmation, identité ou commentaire.
4. **Tests présents** : un test accepte `scheduled → in_progress` et un test rejette un statut lexical inconnu ; aucun test du cycle humain requis.
5. **Tests exécutés** : les tests existants passent ; un test exploratoire démontre le contournement critique.
6. **Résultats des commandes** : un ordre `critical` initialement `proposed` passe à `completed` avec HTTP 200 et sans opérateur.
7. **Erreurs trouvées** : routes accept/modify/reject/request-observation absentes ; états et journal humain absents ; pas de contrôle de transition, permissions, version optimiste ou concurrence.
8. **Risques** : contournement de validation, perte de l'ancienne recommandation, écrasement concurrent, ordre actif après refus impossible à empêcher.
9. **Tâches manquantes** : modèle de décision, endpoints, machine d'état, verrou critique, événement de nouvelle observation, RBAC, confirmation frontend et tests de concurrence.
10. **Priorité** : P0, car l'API actuelle autorise une transition critique non contrôlée.
11. **Preuve du statut** : réponse observée `{'status_code': 200, 'priority': 'critical', 'initial_status': 'proposed', 'result_status': 'completed', 'operator_required': False}`.

Le Contract Net `accept-proposal/reject-proposal` est une négociation automatique entre agents de ressources ; il ne représente pas une validation humaine.

## 9. Phase 8G — Expérimentation complète

**Statut : COMMENCÉE**

1. **Fichiers analysés** : scripts train/evaluate/benchmark, JSON de métriques, split RUL, configs, docs et plots.
2. **Fonctionnalités trouvées** : seeds, splits de trajectoires RUL disjoints, métriques phases 2–6, benchmark multi-agent et graphiques générés.
3. **Fonctionnalités utilisées** : les scripts phases 2–6 produisent des métriques réelles pour leur périmètre.
4. **Tests présents** : reproductibilité simulation/RUL et tests unitaires ; aucune matrice expérimentale phase 8.
5. **Tests exécutés** : 136 tests Python passent ; lancement SPADE 100 puis 400 mesures effectué.
6. **Résultats des commandes** : run 400 mesures : 116 anomalies/diagnostics/RUL/recommandations, 8 ordres, 1 timeout, 15 traces échouées, 449 messages perdus, succès pipeline 0,9635, moyenne 22,098 s, P95 59,283 s.
7. **Erreurs trouvées** : aucune des 5 baselines et 7 ablations requises ; métriques perception/decision incomplètes ; pas de campagne robustesse ; pas de commande unique phase 8 ; code de sortie 0 malgré l'échec partiel.
8. **Risques** : graphiques historiques non reliés à un manifeste immuable ; résultats partiels susceptibles d'être interprétés comme un succès complet.
9. **Tâches manquantes** : runner d'expériences, manifests, seeds globaux, toutes les baselines/ablations/robustesses, statistiques, artefacts bruts et contrôle de seuil de latence.
10. **Priorité** : P0 après disponibilité de 8A–8F ; P1 pour rendre le runtime honnête sur ses erreurs dès maintenant.
11. **Preuve du statut** : les JSON présents exposent seulement anomalies, diagnostic, RUL, maintenance et multi-agent. Aucun résultat ne compare système complet/sans vision/sans LLM/sans belief/fusions.

La cible P95 < 10 s échoue sur le run forcé : 59,283 s. Un ancien artefact versionné indique déjà 33,007 s.

## 10. Vérification d'intégration globale

| Étape demandée | Résultat | Preuve |
| --- | --- | --- |
| Démarrer les services | Partiel | FastAPI/TestClient, WebSocket et SPADE embarqué démarrent |
| Générer/charger scénario et capteurs | Réussi | CSV synthétique, 400 mesures publiées |
| Injecter une image | Échoué | Aucun chargeur ni endpoint vision |
| Détecter anomalie | Réussi sur socle | 116 anomalies sur le run forcé |
| Diagnostic | Réussi avec pertes | 116 produits selon métriques |
| RUL | Réussi avec pertes | 116 produites selon métriques |
| Interroger RAG | Échoué | RAG absent |
| Mettre à jour belief | Échoué | Belief absent |
| Fusionner modalités | Échoué | Fusion absente |
| Générer trois actions | Échoué | Une recommandation seulement |
| Simuler/classer | Échoué | Simulateur/utilité absents |
| Validation opérateur | Échoué | Workflow absent, contournement critique possible |
| Persister/afficher toutes les étapes | Échoué | Tables et pages phase 8 absentes |
| Même `trace_id` | Partiel | 51 traces observées avec la chaîne phase 1–6 requise ; 0 type de message phase 8 |
| Même equipment_id | Réussi sur messages observés | 0 trace contenant plusieurs equipment_id |

Le scénario end-to-end phase 8 est **échoué** dès l'étape image. Le run SPADE phase 0–7 ne peut pas servir de substitut.

## 11. Résultats des commandes

| Commande/vérification | Résultat |
| --- | --- |
| `git status --short --branch` | Propre : `main...origin/main` |
| `python -m pytest -v` | 136 réussis, 0 échoué, 1 avertissement, 38,15 s |
| `python -m pytest --cov=indusguard --cov-report=term-missing` | Échec initial : arguments `--cov` inconnus ; après correction d'outillage : 138 réussis, couverture totale 67 % |
| `ruff check .` | Non exécuté : `ruff` absent |
| `mypy indusguard` | Non exécuté : `mypy` absent |
| `pre-commit run --all-files` | Non exécuté : `pre-commit` absent |
| `npm install` | Réussi, à jour, 0 vulnérabilité signalée |
| `npm run lint` | Réussi |
| `npm run test` | 1 fichier, 4 tests réussis, 0 échoué |
| `npm run build` | Réussi ; bundles JS principaux 528,63 kB et 1 085,95 kB |
| `alembic heads/current/upgrade head` | Réussi, `0001_phase7 (head)` |
| API `/health` | HTTP 200, DB connectée |
| `/openapi.json` | HTTP 200, 42 chemins ; chemins phase 8 absents |
| WebSocket `/ws/dashboard` | Souscription réussie |
| SPADE 100 mesures | Code 0, branche normale seulement, P95 3,082 s |
| SPADE 400 mesures | Code 0 malgré timeout/pertes, P95 59,283 s |

L'avertissement Python concerne la dépréciation de `fastapi.testclient` avec la version de `httpx` installée. Il ne fait pas échouer les tests.

## 12. Faux positifs de réalisation et défauts transverses

- Les termes « fusion hybride » et « fusion des sorties » concernent des résultats capteurs/CSV, pas des modalités indépendantes.
- `accept-proposal`/`reject-proposal` correspond au Contract Net automatique, pas à un Human-in-the-loop.
- Les fichiers PNG sont des graphiques, pas un corpus vision.
- Les confidences scalaires ne sont pas un belief state.
- Le benchmark phase 6 n'est pas une expérimentation comparative phase 8G.
- `tests/test_multi_agent_end_to_end.py` appelle directement quatre adaptateurs sur une seule ligne et explicitement sans serveur XMPP ; il ne valide pas un E2E système complet.
- `tests/test_spade_embedded_integration.py` valide un message XMPP contenant `value: 42`, pas la chaîne métier.
- Le frontend n'a que 4 tests sur des composants partagés ; les pages, boutons de run, changement de statut, API et scénarios d'erreur ne sont pas testés côté UI.
- `DashboardPersistenceAdapter` ignore silencieusement `queue.Full` et toute exception SQL : la source CSV continue, mais la perte SQL n'est ni métrée ni visible.
- Le runtime retourne le code 0 malgré un timeout et des traces échouées ; le dashboard peut marquer le run `completed`.
- Les statuts d'ordre sont validés lexicalement, pas par une machine de transitions.
- Aucun test vide sans assertion n'a été trouvé par le contrôle statique simple.
- Les `pass` trouvés sont surtout des classes marqueurs ou des gestions d'annulation ; les canaux Email/SMS/Slack sont explicitement non implémentés et documentés comme futurs.
- Les résultats historiques phases 0–7 n'ont pas été modifiés pendant l'audit.

## 13. Plan de correction priorisé

### P0 — Bloquant

| Phase | Fichier concerné | Problème | Correction proposée | Tests à ajouter | Critère d'acceptation |
| --- | --- | --- | --- | --- | --- |
| 8A | Nouveau `indusguard/vision/`, agent, API, UI | Phase absente | Concevoir dataset/licence/splits, pipeline demo, modèle, scripts et événement versionné | Unitaires + image→belief/dashboard | Une image test produit défaut, confiance, frame, équipement et trace persistés |
| 8B | Nouveau domaine belief + migration | Phase absente | Schéma probabiliste normalisé, versionné et persistant | Normalisation, null, contradiction, provenance, concurrence | Une observation modifie et versionne une distribution consultable |
| 8C | Nouveau service fusion + config | Phase absente | Fusion probabiliste pondérée avec modalités absentes/contradictoires | Les 6 scénarios obligatoires + baseline moyenne | Résultat et contributions changent selon modalités |
| 8D | Nouveau domaine knowledge/RAG | Phase absente | Corpus licencié, ingestion, index, retrieval, sortie Pydantic, citations, fallback | Les 10 tests obligatoires | Connaissance structurée avec citation vérifiable |
| 8E | Nouveau simulateur décision + tables/API/UI | Comparaison absente | Simuler au moins 3 actions avec utilité configurable | Classement, sécurité, incertitude, persistance | Trois alternatives distinctes classées et consultables |
| 8F | Modèles/routes/UI validation | Contournement critique | Machine d'état opérateur, RBAC, audit immuable, optimistic locking | Accept/modify/reject/observe, critique, refus, concurrence | Aucun ordre critique actif/exécuté avant validation explicite |
| 8G | Nouveau runner `experiments/` | Campagne absente | Orchestrateur reproductible des baselines/ablations/robustesses | Reproductibilité, provenance, seuils qualité | Une commande reconstruit tableaux et graphes depuis résultats bruts |

### P1 — Important

| Phase | Fichier concerné | Problème | Correction proposée | Tests à ajouter | Critère d'acceptation |
| --- | --- | --- | --- | --- | --- |
| 8G/6 | `multi_agent/runtime.py`, lanceur | Code 0 malgré pertes/timeouts | Échouer ou déclarer `degraded` selon seuils configurés | Timeout, traces perdues, code retour | Le dashboard ne marque jamais `completed` un run hors seuil |
| 8G/7 | `dashboard_persistence_adapter.py` | Exceptions/pertes silencieuses | Journaliser et métriser queue pleine et erreurs SQL | Queue pleine, contrainte SQL, reprise | Toute perte est observable sans interrompre le pipeline |
| 8G | dépendances de test | Couverture impossible | Déclarer `pytest-cov` dans les dépendances de développement | CI coverage | La commande demandée produit un pourcentage et un rapport missing |
| 8F | page Maintenance | Mutation sans confirmation | Dialogue de confirmation et affichage conséquences/incertitude | Tests UI interactions/erreurs | Toute décision humaine est explicite et confirmée |
| 8G | tests E2E | Tests actuels trop étroits | Ajouter test réel métier XMPP/API/DB/WebSocket | Scénario anomalie complet | Une trace traverse réellement tous les composants disponibles |

### P2 — Amélioration

| Phase | Fichier concerné | Problème | Correction proposée | Tests à ajouter | Critère d'acceptation |
| --- | --- | --- | --- | --- | --- |
| Toutes | requirements/config qualité | Ruff, mypy, pre-commit absents | Ajouter dépendances, configurations et CI | Lint/type hooks | Commandes documentées et vertes |
| 8G | métriques | AUROC/AUPRC/Brier/ECE absents | Étendre évaluateurs avec calibration | Jeux synthétiques connus | Valeurs reproductibles et interprétées |
| 7/8 | frontend | Bundle Plotly volumineux | Vérifier découpage/lazy loading | Budget bundle | Build sous budget défini |
| 7 | compatibilité | Avertissement TestClient/httpx | Aligner versions FastAPI/Starlette/httpx | Suite API | Aucun avertissement de compatibilité |

### P3 — Optionnel

| Phase | Fichier concerné | Problème | Correction proposée | Tests à ajouter | Critère d'acceptation |
| --- | --- | --- | --- | --- | --- |
| 8A | acquisition | Pas de caméra réelle | Ajouter adaptateur caméra optionnel après validation demo | Caméra absente/reconnexion | Le mode demo reste totalement fonctionnel sans matériel |
| 8D | LLM | Aucun backend alternatif | Supporter Ollama et llama.cpp derrière interface | Contract tests backend | Les deux backends respectent le même schéma |
| 8G | statistiques | Pas de tests statistiques | Ajouter intervalles/bootstrap quand taille suffisante | Reproductibilité bootstrap | Incertitude des comparaisons publiée |

## 14. Corrections post-audit

Cette section est volontairement séparée du diagnostic initial. Elle doit être complétée après application et revalidation des seules corrections simples autorisées. Une correction d'outillage ou d'observabilité ne valide pas une phase absente.

Deux corrections non destructives ont été appliquées après le diagnostic :

1. `pytest-cov` a été ajouté à `requirements.txt`. La commande de couverture demandée est maintenant exécutable et reproductible. Résultat : **138 tests réussis, 0 échoué, couverture globale 67 %**.
2. `DashboardPersistenceAdapter` journalise maintenant une file pleine et les exceptions SQL au lieu de les ignorer silencieusement. Deux tests vérifient ces deux chemins d'erreur.
3. Les artefacts `.coverage` et `htmlcov/` sont maintenant ignorés par Git ; l'artefact temporaire produit pendant l'audit a été supprimé.

La couverture met notamment en évidence :

- 0 % sur l'importeur historique dashboard et plusieurs évaluateurs/visualiseurs ;
- 37 % sur le runtime multi-agent ;
- 27 à 56 % sur les agents principaux ;
- 36 % sur le gestionnaire de processus dashboard ;
- 46 % sur l'adaptateur de persistance dashboard malgré les deux nouveaux chemins testés.

Ces corrections améliorent l'auditabilité et l'outillage, mais ne créent aucune fonctionnalité 8A–8G. Tous les statuts restent donc inchangés.

## 15. Synthèse terminale

```text
AUDIT INDUSGUARD-ADT TERMINÉ

Phase 8A — ABSENTE
Phase 8B — ABSENTE
Phase 8C — ABSENTE
Phase 8D — ABSENTE
Phase 8E — COMMENCÉE
Phase 8F — COMMENCÉE
Phase 8G — COMMENCÉE

Tests Python : 138 réussis / 0 échoué
Tests frontend : 4 réussis / 0 échoué
Couverture : 67 % après ajout de pytest-cov
Lint : frontend réussi ; Python non exécuté (ruff absent)
Build frontend : réussi
Scénario end-to-end : échoué

Rapport :
docs/audit_phases_8A_8G.md

Conclusion générale :
Projet non conforme aux phases 8A à 8G
```
