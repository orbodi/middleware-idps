"""
Interfaces communes pour les composants du micro-middleware IDPS
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path

from middleware.idps.models.file_info import IDPSFileInfo


class IFilePatternMatcher(ABC):
    """Interface pour le matching de patterns de fichiers IDPS"""

    @abstractmethod
    def matches(self, file_name: str) -> bool:
        """Vérifie si un fichier correspond au pattern IDPS"""
        pass

    @abstractmethod
    def parse_file_name(self, file_name: str) -> Optional[Dict[str, Any]]:
        """Parse le nom de fichier pour extraire les informations"""
        pass


class IModuleFileDetector(ABC):
    """Interface pour la détection de fichiers IDPS"""

    @abstractmethod
    def detect_files(self, input_dir: Path = None) -> List[IDPSFileInfo]:
        """Détecte les fichiers IDPS dans le répertoire"""
        pass


class IModuleValidator(ABC):
    """Interface pour la validation spécifique IDPS"""

    @abstractmethod
    def validate_schema(self, data: List[Dict[str, Any]], file_info: IDPSFileInfo) -> Optional[str]:
        """Valide le schéma des données selon les règles IDPS"""
        pass


class IModuleTransformer(ABC):
    """Interface pour la transformation spécifique IDPS"""

    @abstractmethod
    def map_to_module_schema(self, transformed: Dict[str, Any], file_info: IDPSFileInfo) -> Dict[str, Any]:
        """Mappe les données transformées vers le schéma spécifique IDPS"""
        pass


class IModuleRepository(ABC):
    """Interface pour le repository IDPS"""

    @abstractmethod
    def insert_events(self, data: List[Dict[str, Any]], category: str) -> int:
        """Insère les événements dans les tables IDPS"""
        pass


class IModule(ABC):
    """Interface principale pour le module IDPS"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Nom du module"""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Nom d'affichage du module"""
        pass

    @abstractmethod
    def get_file_pattern_matcher(self) -> IFilePatternMatcher:
        """Retourne le matcher de pattern pour IDPS"""
        pass

    @abstractmethod
    def get_file_detector(self) -> IModuleFileDetector:
        """Retourne le détecteur de fichiers pour IDPS"""
        pass

    @abstractmethod
    def get_validator(self) -> IModuleValidator:
        """Retourne le validateur pour IDPS"""
        pass

    @abstractmethod
    def get_transformer(self) -> IModuleTransformer:
        """Retourne le transformateur pour IDPS"""
        pass

    @abstractmethod
    def get_repository(self) -> IModuleRepository:
        """Retourne le repository pour IDPS"""
        pass
