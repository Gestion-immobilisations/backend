# -*- coding: utf-8 -*-
"""
Schémas Pydantic pour l'authentification et la gestion des tokens
"""
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime
import re


# === Schémas de requête ===

class LoginRequest(BaseModel):
    """Schéma pour la requête de connexion"""
    email: EmailStr
    mot_de_passe: str
    
    @field_validator('mot_de_passe')
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Validation de la complexité du mot de passe"""
        if len(v) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères")
        if not re.search(r'[A-Z]', v):
            raise ValueError("Le mot de passe doit contenir au moins une majuscule")
        if not re.search(r'[a-z]', v):
            raise ValueError("Le mot de passe doit contenir au moins une minuscule")
        if not re.search(r'\d', v):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre")
        return v


class RefreshTokenRequest(BaseModel):
    """Schéma pour la requête de rafraîchissement de token"""
    refresh_token: str


# === Schémas de réponse ===

class Token(BaseModel):
    """Schéma pour les tokens d'authentification"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes en secondes


class TokenPayload(BaseModel):
    """Payload décodé d'un token JWT"""
    sub: Optional[str] = None
    exp: Optional[datetime] = None
    type: Optional[str] = None


class UserAuthResponse(BaseModel):
    """Informations utilisateur retournées après authentification"""
    id: int
    email: EmailStr
    nom: str
    post_nom: Optional[str] = None
    prenom: str
    telephone: Optional[str] = None
    roles: List[str] = []
    est_actif: bool
    last_login: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    """Réponse complète après connexion réussie"""
    message: str = "Connexion réussie"
    token: Token
    user: UserAuthResponse


class LogoutResponse(BaseModel):
    """Réponse après déconnexion"""
    message: str = "Déconnexion réussie"


# === Schémas pour la gestion du profil ===

class ChangePasswordRequest(BaseModel):
    """Schéma pour changer son mot de passe"""
    ancien_mot_de_passe: str
    nouveau_mot_de_passe: str
    
    @field_validator('nouveau_mot_de_passe')
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères")
        if not re.search(r'[A-Z]', v):
            raise ValueError("Le mot de passe doit contenir au moins une majuscule")
        if not re.search(r'[a-z]', v):
            raise ValueError("Le mot de passe doit contenir au moins une minuscule")
        if not re.search(r'\d', v):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre")
        return v


class ForgotPasswordRequest(BaseModel):
    """Schéma pour demander une réinitialisation de mot de passe"""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Schéma pour réinitialiser son mot de passe avec un token"""
    token: str
    nouveau_mot_de_passe: str
    
    @field_validator('nouveau_mot_de_passe')
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères")
        return v