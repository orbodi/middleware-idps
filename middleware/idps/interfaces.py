"""
Interfaces (abstractions) pour le micro-middleware IDPS
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pathlib import Path

from middleware.idps.models.file_info import IDPSFileInfo
from middleware.idps.models.validation_result import ValidationResult
from middleware.idps.models.transformation_result import TransformationResult
from middleware.idps.models.ingestion_result import IngestionResult


class IFileValidator(ABC):
    """Interface pour la validation de fichiers IDPS"""

    @abstractmethod
    def validate_file(self, file_path: Path, file_info: IDPSFileInfo) -> ValidationResult:
        """Valide un fichier IDPS"""
        pass


class IDataTransformer(ABC):
    """Interface pour la transformation de données IDPS"""

    @abstractmethod
    def transform(self, data: List[Dict[str, Any]], file_info: IDPSFileInfo) -> TransformationResult:
        """Transforme les données brutes en données structurées pour IDPS"""
        pass
