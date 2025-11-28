"""
Orchestrateur pour le micro-middleware IDPS
Orchestre le processus complet d'ingestion
"""
import logging
import time
from typing import List
from datetime import datetime

from middleware.idps.services.file_detection_service import FileDetectionService
from middleware.idps.services.file_validation_service import FileValidationService
from middleware.idps.services.data_transformation_service import DataTransformationService
from middleware.idps.services.file_archive_service import FileArchiveService
from middleware.idps.validator import IDPSValidator
from middleware.idps.transformer import IDPSTransformer
from middleware.idps.repository.database_repository import IDPSDatabaseRepository
from middleware.idps.models.file_info import IDPSFileInfo
from middleware.idps.models.ingestion_result import IngestionResult
from middleware.exceptions import MiddlewareException

logger = logging.getLogger(__name__)


class IDPSOrchestrator:
    """
    Orchestrateur pour le micro-middleware IDPS
    Orchestre le processus complet : détection, validation, transformation, chargement, archivage
    """
    
    def __init__(self):
        """Initialise l'orchestrateur IDPS"""
        from middleware.idps.config.files_config import IDPSFilesConfig
        from middleware.idps.config.database_config import IDPSDatabaseConfig
        
        self.files_config = IDPSFilesConfig.from_env()
        self.db_config = IDPSDatabaseConfig.from_env()
        
        # Services
        self.file_detection_service = FileDetectionService(self.files_config)
        self.file_validation_service = FileValidationService(self.files_config)
        self.data_transformation_service = DataTransformationService(self.files_config)
        self.file_archive_service = FileArchiveService(self.files_config)
        
        # Services spécifiques IDPS
        self.idps_validator = IDPSValidator()
        self.idps_transformer = IDPSTransformer()
        self.idps_repository = IDPSDatabaseRepository(self.db_config)
    
    def process_file(self, file_info: IDPSFileInfo) -> IngestionResult:
        """
        Traite un fichier IDPS complet selon le pipeline d'ingestion
        
        Args:
            file_info: Informations sur le fichier à traiter
        
        Returns:
            IngestionResult contenant le résultat du traitement
        """
        start_time = time.time()
        file_path = file_info.path
        
        logger.info(f"Début du traitement du fichier IDPS: {file_path.name}")
        
        try:
            # 1. Validation générique
            validation_result = self.file_validation_service.validate_file(file_path, file_info)
            if not validation_result.is_valid:
                logger.error(f"Validation échouée pour {file_path.name}: {validation_result.error_message}")
                return self._handle_error(file_info, validation_result.error_message, 0)
            
            # 2. Validation spécifique IDPS
            schema_error = self.idps_validator.validate_schema(validation_result.data, file_info)
            if schema_error:
                logger.error(f"Validation de schéma IDPS échouée pour {file_path.name}: {schema_error}")
                return self._handle_error(file_info, f"Schéma invalide: {schema_error}", 0)
            
            # 3. Transformation générique
            transformation_result = self.data_transformation_service.transform(validation_result.data, file_info)
            if not transformation_result.transformed_data:
                logger.warning(f"Aucune donnée transformée pour {file_path.name}")
                return self._handle_error(
                    file_info, "Aucune donnée transformée",
                    transformation_result.original_count
                )
            
            # 4. Transformation spécifique IDPS
            final_data = []
            for row in transformation_result.transformed_data:
                mapped_row = self.idps_transformer.map_to_module_schema(row, file_info)
                final_data.append(mapped_row)
            
            # 5. Chargement en base via le repository IDPS
            rows_inserted = self.idps_repository.insert_events(final_data, file_info.category)
            
            if rows_inserted == 0:
                logger.warning(f"Aucune ligne insérée pour {file_path.name}")
                return self._handle_error(
                    file_info, "Aucune ligne insérée",
                    transformation_result.transformed_count
                )
            
            # 6. Marquer le fichier comme traité AVANT l'archivage (le fichier sera déplacé)
            self.file_detection_service.mark_as_processed(file_path, file_info)
            
            # 7. Archivage
            file_info.ingestion_timestamp = datetime.now()
            self.file_archive_service.archive_file(file_path, file_info, success=True)
            
            # 8. Log d'audit via le repository IDPS
            # TODO: utiliser records_expected / records_inserted plus précis
            self.idps_repository.insert_audit_log(
                file_info=file_info,
                status='success',
                rows_processed=transformation_result.original_count,
                error_message=None,
            )
            
            processing_time = time.time() - start_time
            logger.info(
                f"Traitement réussi pour {file_path.name}: "
                f"{rows_inserted} lignes insérées en {processing_time:.2f}s"
            )
            
            return IngestionResult(
                file_info=file_info,
                status='success',
                rows_processed=transformation_result.original_count,
                rows_inserted=rows_inserted,
                processing_time=processing_time
            )
            
        except MiddlewareException as e:
            logger.error(f"Erreur middleware lors du traitement de {file_path.name}: {e}")
            return self._handle_error(file_info, str(e), 0)
        except Exception as e:
            logger.error(f"Erreur inattendue lors du traitement de {file_path.name}: {e}", exc_info=True)
            return self._handle_error(file_info, f"Erreur inattendue: {str(e)}", 0)
    
    def _handle_error(
        self,
        file_info: IDPSFileInfo,
        error_message: str,
        rows_processed: int
    ) -> IngestionResult:
        """Gère les erreurs de traitement"""
        file_path = file_info.path
        
        try:
            # Archiver le fichier en erreur (seulement s'il existe encore)
            if file_path.exists():
                self.file_archive_service.archive_file(file_path, file_info, success=False)
            else:
                logger.warning(f"Le fichier {file_path.name} n'existe plus, archivage ignoré")
            
            # Enregistrer le log d'audit
            self.idps_repository.insert_audit_log(
                file_info=file_info,
                status='error',
                rows_processed=rows_processed,
                error_message=error_message
            )
        except Exception as e:
            logger.error(f"Erreur lors de la gestion d'erreur: {e}")
        
        return IngestionResult(
            file_info=file_info,
            status='error',
            rows_processed=rows_processed,
            rows_inserted=0,
            error_message=error_message
        )
    
    def run(self) -> List[IngestionResult]:
        """
        Exécute le processus complet d'ingestion IDPS
        
        Returns:
            Liste des résultats d'ingestion
        """
        logger.info("Démarrage du processus d'ingestion IDPS")
        
        # Détecter les fichiers IDPS
        detected_files = self.file_detection_service.detect_files()
        
        if not detected_files:
            logger.info("Aucun nouveau fichier IDPS détecté")
            return []
        
        logger.info(f"{len(detected_files)} fichier(s) IDPS détecté(s)")
        
        # Traiter chaque fichier
        results = []
        for file_info in detected_files:
            result = self.process_file(file_info)
            results.append(result)
        
        # Statistiques
        success_count = sum(1 for r in results if r.is_success)
        error_count = sum(1 for r in results if r.is_error)
        total_rows = sum(r.rows_inserted for r in results)
        
        logger.info(
            f"Traitement IDPS terminé: {success_count} succès, {error_count} erreurs, "
            f"{total_rows} lignes insérées au total"
        )
        
        return results

