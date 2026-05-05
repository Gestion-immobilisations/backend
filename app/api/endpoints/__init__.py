# -*- coding: utf-8 -*-
"""
Package endpoints - Export des routers API FastAPI

Ce module centralise l'accès aux endpoints de l'application.
Il permet des imports propres tout en évitant les imports circulaires
au démarrage de l'application via un chargement différé (lazy loading).

Exemple d'utilisation :
    # Import direct (recommandé dans main.py) :
    from app.api.endpoints import auth, utilisateurs, roles
    
    # Ou via fonction utilitaire (chargement différé) :
    from app.api.endpoints import get_router
    router = get_router("auth")
"""
from typing import Optional, Dict
from fastapi import APIRouter
from .biens import router as biens_router
from .vehicules import router as vehicules_router
from .machines import router as machines_router
from .ordinateurs import router as ordinateurs_router
from .qr_code import router as qr_code_router


# =============================================================================
# CONSTANTS - Noms des routers disponibles
# =============================================================================
AVAILABLE_ROUTERS: list[str] = [
    "auth",
    "utilisateurs",
    "roles",
    "biens",
    "vehicules",
    "machines",
    "ordinateurs",
    "pannes",
    "amortissements",
    "maintenances",
    "validations",
    "besoins",
    "pieces",
    "ecritures_comptables",
    "dashboard",
    "audit",
    "notifications",
    "rapports",
    "qr_code",
    "ia_decision",
]


# =============================================================================
# FONCTIONS UTILITAIRES - Chargement différé pour éviter circular imports
# =============================================================================

def get_router(name: str) -> Optional[APIRouter]:
    """
    Récupère un router API par son nom via import dynamique.
    
    Cette approche évite d'importer tous les modules au chargement
    du package, prévenant ainsi les erreurs d'imports circulaires.
    
    Args:
        name: Nom du router (ex: "auth", "utilisateurs", "biens")
        
    Returns:
        APIRouter: L'instance du router demandé, ou None si introuvable
        
    Raises:
        ImportError: Si le module endpoint n'existe pas ou n'exporte pas 'router'
    """
    if name not in AVAILABLE_ROUTERS:
        return None
    
    try:
        # Import dynamique du module endpoint
        module = __import__(
            f"app.api.endpoints.{name}",
            fromlist=["router"]
        )
        return getattr(module, "router", None)
    except (ImportError, AttributeError) as e:
        # Router non prêt ou mal configuré - retourne None sans crash
        # Utile en développement quand on ajoute progressivement les endpoints
        return None


def get_all_active_routers() -> Dict[str, APIRouter]:
    """
    Récupère tous les routers actuellement disponibles et fonctionnels.
    
    Returns:
        dict: Mapping nom → APIRouter pour les routers chargés avec succès
    """
    routers = {}
    for name in AVAILABLE_ROUTERS:
        router = get_router(name)
        if router is not None:
            routers[name] = router
    return routers


def register_routers(app, prefix: str = "/api/v1"):
    """
    Enregistre automatiquement tous les routers disponibles dans l'application FastAPI.
    
    Args:
        app: Instance FastAPI
        prefix: Préfixe commun pour toutes les routes (ex: "/api/v1")
        
    Usage dans main.py :
        from app.api.endpoints import register_routers
        register_routers(app, prefix="/api/v1")
    """
    from fastapi import FastAPI
    
    if not isinstance(app, FastAPI):
        raise TypeError("L'argument 'app' doit être une instance de FastAPI")
    
    active_routers = get_all_active_routers()
    
    for name, router in active_routers.items():
        app.include_router(router, prefix=f"{prefix}/{name}" if name != "auth" else prefix)


# =============================================================================
# EXPORTS PUBLICS - Ce qui est accessible via 'from app.api.endpoints import *'
# =============================================================================
__all__ = [
    "AVAILABLE_ROUTERS",
    "get_router",
    "get_all_active_routers",
    "register_routers",
    "biens_router",
    "vehicules_router",
    "machines_router",
    "ordinateurs_router",
    "qr_code_router"
]