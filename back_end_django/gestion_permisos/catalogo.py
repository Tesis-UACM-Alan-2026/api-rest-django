"""
Catálogo de permisos del sistema (convención: <recurso>.<accion>).
Lo usa el comando `sembrar_permisos` y debe coincidir con los
`permisos_requeridos` declarados en las vistas.
"""

PERMISOS = [
    # (codename, nombre, descripcion)
    ("productos.ver", "Ver productos", "Listar, consultar y buscar productos."),
    ("productos.crear", "Crear productos", "Registrar productos nuevos."),
    ("productos.editar", "Editar productos", "Modificar productos existentes."),
    ("productos.eliminar", "Eliminar productos", "Eliminar productos."),

    ("categorias.ver", "Ver categorías", "Listar y consultar categorías."),
    ("categorias.crear", "Crear categorías", "Registrar categorías nuevas."),
    ("categorias.editar", "Editar categorías", "Modificar categorías existentes."),
    ("categorias.eliminar", "Eliminar categorías", "Eliminar categorías."),

    ("usuarios.ver", "Ver usuarios", "Listar y consultar usuarios."),
    ("usuarios.crear", "Crear usuarios", "Registrar usuarios nuevos."),
    ("usuarios.editar", "Editar usuarios", "Modificar datos de usuarios."),
    ("usuarios.eliminar", "Eliminar usuarios", "Eliminar (borrado lógico) usuarios."),
    ("usuarios.cambiar_estado", "Cambiar estado de usuarios", "Activar, desactivar y restaurar usuarios."),
    ("usuarios.verificar_email", "Verificar email de usuarios", "Marcar el email de un usuario como verificado."),
    ("usuarios.asignar_roles", "Asignar roles a usuarios", "Asignar y quitar roles de un usuario."),

    ("permisos.ver", "Ver permisos", "Listar y consultar permisos."),
    ("permisos.crear", "Crear permisos", "Registrar permisos nuevos."),
    ("permisos.editar", "Editar permisos", "Modificar permisos existentes."),
    ("permisos.eliminar", "Eliminar permisos", "Eliminar permisos."),

    ("roles.ver", "Ver roles", "Listar y consultar roles."),
    ("roles.crear", "Crear roles", "Registrar roles nuevos."),
    ("roles.editar", "Editar roles", "Modificar roles existentes."),
    ("roles.eliminar", "Eliminar roles", "Eliminar roles."),
    ("roles.asignar_permisos", "Asignar permisos a roles", "Asignar y quitar permisos de un rol."),
]

# Roles base: nombre -> (descripcion, [codenames])
ROLES_BASE = {
    "Administrador": (
        "Acceso total al sistema.",
        [codename for codename, _, _ in PERMISOS],
    ),
    "Consulta": (
        "Acceso de solo lectura.",
        [codename for codename, _, _ in PERMISOS if codename.endswith(".ver")],
    ),
}