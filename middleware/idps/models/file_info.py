"""
Modèle FileInfo pour IDPS
"""
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


@dataclass
class IDPSFileInfo:
    """Informations sur un fichier IDPS détecté"""
    path: Path
    name: str
    file_type: str
    date: datetime
    size: int
    category: str  # 'workflow' ou 'error'
    ingestion_timestamp: Optional[datetime] = None
    
    @property
    def module(self) -> str:
        """Retourne toujours 'IDPS'"""
        return 'IDPS'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire"""
        return {
            'path': str(self.path),
            'name': self.name,
            'file_type': self.file_type,
            'date': self.date.isoformat(),
            'size': self.size,
            'module': self.module,
            'category': self.category,
            'ingestion_timestamp': self.ingestion_timestamp.isoformat() if self.ingestion_timestamp else None
        }

