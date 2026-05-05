# -*- coding: utf-8 -*-
"""
Endpoints pour la gestion des rôles et permissions
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...api.dependencies import get_current_user, is_admin

router = APIRouter(prefix="/roles", tags=["Rôles"])


@router.get("/")
def list_roles(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Liste tous les rôles"""
    return {"roles": ["ADMIN", "DG", "COMPTABLE", "TECHNICIEN", "CAISSE"]}