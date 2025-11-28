"""
Configuration centralisée du logger
"""
import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logger(name: str, log_level: int = logging.INFO) -> logging.Logger:
    """
    Configure et retourne un logger
    
    Args:
        name: Nom du logger
        log_level: Niveau de log (par défaut: INFO)
    
    Returns:
        Logger configuré
    """
    logger = logging.getLogger(name)
    
    # Éviter la duplication des handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(log_level)
    
    # Format des logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler pour la console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler pour le fichier (optionnel)
    try:
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        # Si on ne peut pas créer le fichier de log, continuer sans
        logger.warning(f"Impossible de créer le fichier de log: {e}")
    
    return logger
