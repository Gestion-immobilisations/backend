# backend/app/api/endpoints/biens.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
import io
from typing import List, Optional
import logging
from ...core.database import get_db
from ...schemas.bien import BienCreate, BienUpdate, BienResponse, BienListResponse
from ...services.bien_service import BienService
from ...services.qr_code_service import QRCodeService
from ...api.dependencies import get_current_user  # ← import corrigé
from ...models.utilisateur import Utilisateur
from ...models.bien import EtatBien

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/biens", tags=["Biens"])

def check_permission(user: Utilisateur, required_permission: str) -> bool:
    if not user:
        return False
    role_name = None
    if user.role:
        if hasattr(user.role, 'nom'):
            role_name = user.role.nom
        else:
            role_name = str(user.role)
    if role_name and role_name.upper() == "ADMIN":
        return True
    role_permissions = {
        "ADMIN": ["create_bien", "view_bien", "edit_bien", "delete_bien"],
        "DG": ["create_bien", "view_bien", "edit_bien", "delete_bien"],
        "GESTIONNAIRE": ["create_bien", "view_bien", "edit_bien", "delete_bien"],
        "COMPTABLE": ["view_bien"],
        "TECHNICIEN": ["view_bien", "edit_bien"],
        "CAISSE": ["view_bien"],
        "USER": ["view_bien"]
    }
    role = role_name.upper() if role_name else "USER"
    allowed = role_permissions.get(role, role_permissions["USER"])
    return required_permission in allowed

@router.post("/", response_model=BienResponse, status_code=status.HTTP_201_CREATED)
async def create_bien(
    bien_data: BienCreate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    service = BienService(db)
    if not check_permission(current_user, "create_bien"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissions insuffisantes pour créer un bien"
        )
    return service.create_bien(bien_data)

@router.get("/", response_model=BienListResponse)
async def get_biens(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    type_bien: Optional[str] = None,
    etat: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    service = BienService(db)
    if not check_permission(current_user, "view_bien"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissions insuffisantes pour voir les biens"
        )
    biens = service.get_all_biens(
        skip=skip, 
        limit=limit,
        type_bien=type_bien,
        etat=etat
    )
    return BienListResponse(
        total=len(biens),
        page=(skip // limit) + 1,
        page_size=limit,
        biens=biens
    )

@router.get("/{bien_id}", response_model=BienResponse)
async def get_bien(
    bien_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    service = BienService(db)
    if not check_permission(current_user, "view_bien"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissions insuffisantes pour voir ce bien"
        )
    bien = service.get_bien_by_id(bien_id)
    if not bien:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bien {bien_id} non trouvé"
        )
    return bien

@router.put("/{bien_id}", response_model=BienResponse)
async def update_bien(
    bien_id: int,
    bien_data: BienUpdate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    service = BienService(db)
    if not check_permission(current_user, "edit_bien"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissions insuffisantes pour modifier un bien"
        )
    bien = service.update_bien(bien_id, bien_data)
    if not bien:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bien {bien_id} non trouvé"
        )
    return bien

@router.delete("/{bien_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bien(
    bien_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    service = BienService(db)
    if not check_permission(current_user, "delete_bien"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissions insuffisantes pour supprimer un bien"
        )
    if not service.delete_bien(bien_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bien {bien_id} non trouvé"
        )

@router.get("/{bien_id}/qr-code")
async def get_bien_qr_code(
    bien_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    service = BienService(db)
    if not check_permission(current_user, "view_bien"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissions insuffisantes"
        )
    bien = service.get_bien_by_id(bien_id)
    if not bien:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bien {bien_id} non trouvé"
        )
    qr_service = QRCodeService()
    qr_code_image = qr_service.generate_qr_code(bien.qr_code, bien_id)
    return StreamingResponse(
        io.BytesIO(qr_code_image),
        media_type="image/png",
        headers={"Content-Disposition": f"inline; filename=qr_code_{bien_id}.png"}
    )

@router.get("/{bien_id}/age")
async def get_bien_age(
    bien_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    service = BienService(db)
    if not check_permission(current_user, "view_bien"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissions insuffisantes"
        )
    age = service.calculer_age_bien(bien_id)
    if age is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bien {bien_id} non trouvé"
        )
    return {"bien_id": bien_id, "age_years": age}

@router.patch("/{bien_id}/etat")
async def change_bien_etat(
    bien_id: int,
    nouvel_etat: str,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    service = BienService(db)
    if not check_permission(current_user, "edit_bien"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissions insuffisantes pour modifier l'état d'un bien"
        )
    try:
        etat = EtatBien(nouvel_etat)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"État invalide. Valeurs possibles: {[e.value for e in EtatBien]}"
        )
    bien = service.changer_etat_bien(bien_id, etat)
    if not bien:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bien {bien_id} non trouvé"
        )
    return bien

@router.get("/statistics/summary")
async def get_biens_statistics(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    if not check_permission(current_user, "view_bien"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissions insuffisantes"
        )
    service = BienService(db)
    return service.get_statistics()