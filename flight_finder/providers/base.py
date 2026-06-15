"""Interface comum a todos os provedores de dados."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..config import SearchConfig
from ..models import FlightOffer


class FlightProvider(ABC):
    """Contrato que todo provedor de passagens deve implementar."""

    name: str = "base"

    @abstractmethod
    def search(self, config: SearchConfig) -> list[FlightOffer]:
        """Retorna as ofertas encontradas para a configuração informada."""
        raise NotImplementedError
