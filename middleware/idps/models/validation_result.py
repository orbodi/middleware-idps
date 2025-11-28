"""
Résultat de la validation d'un fichier IDPS
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class ValidationResult:
    """Résultat de la validation d'un fichier IDPS"""
    is_valid: bool
    error_message: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    encoding: Optional[str] = None
    line_count: int = 0

    def __bool__(self) -> bool:
        return self.is_valid
