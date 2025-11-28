"""
Service de validation de fichiers CSV pour IDPS
Utilise pandas pour lire les CSV
"""
import chardet
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from middleware.idps.interfaces import IFileValidator
from middleware.idps.models.validation_result import ValidationResult
from middleware.idps.models.file_info import IDPSFileInfo
from middleware.idps.config.files_config import IDPSFilesConfig
from middleware.exceptions import FileValidationError

logger = logging.getLogger(__name__)


class FileValidationService(IFileValidator):
    """Service de validation des fichiers CSV pour IDPS"""
    
    def __init__(self, files_config: IDPSFilesConfig = None):
        """Initialise le service de validation"""
        self.files_config = files_config or IDPSFilesConfig.from_env()
    
    def validate_file(self, file_path: Path, file_info: IDPSFileInfo) -> ValidationResult:
        """
        Valide un fichier CSV
        
        Args:
            file_path: Chemin du fichier à valider
            file_info: Informations sur le fichier
        
        Returns:
            ValidationResult contenant le résultat de la validation
        
        Raises:
            FileValidationError: Si une erreur critique survient
        """
        # Vérifier l'existence du fichier
        if not file_path.exists():
            error_msg = f"Le fichier n'existe pas: {file_path}"
            logger.error(error_msg)
            return ValidationResult(
                is_valid=False,
                error_message=error_msg,
                line_count=0
            )
        
        try:
            # Détecter l'encodage
            encoding = self._detect_encoding(file_path)
            if not encoding:
                return ValidationResult(
                    is_valid=False,
                    error_message="Impossible de détecter l'encodage du fichier",
                    line_count=0
                )
            
            # Lire et valider le format CSV
            data, csv_error = self._read_and_validate_csv(file_path, encoding)
            if csv_error:
                return ValidationResult(
                    is_valid=False,
                    error_message=csv_error,
                    encoding=encoding,
                    line_count=0
                )
            
            logger.info(f"Fichier validé avec succès: {file_path.name} ({len(data)} lignes)")
            return ValidationResult(
                is_valid=True,
                data=data,
                encoding=encoding,
                line_count=len(data)
            )
            
        except Exception as e:
            error_msg = f"Erreur lors de la validation du fichier {file_path.name}: {e}"
            logger.error(error_msg, exc_info=True)
            raise FileValidationError(error_msg, file_path=str(file_path)) from e
    
    def _detect_encoding(self, file_path: Path) -> Optional[str]:
        """Détecte l'encodage du fichier"""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)  # Lire les 10 premiers KB
                result = chardet.detect(raw_data)
                encoding = result.get('encoding')
                
                if encoding:
                    confidence = result.get('confidence', 0)
                    logger.debug(f"Encodage détecté: {encoding} (confiance: {confidence:.2%})")
                    return encoding
                else:
                    logger.warning(f"Impossible de détecter l'encodage, utilisation de {self.files_config.csv_encoding}")
                    return self.files_config.csv_encoding
        except Exception as e:
            logger.error(f"Erreur lors de la détection d'encodage: {e}")
            return self.files_config.csv_encoding
    
    def _read_and_validate_csv(self, file_path: Path, encoding: str) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
        """Lit et valide le format CSV en utilisant pandas"""
        try:
            # Lire le CSV avec pandas
            df = pd.read_csv(
                file_path,
                encoding=encoding,
                sep=self.files_config.csv_separator,
                dtype=str,  # Tout lire comme string pour éviter les problèmes de type
                keep_default_na=False,  # Ne pas convertir les chaînes vides en NaN
                na_values=[''],  # Traiter les chaînes vides comme NaN mais les garder comme chaînes
                on_bad_lines='skip'  # Ignorer les lignes mal formées
            )
            
            # Vérifier que le fichier n'est pas vide
            if df.empty:
                return None, "Le fichier CSV est vide ou ne contient aucune donnée"
            
            # Nettoyer les noms de colonnes (supprimer BOM, espaces, etc.)
            df.columns = df.columns.str.strip().str.lstrip('\ufeff').str.strip()
            
            # Convertir le DataFrame en liste de dictionnaires
            data = []
            for idx, row in df.iterrows():
                row_dict = row.to_dict()
                # Convertir les NaN en None et les garder comme chaînes vides
                cleaned_row = {}
                for key, value in row_dict.items():
                    if pd.isna(value):
                        cleaned_row[key] = None
                    else:
                        cleaned_row[key] = str(value) if value is not None else None
                cleaned_row['_line_number'] = idx + 2  # +2 car idx commence à 0 et on compte l'en-tête
                data.append(cleaned_row)
            
            if not data:
                return None, "Le fichier CSV ne contient aucune donnée valide"
            
            logger.debug(f"Fichier lu avec succès: {len(data)} lignes, {len(df.columns)} colonnes")
            logger.debug(f"Colonnes détectées: {list(df.columns)}")
            return data, None
                
        except pd.errors.EmptyDataError:
            return None, "Le fichier CSV est vide"
        except pd.errors.ParserError as e:
            return None, f"Erreur de format CSV: {str(e)}"
        except Exception as e:
            return None, f"Erreur lors de la lecture du fichier: {str(e)}"

