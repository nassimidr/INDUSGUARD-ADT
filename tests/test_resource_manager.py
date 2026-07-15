from indusguard.maintenance_planning.resource_manager import ResourceManager


def test_resource_selection_uses_generic_skills() -> None:
    resources = {"technicians": {"mechanical_technician": {"hourly_cost": 40, "expertise": "senior"}}, "tools": {"bearing": ["extractor"]}, "safety_instructions": {"bearing": ["lockout"]}}
    selected = ResourceManager(resources).select("bearing", ("mechanical_technician",))
    assert selected.technician_count == 1
    assert selected.tools == ("extractor",)

