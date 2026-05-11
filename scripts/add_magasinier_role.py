# -*- coding: utf-8 -*-
"""
Script dédié pour ajouter le rôle MAGASINIER dans la base de données.
Ne modifie pas les rôles existants.
"""
import sys
import os
from pathlib import Path

# Ajouter le dossier backend au PATH pour les imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.core.database import SessionLocal
from app.models.role import Role
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def add_magasinier_role():
    """
    Ajoute le rôle MAGASINIER s'il n'existe pas déjà.
    """
    db = SessionLocal()
    
    try:
        # Vérifier si le rôle MAGASINIER existe déjà
        existing_role = db.query(Role).filter(Role.nom == "MAGASINIER").first()
        
        if existing_role:
            logger.info(f"✅ Le rôle 'MAGASINIER' existe déjà (ID: {existing_role.id_role})")
            return True
        
        # Calculer le prochain ID disponible
        next_id = Role.get_next_id(db)
        logger.info(f"🔢 Prochain ID disponible : {next_id}")
        
        # Créer le nouveau rôle
        new_role = Role(
            id_role=next_id,
            nom="MAGASINIER",
            description="Magasinier - Gestion des stocks et des pièces de rechange",
            actif=True
        )
        
        db.add(new_role)
        db.commit()
        db.refresh(new_role)
        
        logger.info(f"✅ Rôle 'MAGASINIER' créé avec succès !")
        logger.info(f"   ID: {new_role.id_role}")
        logger.info(f"   Nom: {new_role.nom}")
        logger.info(f"   Description: {new_role.description}")
        logger.info(f"   Actif: {new_role.actif}")
        
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur lors de la création du rôle MAGASINIER: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    try:
        success = add_magasinier_role()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.warning("⚠️  Processus interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Erreur fatale : {e}")
        sys.exit(1)