"""Affiche la recommandation de maintenance d'un équipement."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

from generate_maintenance_plan import load_yaml


def resolve_equipment(data: pd.DataFrame, query: str) -> pd.Series:
    """Résout un identifiant exact ou un alias comme bearing_03."""
    exact = data[data["equipment_id"].str.casefold() == query.casefold()]
    if not exact.empty:
        return exact.iloc[0]
    match = re.fullmatch(r"(motor|bearing|conveyor|pump)[_-]0?(\d+)", query.casefold())
    if match:
        equipment_type, ordinal_text = match.groups()
        candidates = data[data["equipment_type"] == equipment_type].sort_values("equipment_id")
        ordinal = int(ordinal_text)
        if 1 <= ordinal <= len(candidates):
            return candidates.iloc[ordinal - 1]
    raise ValueError(f"Équipement introuvable : {query}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--equipment-id", required=True)
    parser.add_argument("--output", type=Path, help="Enregistrer la recommandation isolée")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    config = load_yaml(root / "configs" / "maintenance_planning.yaml")
    recommendations_path = root / config["paths"]["recommendations"]
    try:
        data = pd.read_csv(recommendations_path)
        row = resolve_equipment(data, args.equipment_id)
        print(f"Équipement : {row['equipment_id']}")
        print(f"Panne probable : {row['diagnosed_fault']}")
        print(f"RUL estimée : {row['predicted_rul_steps']:.1f} cycles ({row['predicted_rul_hours']:.1f} heures)")
        print(f"Action recommandée : {row['recommended_action']}")
        print(f"Stratégie : {row['maintenance_strategy']}")
        print(f"Priorité : {row['priority']} ({row['priority_score']:.1f}/100)")
        print(f"Date limite : {row['recommended_deadline']}")
        print(f"Durée estimée : {row['estimated_duration_hours']:.1f} heures")
        print(f"Techniciens : {row['required_skills']}")
        print(f"Pièces : {row['required_parts'] or 'aucune pièce obligatoire'}")
        print(f"Arrêt requis : {'oui' if row['shutdown_required'] else 'non'}")
        print(f"Confiance : {row['recommendation_confidence']:.0%}")
        print(f"Explication : {row['recommendation_explanation']}")
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            row.to_frame().T.to_csv(args.output, index=False, encoding="utf-8")
        return 0
    except (FileNotFoundError, OSError, TypeError, ValueError, KeyError) as error:
        print(f"Erreur : {error}"); return 1


if __name__ == "__main__":
    raise SystemExit(main())
