"""
Configuration de la base de données pour IDPS
"""
import os
from dataclasses import dataclass
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


@dataclass
class IDPSDatabaseConfig:
    """Configuration de la base de données IDPS"""
    host: str
    port: int
    database: str
    user: str
    password: str
    
    def to_connection_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour psycopg2 (compatibilité)"""
        return {
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'user': self.user,
            'password': self.password
        }
    
    def to_sqlalchemy_url(self) -> str:
        """Génère l'URL de connexion SQLAlchemy (driver psycopg v3)"""
        # Utilise le dialecte postgresql+psycopg pour le driver psycopg v3
        return (
            f"postgresql+psycopg://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}"
        )
    
    @classmethod
    def from_env(cls) -> 'IDPSDatabaseConfig':
        """
        Charge la configuration depuis les variables d'environnement
        
        Returns:
            Instance de IDPSDatabaseConfig
        """
        return cls(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            database=os.getenv('DB_NAME', 'biometrics_db'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres')
        )

