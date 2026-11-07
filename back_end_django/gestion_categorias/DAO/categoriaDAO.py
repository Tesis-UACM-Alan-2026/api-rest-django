from django.db import IntegrityError
from django.db.models.deletion import ProtectedError

from gestion_categorias.models import Categoria
from gestion_categorias.exceptions.categoriaExceptions import (
    CategoriaNoEncontrada_404,
    CategoriaDuplicada_409,
    CategoriaConProductos_409,
)


class CategoriaDAO:

    CAMPOS_EDITABLES = ("nombre", "descripcion")

    @staticmethod
    def obtener_todas():
        """Obtiene todas las categorías registradas."""
        return Categoria.objects.all().order_by("id")

    @staticmethod
    def obtener_por_id(categoria_id):
        """Obtiene una categoría mediante su identificador."""
        try:
            return Categoria.objects.get(id=categoria_id)
        except (Categoria.DoesNotExist, ValueError, TypeError):
            raise CategoriaNoEncontrada_404()

    @staticmethod
    def existe_nombre(nombre, excluir_id=None):
        """Indica si ya existe una categoría con ese nombre (sin distinguir mayúsculas)."""
        consulta = Categoria.objects.filter(nombre__iexact=nombre)

        if excluir_id is not None:
            consulta = consulta.exclude(id=excluir_id)

        return consulta.exists()

    @staticmethod
    def crear_categoria(nombre, descripcion=None):
        """Registra una nueva categoría."""
        if CategoriaDAO.existe_nombre(nombre):
            raise CategoriaDuplicada_409()

        try:
            return Categoria.objects.create(
                nombre=nombre,
                descripcion=descripcion
            )
        except IntegrityError:
            # Respaldo ante condiciones de carrera (restricción unique de la BD)
            raise CategoriaDuplicada_409()

    @staticmethod
    def actualizar_categoria(categoria_id, **datos):
        """Actualiza los datos de una categoría."""
        categoria = CategoriaDAO.obtener_por_id(categoria_id)

        if "nombre" in datos and CategoriaDAO.existe_nombre(
                datos["nombre"], excluir_id=categoria.id
        ):
            raise CategoriaDuplicada_409()

        for campo, valor in datos.items():
            if campo in CategoriaDAO.CAMPOS_EDITABLES:
                setattr(categoria, campo, valor)

        try:
            categoria.save()
        except IntegrityError:
            raise CategoriaDuplicada_409()

        return categoria

    @staticmethod
    def actualizar_categoria_parcial(categoria_id, **datos):
        """Actualiza parcialmente una categoría."""
        return CategoriaDAO.actualizar_categoria(categoria_id, **datos)

    @staticmethod
    def eliminar_categoria(categoria_id):
        """Elimina una categoría si no tiene productos asociados (FK PROTECT)."""
        categoria = CategoriaDAO.obtener_por_id(categoria_id)

        try:
            categoria.delete()
        except ProtectedError:
            raise CategoriaConProductos_409()

        return True