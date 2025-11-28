"""
Exceptions personnalisées pour le middleware
"""
from typing import Optional, Dict, Any


class MiddlewareException(Exception):
    """Exception de base pour toutes les exceptions du middleware"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message)
        self.message = message
        self.extra = kwargs


class FileDetectionError(MiddlewareException):
    """Erreur lors de la détection de fichiers"""
    
    def __init__(self, message: str, file_path: Optional[str] = None, **kwargs):
        super().__init__(message, file_path=file_path, **kwargs)
        self.file_path = file_path


class FileValidationError(MiddlewareException):
    """Erreur lors de la validation de fichiers"""
    
    def __init__(self, message: str, file_path: Optional[str] = None, **kwargs):
        super().__init__(message, file_path=file_path, **kwargs)
        self.file_path = file_path


class DataTransformationError(MiddlewareException):
    """Erreur lors de la transformation des données"""
    
    def __init__(self, message: str, row_data: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(message, row_data=row_data, **kwargs)
        self.row_data = row_data


class DatabaseError(MiddlewareException):
    """Erreur lors des opérations de base de données"""
    
    def __init__(self, message: str, module: Optional[str] = None, operation: Optional[str] = None, **kwargs):
        super().__init__(message, module=module, operation=operation, **kwargs)
        self.module = module
        self.operation = operation


class ArchiveError(MiddlewareException):
    """Erreur lors de l'archivage de fichiers"""
    
    def __init__(self, message: str, file_path: Optional[str] = None, **kwargs):
        super().__init__(message, file_path=file_path, **kwargs)
        self.file_path = file_path


class ConfigurationError(MiddlewareException):
    """Erreur de configuration"""
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        super().__init__(message, config_key=config_key, **kwargs)
        self.config_key = config_key
