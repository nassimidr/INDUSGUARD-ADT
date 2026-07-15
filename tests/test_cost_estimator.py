from indusguard.maintenance_planning.cost_estimator import estimate_cost


def test_cost_formula_is_correct() -> None:
    result = estimate_cost(2, 2, 50, 100, True, {"production_loss_per_hour": 500, "delayed_risk_multiplier": 1.5}, 80)
    assert result.labor_cost == 200
    assert result.parts_cost == 100
    assert result.downtime_cost == 1000
    assert result.total_cost == 1300
    assert result.delayed_risk_cost == 1560

