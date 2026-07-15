from indusguard.multi_agent.asset_registry import AssetRegistry
def test_alias_resolution(): assert AssetRegistry().resolve("motor_01")=="MOTOR-001"
def test_historical_ids(): assert AssetRegistry().equipment_type("BEARING-RUL-023")=="bearing"
def test_parent_child(): assert AssetRegistry().parent("BEARING-001")=="MOTOR-001"
