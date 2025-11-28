"""
Validateur spécifique au module IDPS
"""
from typing import List, Dict, Any, Optional

from middleware.idps.domain_interfaces import IModuleValidator
from middleware.idps.models.file_info import IDPSFileInfo


class IDPSValidator(IModuleValidator):
    """Validateur spécifique pour les fichiers IDPS"""
    
    # Colonnes obligatoires selon le type de fichier
    REQUIRED_COLUMNS = {
        'WO-BACKLOG': [],  # TODO: Définir les colonnes obligatoires
        'WO-FINISH': [],
        'QC-ERROR': [],
        'PERSO-ERROR': [],
        'SUP-ERROR': []
    }
    
    def validate_schema(self, data: List[Dict[str, Any]], file_info: IDPSFileInfo) -> Optional[str]:
        """Valide le schéma des données selon les règles IDPS"""
        if not data:
            return "Aucune donnée à valider"
        
        file_type = file_info.file_type
        
        # Validation basique: vérifier que toutes les lignes ont le même nombre de colonnes
        first_row_keys = set(data[0].keys())
        for i, row in enumerate(data[1:], start=2):
            row_keys = set(row.keys())
            if row_keys != first_row_keys:
                return f"Ligne {i}: nombre de colonnes incohérent"
        
        # Validation spécifique selon le type de fichier
        required_cols = self.REQUIRED_COLUMNS.get(file_type, [])
        if required_cols:
            missing_cols = [col for col in required_cols if col not in first_row_keys]
            if missing_cols:
                return f"Colonnes manquantes pour {file_type}: {', '.join(missing_cols)}"
        
        return None

