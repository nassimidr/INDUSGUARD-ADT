# Phase 5 — recommandation et planification de maintenance

## Objectif

La phase 5 transforme les résultats techniques des phases 2 à 4 en un plan d'intervention compréhensible : action, priorité, échéance, ressources, pièces, coût, ordre de travail et créneau planifié.

## Entrées et fusion

Le service lit les anomalies, les diagnostics et les prédictions RUL sans modifier leurs formats. Les phases 2 et 3 décrivent quatre équipements de ligne, alors que la phase 4 fournit douze trajectoires incomplètes représentant des actifs actuellement en service.

Le parc courant est donc constitué de la dernière mesure de chaque trajectoire RUL incomplète. Pour chaque actif, le service recherche un diagnostic de phase 3 du même équipement et de la même panne. Lorsqu'aucune classe équivalente n'existe, le type synthétique de trajectoire RUL sert de fallback avec une confiance volontairement réduite à 0,58. La colonne `diagnosis_source` rend ce choix visible.

## Catalogue et stratégies

Le catalogue YAML centralise les actions, compétences, pièces, durées, besoins d'arrêt et inspections pour chaque panne. Les stratégies disponibles sont `monitor`, `inspect`, `preventive_maintenance`, `component_replacement`, `corrective_maintenance` et `emergency_shutdown`.

Une situation normale reste sous surveillance. Une confiance faible conduit à une inspection. Une dégradation confirmée conduit à une maintenance préventive. Une RUL très faible avec forte gravité peut déclencher un remplacement. Une cascade, une sévérité critique ou une RUL inférieure à cinq cycles déclenche un arrêt d'urgence.

## Calcul de priorité

Le score entre 0 et 100 combine : gravité 25 %, RUL 25 %, risque 20 %, cascade 10 %, sécurité 8 %, impact production 7 % et confiance 5 %. Les seuils donnent les niveaux low, medium, high, urgent et critical. Toute sévérité critique, cascade ou RUL ≤ 5 reçoit au minimum le seuil critique.

Chaque composante est enregistrée au format JSON dans `priority_components` afin que le calcul reste vérifiable.

## Fenêtre d'intervention

La fenêtre part du timestamp le plus récent disponible dans le parc. La date limite est antérieure à la panne estimée grâce à une marge de sécurité de 25 %. Cette marge passe à 40 % si la confiance est faible et à 55 % en situation critique.

## Ressources et pièces

Les ressources sont des rôles génériques : mécanicien, électricien, automaticien, spécialiste pompe ou convoyeur, superviseur et responsable sécurité. Aucun nom de personne n'est créé. Les effectifs, coûts horaires, expertises et horaires de travail sont synthétiques et configurables.

Le stock de pièces est réservé seulement lorsqu'un ordre peut être planifié. Une pièce obligatoire indisponible bloque l'ordre avec une raison explicite. Les pièces facultatives n'empêchent pas la planification.

## Planificateur

L'algorithme trie les ordres par priorité décroissante puis par date limite. Pour toutes les compétences demandées, il cherche la première ressource disponible, décale l'intervention dans les heures ouvrées et vérifie l'échéance. Les disponibilités sont ensuite mises à jour, ce qui empêche deux ordres d'utiliser la même ressource simultanément.

Dans le plan de référence, neuf conflits potentiels ont été détectés et résolus par décalage. Trois ordres restent bloqués faute de créneau avant la date limite et un autre faute de capteur en stock.

## Ordres de travail

Chaque ordre contient l'équipement, la panne, la stratégie, la priorité, les dates, la durée, les compétences, les pièces, le besoin d'arrêt, le coût et le statut. Les statuts produits sont principalement `scheduled`, `urgent` et `blocked`.

## Coûts synthétiques

La main-d'œuvre vaut durée × nombre de techniciens × coût horaire moyen. Les pièces utilisent les prix du stock. Le coût d'arrêt vaut durée × perte de production horaire. Ces montants servent uniquement à comparer des scénarios ; ils ne représentent pas un devis industriel.

## Confiance

La confiance de recommandation combine confiance du diagnostic, confiance RUL, cohérence avec le catalogue, largeur de l'intervalle et complétude des données. Il s'agit d'un indicateur technique non calibré, pas d'une probabilité statistique.

## Résultats de référence

- 12 équipements et 12 recommandations ;
- 9 maintenances préventives, 2 arrêts d'urgence, 1 inspection ;
- 2 priorités critiques, 6 élevées, 4 moyennes ;
- 8 ordres planifiés, 4 bloqués ;
- 100 % des échéances planifiées respectées ;
- 27,5 heures d'intervention estimées ;
- coût synthétique total : 26 881,50 ;
- 9 conflits de ressources détectés et résolus.

## Sécurité

Les consignes générées rappellent la consignation, l'absence de tension, la dépressurisation ou la sécurisation de zone selon l'équipement. Elles ne remplacent jamais les procédures officielles, l'analyse de risques, les permis de travail ou la réglementation applicable.

## Limites et améliorations futures

- La correspondance phases 3–4 se fait par type d'équipement et panne, car les identifiants de simulation diffèrent.
- Les stocks, coûts, effectifs et horaires sont synthétiques.
- Le planificateur est heuristique et n'optimise pas mathématiquement le coût global.
- Il ne gère ni compétences individuelles, ni congés, ni dépendances complexes entre tâches.
- Les recommandations n'ont pas de vérité terrain complète.

Les améliorations futures sont une nomenclature d'actifs commune, une intégration GMAO, des calendriers réels, des durées probabilistes, des dépendances de tâches, une optimisation multi-objectifs et une validation par des experts maintenance.
