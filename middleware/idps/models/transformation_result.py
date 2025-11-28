"""
Résultat de la transformation des données IDPS
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class TransformationResult:
    """Résultat de la transformation des données IDPS"""
    transformed_data: List[Dict[str, Any]]
    original_count: int
    transformed_count: int
    errors: List[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Taux de succès de la transformation"""
        if self.original_count == 0:
            return 0.0
        return (self.transformed_count / self.original_count) * 100
