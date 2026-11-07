from django.db import IntegrityError

from gestion_permisos.models import Permiso
from gestion_permisos.exceptions.permisoExceptions import (
    PermisoNoEncontrado_404,
    PermisoDuplicado_409,
    PermisoEnUso_409,
)


class PermisoDAO:

    CAMPOS_EDITABLES = ("codename", "nombre", "descripcion")

    @staticmethod
    def obtener_todos():
        """Obtiene todos los permisos registrados."""
        return Permiso.objects.all().order_by("id")

    @staticmethod
    def obtener_por_id(permiso_id):
        """Obtiene un permiso mediante su identificador."""
        try:
            return Permiso.objects.get(id=permiso_id)
        except (Permiso.DoesNotExist, ValueError, TypeError):
            raise PermisoNoEncontrado_404()

    @staticmethod
    def existe_codename(codename, excluir_id=None):
        """Indica si ya existe un permiso con ese codename."""
        consulta = Permiso.objects.filter(codename__iexact=codename)

        if excluir_id is not None:
            consulta = consulta.exclude(id=excluir_id)

        return consulta.exists()

    @staticmethod
    def crear_permiso(codename, nombre, descripcion=None):
        """Registra un nuevo permiso."""
        if PermisoDAO.existe_codename(codename):
            raise PermisoDuplicado_409()

        try:
            return Permiso.objects.create(
                codename=codename,
                nombre=nombre,
                descripcion=descripcion
            )
        except IntegrityError:
            raise PermisoDuplicado_409()

    @staticmethod
    def actualizar_permiso(permiso_id, **datos):
        """Actualiza los datos de un permiso."""
        permiso = PermisoDAO.obtener_por_id(permiso_id)

        if "codename" in datos and PermisoDAO.existe_codename(
                datos["codename"], excluir_id=permiso.id
        ):
            raise PermisoDuplicado_409()

        for campo, valor in datos.items():
            if campo in PermisoDAO.CAMPOS_EDITABLES:
                setattr(permiso, campo, valor)

        try:
            permiso.save()
        except IntegrityError:
            raise PermisoDuplicado_409()

        return permiso

    @staticmethod
    def actualizar_permiso_parcial(permiso_id, **datos):
        """Actualiza parcialmente un permiso."""
        return PermisoDAO.actualizar_permiso(permiso_id, **datos)

    @staticmethod
    def eliminar_permiso(permiso_id):
        """Elimina un permiso siempre que no esté asignado a algún rol."""
        permiso = PermisoDAO.obtener_por_id(permiso_id)

        if permiso.roles.exists():
            raise PermisoEnUso_409()

        permiso.delete()
        return True

    @staticmethod
    def obtener_codenames_por_usuario(usuario_id):
        """Codenames de todos los permisos que el usuario recibe por sus roles."""
        return set(
            Permiso.objects
            .filter(roles__usuarios__id=usuario_id)
            .values_list("codename", flat=True)
        )