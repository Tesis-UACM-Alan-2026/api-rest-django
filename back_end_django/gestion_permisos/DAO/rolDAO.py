from django.db import IntegrityError, transaction

from gestion_permisos.models import Rol, Permiso
from gestion_permisos.exceptions.permisoExceptions import (
    DatosInvalidosPermisos_400,
    RolNoEncontrado_404,
    RolDuplicado_409,
    RolEnUso_409,
)


class RolDAO:

    CAMPOS_EDITABLES = ("nombre", "descripcion")

    @staticmethod
    def obtener_todos():
        """Obtiene todos los roles con sus permisos."""
        return Rol.objects.prefetch_related("permisos").order_by("id")

    @staticmethod
    def obtener_por_id(rol_id):
        """Obtiene un rol mediante su identificador."""
        try:
            return Rol.objects.prefetch_related("permisos").get(id=rol_id)
        except (Rol.DoesNotExist, ValueError, TypeError):
            raise RolNoEncontrado_404()

    @staticmethod
    def existe_nombre(nombre, excluir_id=None):
        """Indica si ya existe un rol con ese nombre."""
        consulta = Rol.objects.filter(nombre__iexact=nombre)

        if excluir_id is not None:
            consulta = consulta.exclude(id=excluir_id)

        return consulta.exists()

    @staticmethod
    def crear_rol(nombre, descripcion=None):
        """Registra un nuevo rol."""
        if RolDAO.existe_nombre(nombre):
            raise RolDuplicado_409()

        try:
            return Rol.objects.create(
                nombre=nombre,
                descripcion=descripcion
            )
        except IntegrityError:
            raise RolDuplicado_409()

    @staticmethod
    def actualizar_rol(rol_id, **datos):
        """Actualiza los datos de un rol."""
        rol = RolDAO.obtener_por_id(rol_id)

        if "nombre" in datos and RolDAO.existe_nombre(
                datos["nombre"], excluir_id=rol.id
        ):
            raise RolDuplicado_409()

        for campo, valor in datos.items():
            if campo in RolDAO.CAMPOS_EDITABLES:
                setattr(rol, campo, valor)

        try:
            rol.save()
        except IntegrityError:
            raise RolDuplicado_409()

        return rol

    @staticmethod
    def actualizar_rol_parcial(rol_id, **datos):
        """Actualiza parcialmente un rol."""
        return RolDAO.actualizar_rol(rol_id, **datos)

    @staticmethod
    def eliminar_rol(rol_id):
        """Elimina un rol siempre que no esté asignado a algún usuario."""
        rol = RolDAO.obtener_por_id(rol_id)

        if rol.usuarios.exists():
            raise RolEnUso_409()

        rol.delete()
        return True

    @staticmethod
    @transaction.atomic
    def asignar_permisos(rol_id, permisos_ids):
        """Agrega permisos a un rol (los ya asignados se ignoran)."""
        rol = RolDAO.obtener_por_id(rol_id)
        ids = set(permisos_ids)

        permisos = list(Permiso.objects.filter(id__in=ids))
        inexistentes = ids - {p.id for p in permisos}

        if inexistentes:
            raise DatosInvalidosPermisos_400(
                f"Los siguientes permisos no existen: {sorted(inexistentes)}"
            )

        rol.permisos.add(*permisos)
        return RolDAO.obtener_por_id(rol_id)

    @staticmethod
    @transaction.atomic
    def quitar_permisos(rol_id, permisos_ids):
        """Quita permisos de un rol (los no asignados se ignoran)."""
        rol = RolDAO.obtener_por_id(rol_id)

        rol.permisos.remove(*set(permisos_ids))
        return RolDAO.obtener_por_id(rol_id)