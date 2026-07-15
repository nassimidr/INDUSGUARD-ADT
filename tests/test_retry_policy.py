from indusguard.multi_agent.retry_policy import RetryPolicy
def test_exponential_bounded_retry(): p=RetryPolicy(3,1,2,2);assert [p.delay(i) for i in range(3)]==[1,2,2];assert p.should_retry(1) and not p.should_retry(2)
