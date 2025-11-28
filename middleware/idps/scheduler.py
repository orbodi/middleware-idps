"""
Scheduler pour l'exécution automatique du micro-middleware IDPS
Exécution planifiée via schedule (cron-like)
"""
import schedule
import time
import logging

from middleware.idps.handler import main as idps_main
from middleware.idps.config.files_config import IDPSFilesConfig
from middleware.utils.logger import setup_logger

# Configuration du logger
logger = setup_logger('idps_scheduler')


def main():
    """Configure et démarre le scheduler pour IDPS"""
    files_config = IDPSFilesConfig.from_env()
    
    # Configuration du scheduler (peut être spécifique à IDPS ou utiliser la config globale)
    start_time = '03:00'  # TODO: Peut être chargé depuis la config
    
    # Planifier l'exécution quotidienne
    schedule.every().day.at(start_time).do(idps_main)
    
    logger.info(f"Scheduler IDPS configuré - Exécution quotidienne à {start_time}")
    logger.info("Le scheduler IDPS est en cours d'exécution. Appuyez sur Ctrl+C pour arrêter.")
    
    # Boucle principale
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Vérifier toutes les minutes
    except KeyboardInterrupt:
        logger.info("Arrêt du scheduler IDPS demandé par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur dans le scheduler IDPS: {e}", exc_info=True)


if __name__ == '__main__':
    main()

