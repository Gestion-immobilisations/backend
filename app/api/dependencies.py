# -*- coding: utf-8 -*-
"""
Dépendances FastAPI pour l'authentification et la gestion des rôles
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError
from typing import Optional, List

from ..core.database import get_db
from ..core.security import decode_token, get_token_subject
from ..models.utilisateur import Utilisateur
from ..core.enums import RoleEnum
import logging

logger = logging.getLogger(__name__)

# Configuration OAuth2 pour l'extraction du token depuis le header Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme)
) -> Utilisateur:
    """
    Dépendance pour récupérer l'utilisateur connecté à partir du token JWT.
    
    Args:
        request: Requête HTTP (pour logging)
        db: Session SQLAlchemy
        token: Token JWT extrait du header Authorization
        
    Returns:
        Utilisateur: L'utilisateur authentifié
        
    Raises:
        HTTPException: Si le token est manquant, invalide ou expiré
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants d'authentification invalides",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Vérifier que le token est présent
    if not token:
        # Vérifier si le token est dans les cookies (fallback)
        token = request.cookies.get("access_token")
        if not token:
            logger.warning("Tentative d'accès sans token d'authentification")
            raise credentials_exception
    
    try:
        # Décoder le token pour obtenir l'ID utilisateur
        user_id = get_token_subject(token)
        if not user_id:
            raise credentials_exception
        
        # Rechercher l'utilisateur en base
        user = db.query(Utilisateur).filter(Utilisateur.id == int(user_id)).first()
        if not user:
            logger.warning(f"Utilisateur avec ID {user_id} non trouvé en base")
            raise credentials_exception
        
        # Vérifier que le compte est actif
        if not user.est_actif:
            logger.warning(f"Tentative d'accès avec compte désactivé : {user.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Compte utilisateur désactivé"
            )
        
        return user
        
    except JWTError as e:
        logger.error(f"Erreur de validation du token JWT : {e}")
        raise credentials_exception
    except ValueError:
        logger.error("ID utilisateur invalide dans le token")
        raise credentials_exception
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la récupération de l'utilisateur : {e}")
        raise credentials_exception


def get_optional_user(
    request: Request,
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme)
) -> Optional[Utilisateur]:
    """
    Dépendance pour récupérer l'utilisateur si authentifié, sinon None.
    Utile pour les endpoints publics avec fonctionnalités supplémentaires pour les connectés.
    """
    try:
        return get_current_user(request, db, token)
    except HTTPException:
        return None


def require_role(allowed_roles: List[RoleEnum]):
    """
    Factory pour créer un décorateur de vérification de rôle.
    
    Args:
        allowed_roles: Liste des rôles autorisés à accéder à l'endpoint
        
    Returns:
        Fonction décorateur à utiliser avec Depends()
    """
    def role_checker(
        current_user: Utilisateur = Depends(get_current_user)
    ) -> Utilisateur:
        user_roles = [role.nom for role in current_user.roles]
        
        # Vérifier si l'utilisateur a l'un des rôles autorisés
        if not any(role.value in user_roles for role in allowed_roles):
            logger.warning(
                f"Accès refusé : utilisateur {current_user.email} "
                f"(rôles: {user_roles}) tente d'accéder à une ressource "
                f"nécessitant l'un des rôles : {[r.value for r in allowed_roles]}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Accès réservé aux rôles : {[r.value for r in allowed_roles]}"
            )
        
        return current_user
    
    return role_checker


# === Décorateurs prêts à l'emploi par rôle ===

def is_admin(current_user: Utilisateur = Depends(get_current_user)) -> Utilisateur:
    """Vérifie que l'utilisateur a le rôle ADMIN"""
    if not current_user.has_role("ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs"
        )
    return current_user


def is_dg(current_user: Utilisateur = Depends(get_current_user)) -> Utilisateur:
    """Vérifie que l'utilisateur a le rôle DG ou ADMIN"""
    if not (current_user.has_role("DG") or current_user.has_role("ADMIN")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé au Directeur Général"
        )
    return current_user


def is_comptable(current_user: Utilisateur = Depends(get_current_user)) -> Utilisateur:
    """Vérifie que l'utilisateur a le rôle COMPTABLE ou ADMIN"""
    if not (current_user.has_role("COMPTABLE") or current_user.has_role("ADMIN")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé au service comptable"
        )
    return current_user


def is_technicien(current_user: Utilisateur = Depends(get_current_user)) -> Utilisateur:
    """Vérifie que l'utilisateur a le rôle TECHNICIEN ou ADMIN"""
    if not (current_user.has_role("TECHNICIEN") or current_user.has_role("ADMIN")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux techniciens"
        )
    return current_user


def is_caisse(current_user: Utilisateur = Depends(get_current_user)) -> Utilisateur:
    """Vérifie que l'utilisateur a le rôle CAISSE ou ADMIN"""
    if not (current_user.has_role("CAISSE") or current_user.has_role("ADMIN")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé au service caisse"
        )
    return current_user