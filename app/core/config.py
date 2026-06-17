# -*- coding: utf-8 -*-
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional, List
from urllib.parse import quote_plus
import os

class Settings(BaseSettings):
    # === Base de données ===
    # Si DATABASE_URL est fournie (par Railway), on l'utilise directement
    DATABASE_URL: Optional[str] = None

    # Variables pour la construction locale (fallback)
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "7234"  # À modifier selon votre environnement local
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "gestion_immobilisations"

    # === Sécurité JWT ===
    SECRET_KEY: str = "aCQ3jPNuPqa69hT0QxV5QgPDzagml8s48pw9PvTYxss"  # À remplacer par une variable d'environnement en prod
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # === CORS ===
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]

    # === Application ===
    APP_NAME: str = "Gestion Immobilisations"
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def database_url(self) -> str:
        """Retourne l'URL de connexion à la base de données."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        # Construction locale avec encodage du mot de passe
        encoded_password = quote_plus(self.POSTGRES_PASSWORD)
        return (
            f"postgresql://{self.POSTGRES_USER}:{encoded_password}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()