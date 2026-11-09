# core/testing.py

"""
Utilidades compartidas por los tests (no se llama tests*.py a propósito,
para que pytest no intente recolectarlo como un archivo de pruebas).
"""
from django.contrib.auth import get_user_model

from gestion_permisos.models import Permiso, Rol

User = get_user_model()

PASSWORD = "Pass12345"


def crear_usuario(email="usuario@test.com", password=PASSWORD, **extra):
    """Usuario normal, sin roles ni permisos."""
    datos = {"first_name": "Test", "last_name": "Usuario"}
    datos.update(extra)
    return User.objects.create_user(email=email, password=password, **datos)


def crear_superusuario(email="admin@test.com", password=PASSWORD):
    return User.objects.create_superuser(
        email=email,
        password=password,
        first_name="Administrador",
        last_name="Pruebas",
    )


def crear_rol_con_permisos(nombre, codenames):
    """Crea un rol y le asigna los permisos indicados (los crea si no existen)."""
    rol = Rol.objects.create(nombre=nombre)

    for codename in codenames:
        permiso, _ = Permiso.objects.get_or_create(
            codename=codename, defaults={"nombre": codename}
        )
        rol.permisos.add(permiso)

    return rol


def crear_usuario_con_permisos(codenames, email="rbac@test.com", password=PASSWORD):
    """Usuario normal cuyo único acceso viene de un rol con esos permisos."""
    usuario = crear_usuario(email=email, password=password)

    if codenames:
        rol = crear_rol_con_permisos(f"rol de {email}", codenames)
        usuario.roles.add(rol)

    return usuario