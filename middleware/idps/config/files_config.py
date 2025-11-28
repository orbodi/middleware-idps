"""
Configuration des fichiers pour IDPS
"""
import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class IDPSFilesConfig:
    """Configuration des répertoires et fichiers pour IDPS"""
    input_dir: Path
    archive_dir: Path
    error_dir: Path
    logs_dir: Path
    
    # Configuration CSV
    csv_encoding: str
    csv_separator: str
    date_format: str
    
    def __post_init__(self):
        """Crée les répertoires s'ils n'existent pas"""
        for directory in [
            self.input_dir, self.archive_dir,
            self.error_dir, self.logs_dir
        ]:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def from_env(cls, base_dir: Path = None) -> 'IDPSFilesConfig':
        """
        Charge la configuration depuis les variables d'environnement
        
        Args:
            base_dir: Répertoire de base (utilise le répertoire courant si None)
        
        Returns:
            Instance de IDPSFilesConfig
        """
        if base_dir is None:
            base_dir = Path.cwd()
        
        return cls(
            input_dir=Path(os.getenv('INPUT_DIR', base_dir / 'input')),
            archive_dir=Path(os.getenv('ARCHIVE_DIR', base_dir / 'archive')),
            error_dir=Path(os.getenv('ERROR_DIR', base_dir / 'error')),
            logs_dir=Path(os.getenv('LOGS_DIR', base_dir / 'logs')),
            csv_encoding=os.getenv('CSV_ENCODING', 'utf-8'),
            csv_separator=os.getenv('CSV_SEPARATOR', ';'),
            date_format=os.getenv('DATE_FORMAT', '%Y-%m-%d')
        )

