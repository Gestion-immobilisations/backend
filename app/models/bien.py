#from sqlalchemy import Column, Integer, String, Date, DateTime, Enum, Numeric, ForeignKey
from sqlalchemy import Column, Integer, String, Date, DateTime, Enum, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from ..core.database import Base

class EtatBien(enum.Enum):
    NEUF = "NEUF"
    BON = "BON"
    USAGE = "USAGE"
    PANNE = "PANNE"
    REFORME = "REFORME"
    MAINTENANCE = "MAINTENANCE"

class Bien(Base):
    __tablename__ = "biens"
    
    id_bien = Column(Integer, primary_key=True, index=True)
    qr_code = Column(String(100), unique=True, index=True)
    date_acquisition = Column(Date)
    prix_acquisition = Column(Numeric(10, 2))
    etat = Column(Enum(EtatBien), default=EtatBien.NEUF)
    localisation = Column(String(200))
    description = Column(String(500))
    image = Column(String(500))
    date_creation = Column(DateTime, default=datetime.utcnow)
    
    # Relations
   # amortissements = relationship("Amortissement", back_populates="bien")
    #pannes = relationship("Panne", back_populates="bien")
    #maintenances = relationship("Maintenance", back_populates="bien")
    #ecritures_comptables = relationship("EcritureComptable", back_populates="bien")
    
    # Discriminator pour l'héritage
    type_bien = Column(String(50))
    
    __mapper_args__ = {
        "polymorphic_identity": "bien",
        "polymorphic_on": type_bien
    }
    
    def calcul_age(self) -> int:
        """Calcule l'âge du bien en années"""
        from datetime import date
        return date.today().year - self.date_acquisition.year
    
    def changer_etat(self, nouvel_etat: EtatBien):
        """Change l'état du bien"""
        self.etat = nouvel_etat
    
    def est_en_panne(self) -> bool:
        """Vérifie si le bien est en panne"""
        return self.etat == EtatBien.PANNE