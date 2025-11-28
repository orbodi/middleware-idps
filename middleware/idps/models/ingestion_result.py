"""
Résultat d'une ingestion complète IDPS
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from middleware.idps.models.file_info import IDPSFileInfo


@dataclass
class IngestionResult:
    """Résultat d'une ingestion complète pour IDPS"""
    file_info: IDPSFileInfo
    status: str  # 'success', 'error', 'partial'
    rows_processed: int
    rows_inserted: int
    error_message: Optional[str] = None
    processing_time: Optional[float] = None

    @property
    def is_success(self) -> bool:
        return self.status == 'success'

    @property
    def is_error(self) -> bool:
        return self.status == 'error'
