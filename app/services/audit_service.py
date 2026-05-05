# -*- coding: utf-8 -*-
"""
Service d'audit : journalisation des actions utilisateurs pour traçabilité
"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Dict, Any, Union
import logging

logger = logging.getLogger(__name__)


class AuditService:
    """
    Service centralisé pour la journalisation des actions dans le système.
    Toutes les opérations CRUD, connexions, validations sont tracées ici.
    """
    
    @staticmethod
    def log_action(
        db: Session,
        user_id: Optional[int],
        table_name: str,
        record_id: Optional[int],
        action: str,
        anciennes_valeurs: Optional[Dict[str, Any]] = None,
        nouvelles_valeurs: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """
        Journalise une action dans la table journal_audit.
        
        Args:
            db: Session SQLAlchemy
            user_id: ID de l'utilisateur qui a effectué l'action (None si anonyme)
            table_name: Nom de la table concernée (ex: "utilisateurs", "biens")
            record_id: ID de l'enregistrement concerné dans la table
            action: Type d'action (CREATE, READ, UPDATE, DELETE, LOGIN, LOGOUT, etc.)
            anciennes_valeurs: Dict des valeurs avant modification (pour UPDATE/DELETE)
            nouvelles_valeurs: Dict des valeurs après modification (pour CREATE/UPDATE)
            ip_address: Adresse IP de la requête (optionnel)
            user_agent: User-Agent du navigateur/client (optionnel)
            
        Returns:
            bool: True si journalisation réussie, False sinon
        """
        try:
            # Import dynamique pour éviter les circular imports
            from app.models.journal_audit import JournalAudit
            
            audit_entry = JournalAudit(
                id_utilisateur=user_id,
                table_concernee=table_name,
                id_enregistrement=record_id,
                action=action,
                anciennes_valeurs=anciennes_valeurs,
                nouvelles_valeurs=nouvelles_valeurs,
                date_action=datetime.utcnow(),
                adresse_ip=ip_address,
                user_agent=user_agent
            )
            
            db.add(audit_entry)
            db.commit()
            
            logger.info(f"Audit : {action} sur {table_name}#{record_id} par user#{user_id}")
            return True
            
        except ImportError:
            # Table journal_audit non créée encore → logger en console uniquement
            logger.warning(
                f"Audit (non persisté) : {action} sur {table_name}#{record_id} "
                f"par user#{user_id} - Table journal_audit non disponible"
            )
            return False
            
        except Exception as e:
            db.rollback()
            logger.error(f"Erreur lors de la journalisation audit : {e}")
            return False
    
    @staticmethod
    def get_user_actions(
        db: Session,
        user_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> list:
        """
        Récupère l'historique des actions d'un utilisateur.
        
        Args:
            db: Session SQLAlchemy
            user_id: ID de l'utilisateur
            limit: Nombre maximum de résultats
            offset: Décalage pour la pagination
            
        Returns:
            list: Liste des entrées d'audit
        """
        try:
            from app.models.journal_audit import JournalAudit
            
            return db.query(JournalAudit)\
                .filter(JournalAudit.id_utilisateur == user_id)\
                .order_by(JournalAudit.date_action.desc())\
                .offset(offset)\
                .limit(limit)\
                .all()
                
        except ImportError:
            logger.warning("Table journal_audit non disponible pour la requête")
            return []
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des actions : {e}")
            return []
    
    @staticmethod
    def get_table_history(
        db: Session,
        table_name: str,
        record_id: int,
        limit: int = 50
    ) -> list:
        """
        Récupère l'historique complet des modifications d'un enregistrement.
        
        Args:
            db: Session SQLAlchemy
            table_name: Nom de la table (ex: "biens", "utilisateurs")
            record_id: ID de l'enregistrement
            limit: Nombre maximum de résultats
            
        Returns:
            list: Historique des modifications
        """
        try:
            from app.models.journal_audit import JournalAudit
            
            return db.query(JournalAudit)\
                .filter(
                    JournalAudit.table_concernee == table_name,
                    JournalAudit.id_enregistrement == record_id
                )\
                .order_by(JournalAudit.date_action.desc())\
                .limit(limit)\
                .all()
                
        except ImportError:
            return []
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'historique : {e}")
            return []