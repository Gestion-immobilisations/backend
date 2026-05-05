# backend/app/services/bien_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import uuid
from datetime import datetime
from ..models.bien import Bien, EtatBien
from ..models.vehicule import Vehicule
from ..models.machine import Machine
from ..models.ordinateur import Ordinateur
from ..schemas.bien import BienCreate, BienUpdate
from .qr_code_service import QRCodeService
import logging

logger = logging.getLogger(__name__)

# Mapping pour les préfixes QR
PREFIX_MAPPING = {
    "vehicule": "VEH",
    "machine": "MAC",
    "ordinateur": "ORD"
}

class BienService:
    def __init__(self, db: Session):
        self.db = db

    def _generate_qr_code(self, type_bien: str) -> str:
        """
        Génère un code QR unique pour un bien
        
        Args:
            type_bien: Type de bien (vehicule, machine, ordinateur)
            
        Returns:
            str: Code QR unique
        """
        prefix = PREFIX_MAPPING.get(type_bien, "BIEN")
        
        # Générer un code unique avec préfixe, timestamp et UUID
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())[:8].upper()
        
        qr_code = f"{prefix}-{timestamp}-{unique_id}"
        
        return qr_code
    
    def generate_and_save_qr_code(self, bien: Bien) -> str:
        """
        Génère le fichier QR code et le sauvegarde
        
        Args:
            bien: Instance du bien
            
        Returns:
            str: Chemin du fichier QR code
        """
        qr_service = QRCodeService()
        
        # Génération du QR code en bytes
        qr_image = qr_service.generate_qr_code(data=bien.qr_code, bien_id=bien.id_bien)
        
        # Sauvegarde du fichier
        file_path = qr_service.generate_qr_file_path(bien.qr_code)
        
        with open(file_path, 'wb') as f:
            f.write(qr_image)
        
        return str(file_path)

    def create_bien(self, bien_data: BienCreate) -> Bien:
        """Crée un nouveau bien avec génération automatique du QR code"""
        qr_code = self._generate_qr_code(bien_data.type_bien)
        
        bien_dict = {
            "qr_code": qr_code,
            "date_acquisition": bien_data.date_acquisition,
            "prix_acquisition": bien_data.prix_acquisition,
            "etat": bien_data.etat,
            "localisation": bien_data.localisation,
            "description": bien_data.description,
            "image": bien_data.image,
            "type_bien": bien_data.type_bien
        }
        
        if bien_data.type_bien == "vehicule":
            bien = Vehicule(**bien_dict)
            bien.type_vehicule = bien_data.type_vehicule
            bien.marque = bien_data.marque
            bien.modele = bien_data.modele
            bien.immatriculation = bien_data.immatriculation
            bien.poids = bien_data.poids
            bien.dimension = bien_data.dimension
            bien.type_carburant = bien_data.type_carburant
            bien.consommation_carburant = bien_data.consommation_carburant
            bien.consommation_huile = bien_data.consommation_huile
            bien.type_propulsion = bien_data.type_propulsion
            
        elif bien_data.type_bien == "machine":
            bien = Machine(**bien_dict)
            bien.numero_serie = bien_data.numero_serie
            bien.fabricant = bien_data.fabricant
            bien.modele = bien_data.modele
            bien.puissance = bien_data.puissance
            bien.type_alimentation = bien_data.type_alimentation
            bien.tension_normal = bien_data.tension_normal
            bien.service_affecte = bien_data.service_affecte
            bien.responsable = bien_data.responsable
            bien.consommation_elec = bien_data.consommation_elec
            bien.frequence_maintenance = bien_data.frequence_maintenance
            
        elif bien_data.type_bien == "ordinateur":
            bien = Ordinateur(**bien_dict)
            bien.marque = bien_data.marque
            bien.modele = bien_data.modele
            bien.processeur = bien_data.processeur
            bien.ram = bien_data.ram
            bien.stockage = bien_data.stockage
            bien.adresse_ip = bien_data.adresse_ip
            bien.utilisateur_affecte = bien_data.utilisateur_affecte
        else:
            bien = Bien(**bien_dict)
        
        self.db.add(bien)
        self.db.commit()
        self.db.refresh(bien)
        return bien

    def get_bien_by_id(self, bien_id: int) -> Optional[Bien]:
        """Récupère un bien par son ID"""
        return self.db.query(Bien).filter(Bien.id_bien == bien_id).first()

    def get_all_biens(self, skip: int = 0, limit: int = 100, 
                      type_bien: Optional[str] = None,
                      etat: Optional[EtatBien] = None) -> List[Bien]:
        """Récupère tous les biens avec filtres"""
        query = self.db.query(Bien)
        
        if type_bien:
            query = query.filter(Bien.type_bien == type_bien)
        if etat:
            query = query.filter(Bien.etat == etat)
        
        return query.offset(skip).limit(limit).all()

    def update_bien(self, bien_id: int, bien_data: BienUpdate) -> Optional[Bien]:
        """Met à jour un bien"""
        bien = self.get_bien_by_id(bien_id)
        if not bien:
            return None
        
        update_data = bien_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(bien, field, value)
        
        self.db.commit()
        self.db.refresh(bien)
        return bien

    def delete_bien(self, bien_id: int) -> bool:
        """Supprime un bien"""
        bien = self.get_bien_by_id(bien_id)
        if not bien:
            return False
        
        self.db.delete(bien)
        self.db.commit()
        return True

    def calculer_age_bien(self, bien_id: int) -> Optional[int]:
        """Calcule l'âge d'un bien en années"""
        bien = self.get_bien_by_id(bien_id)
        if not bien:
            return None
        return bien.calcul_age()

    def changer_etat_bien(self, bien_id: int, nouvel_etat: EtatBien) -> Optional[Bien]:
        """Change l'état d'un bien"""
        bien = self.get_bien_by_id(bien_id)
        if not bien:
            return None
        
        bien.changer_etat(nouvel_etat)
        self.db.commit()
        self.db.refresh(bien)
        return bien

    def get_statistics(self) -> dict:
        """Retourne des statistiques sur les biens"""
        total = self.db.query(func.count(Bien.id_bien)).scalar()
        
        par_type = self.db.query(
            Bien.type_bien, 
            func.count(Bien.id_bien)
        ).group_by(Bien.type_bien).all()
        
        par_etat = self.db.query(
            Bien.etat, 
            func.count(Bien.id_bien)
        ).group_by(Bien.etat).all()
        
        return {
            "total": total,
            "par_type": {t: c for t, c in par_type},
            "par_etat": {e.value: c for e, c in par_etat}
        }