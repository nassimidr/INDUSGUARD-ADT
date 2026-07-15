# Phase 7 — Supervision temps réel

## Périmètre

Cette phase rend les résultats des phases 1 à 6 consultables depuis une interface locale. Elle ne pilote aucun automate : tous les scénarios et toutes les décisions sont synthétiques. L'API écoute par défaut uniquement sur `127.0.0.1`.

## Architecture

Le backend FastAPI expose les routes versionnées sous `/api/v1` et le flux `/ws/dashboard`. SQLAlchemy persiste 15 familles de données dans SQLite : actifs, mesures, anomalies, diagnostics, RUL, recommandations, ordres, planning, santé et messages agents, événements, décisions, alertes, traces et exécutions.

L'importeur lit les CSV/JSONL générés par le projet. Les clés naturelles et index uniques rendent son exécution idempotente. SQLite utilise WAL et les clés étrangères sont activées à chaque connexion. Alembic porte le schéma initial dans `migrations/versions/0001_phase7_dashboard.py`.

L'adaptateur `DashboardPersistenceAdapter` utilise une file bornée et un thread d'écriture. Le pipeline SPADE continue si le dashboard est indisponible ; les fichiers CSV/JSONL restent la source reconstructible.

Le frontend Vite utilise React, TypeScript strict, MUI, TanStack Query et Plotly. Le serveur Vite relaie `/api` et `/ws` vers l'API locale.

## Installation et démarrage

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-dashboard.txt
python import_dashboard_history.py
python run_dashboard.py
```

Dans un second terminal :

```bash
cd frontend
npm install
npm run dev
```

- Interface : `http://127.0.0.1:5173`
- OpenAPI : `http://127.0.0.1:8000/docs`
- Santé : `http://127.0.0.1:8000/api/v1/health`

Une base vide peut être initialisée avec `alembic upgrade head`. Les futures modifications de schéma doivent être ajoutées sous forme de nouvelle révision.

## Temps réel

Le client se connecte à `/ws/dashboard`, puis envoie :

```json
{"event_types": ["alert.created", "work_order.updated", "system_run.started"]}
```

Une liste vide souscrit à tous les événements. Les messages reçus suivent `{"event": "...", "data": {...}}`.

Pour persister aussi les événements SPADE dans SQLite :

```powershell
$env:INDUSGUARD_DASHBOARD_ENABLED="1"
python run_multi_agent_system.py --scenario normal --max-measurements 100
```

## Sécurité et limites

- écoute loopback et CORS restreint au frontend local ;
- validation Pydantic des commandes et statuts ;
- scénarios limités à la liste blanche YAML ;
- processus démarrés par liste d'arguments avec `shell=False` ;
- aucun accès XMPP ou SQLite depuis le navigateur ;
- aucune commande d'équipement physique ;
- absence volontaire d'authentification, acceptable uniquement pour cette démonstration locale.

Avant une exposition réseau, ajouter TLS, authentification, contrôle d'accès, gestion de secrets, limites de débit et une base serveur.

## Validation

```bash
python -m pytest -q
cd frontend
npm run test
npm run lint
npm run build
```

La seconde exécution de `python import_dashboard_history.py` doit afficher zéro ajout pour chaque catégorie.
