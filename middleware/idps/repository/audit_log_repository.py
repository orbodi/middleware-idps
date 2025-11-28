"""
Repository SQLAlchemy pour la table idps.ingestion_audit_log
"""
from typing import Optional
import logging
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from middleware.idps.config.database_config import IDPSDatabaseConfig
from middleware.idps.config.sqlalchemy_config import get_session, init_database
from middleware.idps.models.file_info import IDPSFileInfo
from middleware.idps.models.audit_log_model import IDPSAuditLogModel
from middleware.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class AuditLogRepository:
    """Repository pour les logs d'audit IDPS (idps.ingestion_audit_log)"""

    def __init__(self, db_config: IDPSDatabaseConfig = None):
        self.db_config = db_config or IDPSDatabaseConfig.from_env()
        self.module = 'idps.ingestion_audit_log'
        init_database(self.db_config)

    @contextmanager
    def _get_session(self) -> Session:
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

    def insert_audit_log(self, file_info: IDPSFileInfo, status: str,
                          records_expected: int, records_inserted: int,
                          error_message: Optional[str] = None) -> int:
        """Insère un log d'audit pour un fichier IDPS"""
        try:
            with self._get_session() as session:
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
                logger.info(f"Log d'audit IDPS inséré avec l'ID: {log_id}")
                return log_id

        except SQLAlchemyError as e:
            error_msg = f"Erreur SQLAlchemy lors de l'insertion du log d'audit: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, module=self.module, operation='insert') from e
        except Exception as e:
            error_msg = f"Erreur lors de l'insertion du log d'audit: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, module=self.module, operation='insert') from e
