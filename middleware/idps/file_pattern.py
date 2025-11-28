"""
Pattern matcher pour les fichiers IDPS
"""
import re
from typing import Optional, Dict, Any
from datetime import datetime

from middleware.idps.domain_interfaces import IFilePatternMatcher


class IDPSFilePatternMatcher(IFilePatternMatcher):
    """Matcher de pattern pour les fichiers IDPS"""
    
    # Pattern: IDPS-TG-EID-{TYPE}-{YYYY-MM-DD}.csv
    PATTERN = re.compile(r'IDPS-TG-EID-([A-Z-]+)-(\d{4}-\d{2}-\d{2})\.csv')
    
    # Types de fichiers IDPS
    WORKFLOW_TYPES = {'WO-BACKLOG', 'WO-FINISH'}
    ERROR_TYPES = {'QC-ERROR', 'PERSO-ERROR', 'SUP-ERROR'}
    
    def matches(self, file_name: str) -> bool:
        """Vérifie si un fichier correspond au pattern IDPS"""
        return bool(self.PATTERN.match(file_name))
    
    def parse_file_name(self, file_name: str) -> Optional[Dict[str, Any]]:
        """Parse le nom de fichier pour extraire les informations"""
        match = self.PATTERN.match(file_name)
        if not match:
            return None
        
        try:
            file_type = match.group(1)
            date_str = match.group(2)
            file_date = datetime.strptime(date_str, '%Y-%m-%d')
            
            # Déterminer la catégorie
            if file_type in self.WORKFLOW_TYPES:
                category = 'workflow'
            elif file_type in self.ERROR_TYPES:
                category = 'error'
            else:
                category = 'unknown'
            
            return {
                'file_type': file_type,
                'date': file_date,
                'category': category,
                'module': 'IDPS'
            }
        except (ValueError, IndexError):
            return None

