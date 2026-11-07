class PermisosError(Exception):
    """Base de las excepciones del módulo de permisos y roles."""
    mensaje_por_defecto = "Error en la gestión de permisos."

    def __init__(self, mensaje=None):
        super().__init__(mensaje or self.mensaje_por_defecto)


class DatosInvalidosPermisos_400(PermisosError):
    mensaje_por_defecto = "Los datos proporcionados no son válidos."


# ---------- Permiso ----------
class PermisoNoEncontrado_404(PermisosError):
    mensaje_por_defecto = "Permiso no encontrado."


class PermisoDuplicado_409(PermisosError):
    mensaje_por_defecto = "Ya existe un permiso con ese codename."


class PermisoEnUso_409(PermisosError):
    mensaje_por_defecto = (
        "No se puede eliminar el permiso porque está asignado a uno o más roles."
    )


# ---------- Rol ----------
class RolNoEncontrado_404(PermisosError):
    mensaje_por_defecto = "Rol no encontrado."


class RolDuplicado_409(PermisosError):
    mensaje_por_defecto = "Ya existe un rol con ese nombre."


class RolEnUso_409(PermisosError):
    mensaje_por_defecto = (
        "No se puede eliminar el rol porque está asignado a uno o más usuarios."
    )