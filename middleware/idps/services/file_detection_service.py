"""
Service de détection de fichiers pour IDPS
"""
import logging
from pathlib import Path
from typing import List, Set

from middleware.idps.config.files_config import IDPSFilesConfig
from middleware.idps.file_pattern import IDPSFilePatternMatcher
from middleware.idps.models.file_info import IDPSFileInfo
from middleware.exceptions import FileDetectionError

logger = logging.getLogger(__name__)


class FileDetectionService:
    """Service de détection de fichiers IDPS"""
    
    def __init__(self, files_config: IDPSFilesConfig = None):
        """
        Initialise le service de détection
        
        Args:
            files_config: Configuration des fichiers (charge depuis env si None)
        """
        self.files_config = files_config or IDPSFilesConfig.from_env()
        self.pattern_matcher = IDPSFilePatternMatcher()
        self.processed_files: Set[str] = set()
    
    def detect_files(self, input_dir: Path = None) -> List[IDPSFileInfo]:
        """
        Détecte les fichiers IDPS dans le répertoire
        
        Args:
            input_dir: Répertoire à scanner (utilise la config par défaut si None)
        
        Returns:
            Liste des fichiers IDPS détectés
        
        Raises:
            FileDetectionError: Si le répertoire n'existe pas ou erreur de scan
        """
        scan_dir = input_dir or self.files_config.input_dir
        
        if not scan_dir.exists():
            raise FileDetectionError(f"Le répertoire d'entrée n'existe pas: {scan_dir}")
        
        detected_files = []
        
        try:
            for file_path in scan_dir.glob('*.csv'):
                if not self.pattern_matcher.matches(file_path.name):
                    continue
                
                if self._is_already_processed(file_path):
                    continue
                
                file_info = self._create_file_info(file_path)
                if file_info:
                    detected_files.append(file_info)
                    logger.info(f"Fichier IDPS détecté: {file_path.name}")
        except Exception as e:
            raise FileDetectionError(f"Erreur lors du scan du répertoire: {e}") from e
        
        return detected_files
    
    def _create_file_info(self, file_path: Path) -> IDPSFileInfo:
        """Crée un objet IDPSFileInfo à partir d'un fichier"""
        parsed = self.pattern_matcher.parse_file_name(file_path.name)
        if not parsed:
            return None
        
        try:
            return IDPSFileInfo(
                path=file_path,
                name=file_path.name,
                file_type=parsed['file_type'],
                date=parsed['date'],
                size=file_path.stat().st_size,
                category=parsed['category']
            )
        except (OSError, KeyError) as e:
            logger.warning(f"Erreur lors de la création de IDPSFileInfo pour {file_path.name}: {e}")
            return None
    
    def _is_already_processed(self, file_path: Path) -> bool:
        """Vérifie si un fichier a déjà été traité"""
        try:
            file_id = f"{file_path.name}_{file_path.stat().st_mtime}"
            return file_id in self.processed_files
        except (OSError, FileNotFoundError):
            # Le fichier n'existe plus (déjà archivé), on considère qu'il n'a pas été traité dans cette session
            return False
    
    def mark_as_processed(self, file_path: Path = None, file_info: IDPSFileInfo = None) -> None:
        """
        Marque un fichier comme traité
        
        Args:
            file_path: Chemin du fichier (si disponible)
            file_info: Informations sur le fichier (utilisé si file_path n'existe plus)
        """
        if file_info:
            # Utiliser file_info si disponible (même si le fichier a été déplacé)
            try:
                if file_path and file_path.exists():
                    file_id = f"{file_path.name}_{file_path.stat().st_mtime}"
                else:
                    # Le fichier a été déplacé, utiliser le nom et la date du fichier
                    file_id = f"{file_info.name}_{file_info.date.isoformat()}"
            except (OSError, FileNotFoundError):
                file_id = f"{file_info.name}_{file_info.date.isoformat()}"
        elif file_path:
            try:
                file_id = f"{file_path.name}_{file_path.stat().st_mtime}"
            except (OSError, FileNotFoundError):
                logger.warning(f"Impossible de marquer le fichier comme traité (fichier introuvable): {file_path.name}")
                return
        else:
            logger.warning("mark_as_processed appelé sans file_path ni file_info")
            return
        
        self.processed_files.add(file_id)
        file_name = file_info.name if file_info else (file_path.name if file_path else "unknown")
        logger.debug(f"Fichier marqué comme traité: {file_name}")

