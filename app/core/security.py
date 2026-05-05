# -*- coding: utf-8 -*-
"""
Module de sécurité : hachage des mots de passe, gestion JWT et dépendances d'authentification
"""
from datetime import datetime, timedelta
from typing import Optional, Union, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from .config import settings
from ..models.utilisateur import Utilisateur
from ..core.database import get_db
import logging

logger = logging.getLogger(__name__)

# Configuration OAuth2 pour extraire le token depuis le header Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

# Configuration du hachage des mots de passe (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# === Gestion des mots de passe ===

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie si un mot de passe en clair correspond à un hash bcrypt."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Erreur vérification mot de passe : {e}")
        return False


def get_password_hash(password: str) -> str:
    """Génère un hash bcrypt sécurisé."""
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.error(f"Erreur hachage mot de passe : {e}")
        raise


# === Gestion des tokens JWT ===

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Crée un token d'accès JWT signé."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: Union[str, Any]) -> str:
    """Crée un refresh token JWT (durée de vie : 7 jours)."""
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """Décode et vérifie un token JWT."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.ExpiredSignatureError:
        logger.warning("Token JWT expiré")
        raise JWTError("Token expiré")
    except jwt.JWTError as e:
        logger.error(f"Erreur décodage token JWT : {e}")
        raise JWTError(f"Token invalide : {str(e)}")


def get_token_subject(token: str) -> Optional[str]:
    """Extrait l'identifiant utilisateur depuis un token."""
    try:
        payload = decode_token(token)
        return payload.get("sub")
    except JWTError:
        return None


# === ✅ CORRIGÉ : Dépendance d'authentification pour FastAPI ===

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Utilisateur:
    """
    Dépendance FastAPI pour récupérer l'utilisateur authentifié.
    À utiliser dans les endpoints protégés.
    
    Raises:
        HTTPException 401: Si le token est manquant ou invalide
        HTTPException 404: Si l'utilisateur n'existe plus en base
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants invalides ou token expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise credentials_exception
    
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # ✅ CORRIGÉ : Utilisation de 'id' au lieu de 'id_utilisateur'
    user = db.query(Utilisateur).filter(Utilisateur.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    
    # ✅ CORRIGÉ : Utilisation de 'est_actif' au lieu de 'actif'
    if not user.est_actif:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte utilisateur désactivé"
        )
    
    return user


def get_current_active_user(
    current_user: Utilisateur = Depends(get_current_user)
) -> Utilisateur:
    """
    Dépendance supplémentaire pour vérifier que l'utilisateur est actif.
    Utile si get_current_user ne suffit pas.
    """
    if not current_user.est_actif:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte utilisateur inactif"
        )
    return current_user


def check_permission(permission_name: str):
    """
    Factory pour créer une dépendance de vérification de permission.
    Usage: Depends(check_permission("create_bien"))
    """
    def permission_checker(
        current_user: Utilisateur = Depends(get_current_user)
    ) -> Utilisateur:
        if not current_user.has_permission(permission_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission_name}' requise"
            )
        return current_user
    return permission_checker