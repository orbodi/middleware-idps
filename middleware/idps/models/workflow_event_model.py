"""
Modèle SQLAlchemy pour la table idps.workflow_events
"""
from sqlalchemy import Column, BigInteger, String, DateTime
from datetime import datetime

from middleware.idps.config.sqlalchemy_config import Base


class IDPSWorkflowEventModel(Base):
    """Modèle SQLAlchemy pour la table idps.workflow_events"""

    __tablename__ = 'workflow_events'
    __table_args__ = {'schema': 'idps'}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    event_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    document_type = Column(String(10), nullable=False)
    destination_code = Column(String(20), nullable=False, index=True)
    request_id = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)  # BACKLOG ou FINISH
    file_name = Column(String(255), nullable=False, index=True)
    ingested_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now, index=True)

    def __repr__(self):
        return (
            f"<IDPSWorkflowEvent(id={self.id}, request_id='{self.request_id}', "
            f"status='{self.status}', file_name='{self.file_name}')>"
        )

    def to_dict(self):
        """Convertit le modèle en dictionnaire"""
        return {
            'id': self.id,
            'event_timestamp': self.event_timestamp.isoformat() if self.event_timestamp else None,
            'document_type': self.document_type,
            'destination_code': self.destination_code,
            'request_id': self.request_id,
            'status': self.status,
            'file_name': self.file_name,
            'ingested_at': self.ingested_at.isoformat() if self.ingested_at else None,
        }
