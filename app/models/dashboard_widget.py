# backend/app/models/dashboard_widget.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from ..core.database import Base

class DashboardWidget(Base):
    __tablename__ = "dashboard_widgets"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nom_widget = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)
    position = Column(Integer, default=0)
    visibilite = Column(Boolean, default=True)
    id_role = Column(Integer, ForeignKey('roles.id_role', ondelete='CASCADE'), nullable=False)
    can_view = Column(Boolean, default=True)
    can_edit = Column(Boolean, default=False)
    
    # ✅ Relation corrigée - Utiliser une chaîne
    role = relationship("Role", back_populates="dashboard_widgets")