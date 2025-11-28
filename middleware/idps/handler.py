"""
Point d'entrée principal du micro-middleware IDPS
"""
from middleware.idps.orchestrator import IDPSOrchestrator
from middleware.utils.logger import setup_logger

# Configuration du logger
logger = setup_logger('idps_handler')


def main():
    """
    Point d'entrée principal pour l'exécution du handler IDPS
    """
    logger.info("=" * 60)
    logger.info("Démarrage du Micro-Middleware IDPS")
    logger.info("=" * 60)
    
    try:
        # Créer l'orchestrateur IDPS
        orchestrator = IDPSOrchestrator()
        
        # Exécuter le processus d'ingestion
        logger.info("Démarrage du processus d'ingestion IDPS...")
        results = orchestrator.run()
        
        # Afficher un résumé
        if results:
            success_count = sum(1 for r in results if r.is_success)
            error_count = sum(1 for r in results if r.is_error)
            total_rows = sum(r.rows_inserted for r in results)
            
            logger.info("=" * 60)
            logger.info(f"Résumé de l'ingestion IDPS:")
            logger.info(f"  - Fichiers traités: {len(results)}")
            logger.info(f"  - Succès: {success_count}")
            logger.info(f"  - Erreurs: {error_count}")
            logger.info(f"  - Lignes insérées: {total_rows}")
            logger.info("=" * 60)
        else:
            logger.info("Aucun fichier IDPS à traiter")
        
        logger.info("Micro-Middleware IDPS terminé avec succès")
        
    except Exception as e:
        logger.error(f"Erreur critique lors de l'exécution du handler IDPS: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
