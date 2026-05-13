# -*- coding: utf-8 -*-
"""
Script dédié pour ajouter l'utilisateur MAGASINIER dans la base de données.
Ne modifie pas les utilisateurs existants.
"""
import sys
import os
from pathlib import Path

# Ajouter le dossier backend au PATH pour les imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.core.database import SessionLocal
from app.models.utilisateur import Utilisateur
from app.models.role import Role
from app.core.security import get_password_hash
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def add_magasinier_user():
    """
    Ajoute l'utilisateur MAGASINIER s'il n'existe pas déjà.
    """
    db = SessionLocal()
    
    # Informations du magasinier
    email = "magasinier@it.com"
    nom = "Gestionnaire"
    prenom = "Robert"
    post_nom = "Stock"
    telephone = "+243 800 000 006"
    mot_de_passe = "magasin123"
    role_nom = "MAGASINIER"
    
    try:
        # 1. Vérifier si l'utilisateur existe déjà
        existing_user = db.query(Utilisateur).filter(Utilisateur.email == email).first()
        if existing_user:
            logger.info(f"✅ L'utilisateur magasinier existe déjà (ID: {existing_user.id}, Email: {existing_user.email})")
            return True
        
        # 2. Vérifier que le rôle MAGASINIER existe
        role = db.query(Role).filter(Role.nom == role_nom).first()
        if not role:
            logger.error(f"❌ Le rôle '{role_nom}' n'existe pas dans la base de données")
            logger.info("💡 Exécutez d'abord: python scripts/add_magasinier_role.py")
            return False
        
        # 3. Calculer le prochain ID disponible
        next_id = Utilisateur.get_next_id(db)
        logger.info(f"🔢 Prochain ID disponible : {next_id}")
        
        # 4. Hasher le mot de passe
        hashed_password = get_password_hash(mot_de_passe)
        
        # 5. Créer l'utilisateur
        new_user = Utilisateur(
            id=next_id,
            email=email,
            nom=nom,
            post_nom=post_nom,
            prenom=prenom,
            telephone=telephone,
            mot_de_passe=hashed_password,
            role_id=role.id_role,
            est_actif=True
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"✅ Utilisateur magasinier créé avec succès !")
        logger.info(f"   ID: {new_user.id}")
        logger.info(f"   Email: {new_user.email}")
        logger.info(f"   Nom complet: {new_user.nom} {new_user.post_nom} {new_user.prenom}")
        logger.info(f"   Rôle: {role_nom}")
        logger.info(f"   Téléphone: {new_user.telephone}")
        logger.info(f"   Mot de passe: {mot_de_passe} (à changer à la première connexion)")
        
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur lors de la création de l'utilisateur magasinier: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    try:
        success = add_magasinier_user()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.warning("⚠️  Processus interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Erreur fatale : {e}")
        sys.exit(1)