from django.db import IntegrityError
from django.db.models import Q
from rest_framework.exceptions import ValidationError

from gestion_productos.models import Productos
from gestion_productos.exceptions.productoExceptions import ProductoNoEncontrado_404


class ProductoDAO:

    @staticmethod
    def obtener_todos():
        """Obtiene todos los productos junto con su categoría."""
        return (
            Productos.objects
            .select_related("categoria")
            .all()
            .order_by("id")
        )

    @staticmethod
    def obtener_producto_por_id(producto_id):
        """Obtiene un producto por su identificador."""
        try:
            return (
                Productos.objects
                .select_related("categoria")
                .get(id=producto_id)
            )
        except (Productos.DoesNotExist, ValueError, TypeError):
            raise ProductoNoEncontrado_404()

    @staticmethod
    def crear_producto(nombre, precio, stock=0, categoria=None):
        """Registra un producto nuevo."""
        try:
            return Productos.objects.create(
                nombre=nombre,
                precio=precio,
                stock=stock,
                categoria=categoria
            )
        except IntegrityError:
            raise ValidationError({
                "error": "No fue posible crear el producto."
            })

    @staticmethod
    def actualizar_producto(producto_id, **datos):
        """Actualiza todos los campos recibidos y validados."""
        producto = ProductoDAO.obtener_producto_por_id(producto_id)

        for campo, valor in datos.items():
            setattr(producto, campo, valor)

        producto.save()
        return producto

    @staticmethod
    def actualizar_producto_parcial(producto_id, **datos):
        """Actualiza únicamente los campos proporcionados."""
        return ProductoDAO.actualizar_producto(producto_id, **datos)

    @staticmethod
    def eliminar_producto(producto_id):
        """Elimina físicamente un producto."""
        producto = ProductoDAO.obtener_producto_por_id(producto_id)
        producto.delete()
        return True

    @staticmethod
    def buscar_productos(query):
        """Busca productos por coincidencia en el nombre."""
        return (
            Productos.objects
            .select_related("categoria")
            .filter(Q(nombre__icontains=query))
            .order_by("id")
        )

    @staticmethod
    def filtrar_por_rango_precio(precio_min, precio_max):
        """Filtra productos dentro de un rango de precios."""
        return (
            Productos.objects
            .select_related("categoria")
            .filter(
                precio__gte=precio_min,
                precio__lte=precio_max
            )
            .order_by("precio", "id")
        )