# INDUSGUARD-ADT

**INDUSGUARD-ADT** est un projet générique de jumeau numérique agentique destiné à la maintenance prescriptive industrielle. À terme, il pourra aider à surveiller des équipements, étudier leur dégradation et comparer des décisions de maintenance dans différents domaines industriels.

Cette première phase reste volontairement simple : elle simule uniquement les mesures d'un roulement industriel. Elle ne contient ni intelligence artificielle, ni agents, ni interface web, ni base de données.

## Comprendre la simulation

Un **roulement** est une pièce mécanique qui aide un axe à tourner en réduisant les frottements.

Un **simulateur** est un programme qui reproduit de manière simplifiée le comportement d'un système. Ici, le programme imite l'évolution des capteurs d'un roulement sans se connecter à une machine réelle.

Une **donnée synthétique** est une donnée créée artificiellement. Les mesures de ce projet sont réalistes dans leur forme, mais elles ne proviennent pas d'un véritable équipement.

Commencer par une simulation permet de construire et tester la chaîne de génération de données de façon sûre, peu coûteuse et reproductible. Grâce à la graine aléatoire configurée, les mêmes paramètres produisent les mêmes valeurs numériques.

Le scénario comporte trois états :

- `normal` : 100 mesures pendant lesquelles le roulement fonctionne correctement ;
- `degradation` : 60 mesures pendant lesquelles les vibrations et la température augmentent tandis que la santé diminue ;
- `critique` : 40 mesures pendant lesquelles le roulement est fortement dégradé.

## Contenu du fichier CSV

| Colonne | Signification |
|---|---|
| `timestamp` | Date et heure de la mesure |
| `equipment_id` | Identifiant du roulement simulé |
| `vibration_rms_mm_s` | Vibration RMS en millimètres par seconde |
| `temperature_c` | Température en degrés Celsius |
| `speed_rpm` | Vitesse de rotation en tours par minute |
| `load_pct` | Charge de fonctionnement en pourcentage |
| `health_score` | Score de santé compris entre 0 et 100 |
| `state` | État : `normal`, `degradation` ou `critique` |
| `fault_active` | Indique si un défaut est actif |
| `fault_type` | `none` à l'état normal, sinon `bearing_wear` |

## Structure du projet

```text
indusguard-adt/
├── configs/
│   └── simulation.yaml
├── data/
│   └── synthetic/
├── indusguard/
│   ├── __init__.py
│   └── digital_twin/
│       ├── __init__.py
│       └── bearing_simulator.py
├── outputs/
│   └── plots/
├── tests/
│   ├── __init__.py
│   └── test_bearing_simulator.py
├── .gitignore
├── requirements.txt
├── README.md
└── run_simulation.py
```

Le fichier `configs/simulation.yaml` rassemble les paramètres modifiables. Le code du simulateur se trouve dans `indusguard/digital_twin/`. Les données et graphiques générés sont placés dans `data/` et `outputs/`. Les vérifications automatiques se trouvent dans `tests/`.

## Prérequis

- Python 3.11 ou une version plus récente ;
- Git pour récupérer le projet ;
- un terminal PowerShell sous Windows, ou un terminal sous Linux/macOS.

## Installation

Récupérer le dépôt et entrer dans son dossier :

```powershell
git clone <URL_DU_DEPOT>
cd indusguard-adt
```

Créer et activer un environnement virtuel sous Windows PowerShell :

```powershell
python -m venv .venv
.venv\Scripts\activate
```

Sous Linux ou macOS, l'activation se fait ainsi :

```bash
source .venv/bin/activate
```

Installer ensuite les dépendances :

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Exécution

Lancer la simulation depuis la racine du projet :

```powershell
python run_simulation.py
```

Le programme lit la configuration, génère 200 mesures, les valide, écrit le CSV, crée trois graphiques et affiche un résumé.

## Tests

Exécuter les tests automatisés avec :

```powershell
pytest -v
```

Ils vérifient notamment les colonnes, les limites des valeurs, les trois périodes, les défauts, les timestamps et la reproductibilité.

## Fichiers produits

Après l'exécution, les fichiers suivants sont disponibles :

- `data/synthetic/bearing_scenario_001.csv` ;
- `outputs/plots/vibration.png` ;
- `outputs/plots/temperature.png` ;
- `outputs/plots/health_score.png`.

## Limites et avertissement

Cette phase représente un scénario simplifié. Elle ne modélise pas toute la physique d'un roulement, ne détecte pas automatiquement les anomalies et ne recommande aucune maintenance.

**Les données générées ne viennent pas d'une véritable machine et ne doivent pas être utilisées pour commander un équipement industriel.**

## Étape suivante

La prochaine phase consistera à utiliser les données générées pour créer un premier système de détection d'anomalies.
