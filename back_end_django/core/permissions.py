# core/permissions.py
from rest_framework import permissions

class TienePermiso(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        codename = getattr(view, "permisos_requeridos", {}).get(view.action)
        if codename is None:
            return True  # la acción no exige un permiso específico

        return request.user.usuario.rol.permisos.filter(
            codename=codename
        ).exists()