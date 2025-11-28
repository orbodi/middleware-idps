"""
Repository SQLAlchemy pour la table idps.workflow_events
"""
from typing import List, Dict, Any
import logging
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from middleware.idps.config.database_config import IDPSDatabaseConfig
from middleware.idps.config.sqlalchemy_config import get_session, init_database
from middleware.idps.models.workflow_event_model import IDPSWorkflowEventModel
from middleware.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class WorkflowEventRepository:
    """Repository pour les événements de workflow IDPS (idps.workflow_events)"""

    def __init__(self, db_config: IDPSDatabaseConfig = None):
        self.db_config = db_config or IDPSDatabaseConfig.from_env()
        self.module = 'idps.workflow_events'
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

    def insert_events(self, data: List[Dict[str, Any]]) -> int:
        """Insère une liste d'événements de workflow"""
        if not data:
            return 0

        try:
            with self._get_session() as session:
                events = []
                for row in data:
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
                logger.info(f"{rows_inserted} événements insérés dans idps.workflow_events")
                return rows_inserted

        except SQLAlchemyError as e:
            error_msg = f"Erreur SQLAlchemy lors de l'insertion des événements de workflow: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, module=self.module, operation='insert') from e
        except Exception as e:
            error_msg = f"Erreur lors de l'insertion des événements de workflow: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, module=self.module, operation='insert') from e

    def get_events(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Récupère les événements de workflow récents"""
        try:
            with self._get_session() as session:
                events = (
                    session.query(IDPSWorkflowEventModel)
                    .order_by(IDPSWorkflowEventModel.event_timestamp.desc())
                    .limit(limit)
                    .offset(offset)
                    .all()
                )

                return [event.to_dict() for event in events]

        except SQLAlchemyError as e:
            error_msg = f"Erreur SQLAlchemy lors de la récupération des événements de workflow: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg, module=self.module, operation='get') from e
