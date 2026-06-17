# backend/app/api/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Any

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
    login_data: LoginRequest,  # ← utilisation du schéma
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    audit_service = AuditService()
    
    # Authentification
    user = AuthService.authenticate_user(db, login_data.email, login_data.mot_de_passe)
    
    if not user:
        audit_service.log_action(
            db=db,
            user_id=None,
            table_name="utilisateurs",
            record_id=None,
            action="LOGIN_FAILED",
            anciennes_valeurs=None,
            nouvelles_valeurs={"email_tente": login_data.email, "ip": request.client.host}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    tokens = AuthService.create_tokens(user.id)
    AuthService.update_last_login(db, user, audit_service)
    
    roles = AuthService.get_user_roles(db, user)
    if not roles:
        roles = []
    elif isinstance(roles, str):
        roles = [roles]
    
    logger.info(f"✅ Connexion réussie - Email: {user.email}, Rôles: {roles}")
    
    user_response = UserAuthResponse(
        id=user.id,
        email=user.email,
        nom=user.nom,
        post_nom=user.post_nom,
        prenom=user.prenom,
        telephone=user.telephone,
        roles=roles,
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
    roles = AuthService.get_user_roles(db, current_user)
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
        roles=roles,
        est_actif=current_user.est_actif,
        last_login=current_user.last_login
    )

@router.post("/logout", response_model=LogoutResponse, status_code=status.HTTP_200_OK)
def logout(
    current_user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    logger.info(f"✅ Déconnexion - User: {current_user.email}")
    return LogoutResponse(message="Déconnexion réussie", success=True)

@router.post("/refresh", response_model=Token)
def refresh_token(
    refresh_data: RefreshTokenRequest,  # ← utilisation du schéma
    db: Session = Depends(get_db)
) -> Any:
    try:
        from ...core.security import decode_token, create_access_token
        from datetime import timedelta
        
        payload = decode_token(refresh_data.refresh_token)
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
        
        user = db.query(Utilisateur).filter(Utilisateur.id == int(user_id)).first()
        if not user or not user.est_actif:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Utilisateur invalide ou désactivé"
            )
        
        new_access_token = create_access_token(user.id)
        return Token(
            access_token=new_access_token,
            refresh_token=refresh_data.refresh_token,
            token_type="bearer",
            expires_in=30
        )
    except Exception as e:
        logger.error(f"Erreur refresh token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalide ou expiré"
        )