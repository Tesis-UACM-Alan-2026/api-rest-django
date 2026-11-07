from rest_framework.permissions import BasePermission

from gestion_permisos.service import PermisoService

permisoService = PermisoService()


def obtener_codenames(request):
    """
    Devuelve el conjunto de codenames del usuario autenticado.
    Se consulta una sola vez por petición y se guarda en el request.
    """
    codenames = getattr(request, "_codenames_permisos", None)

    if codenames is None:
        codenames = permisoService.obtener_codenames_usuario(request.user.id)
        request._codenames_permisos = codenames

    return codenames


class HasPermission(BasePermission):
    """
    Autoriza según los permisos que el usuario recibe a través de sus roles.

    Cada ViewSet declara qué permiso exige cada acción:

        permisos_requeridos = {
            "list": "productos.ver",
            "create": "productos.crear",
        }

    Reglas:
      - Usuario no autenticado o inactivo  -> denegado.
      - Superusuario                       -> permitido siempre.
      - Acción NO declarada en el diccionario -> denegado (seguro por defecto).
      - Resto: debe tener el codename requerido en alguno de sus roles.
    """

    message = "No tiene permiso para realizar esta acción."

    def has_permission(self, request, view):
        usuario = request.user

        if not usuario or not usuario.is_authenticated or not usuario.is_active:
            return False

        if usuario.is_superuser:
            return True

        requeridos = getattr(view, "permisos_requeridos", {})
        codename = requeridos.get(getattr(view, "action", None))

        if codename is None:
            return False

        return codename in obtener_codenames(request)