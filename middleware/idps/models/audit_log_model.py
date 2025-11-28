"""
Modèle SQLAlchemy pour la table idps.ingestion_audit_log
"""
from sqlalchemy import Column, BigInteger, String, Date, DateTime, Integer, Text

from middleware.idps.config.sqlalchemy_config import Base


class IDPSAuditLogModel(Base):
    """Modèle SQLAlchemy pour la table idps.ingestion_audit_log"""

    __tablename__ = 'ingestion_audit_log'
    __table_args__ = {'schema': 'idps'}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    file_name = Column(String(255), nullable=False, unique=True, index=True)
    file_type = Column(String(50), nullable=False)
    file_date = Column(Date, nullable=False, index=True)
    records_expected = Column(Integer, nullable=False, default=0)
    records_inserted = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, index=True)  # SUCCESS, PARTIAL_SUCCESS, FAILED
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False, index=True)
    ended_at = Column(DateTime(timezone=True), nullable=True, index=True)

    def __repr__(self):
        return (
            f"<IDPSAuditLog(id={self.id}, file_name='{self.file_name}', "
            f"status='{self.status}', records_inserted={self.records_inserted})>"
        )

    def to_dict(self):
        """Convertit le modèle en dictionnaire"""
        return {
            'id': self.id,
            'file_name': self.file_name,
            'file_type': self.file_type,
            'file_date': self.file_date.isoformat() if self.file_date else None,
            'records_expected': self.records_expected,
            'records_inserted': self.records_inserted,
            'status': self.status,
            'error_message': self.error_message,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
        }
