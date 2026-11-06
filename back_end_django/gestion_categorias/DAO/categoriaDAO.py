from django.db.models.deletion import ProtectedError
from rest_framework.exceptions import NotFound

from gestion_categorias.models import Categoria


class CategoriaDAO:

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
            raise NotFound("Categoría no encontrada.")

    @staticmethod
    def crear_categoria(nombre, descripcion=None):
        """Registra una nueva categoría."""
        return Categoria.objects.create(
            nombre=nombre,
            descripcion=descripcion
        )

    @staticmethod
    def actualizar_categoria(categoria_id, **datos):
        """Actualiza los datos de una categoría."""
        categoria = CategoriaDAO.obtener_por_id(categoria_id)

        for campo, valor in datos.items():
            setattr(categoria, campo, valor)

        categoria.save()
        return categoria

    @staticmethod
    def actualizar_categoria_parcial(categoria_id, **datos):
        """Actualiza parcialmente una categoría."""
        return CategoriaDAO.actualizar_categoria(
            categoria_id,
            **datos
        )

    @staticmethod
    def eliminar_categoria(categoria_id):
        """Elimina una categoría si no tiene productos asociados."""
        categoria = CategoriaDAO.obtener_por_id(categoria_id)
        categoria.delete()
        return True