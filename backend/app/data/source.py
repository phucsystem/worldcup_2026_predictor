from abc import ABC, abstractmethod
from datetime import date

from app.data.models import Match, StandingRow


class DataSource(ABC):
    @abstractmethod
    def get_fixtures(self, date_from: date, date_to: date) -> list[Match]:
        ...

    @abstractmethod
    def get_standings(self) -> list[StandingRow]:
        ...

    @abstractmethod
    def get_events(self, fixture_id: int) -> list[dict]:
        ...
