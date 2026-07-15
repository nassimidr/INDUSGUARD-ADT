from indusguard.multi_agent.idempotency import IdempotencyCache
def test_duplicate_cached_once(): c=IdempotencyCache(2,60);c.put("id",{"ok":1});assert c.contains("id") and c.get("id")=={"ok":1}
def test_lru_size(): c=IdempotencyCache(1,60);c.put("a");c.put("b");assert not c.contains("a") and len(c)==1
