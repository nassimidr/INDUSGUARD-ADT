"""Politique de retry exponentielle bornée."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RetryPolicy:
    maximum_attempts: int = 3
    initial_delay_seconds: float = 1
    backoff_factor: float = 2
    maximum_delay_seconds: float = 10

    def should_retry(self, retry_count: int) -> bool:
        return retry_count < self.maximum_attempts - 1

    def delay(self, retry_count: int) -> float:
        return min(self.maximum_delay_seconds, self.initial_delay_seconds * self.backoff_factor ** retry_count)
