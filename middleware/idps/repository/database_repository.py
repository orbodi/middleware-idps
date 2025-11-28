"""
Repository pour l'accès à la base de données IDPS utilisant SQLAlchemy ORM
"""
from typing import List, Dict, Any, Optional
import logging
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from middleware.idps.domain_interfaces import IModuleRepository
from middleware.idps.config.database_config import IDPSDatabaseConfig
from middleware.idps.config.sqlalchemy_config import get_session, init_database
from middleware.idps.models.file_info import IDPSFileInfo
from middleware.idps.models.workflow_event_model import IDPSWorkflowEventModel
from middleware.idps.models.error_event_model import IDPSErrorEventModel
from middleware.idps.models.audit_log_model import IDPSAuditLogModel
from middleware.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class IDPSDatabaseRepository(IModuleRepository):
    """Repository pour les opérations de base de données IDPS utilisant SQLAlchemy ORM"""
    
    def __init__(self, db_config: IDPSDatabaseConfig = None):
        """
        Initialise le repository IDPS
        
        Args:
            db_config: Configuration de la base de données (charge depuis env si None)
        """
        self.db_config = db_config or IDPSDatabaseConfig.from_env()
        self.module = 'idps'
        
        # Initialiser la base de données (créer les tables si nécessaire)
        init_database(self.db_config)
    
    @contextmanager
    def _get_session(self) -> Session:
        """
        Context manager pour gérer les sessions SQLAlchemy
        
        Yields:
            Session SQLAlchemy
        """
        session = get_session(self.db_config)
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            error_msg = f"Erreur de session SQLAlchemy pour {self.module}: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, module=self.module, operation='session') from e
        finally:
            session.close()
    
    def insert_events(self, data: List[Dict[str, Any]], category: str) -> int:
        """
        Insère les événements dans les tables IDPS
        
        Args:
            data: Données à insérer
            category: Catégorie ('workflow' ou 'error')
        
        Returns:
            Nombre de lignes insérées
        """
        if not data:
            return 0
        
        if category == 'workflow':
            return self._insert_workflow_events(data)
        elif category == 'error':
            return self._insert_error_events(data)
        else:
            logger.warning(f"Catégorie inconnue: {category}, utilisation de workflow_events")
            return self._insert_workflow_events(data)
    
    def _insert_workflow_events(self, data: List[Dict[str, Any]]) -> int:
        """Insère dans idps.workflow_events"""
        try:
            with self._get_session() as session:
                events = []
                for row in data:
                    # `row` est déjà au format spécifique IDPS (voir `IDPSTransformer`)
                    event = IDPSWorkflowEventModel(
                        event_timestamp=row.get('event_timestamp', datetime.now()),
                        document_type=row.get('document_type', ''),
                        destination_code=row.get('destination_code', ''),
                        request_id=row.get('request_id', ''),
                        status=row.get('status', ''),
                        file_name=row.get('file_name', ''),
                        ingested_at=row.get('ingested_at', datetime.now()),
                    )
                    events.append(event)

                session.bulk_save_objects(events)
                session.flush()
                rows_inserted = len(events)
                logger.info(f"{rows_inserted} événements de workflow insérés dans idps.workflow_events")
                return rows_inserted
                
        except SQLAlchemyError as e:
            error_msg = f"Erreur SQLAlchemy lors de l'insertion des événements de workflow: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, module=self.module, operation='insert_workflow') from e
        except Exception as e:
            error_msg = f"Erreur lors de l'insertion des événements de workflow: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, module=self.module, operation='insert_workflow') from e
    
    def _insert_error_events(self, data: List[Dict[str, Any]]) -> int:
        """Insère dans idps.error_events"""
        try:
            with self._get_session() as session:
                events = []
                for row in data:
                    # `row` est déjà au format spécifique IDPS (voir `IDPSTransformer`)
                    event = IDPSErrorEventModel(
                        event_timestamp=row.get('event_timestamp', datetime.now()),
                        document_type=row.get('document_type', ''),
                        destination_code=row.get('destination_code', ''),
                        request_id=row.get('request_id', ''),
                        service_name=row.get('service_name', ''),
                        error_category=row.get('error_category', ''),
                        comment=row.get('comment', ''),
                        file_name=row.get('file_name', ''),
                        ingested_at=row.get('ingested_at', datetime.now()),
                    )
                    events.append(event)

                session.bulk_save_objects(events)
                session.flush()
                rows_inserted = len(events)
                logger.info(f"{rows_inserted} événements d'erreur insérés dans idps.error_events")
                return rows_inserted
                
        except SQLAlchemyError as e:
            error_msg = f"Erreur SQLAlchemy lors de l'insertion des événements d'erreur: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, module=self.module, operation='insert_error') from e
        except Exception as e:
            error_msg = f"Erreur lors de l'insertion des événements d'erreur: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, module=self.module, operation='insert_error') from e
    
    def insert_audit_log(
        self,
        file_info: IDPSFileInfo,
        status: str,
        rows_processed: int,
        error_message: Optional[str] = None,
        ) -> int:
            """
            Insère ou met à jour un log d'audit dans idps.ingestion_audit_log (idempotent sur file_name)
    
            Args:
                file_info: Informations sur le fichier traité
                status: Statut du traitement ('success', 'error', etc.)
                rows_processed: Nombre de lignes traitées
                error_message: Message d'erreur si applicable
    
            Returns:
                ID du log d'audit
            """
            try:
                with self._get_session() as session:
                    records_expected = rows_processed
                    records_inserted = rows_processed if status == 'success' else 0
    
                    # Vérifier si un log existe déjà pour ce fichier (idempotence par file_name)
                    existing: Optional[IDPSAuditLogModel] = (
                        session.query(IDPSAuditLogModel)
                        .filter(IDPSAuditLogModel.file_name == file_info.name)
                        .one_or_none()
                    )
    
                    if existing:
                        # Mettre à jour le log existant
                        existing.file_type = file_info.file_type
                        existing.file_date = file_info.date
                        existing.records_expected = records_expected
                        existing.records_inserted = records_inserted
                        existing.status = status
                        existing.error_message = error_message
                        # On met à jour seulement ended_at; on ne touche pas started_at initial
                        existing.ended_at = datetime.now()
                        log_id = existing.id
                        logger.info(
                            f"Log d'audit IDPS mis à jour pour le fichier {file_info.name} (ID: {log_id})"
                        )
                        return log_id
    
                    # Aucun log existant : création
                    audit_log = IDPSAuditLogModel(
                        file_name=file_info.name,
                        file_type=file_info.file_type,
                        file_date=file_info.date,
                        records_expected=records_expected,
                        records_inserted=records_inserted,
                        status=status,
                        error_message=error_message,
                        started_at=file_info.ingestion_timestamp or datetime.now(),
                        ended_at=datetime.now(),
                    )
    
                    session.add(audit_log)
                    session.flush()
    
                    log_id = audit_log.id
                    logger.info(f"Nouveau log d'audit IDPS inséré avec l'ID: {log_id}")
                    return log_id
    
            except SQLAlchemyError as e:
                error_msg = f"Erreur SQLAlchemy lors de l'insertion du log d'audit: {e}"
                logger.error(error_msg)
                raise DatabaseError(error_msg, module=self.module, operation='insert_audit') from e
            except Exception as e:
                error_msg = f"Erreur lors de l'insertion du log d'audit: {e}"
                logger.error(error_msg)
                raise DatabaseError(error_msg, module=self.module, operation='insert_audit') from e
    
    def get_workflow_events(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Récupère les événements de workflow (exemple de méthode de lecture)
        
        Args:
            limit: Nombre maximum d'événements à récupérer
            offset: Nombre d'événements à ignorer
        
        Returns:
            Liste des événements de workflow
        """
        try:
            with self._get_session() as session:
                events = session.query(IDPSWorkflowEventModel)\
                    .order_by(IDPSWorkflowEventModel.ingested_at.desc())\
                    .limit(limit)\
                    .offset(offset)\
                    .all()
                
                return [event.to_dict() for event in events]
                
        except SQLAlchemyError as e:
            error_msg = f"Erreur SQLAlchemy lors de la récupération des événements: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, module=self.module, operation='get_workflow_events') from e
    
    def get_error_events(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Récupère les événements d'erreur (exemple de méthode de lecture)
        
        Args:
            limit: Nombre maximum d'événements à récupérer
            offset: Nombre d'événements à ignorer
        
        Returns:
            Liste des événements d'erreur
        """
        try:
            with self._get_session() as session:
                events = session.query(IDPSErrorEventModel)\
                    .order_by(IDPSErrorEventModel.ingested_at.desc())\
                    .limit(limit)\
                    .offset(offset)\
                    .all()
                
                return [event.to_dict() for event in events]
                
        except SQLAlchemyError as e:
            error_msg = f"Erreur SQLAlchemy lors de la récupération des événements: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, module=self.module, operation='get_error_events') from e
