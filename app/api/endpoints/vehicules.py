from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ...core.database import get_db
from ...models.vehicule import Vehicule
from ...core.security import get_current_user
from ...models.utilisateur import Utilisateur

router = APIRouter(prefix="/api/vehicules", tags=["Véhicules"])

@router.get("/")
async def get_vehicules(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    type_vehicule: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """Récupère tous les véhicules"""
    query = db.query(Vehicule)
    
    if type_vehicule:
        query = query.filter(Vehicule.type_vehicule == type_vehicule)
    
    vehicules = query.offset(skip).limit(limit).all()
    return {"total": len(vehicules), "vehicules": vehicules}

@router.get("/{bien_id}")
async def get_vehicule(
    bien_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """Récupère un véhicule spécifique"""
    vehicule = db.query(Vehicule).filter(Vehicule.id_bien == bien_id).first()
    if not vehicule:
        raise HTTPException(status_code=404, detail="Véhicule non trouvé")
    return vehicule