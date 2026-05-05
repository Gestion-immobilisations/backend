
# 1. D'abord permission (définit role_permissions)
from .permission import Permission, role_permissions

# 2. Puis Role (utilise role_permissions)
from .role import Role

# 3. Puis Utilisateur (utilise Role)
from .utilisateur import Utilisateur

# 4. Puis JournalAudit (utilise Utilisateur)
from .journal_audit import JournalAudit
from .bien import Bien, EtatBien
from .vehicule import Vehicule
from .machine import Machine
from .ordinateur import Ordinateur
from app.models.dashboard_widget import DashboardWidget

__all__ = [
    "Permission",
    "role_permissions",
    "Role",
    "Utilisateur", 
    "JournalAudit",
    "Bien",
    "EtatBien",
    "Vehicule",
    "Machine",
    "Ordinateur",
    "DashboardWidget"
]