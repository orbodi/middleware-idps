"""
Module IDPS - Implémentation principale du micro-middleware IDPS
"""
from middleware.idps.domain_interfaces import (
    IModule, IFilePatternMatcher, IModuleFileDetector,
    IModuleValidator, IModuleTransformer, IModuleRepository
)
from middleware.idps.file_pattern import IDPSFilePatternMatcher
from middleware.idps.services.file_detection_service import FileDetectionService
from middleware.idps.validator import IDPSValidator
from middleware.idps.transformer import IDPSTransformer
from middleware.idps.repository.database_repository import IDPSDatabaseRepository

logger = __import__('logging').getLogger(__name__)


class IDPSModule(IModule):
    """Module IDPS - Gestion des logs provenant de l'IDPS"""
    
    def __init__(self):
        """Initialise le module IDPS"""
        self._file_pattern_matcher = None
        self._file_detector = None
        self._validator = None
        self._transformer = None
        self._repository = None
    
    @property
    def name(self) -> str:
        """Nom du module"""
        return 'idps'
    
    @property
    def display_name(self) -> str:
        """Nom d'affichage du module"""
        return 'IDPS'
    
    def get_file_pattern_matcher(self) -> IFilePatternMatcher:
        """Retourne le matcher de pattern pour IDPS"""
        if self._file_pattern_matcher is None:
            self._file_pattern_matcher = IDPSFilePatternMatcher()
        return self._file_pattern_matcher
    
    def get_file_detector(self) -> IModuleFileDetector:
        """Retourne le détecteur de fichiers pour IDPS"""
        if self._file_detector is None:
            from middleware.idps.services.file_detection_service import FileDetectionService
            self._file_detector = FileDetectionService()
        return self._file_detector
    
    def get_validator(self) -> IModuleValidator:
        """Retourne le validateur pour IDPS"""
        if self._validator is None:
            self._validator = IDPSValidator()
        return self._validator
    
    def get_transformer(self) -> IModuleTransformer:
        """Retourne le transformateur pour IDPS"""
        if self._transformer is None:
            self._transformer = IDPSTransformer()
        return self._transformer
    
    def get_repository(self) -> IModuleRepository:
        """Retourne le repository pour IDPS"""
        if self._repository is None:
            self._repository = IDPSDatabaseRepository()
        return self._repository

