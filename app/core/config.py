# -*- coding: utf-8 -*-
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional, List  # ← AJOUTÉ: import List
from urllib.parse import quote_plus

class Settings(BaseSettings):
    # === Base de données ===
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "@@@@"  # ← Votre mot de passe avec @
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "gestion_immobilisationsDB"
    
    # === Construction SÉCURISÉE de l'URL de connexion ===
    @property
    def DATABASE_URL(self) -> str:
        # Encode le mot de passe pour gérer les caractères spéciaux (@, :, /, etc.)
        # @@@@ devient %40%40%40%40 dans l'URL
        encoded_password = quote_plus(self.POSTGRES_PASSWORD)
        return (
            f"postgresql://{self.POSTGRES_USER}:{encoded_password}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    # === Sécurité JWT ===
    SECRET_KEY: str = "Ton_Code_Securite_3000"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # === CORS Configuration (NOUVEAU) ===
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",      # Frontend React/Vue par défaut
        "http://localhost:8000",      # Backend lui-même
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        # Ajoutez d'autres origines si nécessaire
        # "http://votre-domaine.com",
    ]
    
    # === Application ===
    APP_NAME: str = "Gestion Immobilisations"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()