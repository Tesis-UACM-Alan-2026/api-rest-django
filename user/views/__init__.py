"""
Inicializa las vistas del módulo de usuarios.

Este archivo permite importar todas las vistas desde la carpeta views
para mantener una interfaz limpia en las rutas o el enrutador principal.
"""

from .create_user import UserCreateView
from .list_users import UserListView
from .block_user import BlockUserView
from .list_permission import PermissionListView
from .change_user_password import ChangeUserPasswordView
from .unblock_user import UnBlockUserView
from .user_data import UserDataView
from .get_roles import RolesListView
from .me_data import MeDataView
from .restore_users import RestoreUserView

__all__ = [
    "UserCreateView",
    "UserListView",
    "BlockUserView",
    "PermissionListView",
    "ChangeUserPasswordView",
    "UnBlockUserView",
    "RolesListView",
    "UserDataView",
    "MeDataView",
    "RestoreUserView",
]
