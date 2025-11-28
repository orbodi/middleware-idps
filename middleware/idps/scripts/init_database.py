"""
Script d'initialisation de la base de données IDPS avec SQLAlchemy
Crée les tables si elles n'existent pas
"""
import sys
from pathlib import Path

# Ajouter le répertoire racine au path
root_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(root_dir))

from middleware.idps.config.sqlalchemy_config import init_database
from middleware.utils.logger import setup_logger

logger = setup_logger('init_database')


def main():
    """Initialise la base de données IDPS"""
    logger.info("Initialisation de la base de données IDPS...")
    
    try:
        init_database()
        logger.info("Base de données IDPS initialisée avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de la base de données: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

