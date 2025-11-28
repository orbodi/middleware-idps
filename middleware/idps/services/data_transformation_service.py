"""
Service de transformation et normalisation des données pour IDPS
"""
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from middleware.idps.interfaces import IDataTransformer
from middleware.idps.models.transformation_result import TransformationResult
from middleware.idps.models.file_info import IDPSFileInfo
from middleware.idps.config.files_config import IDPSFilesConfig
from middleware.exceptions import DataTransformationError

logger = logging.getLogger(__name__)


class DataTransformationService(IDataTransformer):
    """Service de transformation et normalisation des données CSV pour IDPS"""
    
    def __init__(self, files_config: IDPSFilesConfig = None):
        """Initialise le service de transformation"""
        self.files_config = files_config or IDPSFilesConfig.from_env()
        self.date_format = self.files_config.date_format
    
    def transform(self, data: List[Dict[str, Any]], file_info: IDPSFileInfo) -> TransformationResult:
        """
        Transforme les données brutes en format structuré pour la base de données
        
        Args:
            data: Données brutes du CSV
            file_info: Informations sur le fichier
        
        Returns:
            TransformationResult contenant les données transformées
        
        Raises:
            DataTransformationError: Si une erreur critique survient
        """
        original_count = len(data)
        transformed_data = []
        errors = []
        
        for row in data:
            try:
                transformed_row = self._transform_row(row, file_info)
                if transformed_row:
                    transformed_data.append(transformed_row)
            except Exception as e:
                line_num = row.get('_line_number', 'unknown')
                error_msg = f"Ligne {line_num}: {str(e)}"
                errors.append(error_msg)
                logger.warning(error_msg)
                # Continuer avec les autres lignes
        
        transformed_count = len(transformed_data)
        success_rate = (transformed_count / original_count * 100) if original_count > 0 else 0
        
        logger.info(
            f"Transformation terminée: {transformed_count}/{original_count} lignes "
            f"({success_rate:.1f}% de succès)"
        )
        
        return TransformationResult(
            transformed_data=transformed_data,
            original_count=original_count,
            transformed_count=transformed_count,
            errors=errors
        )
    
    def _transform_row(self, row: Dict[str, Any], file_info: IDPSFileInfo) -> Optional[Dict[str, Any]]:
        """Transforme une ligne individuelle"""
        # Créer la structure de base
        transformed = {
            'source_file': file_info.name,
            'file_type': file_info.file_type,
            'file_date': file_info.date,
            'module': file_info.module,
            'category': file_info.category,
            'ingestion_timestamp': datetime.now(),
            'raw_data': row.copy()
        }
        
        # Supprimer le champ interne _line_number
        if '_line_number' in transformed['raw_data']:
            del transformed['raw_data']['_line_number']
        
        # Normaliser les dates
        transformed = self._normalize_dates(transformed, row)
        
        # Extraire et parser les champs JSON si présents
        transformed = self._extract_json_fields(transformed, row)
        
        return transformed
    
    def _normalize_dates(self, transformed: Dict[str, Any], row: Dict[str, Any]) -> Dict[str, Any]:
        """Normalise les champs de date dans les données brutes"""
        date_patterns = ['date', 'timestamp', 'time', 'created', 'updated']
        
        for key, value in row.items():
            # Ignorer les clés non textuelles (par ex. None si le CSV a des colonnes vides)
            if not isinstance(key, str):
                continue
            if any(pattern in key.lower() for pattern in date_patterns):
                if value and isinstance(value, str):
                    normalized_date = self._parse_date(value)
                    if normalized_date:
                        transformed['raw_data'][key] = normalized_date.isoformat()
        
        return transformed
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse une chaîne de date en objet datetime"""
        if not date_str or not isinstance(date_str, str):
            return None
        
        # Formats de date courants
        date_formats = [
            '%Y-%m-%d',
            '%Y-%m-%d %H:%M:%S',
            '%d/%m/%Y',
            '%d/%m/%Y %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y/%m/%d',
            '%d-%m-%Y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        logger.debug(f"Impossible de parser la date: {date_str}")
        return None
    
    def _extract_json_fields(self, transformed: Dict[str, Any], row: Dict[str, Any]) -> Dict[str, Any]:
        """Extrait et parse les champs JSON"""
        json_patterns = ['json', 'data', 'payload', 'metadata']
        
        for key, value in row.items():
            # Ignorer les clés non textuelles (par ex. None si le CSV a des colonnes en trop)
            if not isinstance(key, str):
                continue
            if any(pattern in key.lower() for pattern in json_patterns):
                if value and isinstance(value, str):
                    try:
                        parsed_json = json.loads(value)
                        transformed['raw_data'][key] = parsed_json
                        transformed[f'{key}_parsed'] = parsed_json
                    except json.JSONDecodeError:
                        # Ce n'est pas du JSON valide, on garde la valeur originale
                        pass
        
        return transformed

