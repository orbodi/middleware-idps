"""
Configuration SQLAlchemy pour IDPS
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
import logging

from middleware.idps.config.database_config import IDPSDatabaseConfig

logger = logging.getLogger(__name__)

# Base pour les modèles SQLAlchemy
Base = declarative_base()

# Variables globales pour l'engine et la session
_engine = None
_session_factory = None


def get_engine(db_config: IDPSDatabaseConfig = None):
    """
    Crée ou retourne l'engine SQLAlchemy
    
    Args:
        db_config: Configuration de la base de données (charge depuis env si None)
    
    Returns:
        SQLAlchemy Engine
    """
    global _engine
    
    if _engine is None:
        db_config = db_config or IDPSDatabaseConfig.from_env()
        
        # Utiliser la méthode de la config pour générer l'URL
        database_url = db_config.to_sqlalchemy_url()
        
        _engine = create_engine(
            database_url,
            pool_pre_ping=True,  # Vérifier les connexions avant utilisation
            pool_recycle=3600,    # Recycler les connexions après 1 heure
            echo=False            # Mettre à True pour voir les requêtes SQL
        )
        
        logger.info(f"Engine SQLAlchemy créé pour la base de données: {db_config.database}")
    
    return _engine


def get_session_factory(db_config: IDPSDatabaseConfig = None):
    """
    Crée ou retourne la session factory SQLAlchemy
    
    Args:
        db_config: Configuration de la base de données (charge depuis env si None)
    
    Returns:
        Session factory
    """
    global _session_factory
    
    if _session_factory is None:
        engine = get_engine(db_config)
        _session_factory = scoped_session(
            sessionmaker(bind=engine, autocommit=False, autoflush=False)
        )
        logger.info("Session factory SQLAlchemy créée")
    
    return _session_factory


def get_session(db_config: IDPSDatabaseConfig = None):
    """
    Crée une nouvelle session SQLAlchemy
    
    Args:
        db_config: Configuration de la base de données (charge depuis env si None)
    
    Returns:
        Session SQLAlchemy
    """
    session_factory = get_session_factory(db_config)
    return session_factory()


def init_database(db_config: IDPSDatabaseConfig = None):
    """
    Initialise les tables dans la base de données (crée les tables si elles n'existent pas)
    
    Args:
        db_config: Configuration de la base de données (charge depuis env si None)
    """
    engine = get_engine(db_config)

    # Importer tous les modèles pour qu'ils soient enregistrés auprès de Base
    # (les imports suffisent, même si les noms ne sont pas utilisés directement)
    from middleware.idps.models.workflow_event_model import IDPSWorkflowEventModel  # noqa: F401
    from middleware.idps.models.error_event_model import IDPSErrorEventModel      # noqa: F401
    from middleware.idps.models.audit_log_model import IDPSAuditLogModel          # noqa: F401

    # Créer les tables si elles n'existent pas
    Base.metadata.create_all(engine)
    logger.info("Tables IDPS créées/vérifiées dans la base de données")

