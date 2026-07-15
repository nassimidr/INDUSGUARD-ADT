"""Canaux d'alerte extensibles; seuls console et fichier sont actifs."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .adapters.persistence_adapter import PersistenceAdapter


class NotificationChannel(ABC):
    @abstractmethod
    def notify(self, alert: dict[str, Any]) -> None: ...

class ConsoleNotificationChannel(NotificationChannel):
    def notify(self, alert: dict[str, Any]) -> None:
        print(f"[{str(alert['level']).upper()}] {alert['title']}: {alert['message']}")

class FileNotificationChannel(NotificationChannel):
    def __init__(self,persistence:PersistenceAdapter)->None:self.persistence=persistence
    def notify(self,alert:dict[str,Any])->None:self.persistence.alert(alert)

class _FutureChannel(NotificationChannel):
    def notify(self, alert: dict[str, Any]) -> None: raise NotImplementedError("Canal réservé à une phase future.")

class EmailNotificationChannel(_FutureChannel): pass
class SmsNotificationChannel(_FutureChannel): pass
class SlackNotificationChannel(_FutureChannel): pass
