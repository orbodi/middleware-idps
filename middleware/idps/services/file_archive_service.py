"""
Service d'archivage de fichiers pour IDPS
"""
import shutil
import logging
from pathlib import Path
from typing import Optional

from middleware.idps.config.files_config import IDPSFilesConfig
from middleware.idps.models.file_info import IDPSFileInfo
from middleware.exceptions import ArchiveError

logger = logging.getLogger(__name__)


class FileArchiveService:
    """Service pour gérer l'archivage des fichiers traités IDPS"""
    
    def __init__(self, files_config: IDPSFilesConfig = None):
        """
        Initialise le service d'archivage
        
        Args:
            files_config: Configuration des fichiers (charge depuis env si None)
        """
        self.files_config = files_config or IDPSFilesConfig.from_env()
    
    def archive_file(self, file_path: Path, file_info: IDPSFileInfo, success: bool = True) -> Optional[Path]:
        """
        Archive un fichier traité
        
        Args:
            file_path: Chemin du fichier à archiver
            file_info: Informations sur le fichier
            success: True si le traitement a réussi, False sinon
        
        Returns:
            Chemin du fichier archivé (None si le fichier n'existe plus)
        
        Raises:
            ArchiveError: Si l'archivage échoue
        """
        # Vérifier si le fichier existe encore (il peut avoir été déplacé précédemment)
        if not file_path.exists():
            logger.warning(f"Le fichier {file_path.name} n'existe plus, archivage ignoré")
            return None
        
        try:
            if success:
                archive_path = self._get_archive_path(file_path, file_info)
            else:
                archive_path = self._get_error_path(file_path, file_info)
            
            # Créer le répertoire de destination s'il n'existe pas
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Déplacer le fichier
            shutil.move(str(file_path), str(archive_path))
            
            logger.info(f"Fichier archivé: {file_path.name} -> {archive_path}")
            return archive_path
            
        except Exception as e:
            error_msg = f"Erreur lors de l'archivage du fichier {file_path.name}: {e}"
            logger.error(error_msg)
            raise ArchiveError(error_msg, file_path=str(file_path)) from e
    
    def _get_archive_path(self, file_path: Path, file_info: IDPSFileInfo) -> Path:
        """Génère le chemin d'archive pour un fichier traité avec succès"""
        date_str = file_info.date.strftime('%Y-%m-%d')
        
        # Structure: archive/YYYY-MM-DD/module/category/filename
        archive_path = self.files_config.archive_dir / date_str / file_info.module / file_info.category
        return archive_path / file_path.name
    
    def _get_error_path(self, file_path: Path, file_info: IDPSFileInfo) -> Path:
        """Génère le chemin d'erreur pour un fichier en échec"""
        date_str = file_info.date.strftime('%Y-%m-%d')
        
        # Structure: error/YYYY-MM-DD/filename
        error_path = self.files_config.error_dir / date_str
        return error_path / file_path.name

