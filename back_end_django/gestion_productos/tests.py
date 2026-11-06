from decimal import Decimal

from django.test import TestCase

from gestion_productos.DAO.productoDAO import ProductoDAO
from gestion_productos.exceptions.productoExceptions import (
    ProductoNoEncontrado_404
)


class ProductoDAOTestCase(TestCase):
    """Pruebas unitarias para las operaciones del ProductoDAO."""

    def setUp(self):
        """Prepara los productos necesarios para las pruebas."""
        self.producto = ProductoDAO.crear_producto(
            nombre="Laptop Lenovo",
            precio=Decimal("12500.00"),
            stock=10,
            categoria=None
        )

        self.segundo_producto = ProductoDAO.crear_producto(
            nombre="Mouse Logitech",
            precio=Decimal("450.00"),
            stock=20,
            categoria=None
        )

    def test_obtener_todos(self):
        productos = ProductoDAO.obtener_todos()

        self.assertEqual(productos.count(), 2)

    def test_obtener_producto_por_id(self):
        producto = ProductoDAO.obtener_producto_por_id(
            self.producto.id
        )

        self.assertEqual(producto.nombre, "Laptop Lenovo")

    def test_producto_no_encontrado(self):
        with self.assertRaises(ProductoNoEncontrado_404):
            ProductoDAO.obtener_producto_por_id(999999)

    def test_crear_producto(self):
        producto = ProductoDAO.crear_producto(
            nombre="Teclado mecánico",
            precio=Decimal("850.00"),
            stock=5
        )

        self.assertIsNotNone(producto.id)
        self.assertEqual(producto.nombre, "Teclado mecánico")
        self.assertEqual(producto.stock, 5)

    def test_actualizar_producto(self):
        producto = ProductoDAO.actualizar_producto(
            self.producto.id,
            nombre="Laptop Lenovo ThinkPad",
            precio=Decimal("13500.00"),
            stock=8
        )

        self.assertEqual(producto.nombre, "Laptop Lenovo ThinkPad")
        self.assertEqual(producto.precio, Decimal("13500.00"))
        self.assertEqual(producto.stock, 8)

    def test_actualizar_producto_parcial(self):
        producto = ProductoDAO.actualizar_producto_parcial(
            self.producto.id,
            stock=15
        )

        self.assertEqual(producto.stock, 15)
        self.assertEqual(producto.nombre, "Laptop Lenovo")
        self.assertEqual(producto.precio, Decimal("12500.00"))

    def test_buscar_productos(self):
        productos = ProductoDAO.buscar_productos("Lenovo")

        self.assertEqual(productos.count(), 1)
        self.assertEqual(productos.first().nombre, "Laptop Lenovo")

    def test_filtrar_por_rango_precio(self):
        productos = ProductoDAO.filtrar_por_rango_precio(
            Decimal("400.00"),
            Decimal("500.00")
        )

        self.assertEqual(productos.count(), 1)
        self.assertEqual(productos.first().nombre, "Mouse Logitech")

    def test_eliminar_producto(self):
        producto_id = self.producto.id

        resultado = ProductoDAO.eliminar_producto(producto_id)

        self.assertTrue(resultado)
        self.assertFalse(
            type(self.producto).objects.filter(id=producto_id).exists()
        )