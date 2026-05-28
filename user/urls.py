"""
Configuración de rutas URL para la aplicación de usuarios (`user`).

Este módulo define y agrupa las URLs que permiten el acceso a los servicios REST relacionados
con la gestión de usuarios. La organización se basa en el uso de vistas individuales para funcionalidades
específicas, como creación, listado y bloqueo de usuarios.

Rutas principales disponibles:
- POST /api/users/create/                : Crear un nuevo usuario.
- GET  /api/users/                       : Listar todos los usuarios registrados.
- PATCH /api/users/<uuid:user_id>       : Actualiza parcialmente un usuario.
- POST /api/users/<uuid:user_id>/block  : Bloquear un usuario específico.
- POST /users/{user_id}/restore       : Desbloquear un usuario específico.

Notas:
- Las vistas individuales (`create`, `list`, `block`, `update`) se declaran explícitamente.
"""

from django.urls import path, include


from .views import (
    UserCreateView,
    UserListView,
    BlockUserView,
    UnBlockUserView,
    RolesListView,
    UserDataView,
    MeDataView,
    RestoreUserView,
)


from .views.permissions import CreatePermissionView, AssignPermissionToGroupView
from user.views.role_assign import AssignRoleToUserView
from .views.list_permission import PermissionListView
from user.views.roles import CreateRoleView
from user.views.change_user_password import ChangeUserPasswordView

# --- Rutas adicionales personalizadas (basadas en vistas individuales) ---
custom_urls = [
   
 
    
    path('<uuid:user_id>/assign-role', AssignRoleToUserView.as_view(), name='assign-role-to-user'),
    path("create/", UserCreateView.as_view(), name="user-create"),
    path("", UserListView.as_view(), name="user-list"),
    path("<uuid:user_id>/block", BlockUserView.as_view(), name="user-block"),
    path("<uuid:user_id>", UserDataView.as_view(), name="user-data"),
    path("<uuid:user_id>/unblock", UnBlockUserView.as_view(), name="user-unblock"),
    path(
        "permissions/create/", CreatePermissionView.as_view(), name="permission-create"
    ),
    path(
        "permissions/assign/",
        AssignPermissionToGroupView.as_view(),
        name="permission-assign-to-group",
    ),
    path("permissions", PermissionListView.as_view(), name="permission-list"),
    path("roles/", RolesListView.as_view(), name="get-roles"),
    path("roles/create/", CreateRoleView.as_view(), name="create-role"),
    path("me", MeDataView.as_view(), name="user-me"),
    path('me', MeDataView.as_view(), name='update-me-partial'),
    path(
        "me/change-password", ChangeUserPasswordView.as_view(), name="change-password"
    ),
    path("<uuid:user_id>/restore", RestoreUserView.as_view(), name="user-restore"),
]


# --- Unión de todas las rutas disponibles ---
urlpatterns = [
    # Agrega las vistas individuales al mismo nivel que /api/users/
    *custom_urls
]
