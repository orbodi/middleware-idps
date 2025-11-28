"""
Transformateur spécifique au module IDPS

Son rôle est de transformer la structure générique produite par
`DataTransformationService` en structures prêtes pour les modèles SQLAlchemy.

Le transformer se base sur les modèles SQLAlchemy pour extraire les données.
"""
import json
import logging
from typing import Dict, Any
from datetime import datetime

from middleware.idps.domain_interfaces import IModuleTransformer
from middleware.idps.models.file_info import IDPSFileInfo
from middleware.idps.models.workflow_event_model import IDPSWorkflowEventModel
from middleware.idps.models.error_event_model import IDPSErrorEventModel

logger = logging.getLogger(__name__)


class IDPSTransformer(IModuleTransformer):
    """
    Transformateur spécifique pour les données IDPS
    
    Se base sur les modèles SQLAlchemy pour extraire et mapper les données.
    """
    
    # Mapping des colonnes CSV vers les champs des modèles SQLAlchemy
    # Format: {nom_colonne_csv: nom_champ_modele}
    WORKFLOW_COLUMN_MAPPING = {
        'Timestamp': 'event_timestamp',
        'Type de document': 'document_type',
        'Code de destination': 'destination_code',
        'Request ID': 'request_id',
    }
    
    ERROR_COLUMN_MAPPING = {
        'Timestamp': 'event_timestamp',
        'Service': 'service_name',
        'Type de document': 'document_type',
        'Code de destination': 'destination_code',
        'Request ID': 'request_id',
        'infos_comment': 'comment',
    }
    
    def map_to_module_schema(self, transformed: Dict[str, Any], file_info: IDPSFileInfo) -> Dict[str, Any]:
        """
        Mappe une ligne transformée vers le schéma cible basé sur les modèles SQLAlchemy.

        `transformed` contient au minimum :
          - source_file
          - file_type  (WO-BACKLOG, WO-FINISH, QC-ERROR, PERSO-ERROR, SUP-ERROR)
          - file_date
          - category   ('workflow' ou 'error')
          - ingestion_timestamp
          - raw_data   (dictionnaire avec les colonnes CSV)
        """
        category = file_info.category
        raw = transformed.get("raw_data", {})

        if category == "workflow":
            return self._map_to_workflow_model(transformed, file_info, raw)
        elif category == "error":
            return self._map_to_error_model(transformed, file_info, raw)
        else:
            # Catégorie inconnue : on renvoie quand même la structure générique
            logger.warning(f"Catégorie inconnue: {category}, utilisation de la structure générique")
            return transformed

    def _map_to_workflow_model(
        self, 
        base: Dict[str, Any], 
        file_info: IDPSFileInfo, 
        raw: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Mappe les données CSV vers le modèle IDPSWorkflowEventModel
        
        Colonnes du modèle SQLAlchemy:
        - event_timestamp (DateTime)
        - document_type (String(10))
        - destination_code (String(20))
        - request_id (String(50))
        - status (String(20)) - dérivé de file_type
        - file_name (String(255))
        - ingested_at (DateTime)
        """
        # Extraire les valeurs basées sur le mapping
        mapped_data = {}
        
        # Helper pour obtenir une valeur avec plusieurs variantes de noms
        def get_csv_value(*possible_names, default=""):
            for name in possible_names:
                # Essayer le nom exact
                value = raw.get(name)
                if value is not None and value != "" and str(value).strip() != "":
                    return str(value).strip()
                # Essayer avec BOM
                bom_name = f"\ufeff{name}"
                value = raw.get(bom_name)
                if value is not None and value != "" and str(value).strip() != "":
                    return str(value).strip()
            return default
        
        # event_timestamp: depuis "Timestamp"
        ts_value = get_csv_value("Timestamp", "timestamp", "TIMESTAMP", default=None)
        if ts_value:
            event_timestamp = self._parse_timestamp(ts_value)
        else:
            event_timestamp = base.get("ingestion_timestamp", datetime.now())
        mapped_data["event_timestamp"] = event_timestamp
        
        # document_type: depuis "Type de document"
        mapped_data["document_type"] = get_csv_value(
            "Type de document", "type_de_document", "Document Type", default=""
        )
        
        # destination_code: depuis "Code de destination"
        mapped_data["destination_code"] = get_csv_value(
            "Code de destination", "code_de_destination", "Destination Code", default=""
        )
        
        # request_id: depuis "Request ID"
        mapped_data["request_id"] = get_csv_value(
            "Request ID", "request_id", "RequestID", "requestId", default=""
        )
        
        # status: dérivé de file_type
        if file_info.file_type == "WO-BACKLOG":
            mapped_data["status"] = "BACKLOG"
        elif file_info.file_type == "WO-FINISH":
            mapped_data["status"] = "FINISH"
        else:
            mapped_data["status"] = file_info.file_type
        
        # file_name: depuis source_file ou file_info.name
        mapped_data["file_name"] = base.get("source_file", file_info.name)
        
        # ingested_at: timestamp d'ingestion
        mapped_data["ingested_at"] = base.get("ingestion_timestamp", datetime.now())
        
        logger.debug(f"Mapping workflow: {mapped_data}")
        return mapped_data

    def _map_to_error_model(
        self, 
        base: Dict[str, Any], 
        file_info: IDPSFileInfo, 
        raw: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Mappe les données CSV vers le modèle IDPSErrorEventModel
        
        Colonnes du modèle SQLAlchemy:
        - event_timestamp (DateTime)
        - document_type (String(10))
        - destination_code (String(20))
        - request_id (String(50))
        - service_name (String(50))
        - error_category (String(20)) - dérivé de file_type
        - comment (Text) - depuis infos_comment
        - file_name (String(255))
        - ingested_at (DateTime)
        """
        # Extraire les valeurs basées sur le mapping
        mapped_data = {}
        
        # Helper pour obtenir une valeur avec plusieurs variantes de noms
        def get_csv_value(*possible_names, default=""):
            for name in possible_names:
                # Essayer le nom exact
                value = raw.get(name)
                if value is not None and value != "" and str(value).strip() != "":
                    return str(value).strip()
                # Essayer avec BOM
                bom_name = f"\ufeff{name}"
                value = raw.get(bom_name)
                if value is not None and value != "" and str(value).strip() != "":
                    return str(value).strip()
            return default
        
        # event_timestamp: depuis "Timestamp"
        ts_value = get_csv_value("Timestamp", "timestamp", "TIMESTAMP", default=None)
        if ts_value:
            event_timestamp = self._parse_timestamp(ts_value)
        else:
            event_timestamp = base.get("ingestion_timestamp", datetime.now())
        mapped_data["event_timestamp"] = event_timestamp
        
        # document_type: depuis "Type de document"
        mapped_data["document_type"] = get_csv_value(
            "Type de document", "type_de_document", "Document Type", default=""
        )
        
        # destination_code: depuis "Code de destination"
        mapped_data["destination_code"] = get_csv_value(
            "Code de destination", "code_de_destination", "Destination Code", default=""
        )
        
        # request_id: depuis "Request ID"
        mapped_data["request_id"] = get_csv_value(
            "Request ID", "request_id", "RequestID", "requestId", default=""
        )
        
        # service_name: depuis "Service"
        mapped_data["service_name"] = get_csv_value(
            "Service", "service", "service_name", "SERVICE", default=""
        )
        
        # error_category: dérivé de file_type
        if file_info.file_type == "QC-ERROR":
            mapped_data["error_category"] = "QC_ERROR"
        elif file_info.file_type == "PERSO-ERROR":
            mapped_data["error_category"] = "PERSO_ERROR"
        elif file_info.file_type == "SUP-ERROR":
            mapped_data["error_category"] = "SUP_ERROR"
        else:
            mapped_data["error_category"] = file_info.file_type
        
        # comment: depuis "infos_comment" (peut être JSON)
        infos_comment = get_csv_value("infos_comment", "comment", "Comment", default=None)
        mapped_data["comment"] = self._parse_comment(infos_comment)
        
        # file_name: depuis source_file ou file_info.name
        mapped_data["file_name"] = base.get("source_file", file_info.name)
        
        # ingested_at: timestamp d'ingestion
        mapped_data["ingested_at"] = base.get("ingestion_timestamp", datetime.now())
        
        logger.debug(f"Mapping error: {mapped_data}")
        return mapped_data
    
    def _parse_timestamp(self, ts_value: str) -> datetime:
        """
        Parse une chaîne de timestamp en objet datetime
        
        Args:
            ts_value: Chaîne de timestamp (format: 'YYYY-MM-DD HH:MM:SS.sss')
        
        Returns:
            Objet datetime
        """
        if not ts_value or not isinstance(ts_value, str):
            return datetime.now()
        
        try:
            # Format ISO avec T
            if "T" in ts_value:
                return datetime.fromisoformat(ts_value.replace("Z", "+00:00"))
            # Format 'YYYY-MM-DD HH:MM:SS.sss'
            else:
                # Remplacer l'espace par T pour fromisoformat
                return datetime.fromisoformat(ts_value.replace(" ", "T"))
        except (ValueError, AttributeError) as e:
            logger.warning(f"Impossible de parser le timestamp '{ts_value}': {e}")
            return datetime.now()
    
    def _parse_comment(self, comment_value: Any) -> str:
        """
        Parse la valeur du commentaire (peut être JSON ou chaîne)
        
        Args:
            comment_value: Valeur du commentaire (dict, str JSON, ou str simple)
        
        Returns:
            Chaîne de commentaire extraite
        """
        if not comment_value:
            return None
        
        # Si c'est déjà un dictionnaire
        if isinstance(comment_value, dict):
            return comment_value.get("raw") or str(comment_value)
        
        # Si c'est une chaîne
        if isinstance(comment_value, str):
            # Essayer de parser comme JSON
            try:
                parsed = json.loads(comment_value)
                if isinstance(parsed, dict):
                    return parsed.get("raw") or str(parsed)
                else:
                    return str(parsed)
            except (json.JSONDecodeError, TypeError):
                # Ce n'est pas du JSON, retourner la chaîne telle quelle
                return comment_value
        
        # Autre type, convertir en chaîne
        return str(comment_value)
