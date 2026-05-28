from rest_framework.permissions import BasePermission


"""
Códigos de permisos del sistema para el modelo User.

Este diccionario permite mantener centralizados los nombres internos (codenames) 
de los permisos que se utilizan para asignar y validar accesos, tanto personalizados 
como los generados automáticamente por Django para el modelo User.

Ventajas:
- Evita hardcodeo en vistas, servicios y señales.
- Mejora la legibilidad y mantenimiento del código.
- Facilita cambios si se renombra algún permiso en el futuro.

Uso:
    from user.permissions import PERMISSION_CODENAMES

    codename = PERMISSION_CODENAMES['CAN_BLOCK_USER']
"""

PERMISSION_CODENAMES = {
    # === Permisos personalizados ===
    'CAN_BLOCK_USER': 'can_block_user',               # Bloquear usuarios
    'CAN_UNBLOCK_USER': 'can_unblock_user',           # Desbloquear usuarios
    'CAN_RESTORE_USER': 'can_restore_user',           # Restaurar usuarios eliminados lógicamente
    'CAN_SOFT_DELETE_USER': 'can_soft_delete_user',   # Eliminar lógicamente usuarios
    'CAN_MANAGE_ROLES': 'can_manage_roles',           # Asignar o modificar roles
    'CAN_MANAGE_PERMISSIONS': 'can_manage_permissions', # Asignar o modificar permisos
    'CAN_MANAGE_USERS': 'can_manage_users',           # Acceso general a gestión de usuarios
    'CAN_VIEW_USERS': 'can_view_users',               # Ver usuarios (sin editar)
    'CAN_EDIT_USERS': 'can_edit_users',               # Modificar usuarios (sin crear/borrar)
    'CAN_CREATE_USERS': 'can_create_users',           # Crear nuevos usuarios
    'CAN_DELETE_USERS': 'can_delete_users',           # Eliminar usuarios
    'CAN_VIEW_DASHBOARD': 'can_view_dashboard',       # Acceso al panel administrativo
    'CAN_RESET_PASSWORD': 'can_reset_password',       # Reestablecer contraseñas de otros usuarios
    'CAN_VERIFY_EMAIL': 'can_verify_email',           # Marcar emails como verificados
    'CAN_FORCE_LOGIN': 'can_force_login',             # Iniciar sesión como otro usuario (para soporte)

    # === Permisos nativos del modelo User (generados por Django) ===
    'ADD_USER': 'add_user',                           # Crear usuarios
    'VIEW_USER': 'view_user',                         # Ver usuarios
    'CHANGE_USER': 'change_user',                     # Modificar usuarios
    'DELETE_USER': 'delete_user',                     # Eliminar usuarios (físicamente si no se usa soft delete)
}

class CanManageRoles(BasePermission):
    """
    Permiso personalizado que restringe el acceso a usuarios que tienen explícitamente 
    asignado el permiso 'can_manage_roles' sobre el modelo Group.

    Este permiso es útil para vistas que permiten la creación, modificación o asignación 
    de roles a los usuarios del sistema.

    Requisitos:
        - El usuario debe estar autenticado.
        - El usuario debe tener el permiso 'auth.can_manage_roles', ya sea de forma directa
          o a través de un grupo.

    Uso:
        En la clase de vista, incluirlo dentro de 'permission_classes':
        
        permission_classes = [IsAuthenticated, CanManageRoles]

    Nota:
        El nombre del permiso incluye el nombre de la app y el codename, en este caso:
        'auth.can_manage_roles'
    """

    def has_permission(self, request, view):
        return request.user.has_perm("auth.can_manage_roles")

class CanManagePermissions(BasePermission):
    """
    Permiso personalizado que restringe el acceso a usuarios que tienen explícitamente 
    asignado el permiso 'can_manage_permissions' sobre el modelo Permission.

    Este permiso es útil para vistas que permiten la creación, asignación o gestión 
    de permisos en el sistema.

    Requisitos:
        - El usuario debe estar autenticado.
        - El usuario debe tener el permiso 'auth.can_manage_permissions', ya sea de forma directa
          o a través de un grupo.

    Uso:
        En la clase de vista, incluirlo dentro de 'permission_classes':
        
        permission_classes = [IsAuthenticated, CanManagePermissions]

    Nota:
        El nombre del permiso incluye el nombre de la app y el codename, en este caso:
        'auth.can_manage_permissions'
    """

    def has_permission(self, request, view):
        return request.user.has_perm("auth.can_manage_permissions")

