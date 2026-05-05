# backend/app/api/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Any, List

from ...core.database import get_db
from ...schemas.auth import (
    LoginRequest, LoginResponse, LogoutResponse,
    RefreshTokenRequest, ChangePasswordRequest,
    ForgotPasswordRequest, ResetPasswordRequest,
    Token, UserAuthResponse
)
from ...services.auth_service import AuthService
from ...services.audit_service import AuditService
from ...api.dependencies import get_current_user
from ...models.utilisateur import Utilisateur
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
def login(
    request: Request,
    email: str,
    mot_de_passe: str,
    db: Session = Depends(get_db)
) -> Any:
    audit_service = AuditService()
    
    # Authentification
    user = AuthService.authenticate_user(db, email, mot_de_passe)
    
    if not user:
        audit_service.log_action(
            db=db,
            user_id=None,
            table_name="utilisateurs",
            record_id=None,
            action="LOGIN_FAILED",
            anciennes_valeurs=None,
            nouvelles_valeurs={"email_tente": email, "ip": request.client.host}
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Génération des tokens
    tokens = AuthService.create_tokens(user.id)
    
    # Mise à jour de la dernière connexion
    AuthService.update_last_login(db, user, audit_service)
    
    # ✅ Récupération des rôles - FORCER une liste
    roles = AuthService.get_user_roles(db, user)
    
    # ✅ S'assurer que roles est une liste, même si vide
    if not roles:
        roles = []
    elif isinstance(roles, str):
        roles = [roles]
    
    logger.info(f"✅ Connexion réussie - Email: {user.email}, Rôles: {roles}")
    
    # Préparation de la réponse utilisateur
    user_response = UserAuthResponse(
        id=user.id,
        email=user.email,
        nom=user.nom,
        post_nom=user.post_nom,
        prenom=user.prenom,
        telephone=user.telephone,
        roles=roles,  # ✅ Maintenant c'est une liste garantie
        est_actif=user.est_actif,
        last_login=user.last_login
    )
    
    return LoginResponse(
        message="Connexion réussie",
        token=Token(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=tokens["expires_in"]
        ),
        user=user_response
    )


@router.get("/me", response_model=UserAuthResponse)
def get_current_user_info(
    current_user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Retourne les informations de l'utilisateur connecté."""
    
    # ✅ Récupération des rôles - FORCER une liste
    roles = AuthService.get_user_roles(db, current_user)
    
    # ✅ S'assurer que roles est une liste, même si vide
    if not roles:
        roles = []
    elif isinstance(roles, str):
        roles = [roles]
    
    logger.info(f"✅ GET /me - User: {current_user.email}, Rôles: {roles}")
    
    return UserAuthResponse(
        id=current_user.id,
        email=current_user.email,
        nom=current_user.nom,
        post_nom=current_user.post_nom,
        prenom=current_user.prenom,
        telephone=current_user.telephone,
        roles=roles,  # ✅ Liste garantie
        est_actif=current_user.est_actif,
        last_login=current_user.last_login
    )


# ✅ NOUVEAU : Route logout ajoutée
@router.post("/logout", response_model=LogoutResponse, status_code=status.HTTP_200_OK)
def logout(
    current_user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Déconnexion de l'utilisateur"""
    logger.info(f"✅ Déconnexion - User: {current_user.email}")
    
    # Optionnel : Invalider le token en base (si vous avez une blacklist)
    # AuditService.log_action(db, current_user.id, "auth", current_user.id, "LOGOUT", None, None)
    
    return LogoutResponse(
        message="Déconnexion réussie",
        success=True
    )


# ✅ NOUVEAU : Route refresh token (optionnelle mais recommandée)
@router.post("/refresh", response_model=Token)
def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
) -> Any:
    """Rafraîchir le token d'accès"""
    try:
        from ...core.security import decode_token, create_access_token
        from datetime import timedelta
        
        payload = decode_token(refresh_token)
        
        # Vérifier que c'est bien un refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide"
            )
        
        # Vérifier que l'utilisateur existe toujours
        user = db.query(Utilisateur).filter(Utilisateur.id == int(user_id)).first()
        if not user or not user.est_actif:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Utilisateur invalide ou désactivé"
            )
        
        # Créer un nouveau access token
        new_access_token = create_access_token(user.id)
        
        return Token(
            access_token=new_access_token,
            refresh_token=refresh_token,  # Garder le même refresh token
            token_type="bearer",
            expires_in=30  # 30 minutes
        )
        
    except Exception as e:
        logger.error(f"Erreur refresh token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalide ou expiré"
        )