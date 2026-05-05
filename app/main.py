# -*- coding: utf-8 -*-
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.core.database import engine, Base
from app.core.config import settings

# Import des modèles (nécessaire pour que SQLAlchemy les enregistre)
import app.models

# Import des routers API
from app.api.endpoints import (
    auth,
    utilisateurs,
    roles,
    biens,
    vehicules,
    machines,
    ordinateurs,
    qr_code
)

# Création de l'application FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    description="API de gestion des immobilisations",
    version="1.0.0",
    debug=settings.DEBUG
)

# === Middleware CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Événement de démarrage : initialisation de la base de données ===
@app.on_event("startup")
def init_database():
    """
    Crée les tables dans la base de données.
    ⚠️ Note: En production, privilégiez Alembic pour les migrations.
    """
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tables de la base de données créées avec succès")
    except Exception as e:
        print(f"❌ Erreur lors de la création des tables : {e}")
        raise

# === Préfixe commun pour l'API ===
API_V1_PREFIX = "/api/v1"

# === Enregistrement des Routes (Endpoints) ===
# Authentification
app.include_router(auth.router, prefix=API_V1_PREFIX)

# Gestion des utilisateurs et rôles
app.include_router(utilisateurs.router, prefix=API_V1_PREFIX)
app.include_router(roles.router, prefix=API_V1_PREFIX)

# Gestion des biens (Phase 2)
app.include_router(biens.router, prefix=API_V1_PREFIX)
app.include_router(vehicules.router, prefix=API_V1_PREFIX)
app.include_router(machines.router, prefix=API_V1_PREFIX)
app.include_router(ordinateurs.router, prefix=API_V1_PREFIX)
app.include_router(qr_code.router, prefix=API_V1_PREFIX)

# === Endpoints de base ===
@app.get("/", tags=["Root"])
def read_root():
    """Endpoint racine - Informations générales sur l'API"""
    return {
        "message": "API Gestion des Immobilisations",
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/v1/docs",
        "redoc": "/api/v1/redoc"
    }

@app.get("/health", tags=["Health"])
def health_check():
    """Endpoint de vérification de la santé de l'API et de la base de données"""
    db_status = "unknown"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "database": db_status
    }